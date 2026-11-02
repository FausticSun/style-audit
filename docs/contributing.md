# Contributing

Requires Python 3.12 or newer. Install the package, development tests, and documentation tooling with:

```sh
uv sync --group dev --group docs
```

Run the full pytest suite, documentation and docstring audits, and strict documentation build before submitting a change. Pytest runs both the existing unittest regressions and the pytest-bdd acceptance scenarios:

```sh
uv run --group dev pytest
uv run --group docs style-audit README.md docs/ --select NAS00
uv run style-audit src/ tests/ docs/hooks.py --select NAS00 --format json
uv run --group docs mkdocs build --strict
```

For a local site preview, run `uv run --group docs mkdocs serve --dev-addr 127.0.0.1:8003` and open <http://127.0.0.1:8003/>. The generated `site/` directory is ignored. Do not edit generated HTML. Restart the preview after changing Python rule metadata so the process loads the new registry.

Follow the [dogfooding workflow](dogfooding.md) to audit generated rule descriptions, exercise positive and clean controls, and review findings without confusing a clean local scan with editorial approval.

## Behavioral acceptance scenarios

Gherkin features live in `tests/bdd/features/`. The `tests/bdd/test_cli_behaviors.py` file binds them through pytest-bdd and implements their steps. Fixtures in `tests/bdd/conftest.py` provide temporary projects, isolated working directories and stdin, captured CLI output, and controlled LiteLLM providers. Unexpected chat or decision calls fail the scenario. Tests never require provider credentials.

Run only the acceptance scenarios with:

```sh
uv run --group dev pytest -m bdd -v
```

The features cover local prose, Python docstrings and non-execution, named stdin, original source locations, file/rule glob precedence, nested configuration roots, explicit LLM opt-ins and privacy, the inclusive decision threshold, fabricated chat evidence, and failure without partial JSON. They invoke the real CLI entry function, not a mocked analyzer or configuration parser.

Add scenarios for consumer-visible boundaries, transitions, precedence, and errors. Use concrete input and expected findings rather than implementation details or generated-message wording. Feature docstrings contain TOML, Python, prose, or controlled provider JSON. Data tables describe expected diagnostics. Scenario outlines keep distinct boundary cases together. The `bdd` marker selects the scenarios without changing the legacy test layout.

## Adding or changing a rule

`src/style_audit/rules.py` is the canonical combined metadata registry. Rule IDs are user-visible diagnostics and must not be reused. No-ai-slop LLM IDs (`NAS101` onward) are derived from `_SUBJECTIVE` tuple order: append only, since reordering would renumber later rules. `RDL` uses explicit IDs independent of tuple position.

The ASD-STE100 Issue 9 Part 1 adaptation is maintained in `src/style_audit/ste_rules.py`: it covers 53 numbered rules and eight recommendations with `STE`-prefixed IDs. Preserve source numbering, pinpoint page citations, original summaries, contextual exceptions, and the documented limit that Part 2 dictionary entries are not ingested. The supplied PDF's copyright notice restricts reproduction; do not copy dictionary entries into generated cards. Add or revise cards through the source catalog and its `docs/hooks.py` ruleset mapping, never by copying generated metadata.

Each rule requires an upstream citation, concise description, explicit `scope` from `RuleScope` (`sentence`, `paragraph`, `section`, or `document`), and at least one `RuleExample(before, after, explanation)`. Explain the intended context and exceptions. Preserve stated facts and do not guess missing meaning. The MkDocs hook renders cards at each ruleset page's `<!-- rule-cards -->` marker and `_rule_reference(prefix)` exports audit-friendly Markdown. Do not maintain a second rule metadata catalog.

Choose the smallest logical unit that contains the context needed for the rule: a sentence for a local construction, a paragraph for relations across sentences, a section for a heading-delimited progression, or the document for a throughline or overall balance. Scope is canonical metadata for both deterministic and LLM rules, not a user override. Consult the [segmentation contract](llm.md#canonical-scopes-and-segmentation), including conservative sentence boundaries, soft-wrapped paragraphs, nonoverlapping sections, and masks that preserve logical units. A scope change alters request grouping and diagnostic spans, so treat it as a behavior change rather than a description-only edit.

- For a narrow, literal pattern with a reliable counterexample boundary, add a local detector in `deterministic.py` and keep source offsets tied to the original text. Add positive, negative, quoted/code, and location coverage to the complete `tests/test_deterministic.py` module.
- For cadence, context, or other subjective judgments, register an LLM rule instead of creating a brittle word ban. Add behavioral response-validation cases to `tests/test_llm.py` for both chat and decision judging. Provider tests use controlled responses and must not require credentials.
- If a rule changes CLI or configuration behavior, update the corresponding reference and run the complete affected test file as well as the full test suite.

When changing judging, retain chat's exact contiguous visible-quote validation within the current unit and decision's bounded per-unit questions. Cover grouping by scope for both APIs, requests containing only matching-scope rules and masked unit text, wrong-scope IDs, sentence/paragraph/section/document boundaries, and masks that do not fragment logical units. Cover exact answer IDs and types, finite probabilities, the inclusive threshold boundary, repeated text in different units without relocation, original Unicode offsets, whole-unit decision evidence, and fully masked/whitespace input without remote requests. Deterministic coverage must preserve exact token/emoji locations and selected-rule suppression.

Decision responses use LiteLLM's typed answer objects, not chat `findings` JSON. Test CLI/TOML threshold validation and precedence without credentials. A controlled response or mocked transport demonstrates local behavior, not successful live Microsoft review. Record live evidence separately in the [dogfooding guide](dogfooding.md) only when it was actually exercised.

## Source and licensing

The initial rules adapt [Peter Yang's `no-ai-slop`](https://github.com/petergyang/no-ai-slop), pinned to commit [`000650b`](https://github.com/petergyang/no-ai-slop/commit/000650b156983f5159695b441477f4e63b25dc85). Preserve the required MIT notice in `third_party/no-ai-slop-LICENSE` when changing derived guidance. Do not claim the tool detects AI authorship.

Readability rules adapt Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald's [“Why is AI-generated language so hard to understand?”](https://arxiv.org/html/2610.29162v1), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Preserve author, title, version, license, and adaptation attribution when changing this guidance. The [readability reference](reference/readability.md) distinguishes contextual lint judgments from the paper's dependency parses, corpus baselines, n-gram measurements, and classifier cutoff. Do not introduce word-count, frequency, or comprehension thresholds and present them as findings of the paper. Preserve clear constructions and domain terms rather than adding a blanket grammar or vocabulary ban.

The `STE` catalog adapts all 53 writing rules and eight general recommendations in ASD-STE100 Issue 9 Part 1. The supplied Issue 9 PDF also contains the Part 2 controlled dictionary, which this catalog does not ingest. The generated [technical-English reference](reference/technical-english.md) records provenance, original summaries, examples, source page citations, and this scope limit. This project is independent and is not endorsed by ASD. The standard's publication notice restricts reproduction, and this repository does not reproduce the dictionary entries or source examples.
