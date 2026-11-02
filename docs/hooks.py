"""Render the rule reference from the package's canonical rule registry."""

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


def on_page_markdown(markdown: str, *, page, **kwargs) -> str:
    """Insert rule cards into the corresponding ruleset's source page."""
    for ruleset, (_, path) in _RULESETS.items():
        if page.file.src_uri == path:
            return markdown.replace("<!-- rule-cards -->", _rule_reference(ruleset, cards=True))
    return markdown
