# Dogfooding documentation and source prose

Use `style-audit` to audit its own README, documentation, Python docstrings, Marimo Markdown cells, and Gherkin feature files. Run the installed CLI from the repository root, review each finding, and rerun after editing. Keep this separate from unit tests and the Zensical site build. Those checks do not judge the prose.

## Audit the source files

Install the package and documentation dependencies, then run all current deterministic rules:

```sh
uv sync --group docs
uv run --group docs style-audit README.md docs/ --select NAS00,STE606,STE801
uv run --group docs style-audit README.md docs/ --select NAS00,STE606,STE801 --format json
```

`NAS00` selects `NAS001`–`NAS003`. `STE606` and `STE801` add local ASD-STE100 paragraph-length and semicolon checks. These selections run locally and need no credentials. They send no document text to a model. Explicit local rules keep this workflow local even if LLM review is enabled in project configuration.

The directory scan includes Markdown, reStructuredText, plain-text files, Gherkin feature files, ordinary Python docstrings, and direct Markdown cells in recognized Marimo apps. The `site/` directory is excluded by default. Fenced code, inline code, and paired quotation spans are masked, so rule examples inside those spans are not findings. Masking preserves logical units and original source offsets. Each selected local rule checks its registered scope and reports the exact token or emoji location. A clean result therefore applies only to the selected rules and visible prose, not every sentence or example in the documentation.

## Audit Gherkin feature files

The default include set accepts `*.feature`. Feature and scenario titles plus step wording remain visible to the auditor. The parser masks keywords, tags, comments, data-table rows, Gherkin docstrings (`"""` or `'''`), and fenced code blocks marked by triple backticks. It preserves original source offsets and keeps step boundaries. Fixture values inside docstrings, code blocks, or table cells are not audited as prose.

```sh
uv run style-audit tests/bdd/features/ --select NAS00,STE606,STE801 --format json
```

Review findings against the visible title or step. Do not treat masked fixture data as a clean prose judgment.


## Audit Python docstrings

Audit Python docstrings in the implementation and tests, Gherkin feature files under `tests/bdd/features/`, and the rule-reference generator with the installed CLI:

```sh
uv run style-audit src/ tests/ docs/render_rule_cards.py --select NAS00,STE606,STE801 --format json
```

Ordinary Python `.py` and `.pyi` inputs are parsed, never executed. Only real module, class, function, and async-function docstrings are extracted, while comments, assigned strings, and later string expressions are not audited. Each decoded, cleaned docstring is a separate document, with findings mapped to its original file positions and source spelling. This scan does not judge intentional rule samples or test fixtures stored in non-docstring strings. Use the separate raw-example workflow below for those.

For Python stdin, give a Python filename. This disposable positive control retains a discouraged term in a comment and an assigned string, but only the actual docstring should produce a finding:

```sh
printf '%s\n' '# We utilize comments.' '"""A robust parser."""' 'VALUE = "foster"' | uv run style-audit - --stdin-filename control.py --select NAS00,STE606,STE801 --format json
```

Expect `NAS001` for the docstring's term at line 2, column 6, with exit `1`. Replacing only the docstring with `"""An integer parser."""` should produce no findings and exit `0`. Leave the comment and assigned string unchanged to check exclusion. Invalid Python must fail with exit `2`, not an empty successful audit.

Local checks make no provider calls. For optional editorial review, explicitly select LLM rules and a LiteLLM model, for example `--select NAS00,RDL --model openai/gpt-4o-mini`. Remote requests contain only the current docstring unit's masked prose, never surrounding code or comments. Private prose written in a docstring is still eligible for transmission. Review [Python scope and privacy](llm.md#python-docstrings) before enabling that run.

### Observed own-code audit

Before the site migration, the installed CLI audited `docs/hooks.py` after docstring extraction was added: exit `0`, version-1 JSON with no findings. The former hook has been replaced by `docs/render_rule_cards.py`; the earlier counts (17 Python files and 36 nonempty AST-recognized docstrings) are historical. No docstring wording changes were required by those selected local checks.

A disposable code fixture produced `NAS001` at line 2, column 6, and `NAS003` at line 5, column 11, with exit `1`. Replacing its two docstrings produced exit `0` while leaving discouraged terms in its comment and non-docstring strings unchanged. Python stdin selected by `--stdin-filename` and default directory discovery were also exercised. An invalid Python stdin fixture exited `2`, wrote a located syntax error to stderr, and emitted no JSON report. A CRLF escaped continuation retained its original source spelling in reported evidence.

These are local observations, not a live-provider review or a claim of all-rule editorial accuracy. This record was appended after those runs.

## Audit Marimo Markdown cells

