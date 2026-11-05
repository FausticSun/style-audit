# LLM review and privacy

LLM rules are subjective editorial judgments—not an AI-authorship detector. Unless selection is configured, supported inputs select all `NAS` no-ai-slop and `RDL` readability rules; their selected LLM rules run by default. Other catalogs require explicit selection.

## Default selection and judging

When no global selection or matching per-file entry overrides it, every supported input—including extracted Python docstrings, Marimo Markdown, Gherkin prose, and Git commit messages—uses `NAS` and `RDL`. LLM judging is enabled unless `[tool.style-audit.llm].enabled = false`. Chat completions use `openrouter/openrouter/free` by default; Decisions mode requires a provider-supported model. A configured `model` chooses the model but does not override `enabled = false`. Directory discovery skips `AGENTS.md` and `SKILL.md` at any depth; explicitly named paths remain intentional overrides.

Default LLM review sends each eligible visible prose unit, plus the selected rules' guidance and examples, to the configured provider. It may incur charges. Masking is not sensitive-data redaction; private text in an audited document can still be transmitted. Set `enabled = false` or select only deterministic rules to keep a run local. See [what the request contains](#what-the-request-contains).

## Keep audits local

```toml
[tool.style-audit]
select = ["NAS00"]

[tool.style-audit.llm]
enabled = false
```

`NAS00` selects the local no-ai-slop detectors. The explicit disabled setting keeps later LLM selections local too.

Default settings already judge selected NAS and readability LLM rules. To force LLM judging for one invocation when the project disables it:

```sh
style-audit --llm draft.md
style-audit --model openai/model draft.md
```

