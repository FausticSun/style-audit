"""Extract prose and logical units from English Gherkin feature files."""

import re

from .text import TextDocument

_HEADER = re.compile(r"^[ \t]*(?P<keyword>Feature|Rule|Background|Scenario(?: Outline)?|Examples)[ \t]*:[ \t]*")
_STEP = re.compile(r"^[ \t]*(?:(?:Given|When|Then|And|But)[ \t]+|\*[ \t]+)")


def document_from_feature(path: str, source: str) -> TextDocument:
    """Mask Gherkin syntax and fixtures while preserving source positions and step boundaries."""
    masks: list[tuple[int, int]] = []
    paragraph_breaks: list[int] = []
    section_breaks: list[int] = []
    docstring_marker: str | None = None
    offset = 0

    for line in source.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        stripped = content.lstrip(" \t")
        line_end = offset + len(line)

        if docstring_marker is not None:
            masks.append((offset, line_end))
            if stripped == docstring_marker:
                docstring_marker = None
            offset = line_end
            continue

        if stripped.startswith(('"""', "'''", "```")):
            docstring_marker = stripped[:3]
            masks.append((offset, line_end))
        elif not stripped or stripped.startswith(("@", "#", "|")):
            if stripped:
                masks.append((offset, line_end))
        elif match := _HEADER.match(content):
            masks.append((offset, offset + match.end()))
            paragraph_breaks.append(offset)
            section_breaks.append(offset)
        elif match := _STEP.match(content):
            masks.append((offset, offset + match.end()))
            paragraph_breaks.append(offset)

        offset = line_end

    return TextDocument(
        path,
        source,
        mask_spans=tuple(masks),
        paragraph_breaks=tuple(paragraph_breaks),
        section_breaks=tuple(section_breaks),
    )
