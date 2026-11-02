"""Extract literal Markdown cells from Marimo Python apps without execution."""

import ast
import inspect
import io
import tokenize

from .docstrings import _ast_offset, _clean_docstring, _decode_literal, _parse_python
from .models import AuditError
from .text import SourceMap, TextDocument


def _token_offset(starts: tuple[int, ...], position: tuple[int, int]) -> int:
    return starts[position[0] - 1] + position[1]


def _node_offsets(
    path: str,
    node: ast.AST,
    normalized: str,
    starts: tuple[int, ...],
    label: str,
) -> tuple[int, int]:
    line = getattr(node, "lineno", None)
    column = getattr(node, "col_offset", None)
    end_line = getattr(node, "end_lineno", None)
    end_column = getattr(node, "end_col_offset", None)
    if line is None or column is None or end_line is None or end_column is None:
        raise AuditError(f"{path}: could not locate Marimo {label}")
    return (
        _ast_offset(normalized, starts, line, column),
        _ast_offset(normalized, starts, end_line, end_column),
    )


def _python_tokens(
    path: str,
    normalized: str,
    boundaries: range | tuple[int, ...],
) -> tuple[tokenize.TokenInfo, ...]:
    try:
        return tuple(tokenize.generate_tokens(io.StringIO(normalized).readline))
    except tokenize.TokenError as error:
        message, (line, column) = error.args
        if line == 1:
            column += boundaries[0]
        raise AuditError(f"{path}:{line}:{column + 1}: could not tokenize Python: {message}") from error


def _bindings(tree: ast.Module) -> tuple[set[str], set[str], set[str]]:
    marimo_modules: set[str] = set()
    markdown_functions: set[str] = set()
    app_classes: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            marimo_modules.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name == "marimo"
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "marimo":
            for alias in node.names:
                binding = alias.asname or alias.name
                if alias.name == "md":
                    markdown_functions.add(binding)
                elif alias.name == "App":
                    app_classes.add(binding)
    return marimo_modules, markdown_functions, app_classes


def _is_marimo_app(
    tree: ast.Module,
    marimo_modules: set[str],
    app_classes: set[str],
) -> bool:
    return any(
        isinstance(node, ast.Call)
        and (
            isinstance(node.func, ast.Name) and node.func.id in app_classes
            or isinstance(node.func, ast.Attribute)
            and node.func.attr == "App"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in marimo_modules
        )
        for node in ast.walk(tree)
    )


def _markdown_argument(call: ast.Call) -> ast.expr | None:
    if call.args:
        return call.args[0]
    return next((keyword.value for keyword in call.keywords if keyword.arg == "text"), None)


def _is_markdown_call(
    call: ast.Call,
    marimo_modules: set[str],
    markdown_functions: set[str],
) -> bool:
    if isinstance(call.func, ast.Name):
        return call.func.id in markdown_functions
    return (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "md"
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id in marimo_modules
    )


def _decode_constant(
    path: str,
    node: ast.Constant,
    normalized: str,
    boundaries: range | tuple[int, ...],
    starts: tuple[int, ...],
    tokens: tuple[tokenize.TokenInfo, ...],
) -> tuple[str, list[tuple[int, int]]]:
    first, last = _node_offsets(path, node, normalized, starts, "Markdown string")
    pieces: list[str] = []
    spans: list[tuple[int, int]] = []
    for token in tokens:
        if token.type != tokenize.STRING:
            continue
        token_start = _token_offset(starts, token.start)
        if token_start < first:
            continue
        if token_start >= last:
            break
        token_end = _token_offset(starts, token.end)
        if first <= token_start and token_end <= last:
            value, token_spans = _decode_literal(token.string, token_start, boundaries)
            pieces.append(value)
            spans.extend(token_spans)
    decoded = "".join(pieces)
    if decoded != node.value:
        raise AuditError(f"{path}:{node.lineno}: could not map Marimo Markdown string")
    return decoded, spans


def _fstring_ranges(
    path: str,
    tokens: tuple[tokenize.TokenInfo, ...],
    starts: tuple[int, ...],
) -> tuple[tuple[int, int, bool], ...]:
    start_type = getattr(tokenize, "FSTRING_START", None)
    end_type = getattr(tokenize, "FSTRING_END", None)
    if start_type is None or end_type is None:
        return ()
    stack: list[tuple[int, bool]] = []
    ranges: list[tuple[int, int, bool]] = []
    for token in tokens:
        if token.type == start_type:
            quote = min(
                (index for index in (token.string.find("'"), token.string.find('"')) if index >= 0),
                default=len(token.string),
            )
            raw = "r" in token.string[:quote].casefold()
            stack.append((_token_offset(starts, token.start), raw))
        elif token.type == end_type and stack:
            first, raw = stack.pop()
            ranges.append((first, _token_offset(starts, token.end), raw))
    return tuple(ranges)


