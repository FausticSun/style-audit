"""Render built-in rule-reference pages from the canonical rule registry."""

import argparse
from pathlib import Path
import sys

from style_audit.models import Rule
from style_audit.rules import RULES

_RULESETS = {
    "NAS": ("No AI slop", "reference/no-ai-slop.md"),
    "RDL": ("Readability", "reference/readability.md"),
    "STE": ("Simplified Technical English", "reference/technical-english.md"),
}


def _sample(text: str) -> str:
    """Fence a sample verbatim, including any Markdown it demonstrates."""
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text}\n{fence}"


def _card_sections(
    ruleset: str,
    rules: tuple[Rule, ...],
) -> tuple[tuple[str | None, tuple[Rule, ...]], ...]:
    """Group STE cards by source section; keep other catalogs in one grid."""
    if ruleset != "STE":
        return ((None, rules),)

    sections: dict[int, list[Rule]] = {}
    recommendations: list[Rule] = []
    for rule in rules:
        if rule.code.startswith("STEGR"):
            recommendations.append(rule)
        else:
            section = int(rule.code[3])
            sections.setdefault(section, []).append(rule)

    groups: list[tuple[str, tuple[Rule, ...]]] = []
    for section, section_rules in sorted(sections.items()):
        numbers = tuple(int(rule.code[4:]) for rule in section_rules)
        groups.append((
            f"Rules {section}.{min(numbers)}–{section}.{max(numbers)}",
            tuple(section_rules),
        ))
    if recommendations:
        numbers = tuple(int(rule.code.removeprefix("STEGR")) for rule in recommendations)
        groups.append((
            f"General recommendations (GR-{min(numbers)}–GR-{max(numbers)})",
            tuple(recommendations),
        ))
    return tuple(groups)


def _rule_reference(ruleset: str, *, cards: bool = False) -> str:
    """Render one ruleset. Omit layout markup when auditing its prose."""
    title, _ = _RULESETS[ruleset]
    rules = tuple(rule for rule in RULES if rule.code.startswith(ruleset))
    rows = [] if cards else [f"# {title}", ""]
    rows.extend((
        f"This ruleset contains {len(rules)} {'entries' if ruleset == 'STE' else 'rules'}, rendered from `style_audit.rules.RULES`. Each entry includes its canonical scope and source.",
        "",
        "Before/after pairs illustrate a possible revision in the stated context, not recorded model outcomes or automatic fixes. See [auditing rule prose and raw examples](../dogfooding.md#audit-the-generated-rule-catalog).",
        "",
    ))
    groups = _card_sections(ruleset, rules) if cards else ((None, rules),)
    for section_title, section_rules in groups:
        if cards:
            if section_title is not None:
                rows.extend((f"## {section_title}", ""))
            rows.extend(('<div class="rule-cards" markdown="1">', ""))
        for rule in section_rules:
            if cards:
                rows.extend((f'<article class="rule-card" aria-labelledby="{rule.code.lower()}" markdown="1">', ""))
            heading = f"## `{rule.code}`: {rule.name}"
            if cards:
                heading += f" {{#{rule.code.lower()}}}"
            rows.extend((heading, ""))
            if cards:
                rows.extend(('<div class="rule-card-meta" markdown="1">', ""))
            rows.extend((f"Engine: `{rule.engine}` · Scope: `{rule.scope}`", ""))
            if cards:
                rows.extend(("</div>", ""))
            rows.extend((rule.description, "", f"[Upstream source]({rule.source})", ""))
            for example in rule.examples:
                if cards:
                    rows.extend(('<div class="rule-example" markdown="1">', ""))
                rows.extend((
                    "**Before**", "", _sample(example.before), "",
                    "**After**", "", _sample(example.after), "",
                    example.explanation, "",
                ))
                if cards:
                    rows.extend(("</div>", ""))
            if cards:
                rows.extend(("</article>", ""))
        if cards:
            rows.extend(("</div>", ""))
    return "\n".join(rows)


_START_MARKER = "<!-- generated-rule-cards:start -->"
_END_MARKER = "<!-- generated-rule-cards:end -->"


def _replace_rule_cards(markdown: str, ruleset: str) -> str:
    rendered = _rule_reference(ruleset, cards=True).rstrip()
    has_start = markdown.count(_START_MARKER)
    has_end = markdown.count(_END_MARKER)
    if has_start or has_end:
        if has_start != 1 or has_end != 1:
            raise ValueError(f"{ruleset} page must contain one generated-card start and end marker")
        start = markdown.index(_START_MARKER) + len(_START_MARKER)
        end = markdown.index(_END_MARKER)
        if end < start:
            raise ValueError(f"{ruleset} page has generated-card markers in the wrong order")
        return markdown[:start] + "\n\n" + rendered + "\n\n" + markdown[end:]

    marker = "<!-- rule-cards -->"
    if markdown.count(marker) != 1:
        raise ValueError(f"{ruleset} page must contain one rule-cards marker")
    managed = f"{_START_MARKER}\n\n{rendered}\n\n{_END_MARKER}"
    return markdown.replace(marker, managed)


def _render_rule_pages(*, check: bool) -> tuple[str, ...]:
    docs_root = Path(__file__).resolve().parent
    stale: list[str] = []
    for ruleset, (_, relative_path) in _RULESETS.items():
        path = docs_root / relative_path
        current = path.read_text(encoding="utf-8")
        rendered = _replace_rule_cards(current, ruleset)
        if current == rendered:
            continue
        if check:
            stale.append(relative_path)
        else:
            path.write_text(rendered, encoding="utf-8")
    return tuple(stale)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render or check generated rule-reference cards.")
    parser.add_argument("--check", action="store_true", help="fail if reference pages need regeneration")
    args = parser.parse_args()
    try:
        stale = _render_rule_pages(check=args.check)
    except (OSError, ValueError) as exc:
        print(f"render-rule-cards: error: {exc}", file=sys.stderr)
        return 2
    if stale:
        print("stale rule-reference pages: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
