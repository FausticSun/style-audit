# Contributing

Requires Python 3.12 or newer. Install the package, development tests, and documentation tooling with:

```sh
uv sync --group dev --group docs
```

Run the full pytest suite, documentation and docstring audits, and strict documentation build before submitting a change. Pytest runs both the existing unittest regressions and the pytest-bdd acceptance scenarios:

```sh
uv run --group dev pytest
uv run --group docs style-audit README.md docs/ --select NAS00
uv run style-audit src/ tests/ docs/render_rule_cards.py --select NAS00 --format json
uv run --group docs python docs/render_rule_cards.py
uv run --group docs python docs/render_rule_cards.py --check
uv run --group docs zensical build --strict
```

For a local site preview, run `uv run --group docs zensical serve --dev-addr 127.0.0.1:8003` and open <http://127.0.0.1:8003/>. Zensical reads the compatible `mkdocs.yml`; arbitrary MkDocs hooks are unsupported, so the rule-card generator writes static Markdown before the build. The generated `site/` directory is ignored. Do not edit generated HTML.

Follow the [dogfooding workflow](dogfooding.md) to audit generated rule descriptions, exercise positive and clean controls, and review findings without confusing a clean local scan with editorial approval.

## Behavioral acceptance scenarios

Gherkin features live in `tests/bdd/features/`. The `tests/bdd/test_cli_behaviors.py` file binds them through pytest-bdd and implements their steps. Fixtures in `tests/bdd/conftest.py` provide temporary projects, isolated working directories and stdin, captured CLI output, and controlled LiteLLM providers. Unexpected provider calls fail the scenario. Tests never require provider credentials.

Run only the acceptance scenarios with:

```sh
uv run --group dev pytest -m bdd -v
```

The features cover local prose, Python docstrings and non-execution, named stdin, original source locations, file/rule glob precedence, nested configuration roots, explicit LLM opt-ins and privacy, fabricated chat evidence, response validation, and failure without partial JSON. They invoke the real CLI entry function, not a mocked analyzer or configuration parser.

Add scenarios for consumer-visible boundaries, transitions, precedence, and errors. Use concrete input and expected findings rather than implementation details or generated-message wording. Feature docstrings contain TOML, Python, prose, or controlled provider JSON. Data tables describe expected diagnostics. Scenario outlines keep distinct boundary cases together. The `bdd` marker selects the scenarios without changing the legacy test layout.

## Adding or changing a rule

`src/style_audit/rules/` contains the canonical YAML metadata files, one per ruleset; `src/style_audit/rules/__init__.py` exposes `RULES` using `rule_catalog.py`'s validated loader in stable NAS, RDL, STE, and MWG order. Rule IDs are user-visible diagnostics and must not be reused or renumbered. IDs are explicit in YAML rather than derived from tuple position, so preserve their spelling and catalog order.

The ASD-STE100 Issue 9 Part 1 adaptations live in `technical-english.yaml`: 53 numbered rules and eight recommendations with `STE`-prefixed IDs. Preserve source numbering, pinpoint page citations, original summaries, contextual exceptions, and the documented limit that Part 2 dictionary entries are not ingested. The supplied PDF's copyright notice restricts reproduction; do not copy dictionary entries into generated cards. Add or revise cards through this file and regenerate with `docs/render_rule_cards.py`, never by copying generated metadata.

Every record requires an upstream citation, explicit `scope` from `RuleScope` (`sentence`, `paragraph`, `section`, or `document`), and at least one `RuleExample(before, after, explanation)`. LLM records store their rule-specific instruction in `prompt`; the shared safety and response contract stays in `llm.py`. Deterministic records declare either a Python-regex `detector` or a typed algorithmic detector such as `sentence_count`. The YAML loader rejects duplicate IDs/keys, unknown fields, invalid scopes, and invalid regexes. `docs/render_rule_cards.py` refreshes static cards from the canonical registry at each generated-card marker; `--check` detects stale output, and `_rule_reference(prefix)` exports audit-friendly Markdown. Do not maintain a second rule metadata catalog.

