"""Conservative deterministic checks for explicit source rules."""

import re

from .models import Diagnostic, Rule
from .rules import RULES
from .text import TextDocument

_BANNED_TERMS = (
    "delve",
    "foster",
    "leverage",
    "utilize",
    "facilitate",
    "empower",
    "streamline",
    "robust",
    "cutting-edge",
    "paradigm shift",
    "game changer",
    "this is huge",
    "this changes everything",
    "tapestry",
    "realm",
    "beacon",
    "multifaceted",
    "meticulous",
    "intricate",
    "paramount",
    "transformative",
    "elevate",
    "embark",
    "supercharge",
    "harness",
    "ever-evolving",
)

_BANNED_PATTERN = re.compile(
    r"(?<!\w)(?:" + "|".join(re.escape(term) for term in _BANNED_TERMS) + r")(?!\w)",
    re.IGNORECASE,
)
_EMOJI = re.compile(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]")
_INFLATED_VERB = re.compile(r"(?<!\w)(?:serves as|made a decision|has the ability to)(?!\w)", re.IGNORECASE)
_SEMICOLON = re.compile(r";")
_TABLE_SEPARATOR_CELL = re.compile(r":?-{3,}:?\Z")


def _term_pattern(terms: tuple[str, ...]) -> re.Pattern[str]:
    if not terms:
        return re.compile(r"(?!)")
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(term) for term in terms) + r")(?!\w)", re.IGNORECASE)

def _is_markdown_table(text: str) -> bool:
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    if len(rows) < 2 or any("|" not in row for row in rows):
        return False
    columns = [cell.strip() for cell in rows[1].strip("|").split("|")]
    if not columns or not all(_TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in columns):
        return False
    return all(len(row.strip("|").split("|")) == len(columns) for row in rows)


def analyze_deterministic(
    document: TextDocument,
    rules: tuple[Rule, ...] | None = None,
    *,
    nas_allowed_words: tuple[str, ...] = (),
    nas_disallowed_words: tuple[str, ...] = (),
    ste_disallowed_words: tuple[str, ...] = (),
) -> list[Diagnostic]:
    selected = rules if rules is not None else tuple(rule for rule in RULES if rule.engine == "deterministic")
    allowed = {word.casefold() for word in nas_allowed_words}
    nas_terms = tuple(term for term in _BANNED_TERMS if term.casefold() not in allowed) + nas_disallowed_words
    nas_pattern = _BANNED_PATTERN if not nas_allowed_words and not nas_disallowed_words else _term_pattern(nas_terms)
    checks = {
        "NAS001": (
            nas_pattern,
            "Avoid the explicitly discouraged term {evidence!r}.",
            "Replace it with a direct, concrete word that fits the intended meaning.",
        ),
        "NAS003": (
            _INFLATED_VERB,
            "Replace the inflated verb phrase {evidence!r} with a direct verb.",
            "Use a concise verb, such as 'is', 'has', or 'decided', when it preserves the meaning.",
        ),
        "STE801": (
            _SEMICOLON,
            "A semicolon is not permitted in editable STE prose.",
            "Replace the semicolon with punctuation that preserves the intended meaning.",
        ),
    }
    if ste_disallowed_words:
        checks["STE101"] = (
            _term_pattern(ste_disallowed_words),
            "Term {evidence!r} is disallowed by the configured STE vocabulary.",
            "Use an approved term that preserves the intended technical meaning.",
        )
    findings: list[Diagnostic] = []
    for rule in selected:
        if rule.code == "STE101" and not ste_disallowed_words:
            continue
        if rule.code == "STE606":
            sentences = document.units("sentence")
            sentence_index = 0
            for paragraph in document.units(rule.scope):
                if _is_markdown_table(document.visible_text[paragraph.start:paragraph.end]):
                    continue
                while sentence_index < len(sentences) and sentences[sentence_index].end <= paragraph.start:
                    sentence_index += 1
                first_sentence = sentence_index
                while sentence_index < len(sentences) and sentences[sentence_index].start < paragraph.end:
                    sentence_index += 1
                sentence_count = sentence_index - first_sentence
                if sentence_count <= 6:
                    continue
                line, column, end_line, end_column = document.span(paragraph.start, paragraph.end)
                findings.append(Diagnostic(
                    document.path,
                    rule.code,
                    f"Paragraph has {sentence_count} sentences; the maximum is six.",
                    line,
                    column,
                    end_line,
                    end_column,
                    document.evidence(paragraph.start, paragraph.end),
                    "Split the paragraph at a topic boundary without separating related information.",
                ))
            continue
        if rule.code == "NAS002":
            headings = iter(document.heading_spans)
            heading = next(headings, None)
        for unit in document.units(rule.scope):
            if rule.code == "NAS002":
                while heading is not None and heading[0] < unit.end:
                    heading_start, heading_end = heading
                    heading = next(headings, None)
                    emoji = _EMOJI.search(document.visible_text, heading_start, heading_end)
                    if emoji is None or not unit.start <= emoji.start() < unit.end:
                        continue
                    line, column, end_line, end_column = document.span(emoji.start(), emoji.end())
                    findings.append(Diagnostic(
                        document.path, rule.code, "Remove decorative emoji from this heading.",
                        line, column, end_line, end_column, document.evidence(emoji.start(), emoji.end()),
                        "Use a plain heading that reflects the section's content.",
                    ))
                continue
            pattern, message, fix = checks[rule.code]
            for match in pattern.finditer(document.visible_text, unit.start, unit.end):
                line, column, end_line, end_column = document.span(match.start(), match.end())
                findings.append(Diagnostic(
                    document.path, rule.code, message.format(evidence=match.group()),
                    line, column, end_line, end_column, document.evidence(match.start(), match.end()), fix,
                ))
    return sorted(findings, key=lambda item: (item.line, item.column, item.code))
