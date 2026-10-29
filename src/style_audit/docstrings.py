"""Extract Python docstring prose while retaining its original source spelling."""

import ast
from bisect import bisect_right
import inspect
import io
import sys
import tokenize
import unicodedata

from .models import AuditError
from .text import SourceMap, TextDocument


_ESCAPES = {
    "\\": "\\",
    "'": "'",
    '"': '"',
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}


def _normalize_newlines(
    source: str,
) -> tuple[str, range | tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    """Return BOM-free universal-newline text and original source boundaries."""
    bom_length = int(source.startswith("\ufeff"))
    if "\r" not in source:
        normalized = source[bom_length:]
        starts = (0, *(index + 1 for index, char in enumerate(normalized) if char == "\n"))
        original_starts = (0, *(start + bom_length for start in starts[1:])) if bom_length else starts
        return normalized, range(bom_length, len(source) + 1), starts, original_starts

    chars: list[str] = []
    boundaries = [bom_length]
    index = bom_length
    while index < len(source):
        char = source[index]
        index += 1
        if char == "\r":
            if index < len(source) and source[index] == "\n":
                index += 1
            char = "\n"
        chars.append(char)
        boundaries.append(index)
    normalized = "".join(chars)
    starts = (0, *(index + 1 for index, char in enumerate(normalized) if char == "\n"))
    original_starts = (0, *(boundaries[start] for start in starts[1:]))
    return normalized, tuple(boundaries), starts, original_starts


def _ast_offset(source: str, starts: tuple[int, ...], line: int, byte_column: int) -> int:
    """AST columns count UTF-8 bytes. Tokenizer columns count Unicode characters."""
    start = starts[line - 1]
    end = starts[line] if line < len(starts) else len(source)
    prefix = source[start:end].encode("utf-8")[:byte_column]
    return start + len(prefix.decode("utf-8"))


def _decode_literal(
    spelling: str, start: int, boundaries: range | tuple[int, ...]
) -> tuple[str, list[tuple[int, int]]]:
    """Decode one AST-selected string token, assigning full spans to escapes."""
    quote_start = 0
    while spelling[quote_start] not in "\"'":
        quote_start += 1
    quote = spelling[quote_start]
    quote_length = 3 if spelling.startswith(quote * 3, quote_start) else 1
    content_start = quote_start + quote_length
    content = spelling[content_start:-quote_length]
    raw = "r" in spelling[:quote_start].lower()
    chars: list[str] = []
    spans: list[tuple[int, int]] = []

    def append(value: str, first: int, last: int) -> None:
        chars.append(value)
        span = (boundaries[start + content_start + first], boundaries[start + content_start + last])
        spans.extend([span] * len(value))

    index = 0
    while index < len(content):
        first = index
        char = content[index]
        index += 1
        if raw or char != "\\":
            append(char, first, index)
            continue

        escape = content[index]
        index += 1
        if escape == "\n":
            # An escaped physical newline contributes no decoded character.
            continue
        if escape in _ESCAPES:
            value = _ESCAPES[escape]
        elif escape in "01234567":
            while index < min(first + 4, len(content)) and content[index] in "01234567":
                index += 1
            value = chr(int(content[first + 1:index], 8))
        elif escape in "xuU":
            index += {"x": 2, "u": 4, "U": 8}[escape]
            value = chr(int(content[first + 2:index], 16))
        elif escape == "N":
            end = content.index("}", index + 1)
            value = unicodedata.lookup(content[index + 1:end])
            index = end + 1
        else:
            # Python preserves unrecognized escapes, including their backslash.
            value = "\\" + escape
        append(value, first, index)
    return "".join(chars), spans


def _clean_docstring(
    value: str, spans: list[tuple[int, int]]
) -> tuple[str, tuple[tuple[int, int], ...]]:
    """Apply inspect.cleandoc's tab expansion and trimming to text and spans."""
    chars: list[str] = []
    expanded_spans: list[tuple[int, int]] = []
    column = 0
    for char, span in zip(value, spans, strict=True):
        if char == "\t":
            width = 8 - column % 8
            chars.append(" " * width)
            expanded_spans.extend([span] * width)
            column += width
        else:
            chars.append(char)
            expanded_spans.append(span)
            column = 0 if char in "\r\n" else column + 1
    expanded = "".join(chars)
    lines: list[tuple[int, int]] = []
    start = 0
    for index, char in enumerate(expanded):
        if char == "\n":
            lines.append((start, index))
            start = index + 1
    lines.append((start, len(expanded)))

    margin = sys.maxsize
    for start, end in lines[1:]:
        line = expanded[start:end]
        content_length = len(line.lstrip())
        if content_length:
            margin = min(margin, len(line) - content_length)
    start, end = lines[0]
    lines[0] = (end - len(expanded[start:end].lstrip()), end)
    if margin < sys.maxsize:
        for index in range(1, len(lines)):
            start, end = lines[index]
            lines[index] = (min(start + margin, end), end)
    while lines and lines[-1][0] == lines[-1][1]:
        lines.pop()
    first_line = 0
    while first_line < len(lines) and lines[first_line][0] == lines[first_line][1]:
        first_line += 1

    cleaned: list[str] = []
    cleaned_spans: list[tuple[int, int]] = []
    for index in range(first_line, len(lines)):
        start, end = lines[index]
        cleaned.append(expanded[start:end])
        cleaned_spans.extend(expanded_spans[start:end])
        if index + 1 < len(lines):
            cleaned.append("\n")
            cleaned_spans.append(expanded_spans[end])
    return "".join(cleaned), tuple(cleaned_spans)


def extract_docstrings(path: str, source: str) -> list[TextDocument]:
    """Extract only actual module, class, and function docstrings in source order.

    Input is parsed, never executed. Each document contains decoded prose cleaned
    with `inspect.cleandoc`. Its source map retains escapes, quotes,
    concatenation gaps, indentation, and physical newline spelling for diagnostic
    evidence.
    """
    normalized, boundaries, starts, original_starts = _normalize_newlines(source)
    try:
        tree = ast.parse(normalized, filename=path)
    except SyntaxError as error:
        line = error.lineno
        column = error.offset
        if line == 1 and column:
            column += boundaries[0]
        if line is None:
            offset = max(source.find("\x00"), 0)
            line_index = bisect_right(original_starts, offset) - 1
            line = line_index + 1
            column = offset - original_starts[line_index] + 1
        raise AuditError(f"{path}:{line}:{column or 1}: invalid Python: {error.msg}") from error
    except UnicodeEncodeError as error:
        offset = boundaries[error.start]
        line_index = bisect_right(original_starts, offset) - 1
        column = offset - original_starts[line_index] + 1
        raise AuditError(f"{path}:{line_index + 1}:{column}: invalid Python: {error.reason}") from error

    constants: list[ast.Constant] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.body or not isinstance(node.body[0], ast.Expr):
            continue
        value = node.body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str) and inspect.cleandoc(value.value):
            constants.append(value)
    constants.sort(key=lambda node: (node.lineno, node.col_offset))
    if not constants:
        return []

    limits: list[tuple[int, int]] = []
    for node in constants:
        if node.end_lineno is None or node.end_col_offset is None:
            raise AuditError(f"{path}:{node.lineno}: could not locate Python docstring")
        limits.append((
            _ast_offset(normalized, starts, node.lineno, node.col_offset),
            _ast_offset(normalized, starts, node.end_lineno, node.end_col_offset),
        ))
    pieces: list[list[str]] = [[] for _ in constants]
    character_spans: list[list[tuple[int, int]]] = [[] for _ in constants]
    doc_index = 0
    try:
        for token in tokenize.generate_tokens(io.StringIO(normalized).readline):
            if token.type != tokenize.STRING:
                continue
            token_start = starts[token.start[0] - 1] + token.start[1]
            while doc_index < len(limits) and token_start >= limits[doc_index][1]:
                doc_index += 1
            if doc_index == len(limits):
                break
            token_end = starts[token.end[0] - 1] + token.end[1]
            first, last = limits[doc_index]
            if first <= token_start and token_end <= last:
                value, spans = _decode_literal(token.string, token_start, boundaries)
                pieces[doc_index].append(value)
                character_spans[doc_index].extend(spans)
    except tokenize.TokenError as error:
        message, (line, column) = error.args
        if line == 1:
            column += boundaries[0]
        raise AuditError(f"{path}:{line}:{column + 1}: could not tokenize Python: {message}") from error

    documents: list[TextDocument] = []
    for node, fragments, spans in zip(constants, pieces, character_spans, strict=True):
        decoded = "".join(fragments)
        if decoded != node.value:
            raise AuditError(f"{path}:{node.lineno}: could not map decoded Python docstring")
        cleaned, cleaned_spans = _clean_docstring(decoded, spans)
        if cleaned != inspect.cleandoc(node.value):
            raise AuditError(f"{path}:{node.lineno}: could not map cleaned Python docstring")
        source_map = SourceMap(source_text=source, line_starts=original_starts, spans=cleaned_spans)
        documents.append(TextDocument(path=path, text=cleaned, source_map=source_map))
    return documents
