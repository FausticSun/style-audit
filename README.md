# style-audit

A Python writing-style linter for Markdown, reStructuredText, plain text, Gherkin feature files, Python docstrings, and Marimo Markdown cells. It combines conservative deterministic checks with optional editorial judgments through [LiteLLM](https://docs.litellm.ai/). It reports patterns to review. It does not rewrite prose, score authorship, or claim that text was written by AI.

## Install and run

Requires Python 3.12 or newer. Follow the [new Python/uv project walkthrough](docs/installation.md#use-in-a-new-pythonuv-project) to add the tool as a development dependency, configure `pyproject.toml`, and run local or optional LLM checks. To work on this repository's checkout with [uv](https://docs.astral.sh/uv/):

```sh
uv sync
uv run style-audit README.md
```
Marimo is optional: `uv sync --extra marimo` installs it for running the interactive system-design notebook. Static `.py` extraction does not import or require the Marimo package.

## Documentation

The full user and developer guide starts at [docs/index.md](docs/index.md). It covers installation, CLI behavior, `pyproject.toml`, the generated rule reference, LiteLLM privacy, and contribution workflows. The runtime rule catalog in `src/style_audit/rules.py` is the source of truth.

The [dogfooding guide](docs/dogfooding.md) covers this README, source documentation, generated rule descriptions, Python docstrings, and the Marimo system-design report.

Run the full suite with `uv run --group dev pytest`, or only the Gherkin acceptance scenarios with `uv run --group dev pytest -m bdd -v`. See [behavioral testing](docs/contributing.md#behavioral-acceptance-scenarios) for feature files, step definitions, and isolated provider fixtures.

Preview the MkDocs site locally:

```sh
uv sync --group docs
uv run --group docs mkdocs serve
```

Without paths, `style-audit` scans the current directory for `.md`, `.markdown`, `.rst`, `.txt`, `.feature`, `.py`, and `.pyi` files, excluding `.git`, virtual environments, build output, directories named `site` (including generated documentation output), and Python caches. Ordinary Python inputs audit docstrings; recognized Marimo apps audit literal `mo.md()` cell content. Other explicitly named files are treated as UTF-8 prose. Pass `-` to audit standard input:

```sh
style-audit notes.md
cat draft.txt | style-audit -
style-audit docs/ --format json
```

Exit codes: `0` no findings, `1` findings reported, `2` configuration, input, or provider error. Text diagnostics include file, line, column, rule ID, evidence, and an optional suggestion. JSON output is a versioned object with the same finding fields. Operational errors are written to stderr.

## Python docstrings

Ordinary Python files are parsed, never executed. Module, class, function, async-function, and nested-definition docstrings are audited independently. Comments, assigned strings, later string expressions, bytes, f-strings, and template strings are not docstrings and are excluded. Strings are decoded and cleaned with Python's docstring indentation conventions. Diagnostics retain original file positions and source spelling, including escapes and adjacent literals.

```sh
style-audit src/ tests/ docs/hooks.py --select NAS00 --format json
cat module.py | style-audit - --stdin-filename module.py --select NAS00
```

The stdin name selects Python extraction when it ends in `.py` or `.pyi`: recognized Marimo `.py` apps expose literal Markdown cells, and other Python inputs expose docstrings. Otherwise stdin remains prose. Local checks need no provider. LLM opt-in applies only to extracted prose, never surrounding code or comments. See [Python inputs](docs/reference/cli.md#python-docstrings) and [own-code dogfooding](docs/dogfooding.md#audit-python-docstrings).

### Marimo Markdown cells

Marimo `.py` apps are parsed, not executed. When the source imports Marimo and constructs `App`, direct `mo.md()` string literals become separate audit documents. Literal f-string text is included; interpolation expressions, variable-driven Markdown, widget output, `mo.mermaid()` diagrams, comments, and other Python code are not evaluated or audited. Findings map to original source positions. LLM review can send visible cell prose to the configured provider, so treat it as ordinary remote-audit input.

## Rules and configuration

Rule metadata lives in `src/style_audit/rules.py`, with the source-located ASD-STE100 entries in `src/style_audit/ste_rules.py`. MkDocs renders [one reference page per ruleset](docs/reference/rules.md), with each rule's metadata, examples, and contextual explanation. `NAS` selects no-ai-slop, `RDL` selects the paper-backed readability rules, and `STE` selects all 53 Issue 9 Part 1 writing rules plus eight general recommendations. The supplied Issue 9 PDF also contains Part 2's controlled dictionary, but the rule catalog does not parse those entries or verify vocabulary approval. `STE606` and `STE801` are local checks, while the other STE entries require contextual LLM review. See the [STE reference](docs/reference/technical-english.md), configuration and [dogfooding workflow](docs/dogfooding.md#audit-the-generated-rule-catalog).

Minimal project configuration:

```toml
[tool.style-audit]
select = ["NAS001"]
output = "text"
```

Apply different rules by file pattern with `[tool.style-audit.per-file-select]`, for example `"docs/**" = ["NAS00?"]` and `"src/*.py" = ["NAS001"]`. Matching entries replace global selection. Overlaps combine and ignores win. See [per-file rule selection](docs/configuration.md#per-file-rule-selection) for patterns, stdin, CLI precedence, and file-specific LLM opt-ins.

See the [configuration guide](docs/configuration.md), [CLI reference](docs/reference/cli.md), and [LLM privacy guide](docs/llm.md) for selection precedence, models, and provider behavior. An LLM opt-in never overrides a deterministic-only selection.

Default `.md` audits select no-ai-slop (`NAS`) and readability (`RDL`) rules. This selects checks; LLM judging remains opt-in, so a normal Markdown scan does not send text remotely. Directory discovery skips `AGENTS.md` and `SKILL.md` at any depth; explicitly named paths remain intentional overrides. To use LLM rules, provide a model and opt in with `[tool.style-audit.llm].enabled = true`, `--llm`, `--model`, or explicit LLM-rule selection. OpenRouter requires `OPENROUTER_API_KEY`; remote review may incur charges.

Example configuration:

```toml
[tool.style-audit.llm]
enabled = true
model = "openrouter/microsoft/microsoft-decision-1"
threshold = 0.8
```

LiteLLM routes this model through OpenRouter's Decisions API (`POST https://openrouter.ai/api/alpha/decisions`), not the chat-completions endpoint. It uses LiteLLM's `systemone` adapter; no custom endpoint configuration is required.

Run a scoped review:

```sh
style-audit draft.md --select RDL
```

The readability rules judge interpretation difficulty in English sentences, not AI authorship or a readability score. They preserve familiar constructions and do not pretend to measure n-gram frequency or dependency statistics without reference data. See the [readability guide](docs/reference/readability.md).

LLM rules are grouped by registered scope and sent in one request per eligible unit. Decision-1 returns a probability for each selected rule; the configured threshold controls which findings are reported, including probabilities equal to the threshold.

Remote review may incur charges. The selected scopes and their unit counts determine request volume. Masking preserves logical units but is not sensitive-data redaction. The [LLM guide](docs/llm.md) explains segmentation, privacy, validation, and limitations. The [dogfooding guide](docs/dogfooding.md) separates historical pre-scope observations, including an authentication failure, from current review evidence.


## Source and attribution

The initial rule inventory adapts the editorial guidance in [Peter Yang's `no-ai-slop`](https://github.com/petergyang/no-ai-slop), pinned to commit [`000650b`](https://github.com/petergyang/no-ai-slop/commit/000650b156983f5159695b441477f4e63b25dc85). The upstream project is MIT-licensed. Its required license notice is in [`third_party/no-ai-slop-LICENSE`](third_party/no-ai-slop-LICENSE). Style-audit's conservative deterministic findings implement only literal, source-backed checks. Contextual guidance is kept in LLM judgments rather than brittle word bans.

The `RDL` rules adapt Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald's [“Why is AI-generated language so hard to understand?”](https://arxiv.org/html/2610.29162v1), arXiv:2610.29162v1 (21 October 2026), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The adaptation uses contextual lint judgments rather than reproducing the paper's corpus measurements.

The `STE` rules are original summaries and illustrations of ASD-STE100 Issue 9 Part 1, covering 53 writing rules and eight general recommendations. The supplied full Issue 9 PDF contains Part 2's controlled dictionary; the linter does not ingest it. The [technical-English reference](docs/reference/technical-english.md) documents source citations, copyright and trademark limits, and this scope distinction. The project is independent and is not endorsed by ASD.

## License

Unless otherwise stated, style-audit's original source code is licensed under MIT; see [`LICENSE`](LICENSE). Third-party and source-derived material retains its own terms: the `no-ai-slop` notice is in [`third_party/no-ai-slop-LICENSE`](third_party/no-ai-slop-LICENSE), the RDL attribution is described above, and this license does not grant rights to ASD-STE100 or the supplied standard PDF.
