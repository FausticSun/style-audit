"""Text documents retain Unicode character offsets for diagnostics."""

from bisect import bisect_right
from dataclasses import dataclass, field
import re
from functools import cached_property

from .models import RuleScope

_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(`+)[^`\n]*`+")
_QUOTES = re.compile(r'"[^"\n]*"|“[^”\n]*”|‘[^’\n]*’|(?<!\w)\'[^\'\n]+\'(?!\w)')
_ATX_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+[^\n]*|[ \t]*)(?:\n|$)", re.MULTILINE)
_SETEXT_HEADING = re.compile(r"^ {0,3}\S[^\n]*\n {0,3}(?:=+|-+)[ \t\r]*(?:\n|$)", re.MULTILINE)
_LIST_ITEM = re.compile(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+", re.MULTILINE)
_BLANK_LINE = re.compile(r"\n[ \t\r]*\n")
_SENTENCE_END = re.compile(r"[.!?]+[)\]\"'”’]*(?=\s|$)")
_PRECEDING_WORD = re.compile(r"([A-Za-z]+(?:\.[A-Za-z]+)*)$")
_ABBREVIATIONS = frozenset({"dr", "mr", "mrs", "ms", "prof", "sr", "jr", "st", "vs", "etc", "fig", "eq", "no"})


def _mask_span(chars: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if chars[index] not in "\r\n":
            chars[index] = " "


@dataclass(frozen=True)
class TextUnit:
    """One logical audit target, using original exclusive-end character offsets."""

    scope: RuleScope
    start: int
    end: int


@dataclass(frozen=True)
class SourceMap:
    """Map decoded prose characters to their original Python source spans."""

    source_text: str
    line_starts: tuple[int, ...]
    spans: tuple[tuple[int, int], ...]

    def offsets(self, start: int, end: int) -> tuple[int, int]:
        if start == end:
            if start < len(self.spans):
                offset = self.spans[start][0]
            elif self.spans:
                offset = self.spans[-1][1]
            else:
                offset = 0
            return offset, offset
        return self.spans[start][0], self.spans[end - 1][1]

    def position(self, offset: int) -> tuple[int, int]:
        line_index = bisect_right(self.line_starts, offset) - 1
        return line_index + 1, offset - self.line_starts[line_index] + 1


@dataclass(frozen=True)
class TextDocument:
    path: str
    text: str
    mask_spans: tuple[tuple[int, int], ...] = field(default=(), repr=False)
    paragraph_breaks: tuple[int, ...] = field(default=(), repr=False)
    section_breaks: tuple[int, ...] = field(default=(), repr=False)
    source_map: SourceMap | None = field(default=None, repr=False)
    line_starts: tuple[int, ...] = field(init=False, repr=False)
    visible_text: str = field(init=False, repr=False)
    _code_blocks: tuple[tuple[int, int], ...] = field(init=False, repr=False)
    _quote_sentence_ends: tuple[int, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.source_map is not None and len(self.source_map.spans) != len(self.text):
            raise ValueError("source map length does not match document text")
        if any(not 0 <= start <= end <= len(self.text) for start, end in self.mask_spans):
            raise ValueError("mask span is outside the document")
        if any(not 0 <= boundary <= len(self.text) for boundary in (*self.paragraph_breaks, *self.section_breaks)):
            raise ValueError("logical boundary is outside the document")
        starts = (0, *(index + 1 for index, char in enumerate(self.text) if char == "\n"))
        object.__setattr__(self, "line_starts", starts)
        chars = list(self.text)
        for start, end in self.mask_spans:
            _mask_span(chars, start, end)
        open_fence: str | None = None
        code_blocks: list[tuple[int, int]] = []
        fence_start = 0
        for match in re.finditer(r".*(?:\n|$)", self.text):
            if match.start() == match.end():
                continue
            line = match.group()
            fence = _FENCE.match(line)
            if open_fence is not None:
                _mask_span(chars, match.start(), match.end())
                if fence is not None:
                    marker = fence.group(1)
                    if marker[0] == open_fence[0] and len(marker) >= len(open_fence) and not line[fence.end():].strip():
                        code_blocks.append((fence_start, match.end()))
                        open_fence = None
            elif fence is not None:
                open_fence = fence.group(1)
                fence_start = match.start()
                _mask_span(chars, match.start(), match.end())
        if open_fence is not None:
            code_blocks.append((fence_start, len(self.text)))
        object.__setattr__(self, "_code_blocks", tuple(code_blocks))
        fenced_text = "".join(chars)
        for match in _INLINE_CODE.finditer(fenced_text):
            _mask_span(chars, match.start(), match.end())
        code_masked_text = "".join(chars)
        quote_sentence_ends: list[int] = []
        for match in _QUOTES.finditer(code_masked_text):
            stop = match.end()
            cursor = stop
            while cursor < len(code_masked_text) and code_masked_text[cursor].isspace():
                cursor += 1
            if code_masked_text[stop - 2] in ".!?" and (cursor == len(code_masked_text) or code_masked_text[cursor].isupper()):
                quote_sentence_ends.append(stop)
            _mask_span(chars, match.start(), match.end())
        object.__setattr__(self, "visible_text", "".join(chars))
        object.__setattr__(self, "_quote_sentence_ends", tuple(quote_sentence_ends))

    @cached_property
    def heading_spans(self) -> tuple[tuple[int, int], ...]:
        """Markdown ATX and Setext headings outside code and quotation masks."""
        headings = {match.start(): match.end() for match in _ATX_HEADING.finditer(self.visible_text)}
        for match in _SETEXT_HEADING.finditer(self.visible_text):
            if match.start() not in headings:
                headings[match.start()] = match.end()
        return tuple(sorted(headings.items()))

    def _trim_span(self, start: int, end: int) -> tuple[int, int] | None:
        while start < end and self.text[start].isspace():
            start += 1
        while end > start and self.text[end - 1].isspace():
            end -= 1
        if start == end or not self.visible_text[start:end].strip():
            return None
        return start, end

    @cached_property
    def _section_spans(self) -> tuple[tuple[int, int], ...]:
        boundaries = sorted({0, len(self.text), *self.section_breaks, *(start for start, _ in self.heading_spans)})
        return tuple(span for start, end in zip(boundaries, boundaries[1:])
                     if (span := self._trim_span(start, end)) is not None)

    @cached_property
    def _paragraph_spans(self) -> tuple[tuple[int, int], ...]:
        # Use original blank lines: a fully masked quotation is not a paragraph break.
        boundaries = {0, len(self.text), *self.paragraph_breaks}
        for start, end in (*self.heading_spans, *self._code_blocks):
            boundaries.update((start, end))
        boundaries.update(match.start() for match in _LIST_ITEM.finditer(self.visible_text))
        cuts = sorted(boundaries)
        spans: list[tuple[int, int]] = []
        for start, end in zip(cuts, cuts[1:]):
            cursor = start
            for separator in _BLANK_LINE.finditer(self.text, start, end):
                if (span := self._trim_span(cursor, separator.start())) is not None:
                    spans.append(span)
                cursor = separator.end()
            if (span := self._trim_span(cursor, end)) is not None:
                spans.append(span)
        return tuple(spans)

    @cached_property
    def _sentence_spans(self) -> tuple[tuple[int, int], ...]:
        spans: list[tuple[int, int]] = []
        for start, end in self._paragraph_spans:
            text = self.visible_text[start:end]
            stops: list[int] = []
            for ending in _SENTENCE_END.finditer(text):
                if ending.group().startswith(".") and not ending.group().startswith(".."):
                    word_match = _PRECEDING_WORD.search(text, 0, ending.start())
                    word = word_match.group().casefold() if word_match else ""
                    if word in _ABBREVIATIONS or (word and all(len(part) == 1 for part in word.split("."))):
                        continue
                stops.append(start + ending.end())
            stops.extend(self._quote_sentence_ends[
                bisect_right(self._quote_sentence_ends, start):bisect_right(self._quote_sentence_ends, end)
            ])
            cursor = start
            for stop in sorted(set(stops)):
                if (span := self._trim_span(cursor, stop)) is not None:
                    spans.append(span)
                    cursor = stop
            if (span := self._trim_span(cursor, end)) is not None:
                spans.append(span)
        return tuple(spans)

    def units(self, scope: RuleScope) -> tuple[TextUnit, ...]:
        """Return nonoverlapping logical units. Masks never split a unit into fragments."""
        if scope == "sentence":
            spans = self._sentence_spans
        elif scope == "paragraph":
            spans = self._paragraph_spans
        elif scope == "section":
            spans = self._section_spans
        elif scope == "document":
            span = self._trim_span(0, len(self.text))
            spans = (span,) if span is not None else ()
        else:
            raise ValueError(f"unknown audit scope {scope!r}")
        return tuple(TextUnit(scope, start, end) for start, end in spans)

    def position(self, offset: int) -> tuple[int, int]:
        if not 0 <= offset <= len(self.text):
            raise ValueError("text offset is outside the document")
        if self.source_map is not None:
            source_offset, _ = self.source_map.offsets(offset, offset)
            return self.source_map.position(source_offset)
        line_index = bisect_right(self.line_starts, offset) - 1
        return line_index + 1, offset - self.line_starts[line_index] + 1

    def span(self, start: int, end: int) -> tuple[int, int, int, int]:
        if not 0 <= start <= end <= len(self.text):
            raise ValueError("text span is outside the document")
        if self.source_map is not None:
            source_start, source_end = self.source_map.offsets(start, end)
            return (*self.source_map.position(source_start), *self.source_map.position(source_end))
        line, column = self.position(start)
        end_line, end_column = self.position(end)
        return line, column, end_line, end_column

    def evidence(self, start: int, end: int) -> str:
        """Return original source spelling, including any escapes or literal joins."""
        if self.source_map is None:
            return self.text[start:end]
        source_start, source_end = self.source_map.offsets(start, end)
        return self.source_map.source_text[source_start:source_end]

    def visible_occurrence(self, evidence: str, start: int = 0, end: int | None = None) -> int | None:
        """Return a visible occurrence confined to the requested original source span."""
        if not evidence:
            return None
        stop = len(self.text) if end is None else end
        while (start := self.text.find(evidence, start, stop)) >= 0:
            evidence_end = start + len(evidence)
            if self.visible_text[start:evidence_end] == self.text[start:evidence_end]:
                return start
            start += 1
        return None

