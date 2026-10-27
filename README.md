# style-audit

A Python writing-style linter for Markdown, reStructuredText, and plain-text files. It combines conservative deterministic checks with optional editorial judgments through [LiteLLM](https://docs.litellm.ai/). It reports patterns to review; it does not rewrite prose, score authorship, or claim that text was written by AI.

## Install and run

Requires Python 3.14 or newer. Follow the [new Python/uv project walkthrough](docs/installation.md#use-in-a-new-pythonuv-project) to add the tool as a development dependency, configure `pyproject.toml`, and run local or optional LLM checks. To work on this repository's checkout with [uv](https://docs.astral.sh/uv/):

```sh
uv sync
uv run style-audit README.md
```

## Documentation

The full user and developer guide starts at [docs/index.md](docs/index.md). It covers installation, CLI behavior, `pyproject.toml`, the generated rule reference, LiteLLM privacy, and contribution workflows. The runtime rule catalog in `src/style_audit/rules.py` is the source of truth.

The [dogfooding guide](docs/dogfooding.md) documents auditing this README, source documentation, and generated rule descriptions with the installed tool.

Preview the MkDocs site locally:

```sh
uv sync --group docs
uv run --group docs mkdocs serve
```

Without paths, `style-audit` scans the current directory for `.md`, `.markdown`, `.rst`, and `.txt` files, excluding `.git`, virtual environments, build output, and Python caches. Explicit paths may name any UTF-8 text file. Pass `-` to audit standard input:

```sh
style-audit notes.md
cat draft.txt | style-audit -
style-audit docs/ --format json
```

Exit codes: `0` no findings, `1` findings reported, `2` configuration, input, or provider error. Text diagnostics include file, line, column, rule ID, evidence, and an optional suggestion. JSON output is a versioned object with the same finding fields. Operational errors are written to stderr.

## Rules and configuration

Rule metadata lives in `src/style_audit/rules.py`. MkDocs renders [one reference page per ruleset](docs/reference/rules.md), with each rule's metadata, before/after examples, and contextual explanation together in a card. Cards use one column on mobile and two on wider browsers. The [dogfooding workflow](docs/dogfooding.md#audit-the-generated-rule-catalog) audits each ruleset's generated prose and explains how to exercise raw examples separately. `NAS` selects the no-ai-slop rules; `RDL` selects the paper-backed readability rules. Every rule has a canonical sentence, paragraph, section, or document scope, with no configuration override. Local checks run without a provider. Context-dependent rules use LiteLLM only when explicitly enabled.

Minimal project configuration:

```toml
[tool.style-audit]
select = ["NAS001"]
output = "text"
```

See the [configuration guide](docs/configuration.md), [CLI reference](docs/reference/cli.md), and [LLM privacy guide](docs/llm.md) for selection precedence, models, and provider behavior. An LLM opt-in never overrides a deterministic-only selection.

Optional OpenRouter decision review uses an explicit model and `OPENROUTER_API_KEY` in the environment:

```sh
style-audit draft.md --select NAS106 --model microsoft/microsoft-decision-1 --threshold 0.8
```

Readability review uses the same provider contract:

```sh
style-audit draft.md --select RDL --model microsoft/microsoft-decision-1 --threshold 0.8
```

The readability rules judge interpretation difficulty in English sentences, not AI authorship or a readability score. They preserve familiar constructions and do not pretend to measure n-gram frequency or dependency statistics without reference data. See the [readability guide](docs/reference/readability.md).

The equivalent model name is `openrouter/microsoft/microsoft-decision-1`. Both decision and chat review group selected LLM rules by their registered scope and make one request per eligible unit in each selected scope, containing only that unit's masked text and matching rules. Probabilities greater than or equal to the threshold produce decision findings anchored to the complete original unit, with no generated fix. The default threshold is `0.8`; `--threshold` overrides `[tool.style-audit.llm].threshold`. Other LiteLLM models, such as `openai/gpt-4o-mini`, use chat-based review with exact visible quotes within the current unit and no probability filtering.

Remote review may incur charges; the selected scopes and their unit counts determine request volume. Masking preserves logical units but is not sensitive-data redaction. The [LLM guide](docs/llm.md) explains segmentation, privacy, validation, and limitations; the [dogfooding guide](docs/dogfooding.md) separates historical pre-scope observations, including an authentication failure, from current review evidence.


## Source and attribution

The initial rule inventory adapts the editorial guidance in [Peter Yang's `no-ai-slop`](https://github.com/petergyang/no-ai-slop), pinned to commit [`000650b`](https://github.com/petergyang/no-ai-slop/commit/000650b156983f5159695b441477f4e63b25dc85). The upstream project is MIT-licensed; its required license notice is in [`third_party/no-ai-slop-LICENSE`](third_party/no-ai-slop-LICENSE). Style-audit's conservative deterministic findings implement only literal, source-backed checks; contextual guidance is kept in LLM judgments rather than brittle word bans.

The `RDL` rules adapt Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald's [“Why is AI-generated language so hard to understand?”](https://arxiv.org/html/2610.29162v1), arXiv:2610.29162v1 (21 October 2026), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The adaptation uses contextual lint judgments rather than reproducing the paper's corpus measurements.
