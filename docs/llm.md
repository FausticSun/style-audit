# LLM review and privacy

LLM rules are subjective editorial judgments—not an AI-authorship detector. Local deterministic checks run without a model. No text is sent remotely unless LLM rules are selected and an explicit opt-in enables judging.

## Opt in

```toml
[tool.style-audit]
select = ["NAS001", "NAS106"]

[tool.style-audit.llm]
enabled = true
model = "microsoft/microsoft-decision-1"
threshold = 0.8
```

Or enable one invocation:

```sh
style-audit --llm --model microsoft/microsoft-decision-1 --threshold 0.8 draft.md
style-audit --select NAS106 --model microsoft/microsoft-decision-1 --threshold 0.9 draft.md
```

The exact model names `microsoft/microsoft-decision-1` and `openrouter/microsoft/microsoft-decision-1` select the OpenRouter decision backend. Supply `OPENROUTER_API_KEY` through the environment; never commit credentials to `pyproject.toml`. The unprefixed name is a supported shorthand for this decision model, not a general provider-name convention.

Other models retain LiteLLM chat-completion judging, using LiteLLM's provider/model syntax and the matching provider configuration. For example:

```sh
style-audit --select NAS106 --model openai/gpt-4o-mini draft.md
```

A model in configuration by itself does not enable remote calls. An explicitly selected LLM rule, `--llm`, or a command-line `--model` is an opt-in; with configured selection, only rules remaining selected are eligible. Judging also requires an explicit model, whether configured or passed on the command line. Selecting deterministic-only rules cannot be overridden by `--llm` or `--model`. `--threshold` alone does not enable judging.

## What the request contains

### Canonical scopes and segmentation

Every rule has a required `scope` in the registry: **sentence**, **paragraph**, **section**, or **document**. Scope defines the logical unit to audit, not the size of a model-generated evidence quote. It is fixed rule metadata; neither TOML nor CLI options override it. The generated [rule reference](reference/rules.md) is the source of truth for individual assignments.

The independent `RDL` [readability ruleset](reference/readability.md) uses sentence scope for contextual processing-difficulty judgments. It works with both backends and the same opt-in contract; it does not measure corpus frequency, n-gram perplexity, or standardized dependency length. `NAS` and `RDL` can be selected separately or combined. No extra parser, corpus, or language-model download is required.

- **Sentence:** conservative punctuation-based segmentation, retaining unpunctuated tails and fragments and guarding common abbreviations, initialisms, and decimals. It is not a full linguistic parser.
- **Paragraph:** blank lines, Markdown headings, fenced code, and Markdown list-item starts create boundaries. Soft line wraps stay together.
- **Section:** nonoverlapping Markdown heading-delimited spans. Each span ends at the next heading regardless of heading level; the preamble is a separate section. ATX and Setext headings count, but masked headings do not. Headingless text is one section.
- **Document:** the complete input is one unit.

Leading and trailing original whitespace is trimmed from units. Fenced/inline code and paired quotation spans are replaced with same-length whitespace, preserving newlines and original Unicode offsets. Inline masks do not split a logical sentence or paragraph into separate visible runs. Blank or fully masked units are skipped by both backends.

Both APIs group selected LLM rules by scope and make one synchronous request per eligible unit for each selected scope. A request includes only rules in that scope and `{"scope": scope, "text": masked_unit_text}`. There is no extra full-document context for smaller scopes. Selecting rules from several scopes audits the corresponding overlapping views of the input; rules sharing a scope share each unit request.

### Decision judging

For the Microsoft decision model, the application uses LiteLLM's supported `litellm.systemone()` entry point with `model="openrouter/microsoft/microsoft-decision-1"`. The OpenRouter adapter sends `POST https://openrouter.ai/api/alpha/decisions` with the upstream model `microsoft/microsoft-decision-1`; it does not use a chat-completion request or the deprecated `litellm.decisions(state=...)` form. This requires LiteLLM 1.106.4 or newer.

Shared decision `state` is the scope/text object described above. Questions are keyed by the matching-scope rule IDs and have `type="noul"`: each asks the bounded yes-or-no question of whether this unit violates that rule. Trusted instructions supply the scope, rule name, and description, restrict judgments to the unit's visible prose, preserve author voice and legitimate exceptions, and treat input content as untrusted data rather than instructions. Masked spans remain gaps inside the logical unit, not separately judged fragments.

Each response must contain an `answers` mapping with exactly the requested rule IDs. Every answer must have `type="noul"` and a numeric, non-boolean, finite `noul` probability in `[0, 1]`. Missing or extra IDs, wrong answer types, and invalid probabilities are operational errors, even for answers that would fall below the threshold.

