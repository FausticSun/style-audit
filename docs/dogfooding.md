# Dogfooding documentation and docstrings

Use `style-audit` to audit its own README, documentation, Python docstrings, and Gherkin feature files. Run the installed CLI from the repository root, review each finding, and rerun after editing. Keep this separate from unit tests and the MkDocs build. Those checks do not judge the prose.

## Audit the source files

Install the package and documentation dependencies, then run all current deterministic rules:

```sh
uv sync --group docs
uv run --group docs style-audit README.md docs/ --select NAS00,STE606,STE801
uv run --group docs style-audit README.md docs/ --select NAS00,STE606,STE801 --format json
```

`NAS00` selects `NAS001`–`NAS003`. `STE606` and `STE801` add local ASD-STE100 paragraph-length and semicolon checks. These selections run locally and need no credentials. They send no document text to a model. Explicit local rules keep this workflow local even if LLM review is enabled in project configuration.

The directory scan includes Markdown, reStructuredText, plain-text files, Gherkin feature files, and Python docstrings, including those in `docs/hooks.py`. The `site/` directory is excluded by default. Fenced code, inline code, and paired quotation spans are masked, so rule examples inside those spans are not findings. Masking preserves logical units and original source offsets. Each selected local rule checks its registered scope and reports the exact token or emoji location. A clean result therefore applies only to the selected rules and visible prose, not every sentence or example in the documentation.

## Audit Gherkin feature files

The default include set accepts `*.feature`. Feature and scenario titles plus step wording remain visible to the auditor. The parser masks keywords, tags, comments, data-table rows, Gherkin docstrings (`"""` or `'''`), and fenced code blocks marked by triple backticks. It preserves original source offsets and keeps step boundaries. Fixture values inside docstrings, code blocks, or table cells are not audited as prose.

```sh
uv run style-audit tests/bdd/features/ --select NAS00,STE606,STE801 --format json
```

Review findings against the visible title or step. Do not treat masked fixture data as a clean prose judgment.


## Audit Python docstrings

Audit Python docstrings in the implementation and tests, Gherkin feature files under `tests/bdd/features/`, and the documentation hook with the installed CLI:

```sh
uv run style-audit src/ tests/ docs/hooks.py --select NAS00,STE606,STE801 --format json
```

Python `.py` and `.pyi` inputs are parsed, never executed. Only real module, class, function, and async-function docstrings are extracted, while comments, assigned strings, and later string expressions are not audited. Each decoded, cleaned docstring is a separate document, with findings mapped to its original file positions and source spelling. This scan does not judge intentional rule samples or test fixtures stored in non-docstring strings. Use the separate raw-example workflow below for those.

For Python stdin, give a Python filename. This disposable positive control retains a discouraged term in a comment and an assigned string, but only the actual docstring should produce a finding:

```sh
printf '%s\n' '# We utilize comments.' '"""A robust parser."""' 'VALUE = "foster"' | uv run style-audit - --stdin-filename control.py --select NAS00,STE606,STE801 --format json
```

Expect `NAS001` for the docstring's term at line 2, column 6, with exit `1`. Replacing only the docstring with `"""An integer parser."""` should produce no findings and exit `0`. Leave the comment and assigned string unchanged to check exclusion. Invalid Python must fail with exit `2`, not an empty successful audit.

Local checks make no provider calls. For optional editorial review, explicitly select LLM rules and a model, for example `--select NAS00,RDL --model azure-maas-judge/Decision-1`. Remote requests contain only the current docstring unit's masked prose, never surrounding code or comments. Private prose written in a docstring is still eligible for transmission. Review [Python scope and privacy](llm.md#python-docstrings) before enabling that run.

### Observed own-code audit

The installed CLI ran `style-audit src/ tests/ docs/hooks.py --select NAS00 --format json` after docstring extraction was added: exit `0`, version-1 JSON with no findings. Those paths contained 17 Python files and 36 nonempty AST-recognized docstrings, counted separately from rule examples and test fixtures. No docstring wording changes were required by the selected local checks.

