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


def analyze_deterministic(document: TextDocument, rules: tuple[Rule, ...] | None = None) -> list[Diagnostic]:
    selected = rules if rules is not None else tuple(rule for rule in RULES if rule.engine == "deterministic")
    checks = {
        "NAS001": (
            _BANNED_PATTERN,
            "Avoid the explicitly discouraged term {evidence!r}.",
            "Replace it with a direct, concrete word that fits the intended meaning.",
        ),
        "NAS003": (
            _INFLATED_VERB,
            "Replace the inflated verb phrase {evidence!r} with a direct verb.",
            "Use a concise verb, such as 'is', 'has', or 'decided', when it preserves the meaning.",
        ),
    }
    findings: list[Diagnostic] = []
    for rule in selected:
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
                        line, column, end_line, end_column, document.text[emoji.start():emoji.end()],
                        "Use a plain heading that reflects the section's content.",
                    ))
                continue
            pattern, message, fix = checks[rule.code]
            for match in pattern.finditer(document.visible_text, unit.start, unit.end):
                line, column, end_line, end_column = document.span(match.start(), match.end())
                findings.append(Diagnostic(
                    document.path, rule.code, message.format(evidence=match.group()),
                    line, column, end_line, end_column, document.text[match.start():match.end()], fix,
                ))
    return sorted(findings, key=lambda item: (item.line, item.column, item.code))
