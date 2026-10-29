# Simplified Technical English

`STE` is a source-located, original adaptation of ASD-STE100 Issue 9 (January 2025), Part 1. It covers all **53 numbered writing rules** (Rules 1.1–9.4) and all **eight general recommendations** (GR-1–GR-8): 61 entries total. IDs preserve the source hierarchy: `STE101` is Rule 1.1, `STE904` is Rule 9.4, and `STEGR1`–`STEGR8` are the recommendations.

The cards below are rendered from the canonical `style_audit.rules.RULES` catalog. Each gives an original summary, scope, engine, pinpoint Part 1 citation, and an illustrative before/after pair. General recommendations are advisory, not mandatory rules.

| Source entries | Stable IDs | Count |
| --- | --- | ---: |
| Rules 1.1–1.14 | `STE101`–`STE114` | 14 |
| Rules 2.1–2.2 | `STE201`–`STE202` | 2 |
| Rules 3.1–3.7 | `STE301`–`STE307` | 7 |
| Rules 4.1–4.5 | `STE401`–`STE405` | 5 |
| Rules 5.1–5.5 | `STE501`–`STE505` | 5 |
| Rules 6.1–6.6 | `STE601`–`STE606` | 6 |
| Rules 7.1–7.3 | `STE701`–`STE703` | 3 |
| Rules 8.1–8.7 | `STE801`–`STE807` | 7 |
| Rules 9.1–9.4 | `STE901`–`STE904` | 4 |
| Recommendations GR-1–GR-8 | `STEGR1`–`STEGR8` | 8 |
| **Total** |  | **61** |

Use deterministic checks without a provider:

```sh
style-audit draft.md --select STE606,STE801
```

`STE606` reports paragraphs with more than six sentences. `STE801` reports semicolons in visible prose while leaving masked quotations and code untouched. All other `STE` entries use contextual LLM review. Selecting one explicitly requires a model:

```sh
style-audit draft.md --select STE --model azure-maas-judge/Decision-1
```

See [configuration](../configuration.md#selection-ignoring-and-llm-opt-in) for prefix and glob selection, ignore precedence, and per-file opt-in. Review calls send the selected scoped text to the configured provider. Masking is not sensitive-data redaction. The [LLM guide](../llm.md) describes request boundaries, validation, and privacy.

## Source and limitations

The source is ASD-STE100 Issue 9, Part 1, supplied in the development workspace. ASD's [official Simplified Technical English page](https://www.asd-europe.org/standards-specifications/simplified-technical-english/) and [publication download page](https://www.asd-europe.org/standards-specifications/simplified-technical-english/download-asd-ste-100/) provide the publisher's current information. Each card cites the applicable Issue 9 rule and printed page.

These rules are review prompts, not an official compliance checker or a substitute for an authorized edition. The ASD-STE100 Part 2 dictionary, approved verb forms, company/industry glossary, risk assessments, publication specifications, and other applicable directives are not bundled. Without those resources the tool cannot certify lexical approval, terminology, safety classification, or regulatory correctness. Its LLM may ask for missing context. It must not invent technical facts or silently alter prescribed text. Review findings against the authorized source and responsible technical authority.

The publication's notice reserves rights in the document and its contents. This project does not republish the supplied PDF, its dictionary, or its examples. The rule descriptions are original summaries and the sample pairs are original illustrations. Their citations identify provenance, not endorsement or permission to reproduce the standard. ASD-STE100 is an ASD publication and registered trademark. This project is independent and is not endorsed by ASD.

<!-- rule-cards -->
