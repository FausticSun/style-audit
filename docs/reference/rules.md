# Rulesets

Choose a ruleset to browse its rule cards. Every card contains the rule's ID, name, engine, canonical scope, description, upstream source, before/after examples, and contextual explanation.

- [No AI slop (`NAS`)](no-ai-slop.md): local text patterns and optional editorial judgments adapted from Peter Yang's guidance.
- [Readability (`RDL`)](readability.md): sentence-scoped LLM judgments about interpretation difficulty, adapted from Clark, Martin, and Mahowald's paper.

Scope is required rule metadata, with no CLI or configuration override. See [segmentation and scoped requests](../llm.md#canonical-scopes-and-segmentation). The cards are generated from `style_audit.rules.RULES`; do not maintain another copy of rule metadata.

Use the [generated-rule audit](../dogfooding.md#audit-the-generated-rule-catalog) to check each ruleset's prose, and exercise raw examples separately; intentional samples are masked during documentation audits.

## Selecting rulesets

`NAS00` runs only local no-ai-slop checks. Selecting an LLM rule requires an explicit model; see [LLM review and privacy](../llm.md).

```sh
style-audit draft.md --select NAS00
style-audit draft.md --select NAS00,RDL --model microsoft/microsoft-decision-1
```

See [selection and ignoring](../configuration.md#selection-ignoring-and-llm-opt-in) for exact IDs, prefixes, and configuration precedence.