[Per-file selections](configuration.md#per-file-rule-selection) choose eligible rules per path. Their selected LLM rules are judged by default; other files retain their own selection. `enabled = false` disables judging unless `--llm` or `--model` force-enables that invocation.

When `model` is omitted, style-audit uses `openrouter/openrouter/free` for chat completions. With `api = "decisions"`, there is no default model: set a model supported by the provider's Decisions endpoint in TOML or with `--model`. A TOML model alone does not override `enabled = false`; CLI `--model` force-enables judging. CLI `--select NAS00` replaces file mappings and selects only local checks.

The default chat-completion model uses OpenRouter's `OPENROUTER_API_KEY`; Decisions mode uses the selected decision model's standard credential variable. Do not put raw API keys in TOML. The optional `api_key_env` setting names an environment variable, not its secret value. See [configuration](configuration.md#litellm-transport-settings) for supported transport settings.

Chat-completion judging is the default and returns validated quotes, reasons, and optional fixes. `api = "decisions"` uses LiteLLM's Decisions API and returns predicate probabilities; it requires a model supported by that endpoint. OpenRouter's Decisions API supports TypeSafe Jev models such as `openrouter/typesafe/jev-1.14`, not the `openrouter/openrouter/free` chat route. Jev calls may require OpenRouter credits. See [LiteLLM's OpenRouter Decisions documentation](https://docs.litellm.ai/docs/providers/openrouter#decisions-jev).

```sh
style-audit --select NAS106 --model openrouter/openrouter/free draft.md
```

With `api = "completion"`, the default model is used unless overridden. Decisions mode requires a provider-supported model in configuration or `--model`. With no configured selection, supported inputs select `NAS` and `RDL` and judge their LLM rules by default; `llm.enabled = false` disables those requests. Only retained rules are eligible, so a deterministic-only selection cannot be overridden by `--llm` or `--model`.

## What the request contains

### Canonical scopes and segmentation

Every rule has a required `scope` in the registry: **sentence**, **paragraph**, **section**, or **document**. Scope defines the logical unit to audit, not the size of a model-generated evidence quote. It remains fixed unless a project overrides it in `rule-overrides`. The generated [rule reference](reference/rules.md) documents bundled assignments.

The independent `RDL` [readability ruleset](reference/readability.md) uses sentence scope for contextual processing-difficulty judgments. It works with both backends and the same opt-in contract. It does not measure corpus frequency, n-gram perplexity, or standardized dependency length.

`NAS`, `RDL`, `STE`, and `MWG` can be selected separately or combined. The [STE reference](reference/technical-english.md) distinguishes its two narrow local checks from rules that require contextual review. The [MWG reference](reference/microsoft-writing.md) contains general writing guidance and excludes Microsoft-specific products, terminology, and UI procedures. No extra parser, corpus, or language-model download is required.

- **Sentence:** conservative punctuation-based segmentation, retaining unpunctuated tails and fragments and guarding common abbreviations, initialisms, and decimals. It is not a full linguistic parser. Leading and trailing Markdown table-cell pipes are trimmed, and delimiter-only fragments are skipped.
- **Paragraph:** blank lines, Markdown headings, fenced code, and Markdown list-item starts create boundaries. Soft line wraps stay together.
- **Section:** nonoverlapping Markdown heading-delimited spans. Each span ends at the next heading regardless of heading level. The preamble is a separate section. ATX and Setext headings count, but masked headings do not. Headingless text is one section.
- **Document:** the complete prose input, or one Python docstring, is one unit.

Leading and trailing original whitespace is trimmed from units. Fenced/inline code and paired quotation spans are replaced with same-length whitespace, preserving newlines and original Unicode offsets. Inline masks do not split a logical sentence or paragraph into separate visible runs. Blank or fully masked units are skipped by both backends.

Both APIs group selected LLM rules by scope and audit one eligible unit at a time. Completion mode makes one `litellm.completion` request per unit; Decisions mode makes one `litellm.decisions` request per unit and question batch (at most 128 questions per request). Each request contains only the current masked unit and matching-scope rule guidance/examples; smaller-scope requests do not receive unrelated document context.

### Python docstrings

Python `.py` and `.pyi` inputs are parsed without executing code. Each real module, class, function, or async-function docstring is decoded and cleaned independently before segmentation.

The same rule scopes apply inside that docstring. A document-scoped rule does not review the whole Python file or combine unrelated docstrings. Requests contain only the current docstring unit's masked, decoded prose. Function signatures, comments, assigned strings, and executable code are not added as context. Quote and fenced-code exemptions still apply within docstrings.

Findings map back to the original file. Evidence uses the source spelling, so escaped characters and adjacent literal concatenation can make reported evidence differ from the decoded request text. Original indentation and physical newlines inside the located span remain source context. This is not redaction: private information in a docstring's unmasked prose or visible Gherkin heading/step text is eligible for transmission.

Default directory scans include Python and `.feature` files. The default `NAS` and `RDL` selection applies to ordinary Python docstrings, extracted Marimo Markdown cells, and unmasked Gherkin heading/step prose. Those LLM rules send visible text by default unless judging is disabled or those rules are not selected. Marimo source code, widget output, Mermaid diagrams, and Gherkin fixtures are not sent. Gherkin syntax, tags, comments, tables, and docstring fixtures are masked, and scenarios are not executed. See [Marimo Markdown handling](reference/cli.md#marimo-markdown-cells) and [Gherkin feature handling](reference/cli.md#gherkin-feature-files).

### Marimo Markdown cells

Recognized Marimo `.py` apps are parsed without importing the module or running cells. Direct `mo.md()` string-literal arguments become separate documents; static f-string text is included, while interpolation expressions and other nonliteral arguments are omitted. Code comments, executable code, widget output, and Mermaid diagrams are not audited or sent to a provider. Python rule scopes apply within each extracted Markdown cell, not across the whole app.

Source maps retain original Unicode positions and source spelling through string decoding and indentation cleanup. This is not redaction: private prose in an extracted cell remains eligible for remote transmission when LLM rules are explicitly selected. Variable-derived Markdown and text generated only at runtime are outside the static extraction boundary.


### Chat judging

For each eligible unit in each selected scope, style-audit makes one synchronous `litellm.completion` request. The user message is JSON containing `scope` and masked `text`; the system prompt contains the matching-scope rule guidance and examples, treats the input as untrusted data, and instructs the model not to follow its instructions. The original unmasked document and unrelated units are not added to the request.

The model must return a JSON object containing `findings`. Each finding must include a selected `code`, a non-empty exact `evidence` quote, and a non-empty `reason`; `fix` is optional. Evidence must be a contiguous visible quote within the current unit.

The application rejects malformed JSON, unknown, disabled, or wrong-scope IDs, invalid fields, and quotes inside masked spans or outside the unit. Matching evidence is restored to original source offsets within the current unit, so equal text elsewhere cannot relocate a finding. Temperature is set to zero.


### Decisions judging

Set `api = "decisions"` in `[tool.style-audit.llm]` to use `litellm.decisions` with the OpenAI Decisions request shape. Each enabled rule becomes a named `predicate` question; LiteLLM translates it for supported providers. Style-audit does not validate provider/model compatibility; choose a model accepted by that provider's Decisions endpoint.

The API returns probabilities, not evidence quotes or rationales. A finding is emitted when the rule's probability is greater than or equal to the configured finite `threshold` in `[0, 1]` (default `0.82`); CLI `--threshold` overrides this value for one run. Its evidence and source span cover the full visible logical unit; masked code and quotation spans remain spaces. The diagnostic message combines the rule description and probability, and it has no generated fix. This is deliberately coarser than completion mode's exact quoted evidence.

With `--show-confidences`, the report includes every returned probability, including below-threshold results, with its rule, source span, and visible-unit evidence. This option is available only in Decisions mode and does not make additional provider calls. The scores are model probabilities, not calibrated measures of correctness.

The requested rule must have exactly one `predicate` answer with its requested name and a finite probability in `[0, 1]`. LiteLLM may return answers in a list or tuple. Missing, duplicate, unknown, malformed, or out-of-range answers and provider failures are operational errors, never clean results.


### Privacy, cost, and failures

Masking is a matching and evidence boundary, **not sensitive-data redaction**. Completion requests send the masked current unit and selected rules' guidance/examples. Decisions requests send the same masked unit plus rule-specific question instructions. Rule configuration is sent as written. Do not assume that masking protects secrets. There is no built-in sensitive-data redaction or caching.

Provider credentials are secrets. Keep them in an environment or secret store; do not commit them or place their values in TOML. Review provider terms and retention practices before auditing sensitive content; these are outside the tool's control.

Calls may incur charges. Completion request count is the sum of eligible unit counts across selected scopes. Decisions requests use the same units and scopes, split into batches of at most 128 questions when necessary. Adding another rule in an existing scope adds its guidance to the request; adding a new scope adds that scope's unit requests.

Scopes can overlap, so text may be sent in sentence, paragraph, section, and document requests when all are selected. Unit lengths, rule counts, and response sizes also affect token cost. Smaller scopes omit unrelated document context but can produce more calls. The tool adds no retries. Provider, transport, context-limit, and malformed-response failures are operational errors (exit `2`), never clean results. A valid empty `findings` array means only that no findings were emitted.

Confidence reports repeat visible scope evidence for each evaluated rule and can be large. They expose reviewed text in the local report, including for below-threshold scores; masking is not sensitive-data redaction.

## Limitations and evidence

Completion evidence checks prove that a returned quote occurs in its unit's visible prose; they do not prove correct rule interpretation or complete detection. Decisions mode reports a rule probability for the whole unit and does not identify the offending phrase. Neither mode establishes authorship or truth.


Results from either API may vary across real calls. Working provider credentials and model availability are required for live review. Controlled-response tests cover request boundaries, response validation, source locations, and failure handling, but do not establish live-provider behavior.