The system-design report is a Marimo `.py` app. Style-audit parses the file without importing it: direct `mo.md()` string literals are separate documents, static f-string text is eligible, and interpolation expressions, variables, widgets, Mermaid diagrams, comments, and Python code are excluded. Findings point to the original source. An LLM opt-in sends only visible prose from the selected cell unit; treat that prose as remote input.

Run the deterministic patterns locally, then explicitly opt into both requested editorial rulesets:

```sh
uv run style-audit notebooks/system_design.py --select NAS00,STE606,STE801 --format json
uv run style-audit notebooks/system_design.py --select NAS,RDL --model openai/gpt-4o-mini --format json
```

Before the second command, set `OPENAI_API_KEY` in the environment for this example model. Other LiteLLM models use their provider's standard credentials; see the [configuration guide](configuration.md#litellm-transport-settings) for optional transport settings. The CLI discovers the nearest project `pyproject.toml`, so no `--config` flag is needed. Keep credentials in a secret store or environment variable, never in TOML.


## Audit the generated rule catalog

`docs/reference/rules.md` is the ruleset overview. The no-ai-slop, readability, and STE pages contain generated Markdown cards from the canonical registry; `docs/render_rule_cards.py` maintains those blocks. Export each ruleset with `_rule_reference(prefix)`, omitting HTML layout wrappers. These commands audit generated descriptions and explanations while leaving intentionally fenced examples outside prose checks:

```sh
set -o pipefail  # Bash: propagate a renderer failure through the pipeline.
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/render_rule_cards.py")["_rule_reference"]("NAS"))' | uv run --group docs style-audit - --stdin-filename docs/reference/no-ai-slop.md --select NAS00 --format json
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/render_rule_cards.py")["_rule_reference"]("RDL"))' | uv run --group docs style-audit - --stdin-filename docs/reference/readability.md --select NAS00 --format json
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/render_rule_cards.py")["_rule_reference"]("STE"))' | uv run --group docs style-audit - --stdin-filename docs/reference/technical-english.md --select STE606,STE801 --format json
```

Check both sides of the pipeline. A renderer failure is not a clean catalog audit. An empty input can produce a successful linter result. The Bash setting above also makes a failed renderer fail the pipeline.

If metadata needs revision, update the appropriate YAML file under `src/style_audit/rules/`, then run `uv run --group docs python docs/render_rule_cards.py` and verify with `--check`. Do not edit generated cards by hand. Keep criteria, source citations, context, and exceptions accurate. Do not remove a rule or its scope to silence a finding. Every rule has a before/after pair and an explanation in its required `examples` metadata.

### Exercise raw rule examples

A prose audit intentionally ignores quoted or fenced demonstrations. To exercise a sample, extract its raw text from the same registry and select its own rule:

```sh
set -o pipefail
uv run python -c 'from style_audit.rules import RULES_BY_CODE; print(RULES_BY_CODE["NAS001"].examples[0].before)' | uv run style-audit - --stdin-filename NAS001-before.md --select NAS001 --format json
uv run python -c 'from style_audit.rules import RULES_BY_CODE; print(RULES_BY_CODE["NAS001"].examples[0].after)' | uv run style-audit - --stdin-filename NAS001-after.md --select NAS001 --format json
```

Expect status `1` with a `NAS001` finding for the first command and status `0` for the second. Substitute another ID to exercise its pair. For an LLM rule, also provide a LiteLLM `provider/model`, such as `openai/gpt-4o-mini`. Preserve each sample's Markdown and paragraph breaks so the rule sees its registered scope. The explanation states the author's intended context. The raw sample alone may not contain that context.

Before/after pairs are editorial demonstrations, not guaranteed model classifications. Review a missed before sample or a flagged revision against the rule and its contextual exception. Record the outcome rather than inventing facts or treating a clean documentation audit as detection accuracy. The examples do not change judge prompts.

## Check that findings are still detected

A clean repository scan is not enough to prove detection works. Use a disposable stdin control with one example for each local rule:

```sh
printf '%s\n' '# 🚀 Launch' 'We delve into the details.' 'It serves as an example.' | uv run --group docs style-audit - --select NAS00 --format json
```

Expect status `1` and findings for `NAS002`, `NAS001`, and `NAS003`, on lines 1, 2, and 3 respectively. The control never modifies the documentation. After replacing the decorative heading and inflated wording, check a clean counterpart:

```sh
printf '%s\n' '# Launch' 'We inspect the details.' 'It is an example.' | uv run --group docs style-audit - --select NAS00 --format json
```