Project-specific rulesets are separate from the packaged catalogs: declare their project-relative YAML paths with `[tool.style-audit].rule-catalogs` and select their IDs through the normal global, per-file, or CLI selectors. They use the same strict schema but are not part of the generated built-in rule reference.

Choose the smallest logical unit that contains the context needed for the rule: a sentence for a local construction, a paragraph for relations across sentences, a section for a heading-delimited progression, or the document for a throughline or overall balance. Scope is canonical metadata for both deterministic and LLM rules, not a user override. Consult the [segmentation contract](llm.md#canonical-scopes-and-segmentation), including conservative sentence boundaries, soft-wrapped paragraphs, nonoverlapping sections, and masks that preserve logical units. A scope change alters request grouping and diagnostic spans, so treat it as a behavior change rather than a description-only edit.

- For a narrow, literal pattern with a reliable counterexample boundary, add a `kind: regex` detector to the deterministic record in the appropriate file under `src/style_audit/rules/`. Add a new detector implementation in `deterministic.py` only when the behavior is genuinely algorithmic, and keep source offsets tied to the original text. Add positive, negative, quoted/code, and location coverage to the complete `tests/test_deterministic.py` module.
- For cadence, context, or other subjective judgments, register an LLM rule instead of creating a brittle word ban. Add chat evidence-validation and Decisions probability-response cases to `tests/test_llm.py`. Provider tests use controlled responses and must not require credentials.
- If a rule changes CLI or configuration behavior, update the corresponding reference and run the complete affected test file as well as the full test suite.

When changing judging, retain chat's exact contiguous visible-quote validation within the current unit and Decisions mode's probability, rule-name, and whole-scope evidence validation. Cover grouping by scope, requests containing only matching-scope rules and masked unit text, wrong-scope IDs, sentence/paragraph/section/document boundaries, and masks that do not fragment logical units. Cover exact finding fields, repeated text in different units without relocation, original Unicode offsets, and fully masked or whitespace input without remote requests. Deterministic coverage must preserve exact token/emoji locations and selected-rule suppression.

Chat responses use structured `findings` JSON with exact visible evidence and reasons. Decisions responses contain one finite probability per selected rule and use the configured threshold; their finding spans cover the whole visible scope unit because that API has no phrase-level evidence. Test both contracts and provider failure without credentials. Controlled responses or mocked transport demonstrate local behavior, not live-provider results. Record live evidence separately in the [dogfooding guide](dogfooding.md) only when it was actually exercised.

## Source and licensing

The initial rules adapt [Peter Yang's `no-ai-slop`](https://github.com/petergyang/no-ai-slop), pinned to commit [`000650b`](https://github.com/petergyang/no-ai-slop/commit/000650b156983f5159695b441477f4e63b25dc85). Preserve the required MIT notice in `third_party/no-ai-slop-LICENSE` when changing derived guidance. Do not claim the tool detects AI authorship.

Readability rules adapt Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald's [“Why is AI-generated language so hard to understand?”](https://arxiv.org/html/2610.29162v1), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Preserve author, title, version, license, and adaptation attribution when changing this guidance. The [readability reference](reference/readability.md) distinguishes contextual lint judgments from the paper's dependency parses, corpus baselines, n-gram measurements, and classifier cutoff. Do not introduce word-count, frequency, or comprehension thresholds and present them as findings of the paper. Preserve clear constructions and domain terms rather than adding a blanket grammar or vocabulary ban.

The `STE` catalog adapts all 53 writing rules and eight general recommendations in ASD-STE100 Issue 9 Part 1. The supplied Issue 9 PDF also contains the Part 2 controlled dictionary, which this catalog does not ingest. The generated [technical-English reference](reference/technical-english.md) records provenance, original summaries, examples, source page citations, and this scope limit. This project is independent and is not endorsed by ASD. The standard's publication notice restricts reproduction, and this repository does not reproduce the dictionary entries or source examples.

The `MWG` catalog adapts broadly applicable prose guidance from the [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/) using original summaries and examples. It excludes Microsoft brand-specific guidance, products, terminology, UI procedures, and proprietary word lists. This project is independent and is not endorsed by Microsoft.