A disposable code fixture produced `NAS001` at line 2, column 6, and `NAS003` at line 5, column 11, with exit `1`. Replacing its two docstrings produced exit `0` while leaving discouraged terms in its comment and non-docstring strings unchanged. Python stdin selected by `--stdin-filename` and default directory discovery were also exercised. An invalid Python stdin fixture exited `2`, wrote a located syntax error to stderr, and emitted no JSON report. A CRLF escaped continuation retained its original source spelling in reported evidence.

These are local observations, not a live-provider review or a claim of all-rule editorial accuracy. This record was appended after those runs.

## Audit the generated rule catalog

`docs/reference/rules.md` is the ruleset overview. The no-ai-slop, readability, and STE pages receive cards from the canonical registry through `docs/hooks.py`. Scanning their source pages alone does not check the generated prose. Export each ruleset with `_rule_reference(prefix)`, omitting HTML layout wrappers. These commands audit the generated descriptions and explanations while leaving intentionally fenced examples outside the prose checks:

```sh
set -o pipefail  # Bash: propagate a renderer failure through the pipeline.
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/hooks.py")["_rule_reference"]("NAS"))' | uv run --group docs style-audit - --stdin-filename docs/reference/no-ai-slop.md --select NAS00 --format json
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/hooks.py")["_rule_reference"]("RDL"))' | uv run --group docs style-audit - --stdin-filename docs/reference/readability.md --select NAS00 --format json
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/hooks.py")["_rule_reference"]("STE"))' | uv run --group docs style-audit - --stdin-filename docs/reference/technical-english.md --select STE606,STE801 --format json
```

Check both sides of the pipeline. A renderer failure is not a clean catalog audit. An empty input can produce a successful linter result. The Bash setting above also makes a failed renderer fail the pipeline.

If metadata needs revision, update the source catalog (`rules.py` or `ste_rules.py`), not the generated HTML or a page's source placeholder. Keep criteria, source citations, context, and exceptions accurate. Do not remove a rule or its scope to silence a finding. Every rule has a before/after pair and an explanation in its required `examples` metadata.

### Exercise raw rule examples

A prose audit intentionally ignores quoted or fenced demonstrations. To exercise a sample, extract its raw text from the same registry and select its own rule:

```sh
set -o pipefail
uv run python -c 'from style_audit.rules import RULES_BY_CODE; print(RULES_BY_CODE["NAS001"].examples[0].before)' | uv run style-audit - --stdin-filename NAS001-before.md --select NAS001 --format json
uv run python -c 'from style_audit.rules import RULES_BY_CODE; print(RULES_BY_CODE["NAS001"].examples[0].after)' | uv run style-audit - --stdin-filename NAS001-after.md --select NAS001 --format json
```

Expect status `1` with a `NAS001` finding for the first command and status `0` for the second. Substitute another ID to exercise its pair. For an LLM rule, also provide `--model azure-maas-judge/Decision-1 --threshold 0.8`. Preserve each sample's Markdown and paragraph breaks so the rule sees its registered scope. The explanation states the author's intended context. The raw sample alone may not contain that context.

Before/after pairs are editorial demonstrations, not guaranteed decision-model classifications. Review a missed before sample or a flagged revision against the rule and its contextual exception. Record the outcome rather than lowering the threshold, inventing facts, or treating a clean documentation audit as detection accuracy. The examples do not change judge prompts.

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

The following deterministic runs were observed during the earlier documentation workflow, before decision-model support and per-rule scopes were added. That initial scan was clean and required no prose replacements. These historical results are preserved as observations, not a guarantee about the current files or later edits:

| Scan | Findings | Exit status |
| --- | --- | --- |
| README and source documentation, before edits | 0 | 0 |
| Generated rule-reference Markdown | 0 | 0 |
| Disposable positive control | 3 | 1 |
| Clean control | 0 | 0 |
| README and source documentation, including this guide | 0 | 0 |