def _decode_fstring_fragment(
    path: str,
    node: ast.Constant,
    normalized: str,
    boundaries: range | tuple[int, ...],
    starts: tuple[int, ...],
    ranges: tuple[tuple[int, int, bool], ...],
) -> tuple[str, list[tuple[int, int]]]:
    first, last = _node_offsets(path, node, normalized, starts, "f-string fragment")
    containing = [item for item in ranges if item[0] <= first and last <= item[1]]
    if not containing:
        raise AuditError(f"{path}:{node.lineno}: could not locate Marimo Markdown f-string")
    raw = min(containing, key=lambda item: item[1] - item[0])[2]
    prefix = "r" if raw else ""
    spelling = f'{prefix}"{normalized[first:last]}"'
    decoded, source_spans = _decode_literal(
        spelling,
        first - len(prefix) - 1,
        boundaries,
    )
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(decoded):
        char = decoded[index]
        if char in "{}" and index + 1 < len(decoded) and decoded[index + 1] == char:
            chars.append(char)
            spans.append((source_spans[index][0], source_spans[index + 1][1]))
            index += 2
        else:
            chars.append(char)
            spans.append(source_spans[index])
            index += 1
    value = "".join(chars)
    if value != node.value:
        raise AuditError(f"{path}:{node.lineno}: could not map Marimo Markdown f-string")
    return value, spans


def _decode_joined_string(
    path: str,
    node: ast.JoinedStr,
    normalized: str,
    boundaries: range | tuple[int, ...],
    starts: tuple[int, ...],
    tokens: tuple[tokenize.TokenInfo, ...],
    ranges: tuple[tuple[int, int, bool], ...],
) -> tuple[str, list[tuple[int, int]]]:
    pieces: list[str] = []
    spans: list[tuple[int, int]] = []
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            first, last = _node_offsets(path, part, normalized, starts, "f-string fragment")
            if first == last and not part.value:
                continue
            if any(start <= first and last <= end for start, end, _ in ranges):
                value, part_spans = _decode_fstring_fragment(
                    path, part, normalized, boundaries, starts, ranges
                )
            else:
                value, part_spans = _decode_constant(
                    path, part, normalized, boundaries, starts, tokens
                )
            pieces.append(value)
            spans.extend(part_spans)
        elif isinstance(part, ast.FormattedValue):
            first, last = _node_offsets(path, part, normalized, starts, "interpolation")
            pieces.append("".join("\n" if char == "\n" else " " for char in normalized[first:last]))
            spans.extend((boundaries[index], boundaries[index + 1]) for index in range(first, last))
        else:
            raise AuditError(f"{path}:{getattr(part, 'lineno', 1)}: unsupported Marimo Markdown f-string part")
    return "".join(pieces), spans


def _document(
    path: str,
    value: str,
    spans: list[tuple[int, int]],
    source: str,
    original_starts: tuple[int, ...],
    line: int,
) -> TextDocument | None:
    cleaned, cleaned_spans = _clean_docstring(value, spans)
    if cleaned != inspect.cleandoc(value):
        raise AuditError(f"{path}:{line}: could not map cleaned Marimo Markdown")
    if not cleaned.strip():
        return None
    return TextDocument(
        path=path,
        text=cleaned,
        source_map=SourceMap(source_text=source, line_starts=original_starts, spans=cleaned_spans),
    )


def extract_markdown_cells(path: str, source: str) -> list[TextDocument] | None:
    """Extract literal ``marimo.md``/``mo.md`` cell text from a Marimo app.

    Python is parsed but never imported or executed. F-string expressions and
    nonliteral arguments are omitted; only their static Markdown fragments are
    eligible for auditing.
    """
    normalized, boundaries, starts, original_starts, tree = _parse_python(path, source)
    marimo_modules, markdown_functions, app_classes = _bindings(tree)
    if not _is_marimo_app(tree, marimo_modules, app_classes):
        return None

    tokens = _python_tokens(path, normalized, boundaries)
    ranges = _fstring_ranges(path, tokens, starts)
    calls = sorted(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _is_markdown_call(node, marimo_modules, markdown_functions)
        ),
        key=lambda node: (node.lineno, node.col_offset),
    )
    documents: list[TextDocument] = []
    for call in calls:
        argument = _markdown_argument(call)
        if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
            value, spans = _decode_constant(
                path, argument, normalized, boundaries, starts, tokens
            )
        elif isinstance(argument, ast.JoinedStr):
            value, spans = _decode_joined_string(
                path, argument, normalized, boundaries, starts, tokens, ranges
            )
        else:
            continue
        line = getattr(argument, "lineno", call.lineno)
        document = _document(path, value, spans, source, original_starts, line)
        if document is not None:
            documents.append(document)
    return documents
