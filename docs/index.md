# style-audit

`style-audit` is a Python writing-style linter. It combines conservative, local text rules with optional editorial judgments through LiteLLM. It reports reviewable patterns. It does not rewrite drafts, score authorship, or claim that a person or model wrote a document.

## Start here

- [Install and use in a new Python/uv project](installation.md#use-in-a-new-pythonuv-project)
  — development dependency, `pyproject.toml`, first scan, optional LLM review, and CI.
  The same page covers [working from the tool's checkout](installation.md#install-from-a-checkout).
- [CLI and output reference](reference/cli.md)
- [Project configuration](configuration.md)
- [Rulesets and rule cards](reference/rules.md) — one page per ruleset, generated from the runtime registry.
- [LLM review and privacy](llm.md)
- [Dogfooding documentation and docstrings](dogfooding.md)

## Design

Deterministic rules handle narrow patterns with observable text boundaries. Context-dependent patterns use an LLM judge only after an explicit opt-in. A diagnostic includes source evidence and a location. A remote-provider or malformed-response error is never reported as a clean audit.

The `NAS` rules adapt [Peter Yang's `no-ai-slop`](https://github.com/petergyang/no-ai-slop), pinned to commit [`000650b`](https://github.com/petergyang/no-ai-slop/commit/000650b156983f5159695b441477f4e63b25dc85). Its MIT license notice is included at [`third_party/no-ai-slop-LICENSE`](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/LICENSE) and in this repository's `third_party/no-ai-slop-LICENSE`.

The independent `RDL` [readability ruleset](reference/readability.md) adapts Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald's [“Why is AI-generated language so hard to understand?”](https://arxiv.org/html/2610.29162v1), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It uses sentence-scoped LLM judgments rather than reproducing the paper's corpus measurements.

The `STE` [Simplified Technical English ruleset](reference/technical-english.md) covers all 53 writing rules and eight general recommendations in ASD-STE100 Issue 9 Part 1. The full supplied PDF also contains Part 2's controlled dictionary, but the checker does not parse its entries or certify vocabulary compliance. `STE606` and `STE801` are local checks; other rules use optional LLM review.

## Build or preview this site

```sh
uv sync --group docs
uv run --group docs mkdocs serve
```

See [contributing](contributing.md) for the full test and strict-build commands.
