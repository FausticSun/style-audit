"""Deterministic checks driven by the bundled rule catalog."""

import re
from functools import lru_cache

from .models import Diagnostic, RegexDetector, Rule, SentenceCountDetector
from .rules import RULES
from .text import TextDocument

_TABLE_SEPARATOR_CELL = re.compile(r":?-{3,}:?\Z")


def _term_pattern(terms: tuple[str, ...]) -> re.Pattern[str]:
    if not terms:
        return re.compile(r"(?!)")
    alternatives = "|".join(re.escape(term) for term in terms)
    return re.compile(r"(?<!\w)(?:" + alternatives + r")(?!\w)", re.IGNORECASE)


def _is_markdown_table(text: str) -> bool:
    rows = [line.strip() for line in text.splitlines() if line.strip()]
    if len(rows) < 2 or any("|" not in row for row in rows):
        return False
    columns = [cell.strip() for cell in rows[1].strip("|").split("|")]
    if not columns or not all(_TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in columns):
        return False
    return all(len(row.strip("|").split("|")) == len(columns) for row in rows)


def _diagnostic(
    document: TextDocument,
    rule: Rule,
    start: int,
    end: int,
    message: str,
    fix: str,
) -> Diagnostic:
    line, column, end_line, end_column = document.span(start, end)
    return Diagnostic(
        path=document.path,
        code=rule.code,
        message=message,
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        evidence=document.evidence(start, end),
        fix=fix,
    )


def _merge_matches(primary, additional):
    """Merge detector matches with user-supplied terms in source order."""
    ordered = [(match, 0) for match in primary] + [(match, 1) for match in additional]
    ordered.sort(key=lambda item: (item[0].start(), item[1]))
    selected = []
    for match, _ in ordered:
        if selected and match.start() < selected[-1].end():
            continue
        selected.append(match)
    return selected


def _regex_flags(detector: RegexDetector) -> int:
    return re.IGNORECASE if "ignorecase" in detector.flags else 0


@lru_cache(maxsize=64)
def _compile_pattern(pattern: str, flags: int) -> re.Pattern[str]:
    return re.compile(pattern, flags)


def _append_regex_finding(
    findings: list[Diagnostic],
    document: TextDocument,
    rule: Rule,
    detector: RegexDetector,
    match: re.Match[str],
) -> None:
    if match.start() == match.end():
        return
    findings.append(
        _diagnostic(
            document,
            rule,
            match.start(),
            match.end(),
            detector.message.format(evidence=match.group()),
            detector.fix,
        )
    )


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
    findings: list[Diagnostic] = []
    nas_disallowed_pattern = _term_pattern(nas_disallowed_words) if nas_disallowed_words else None
    ste_disallowed_pattern = _term_pattern(ste_disallowed_words) if ste_disallowed_words else None

    for rule in selected:
        if rule.code == "STE101":
            if ste_disallowed_pattern is not None:
                for unit in document.units(rule.scope):
                    for match in ste_disallowed_pattern.finditer(document.visible_text, unit.start, unit.end):
                        findings.append(_diagnostic(
                            document,
                            rule,
                            match.start(),
                            match.end(),
                            f"Term {match.group()!r} is disallowed by the configured STE vocabulary.",
                            "Use an approved term that preserves the intended technical meaning.",
                        ))
            continue
        if rule.engine != "deterministic":
            continue

        detector = rule.detector
        if isinstance(detector, SentenceCountDetector):
            sentences = document.units("sentence")
            sentence_index = 0
            for unit in document.units(rule.scope):
                if detector.skip_markdown_tables and _is_markdown_table(
                    document.visible_text[unit.start:unit.end]
                ):
                    continue
                while sentence_index < len(sentences) and sentences[sentence_index].end <= unit.start:
                    sentence_index += 1
                first_sentence = sentence_index
                while sentence_index < len(sentences) and sentences[sentence_index].start < unit.end:
                    sentence_index += 1
                sentence_count = sentence_index - first_sentence
                if sentence_count <= detector.max_sentences:
                    continue
                findings.append(_diagnostic(
                    document,
                    rule,
                    unit.start,
                    unit.end,
                    f"Paragraph has {sentence_count} sentences; the maximum is {detector.max_sentences}.",
                    "Split the paragraph at a topic boundary without separating related information.",
                ))
            continue

        if not isinstance(detector, RegexDetector):
            continue
        pattern = _compile_pattern(detector.pattern, _regex_flags(detector))
        additional_pattern = _term_pattern(rule.additional_terms) if rule.additional_terms else None
        if detector.target == "heading":
            scope_units = document.units(rule.scope)
            for heading_start, heading_end in document.heading_spans:
                match = pattern.search(document.visible_text, heading_start, heading_end)
                primary = [match] if match is not None else []
                additional = (
                    list(additional_pattern.finditer(document.visible_text, heading_start, heading_end))
                    if additional_pattern is not None
                    else []
                )
                matches = _merge_matches(primary, additional) if additional else primary
                for match in matches:
                    if not any(unit.start <= match.start() < unit.end for unit in scope_units):
                        continue
                    _append_regex_finding(findings, document, rule, detector, match)
            continue

        for unit in document.units(rule.scope):
            primary = [
                match
                for match in pattern.finditer(document.visible_text, unit.start, unit.end)
                if rule.code != "NAS001" or match.group().casefold() not in allowed
            ]
            additional = (
                list(additional_pattern.finditer(document.visible_text, unit.start, unit.end))
                if additional_pattern is not None
                else []
            )
            if rule.code == "NAS001" and nas_disallowed_pattern is not None:
                additional.extend(nas_disallowed_pattern.finditer(
                    document.visible_text, unit.start, unit.end
                ))
            matches = _merge_matches(primary, additional) if additional else primary
            for match in matches:
                _append_regex_finding(findings, document, rule, detector, match)

    return sorted(findings, key=lambda item: (item.line, item.column, item.code))
