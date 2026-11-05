# style-audit

`style-audit` is a Python writing-style linter. It combines conservative, local text rules with default LLM judgments for the no-ai-slop and readability rulesets. It reports reviewable patterns. It does not rewrite drafts, score authorship, or claim that a person or model wrote a document.

## Start here

- [Install and use in a new Python/uv project](installation.md#use-in-a-new-pythonuv-project)
  — development dependency, `pyproject.toml`, first scan, default LLM review, privacy, and CI.
  The same page covers [working from the tool's checkout](installation.md#install-from-a-checkout).
- [CLI and output reference](reference/cli.md)
- [Project configuration](configuration.md)
- [Rulesets and rule cards](reference/rules.md) — one page per ruleset, generated from the runtime registry.
- [LLM review and privacy](llm.md)
- [Dogfooding documentation and docstrings](dogfooding.md)

## Design

Without a configured global or matching per-file selection, the CLI runs the complete `NAS` no-ai-slop and `RDL` readability rulesets on supported inputs. Context-dependent rules use an LLM judge by default; set `llm.enabled = false` or select deterministic-only rules to keep text local. A diagnostic includes source evidence and a location. A remote-provider or malformed-response error is never reported as a clean audit.

The `NAS` rules adapt [Peter Yang's `no-ai-slop`](https://github.com/petergyang/no-ai-slop), pinned to commit [`000650b`](https://github.com/petergyang/no-ai-slop/commit/000650b156983f5159695b441477f4e63b25dc85). Its MIT license notice is included at [`third_party/no-ai-slop-LICENSE`](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/LICENSE) and in this repository's `third_party/no-ai-slop-LICENSE`.

The independent `RDL` [readability ruleset](reference/readability.md) adapts Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald's [“Why is AI-generated language so hard to understand?”](https://arxiv.org/html/2610.29162v1), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). It uses sentence-scoped LLM judgments rather than reproducing the paper's corpus measurements.

The `STE` [Simplified Technical English ruleset](reference/technical-english.md) covers all 53 writing rules and eight general recommendations in ASD-STE100 Issue 9 Part 1. The full supplied PDF also contains Part 2's controlled dictionary, but the checker does not parse its entries or certify vocabulary compliance. `STE606` and `STE801` are local checks; other rules use LLM review when selected.

The `MWG` [Microsoft Writing Style ruleset](reference/microsoft-writing.md) adapts broadly applicable editorial principles from Microsoft's guide. It uses original summaries and examples, omits Microsoft-specific products, terminology, and UI instructions, and uses LLM review when selected.

## Build or preview this site

```sh
uv sync --group docs
uv run --group docs zensical serve
```

See [contributing](contributing.md) for the full test and strict-build commands.