Expect status `0` and an empty `findings` array. To investigate a real documentation finding, use the reported file, position, evidence, and suggestion. Preserve the technical meaning and rerun the complete documentation scan. For a false positive, check the source-backed rule boundary and add a behavioral regression case rather than hiding the problem with a blanket ignore or unnecessary quoting.

## Interpret results and finish the review

Status `0` means no findings. Status `1` means findings need review. Status `2` means a configuration, input, or provider failure. Operational errors go to stderr. Do not treat an error, a skipped scan, or an empty input as prose approval.

The following deterministic runs were observed during the earlier documentation workflow, before scoped LLM review was added. That initial scan was clean and required no prose replacements. These historical results are preserved as observations, not a guarantee about the current files or later edits:

| Scan | Findings | Exit status |
| --- | --- | --- |
| README and source documentation, before edits | 0 | 0 |
| Generated rule-reference Markdown | 0 | 0 |
| Disposable positive control | 3 | 1 |
| Clean control | 0 | 0 |
| README and source documentation, including this guide | 0 | 0 |

## Review with LiteLLM

For optional editorial review, select LLM rules and provide a model using LiteLLM's `provider/model` syntax. For example, `openai/gpt-4o-mini` uses `OPENAI_API_KEY`; use the selected provider's standard credentials for other models. Keep credentials out of the repository and project TOML.

```sh
uv run --group docs style-audit README.md docs/ --select NAS1 --model openai/gpt-4o-mini --format json
```

`NAS1` selects only the no-ai-slop LLM rules. It does not include the separate `RDL` readability ruleset. Use `--select RDL` for readability alone or `--select NAS1,RDL` for both.

To include generated rule descriptions, pass their rendered Markdown separately:

```sh
set -o pipefail
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/render_rule_cards.py")["_rule_reference"]("NAS"))' | uv run --group docs style-audit - --stdin-filename docs/reference/no-ai-slop.md --select NAS1,RDL --model openai/gpt-4o-mini --format json
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/render_rule_cards.py")["_rule_reference"]("RDL"))' | uv run --group docs style-audit - --stdin-filename docs/reference/readability.md --select NAS1,RDL --model openai/gpt-4o-mini --format json
```

Check renderer success and non-empty input as in the local workflow. Requests are grouped by canonical scope and contain only each unit's masked text and matching-scope rules. Masking preserves units but is not sensitive-data redaction. Default completion findings require exact contiguous visible quotes; Decisions findings use the whole visible scope unit with a score and threshold. Review findings in context and preserve author voice. See [LLM review and privacy](llm.md) for request boundaries, validation, and failures.

These are workflow instructions, not records of completed model requests. This guide does not claim live-provider results.

The reference now has a [ruleset overview](reference/rules.md), a [no-ai-slop page](reference/no-ai-slop.md), and a [readability page](reference/readability.md). The `docs/render_rule_cards.py` generator writes cards into each page from the canonical registry. Each includes ID, name, engine, scope, description, upstream source, and every before/after pair with its explanation.

## Ruleset card layout verification

Chromium verification checked all 31 cards and all 62 verbatim sample texts against the registry, including metadata, source links, explanations, and accessible heading anchors. The Reference menu opened both ruleset pages successfully. Both pages used one column at viewport widths 320, 390, 768, and 991 pixels, and two columns at 992, 1280, and 1600 pixels. Neither page nor its card samples required horizontal scrolling at those widths. Desktop and mobile screenshots were inspected.

Open the Zensical preview and inspect navigation, search, the generated catalog, and narrow-screen layout. The site uses Zensical's modern theme. The architecture diagram loads a pinned Mermaid script from jsDelivr. Rendering that diagram requires network access, but the local prose audit does not.

The strict MkDocs build passed before the site migration. In the Zensical migration check, `uv run --group docs zensical build --strict` finished with “No issues found.” The local preview rendered the homepage and generated No AI slop cards at desktop and narrow mobile widths; the settled mobile layout showed no overlap. The installed CLI returned status `0` with no findings for the README/source-documentation local audit and each ruleset's exported prose using `--select NAS00 --format json`. The earlier preview was a persistent background service on <http://127.0.0.1:8003/>.

The rule criteria were not changed for this layout review, and no additional live-provider review was run. These observations concern presentation only and apply to the files at invocation, before this verification record was appended.

## Separate correctness and site checks

After prose review, run the separate correctness and site checks:

```sh
uv run --group dev --group docs pytest
uv run --group docs zensical build --strict
uv run --group docs zensical serve
```

Open the Zensical preview and inspect navigation, search, the generated catalog, and narrow-screen layout. The site uses Zensical's modern theme. The architecture diagram loads a pinned Mermaid script from jsDelivr. Rendering that diagram requires network access, but the local prose audit does not.