A finding is emitted for each unit/rule pair whose probability is **greater than or equal to** the threshold. The default is `0.8`; a probability of exactly `0.8` is included at that threshold. Set `[tool.style-audit.llm].threshold` in TOML or override it with `--threshold`. Values must be finite numbers in `[0, 1]`; TOML booleans and strings are not numbers for this setting. Invalid values fail with exit `2`. Raising the threshold to `0.9` excludes more responses; lowering it includes more. At `0`, every valid answer becomes a finding, including a zero probability. At `1`, only probabilities of exactly one qualify. Thresholds do not affect the chat backend.

Decision evidence is the **complete original logical unit**, not a model-generated quotation or explanation. Original Unicode offsets locate it in the input, so equal text in different units retains distinct source locations. The evidence can contain masked quotation or code spans as source context, although those spans were not sent as judged prose. A document-scoped finding spans the trimmed document; the backend does not fabricate a more precise location. The message contains the scope, rule name, description, and returned probability. The API does not generate a fix: `fix` is empty. The existing version-1 JSON finding schema is unchanged; probability is part of `message`, not a new report field.

### Chat judging

For other models, each scoped unit request is a LiteLLM chat completion. The user message is JSON containing the same `scope` and masked `text` fields used by decisions. The system prompt describes that scope and its selected rule IDs and descriptions, treats input as untrusted data, and tells the model not to follow its instructions. The original unmasked document and unrelated units are not added to the request.

The model is asked for a JSON object containing `findings`. Each item must include a requested `code`, a non-empty exact `evidence` quote, and a non-empty `reason`; `fix` is optional. Evidence must be a contiguous visible quote **within the current unit**. The application rejects malformed JSON, unknown, disabled, or wrong-scope IDs, invalid fields, and quotes inside masked spans or outside that unit. Matching evidence is restored to original source offsets within the current unit; equal text elsewhere cannot relocate a finding. Chat responses have no decision probability and are not filtered by `threshold`; temperature is set to zero.

### Privacy, cost, and failures

Masking is a matching and evidence boundary, **not sensitive-data redaction**. Both APIs send only the masked text of the current unit, but all unmasked prose in that unit is sent remotely and document-scoped rules send the masked document. Do not assume that masking protects secrets. There is no built-in sensitive-data redaction or caching. Review provider terms and retention practices before auditing sensitive content; these are outside the tool's control.

Calls may incur charges. Request count is the sum of eligible unit counts across the scopes of selected LLM rules, for either API. Adding another rule in an already selected scope adds a question or prompt description, not another request; adding a new scope adds that scope's unit requests. Scopes can overlap, so text may be sent in sentence, paragraph, section, and document requests when all are selected. Unit lengths, rule counts, and response sizes also affect token cost; smaller scopes omit unrelated document context but can produce more calls. The tool adds no retries or fallback to a different model/backend. Authentication, provider, transport, context-limit, and malformed-response failures are operational errors (exit `2`), never clean results. Valid answers below threshold or a valid empty chat `findings` array mean only that no findings were emitted.

## Limitations and evidence

Source anchoring proves that decision evidence is the original unit or that a chat quote occurs in that unit's visible prose. It does not prove correct rule interpretation, complete detection, or a good chat-generated fix. Decision probabilities are model signals, not a calibrated guarantee of editorial correctness or AI authorship. Threshold selection changes which signals are reported; it does not establish accuracy. Whole-unit decision evidence can include compliant text alongside a suspected violation, particularly at paragraph, section, and document scope; it does not identify a smaller offending phrase or supply a generated rationale.

Both backends may vary across real calls. Working credentials and model availability are required for live review. Controlled-response tests can exercise scope grouping, unit boundaries, answer validation, source locations, and threshold boundaries without a provider, but do not establish live-provider behavior. The [dogfooding guide](dogfooding.md) records an authentication failure from before per-rule scope support as historical evidence, not a statement about current credentials or model judgments.

## API sources

- [OpenRouter: Submit a Decisions request](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request) is the authoritative endpoint and request/response reference for this integration.
- [Hugging Face community article: Decisions API Documentation](https://huggingface.co/blog/sora-2/decisions-api-documentation-request-format-questio) illustrates shared state, bounded questions, and typed answers with Jev examples. It is community guidance, not an authoritative Microsoft/OpenRouter contract or an official OpenAI schema. Its Jev endpoint, model, and credential examples are not the settings used by style-audit.