## Review with Azure MaaS Decision-1

Local rules do not assess cadence, concreteness, or other contextual guidance. Optional Decision-1 review requires the OMP model registry entry or project LiteLLM settings described in [installation](installation.md#optional-enable-llm-review). `api_base` may come from TOML or the registry. The API key comes from the registry unless `AZURE_MAAS_JUDGE_API_KEY` or a configured `api_key_env` overrides it. Protect the user-level registry and keep secrets out of the repository. The current report attempt below returned a service-unavailable error and did not validate credentials or model behavior.

```sh
uv run --group docs style-audit README.md docs/ --select NAS1 --model azure-maas-judge/Decision-1 --threshold 0.8 --format json
```

`NAS1` selects only the no-ai-slop LLM rules. It does not include the separate `RDL` readability ruleset. Use `--select RDL` for readability alone or `--select NAS1,RDL` for both. The default threshold is `0.8`, and equality is included. Use `--threshold 0.9` for a narrower set of reported probabilities:

```sh
uv run --group docs style-audit README.md docs/ --select NAS1 --model azure-maas-judge/Decision-1 --threshold 0.9 --format json
```

These commands do not check the generated rule descriptions unless the rendered Markdown is supplied separately:

```sh
set -o pipefail
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/hooks.py")["_rule_reference"]("NAS"))' | uv run --group docs style-audit - --stdin-filename docs/reference/no-ai-slop.md --select NAS1,RDL --model azure-maas-judge/Decision-1 --threshold 0.8 --format json
uv run --group docs python -c 'import runpy; print(runpy.run_path("docs/hooks.py")["_rule_reference"]("RDL"))' | uv run --group docs style-audit - --stdin-filename docs/reference/readability.md --select NAS1,RDL --model azure-maas-judge/Decision-1 --threshold 0.8 --format json
```

Check renderer success and non-empty input as in the local workflow. Selected LLM rules are grouped by their canonical sentence, paragraph, section, or document scope. Both decision and chat APIs make one synchronous request per eligible unit in each selected scope. Each request contains only that unit's masked text and matching-scope rules.

Calls may incur charges. The chosen scopes, unit counts, and text lengths affect cost and latency. Masking preserves units but is not sensitive-data redaction.

Decision findings span the complete original unit, potentially including masked quotations or code as source context, not judged prose. Their messages contain scope, probability, and rule descriptions, and their fixes are empty.

Chat findings instead require exact contiguous visible quotes within the current unit. Review findings in context, preserve author voice, and do not equate a probability with proof. See [LLM review and privacy](llm.md) for segmentation, validation, and threshold limitations.

These are current workflow instructions, not records of completed requests. Historical Decision-1 results below predate the Azure MaaS cutover and do not validate the current OMP/LiteLLM configuration.

### Current report audit attempt

Earlier attempts against `wages-report/report.md` through the OpenAI Decisions adapter returned LiteLLM `ServiceUnavailableError` (HTTP `503`), including a retry with `AZURE_MAAS_JUDGE_API_KEY` unset. After configuring the Foundry project `api_base` with `custom_llm_provider = "azure_ai"`, a live document-scoped `NAS113` audit of the report at threshold `0.8` completed with exit `0` and no findings. The command unset `AZURE_MAAS_JUDGE_API_KEY`, so the request used the OMP registry key.

This verifies one live Decision-1 request for the document-level “Robotic rhythm” rule, not the full configured NAS/RDL report audit. No full report audit has run with the new route.


### Historical Decision-1 verification before scope support (pre-Azure cutover)

All Decision-1 results below predate Azure MaaS configuration. Earlier authenticated runs used the then-configured LiteLLM/OpenRouter Decisions service, and a local smoke used that adapter against a disposable HTTP server.

The historical Azure MaaS path used LiteLLM's `systemone` with `custom_llm_provider = "openai"` and passed the configured Azure MaaS `api_base` and key. For a base ending `/openai/v1`, it constructed `/openai/v1/decisions`. That local HTTP smoke validated routing only, not live endpoint behavior or credentials; it does not validate the current Azure AI project route.

Archived command excerpts are non-runnable. `HISTORICAL_MODEL_ARGUMENT` marks the removed former model argument and is not a supported model name.


Before per-rule scope support, the installed source-audit command was attempted at threshold `0.8` with JSON output. It exited `2`, produced no stdout findings, and reported an authentication error from the then-used LiteLLM/OpenRouter Decisions adapter because its provider credential was unavailable. No live judgments, probabilities, documentation findings, or clean model result were observed in that attempt. This is historical evidence, not a claim about current Azure credentials. The higher-threshold and generated-catalog commands above are workflow instructions, not records of successful runs. Neither this failure nor historical deterministic results establish current scoped behavior or Decision-1 quality.

For a completed live review, record the exact current command and model, threshold, exit status, findings count, representative source-located evidence and probabilities, and the contextual judgment behind any prose edits. Keep secrets out of the record. Treat malformed responses or provider failures as errors, not approval. Controlled-response tests and local HTTP adapter checks can establish local behavior without proving Microsoft model judgments.

Also before scope support, the decision integration's updated README and source documentation were audited again with `--select NAS00 --format json`: exit `0`, empty findings. The installed CLI used the former LiteLLM/OpenRouter Decisions adapter against a disposable local HTTP server at the historical path `/api/alpha/decisions`, using test credentials. That earlier smoke exercised the upstream model name, threshold override, repeated Unicode-located passages under the old passage-based implementation, masked quotation exclusion, invalid-response exit `2`, and deterministic-only provider suppression. These were controlled local answers, not Microsoft judgments or Azure endpoint validation. All 38 behavioral tests and the strict MkDocs build passed in that earlier run. Those observations do not verify the current backend.


### Historical scoped verification (pre-Azure cutover)

After scope support, all 57 behavioral tests passed. A real HTTP/installed-CLI smoke through both LiteLLM clients produced four scope-correct findings for a controlled fixture: sentence, paragraph, section, and document. It also exercised threshold overrides, invalid-answer exit `2` without partial JSON, and deterministic-only provider suppression. These HTTP answers were controlled locally, not Microsoft judgments. The updated README and source documentation passed the local `NAS00` audit with exit `0` and empty findings. The strict MkDocs build passed.

An authenticated four-scope Microsoft decision smoke ran with this input and command:

```text
printf '%s\n' '# Release' 'The launch marks a pivotal moment.' \
  'This is not a tool upgrade. It is a workflow upgrade.' '' \
  'QueueKit, the agent, reviews drafts.' '' \
  'QueueKit, the assistant, scores drafts.' '' '# Outcome' \
  'We shipped on Tuesday. We measured on Wednesday.' | \
  style-audit - --stdin-filename scope-live.md \
    --select NAS106,NAS101,NAS110,NAS113 \
    --model HISTORICAL_MODEL_ARGUMENT --threshold 0.8 --format json
```

The historical live command exited `1` with two findings. `NAS106` anchored to the sentence at line 2, column 1, with evidence `The launch marks a pivotal moment.` and probability `0.852`. `NAS113` anchored to the complete input from line 1, column 1 through line 10, column 49, with probability `0.867`. The paragraph and section rules produced no findings at this threshold. Authentication worked through the former backend in that run, and the earlier missing-key failure remains historical. This fixture records old transport and source anchoring, not Azure transport, calibrated accuracy, or a complete documentation review.

The authenticated source-documentation audit also ran successfully:

```text
style-audit README.md docs/ --select NAS113,NAS115,NAS116,NAS118 \
  --model HISTORICAL_MODEL_ARGUMENT --threshold 0.8 --format json
```

It exited `0` with an empty `findings` array for these four document-scoped rules. This was not an all-LLM-rule audit. Sentence, paragraph, and section rules and the generated catalog were not selected. No documentation prose replacements were needed for this observed run. The fixture and audit records describe the files at the time of invocation, before these verification records were appended. The run used the pre-cutover backend, not Azure MaaS.

### Historical readability verification (pre-Azure cutover)

For the independent `RDL` ruleset, all 58 behavioral tests passed. A disposable local HTTP server exercised both real LiteLLM clients through the installed CLI: all seven readability IDs, sentence-level source anchoring, quoted-only input suppression, ignored rules, mixed `NAS`/`RDL` findings, deterministic-only provider suppression, and rejection of foreign-ruleset answers with exit `2` and no partial JSON. Those HTTP responses were controlled fixtures, not live readability judgments.

An authenticated Microsoft decision run used this ten-sentence fixture:

```text
printf '%s\n' \
  'The report that the manager whom the consultant the board hired advised approved disappeared.' \
  'The intern the editor the manager praised hired left.' \
  'The witness told the lawyer the defendant threatened changed the account.' \
  'The team revised the customer account access exception review escalation policy.' \
  'We spreadsheeted the silence into a calendarable certainty.' \
  'The migration expects the invoice to remember its missing approval.' \
  'The update amortizes consent gravity into reader-patience liquidity.' \
  'The book I read was useful.' \
  'We bottled the whiskey.' \
  'The paper argues that shorter dependencies help readers.' | \
  style-audit - --stdin-filename readability-live.md --select RDL \
    --model HISTORICAL_MODEL_ARGUMENT --threshold 0.8 --format json
```

It exited `1` with ten findings, all on the first three sentences. The decision messages reported these probabilities for representative sentence-located findings:

| Rule | Reported findings | Representative location | Probability |
| --- | --- | --- | --- |
| `RDL101` | 2 | Line 1, column 1 | 0.988 |
| `RDL102` | 2 | Line 1, column 1 | 0.940 |
| `RDL103` | 3 | Line 3, column 1 | 0.958 |
| `RDL104` | 0 | — | — |
| `RDL105` | 0 | — | — |
| `RDL106` | 0 | — | — |
Each emitted finding covered its complete original sentence. The clear short object relative, conventional denominal verb, and conventional metonymy controls on lines 8–10 produced no findings. Neither did the constructed noun-stack, denominal-verb, inanimate-agent, and lexical examples on lines 4–7 at this threshold. These omissions are limits of the observed detection, not proof those sentences are readable.

The fixture records judgments through the former LiteLLM/OpenRouter backend, not the current Azure MaaS endpoint. It does not validate accuracy, paper metrics, calibrated probabilities, or all-rule detection. No live chat-model result is claimed.


The updated README and source documentation also passed the local `NAS00` audit with exit `0` and empty findings, and the strict MkDocs build passed. These observations apply to the files at invocation, before this evidence record was appended. They are not an `RDL` documentation audit.

## Historical rule descriptions and examples audit (pre-Azure cutover)

All 31 rules now have a registry-backed before/after pair and an explanation. The installed CLI audited the generated descriptions and explanations locally with `--select NAS00`: status `0`, no findings. The rendered catalog was also audited with `--select NAS1,RDL` through the former LiteLLM/OpenRouter Decisions backend. The initial historical live result was status `1` with nine findings: three `NAS117`, two `NAS120`, two `RDL106`, and two `RDL107`.

Review removed unnecessary emphasis on the rule count and clarified explanations for `NAS120`, `RDL101`, and `RDL106`. In particular, the original explanation treated a verb as an unmarked noun and used an unclear claim that clauses compete for participants. The per-rule headings were retained: they identify and link complete rule demonstrations, rather than decorate unrelated tiny sections. Masking the samples makes these sections look shorter to the judge than they do to a reader. No rules were disabled and the threshold stayed at `0.8`.

The corrected catalog was audited again with the same model, selection, and threshold. It exited `1` with only two `NAS117` findings: the `NAS002` section at line 63, column 1, probability `0.867`, and the `NAS103` section at line 135, column 1, probability `0.835`. Both concern the retained reference headings and were reviewed as contextual formatting exceptions. No clarity or readability findings remained in that observed run. This is a completed review with two retained findings, not a clean LLM exit.

A disposable runner also supplied each sample's raw text to its own rule, preserving sentence, paragraph, section, and document scope. Local checks and authenticated model calls produced these initial observations:

| Analyzer | Pairs exercised | Before samples flagged | Revisions flagged |
| --- | --- | --- | --- |
| Deterministic | 3 | 3 | 0 |
| Microsoft decision model, threshold 0.8 | 28 | 11 | 1 |

The flagged revision was `NAS113`, probability `0.835`. Review changed its first sentence to an introductory dependent clause, rather than beginning both paragraphs with the same subject and coordinated actions. The revised raw sample then passed the installed CLI with `--select NAS113` in a historical run through the former LiteLLM/OpenRouter Decisions backend: status `0`, no findings. The other 27 LLM revisions had no findings in the initial run.

The nested-fence regression first exposed a masking bug: any fence marker toggled the code-block state, so shorter or different-kind delimiters could leak a sample into audited prose. The fix tracks the opening delimiter and accepts only a matching kind, sufficient length, and whitespace-only remainder as a closer. All 59 behavioral tests passed afterward. An installed-CLI smoke then ignored the complete nested sample while flagging the real trailing `utilize` at line 15, column 4. The sample alone returned status `0` and no findings for both local and LLM-only selections.

Browser verification checked all 31 rendered descriptions, all 62 verbatim sample texts, and the catalog's fragment links. Desktop and 390-pixel layouts were inspected. Prose samples wrap without changing their stored text. The preview runs on <http://127.0.0.1:8003/>. The strict MkDocs build and local source-documentation and generated-catalog audits also passed before these final evidence paragraphs were appended. These are observations at invocation, not a claim of all-rule model accuracy.

The reference now has a [ruleset overview](reference/rules.md), a [no-ai-slop page](reference/no-ai-slop.md), and a [readability page](reference/readability.md). Rule cards are generated from the canonical registry. Each includes ID, name, engine, scope, description, upstream source, and every before/after pair with its explanation.

## Ruleset card layout verification

Chromium verification checked all 31 cards and all 62 verbatim sample texts against the registry, including metadata, source links, explanations, and accessible heading anchors. The Reference menu opened both ruleset pages successfully. Both pages used one column at viewport widths 320, 390, 768, and 991 pixels, and two columns at 992, 1280, and 1600 pixels. Neither page nor its card samples required horizontal scrolling at those widths. Desktop and mobile screenshots were inspected.

Open the preview and inspect navigation, search, the generated catalog, and narrow-screen layout. The site uses MkDocs' bundled `mkdocs` theme. The architecture diagram loads a pinned Mermaid script from jsDelivr. Rendering that diagram requires network access, but the local prose audit does not.

The strict MkDocs build passed. The installed CLI returned status `0` with no findings for the README/source-documentation local audit and for each ruleset's exported prose using `--select NAS00 --format json`. The preview remains a persistent background service on <http://127.0.0.1:8003/>.

The earlier recorded LLM probabilities refer to the combined catalog before this layout change. Rule criteria and judging were not changed, and no additional live-provider review was run for the card layout. These observations apply to the files at invocation, before this verification record was appended.

## Separate correctness and site checks

After prose review, run the separate correctness and site checks:

```sh
uv run --group dev --group docs pytest
uv run --group docs mkdocs build --strict
uv run --group docs mkdocs serve
```

Open the preview and inspect navigation, search, the generated catalog, and narrow-screen layout. The site uses MkDocs' bundled `mkdocs` theme. The architecture diagram loads a pinned Mermaid script from jsDelivr. Rendering that diagram requires network access, but the local prose audit does not.
