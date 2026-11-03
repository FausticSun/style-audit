# Rulesets

Choose a ruleset to browse its rule cards. Every card contains the rule's ID, name, engine, canonical scope, description, upstream source, before/after examples, and contextual explanation.

- [No AI slop (`NAS`)](no-ai-slop.md): local text patterns and optional editorial judgments adapted from Peter Yang's guidance.
- [Readability (`RDL`)](readability.md): sentence-scoped LLM judgments about interpretation difficulty, adapted from Clark, Martin, and Mahowald's paper.
- [Simplified Technical English (`STE`)](technical-english.md): original summaries and examples for all 53 Part 1 writing rules and eight general recommendations in ASD-STE100 Issue 9. Part 2 is a controlled dictionary, not additional writing rules; the checker does not parse its entries.

Scope is required rule metadata, with no CLI or configuration override. See [segmentation and scoped requests](../llm.md#canonical-scopes-and-segmentation). The cards are rendered from `style_audit.rules.RULES`, loaded from the packaged per-ruleset YAML files under `src/style_audit/rules/`. Do not maintain another copy of rule metadata.

Use the [generated-rule audit](../dogfooding.md#audit-the-generated-rule-catalog) to check each ruleset's prose. Exercise raw examples separately because intentional samples are masked during documentation audits.

## Selecting rulesets

`NAS00` runs only local no-ai-slop checks. `STE606` checks the six-sentence maximum in prose paragraphs and skips Markdown tables. `STE801` flags semicolons in editable prose, including table cells. Other `STE` rules use contextual LLM judgments and require an explicit model. See [LLM review and privacy](../llm.md) and the [STE source limitations](technical-english.md#source-and-limitations).

```sh
style-audit draft.md --select NAS00
style-audit draft.md --select STE606,STE801
style-audit draft.md --select STE --model openai/gpt-4o-mini
```

See [selection and ignoring](../configuration.md#selection-ignoring-and-llm-opt-in) for exact IDs, prefixes, rule globs, and CLI precedence. [Per-file rule selection](../configuration.md#per-file-rule-selection) maps file patterns to rulesets in `pyproject.toml`.

