# Simplified Technical English

`STE` is a source-located, original adaptation of ASD-STE100 Issue 9 (January 2025), Part 1. It covers all **53 numbered writing rules** (Rules 1.1–9.4) and all **eight general recommendations** (GR-1–GR-8): 61 entries total. IDs preserve the source hierarchy: `STE101` is Rule 1.1, `STE904` is Rule 9.4, and `STEGR1`–`STEGR8` are the recommendations. The supplied full PDF also contains Part 2's controlled dictionary; it is not a second set of writing rules and this catalog does not parse its entries.

The cards below are grouped by Part 1 rule section, with general recommendations kept separate. They are rendered from the canonical `style_audit.rules.RULES` catalog. Each card gives an original summary, scope, engine, pinpoint Part 1 citation, and an illustrative before/after pair. General recommendations are advisory, not mandatory rules.

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

<!-- generated-rule-cards:start -->

This ruleset contains 61 entries, rendered from `style_audit.rules.RULES`. Each entry includes its canonical scope and source.

Before/after pairs illustrate a possible revision in the stated context, not recorded model outcomes or automatic fixes. See [auditing rule prose and raw examples](../dogfooding.md#audit-the-generated-rule-catalog).

## Rules 1.1–1.14

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste101" markdown="1">

## `STE101`: Lexical authorization {#ste101}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.1 (page 1-1-2). Use terms supported by the controlled vocabulary or justified as technical nouns or verbs for the relevant subject field. Do not infer approval from familiarity, rarity, or technical-sounding form. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Replace the approved component name with an informal substitute.
```

**After**

```text
Use the component name listed in the project glossary.
```

The concern is authorization in the applicable field; an editor must supply the governing dictionary or glossary.

</div>

</article>

<article class="rule-card" aria-labelledby="ste102" markdown="1">

## `STE102`: Authorized part of speech {#ste102}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.2 (page 1-1-2–1-1-3). Use an approved word only in a grammatical role that its dictionary entry permits. Check the entry before treating a familiar form as an approved noun, verb, or adjective. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The operator samples the fluid.
```

**After**

```text
The operator takes a fluid sample.
```

This is a candidate only if the authorized entry permits the noun but not the verb form in this project.

</div>

</article>

<article class="rule-card" aria-labelledby="ste103" markdown="1">

## `STE103`: Authorized word sense {#ste103}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.3 (page 1-1-4). Keep an approved word within the meaning specified for it. Use the sentence and technical context to distinguish restricted meanings; do not substitute a near-synonym without checking that it preserves the intended action or condition. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The procedure follows the green lamps to the exit.
```

**After**

```text
The procedure obeys the green-lamp instructions at the exit.
```

The first wording could assign a different sense to the verb; confirm the approved entry and actual direction before revising.

</div>

</article>

<article class="rule-card" aria-labelledby="ste104" markdown="1">

## `STE104`: Authorized inflections {#ste104}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.4 (page 1-1-4–1-1-5). Use only verb and adjective forms listed for the applicable dictionary entry. Do not assume an inflection or comparison is allowed merely because ordinary English morphology can form it. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The indicator is dimmest at this setting.
```

**After**

```text
The indicator is at its lowest-intensity setting.
```

The superlative needs review against the entry and technical meaning; the alternative is valid only if it describes the same specified condition.

</div>

</article>

<article class="rule-card" aria-labelledby="ste105" markdown="1">

## `STE105`: Technical noun categories {#ste105}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.5 (page 1-1-5–1-1-9). A non-dictionary noun may be used as a technical noun when it names a specified concept in the relevant field and fits the standard's technical-noun categories. Those categories are examples, not a complete vocabulary. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Record the drift value in the service log.
```

**After**

```text
Record the measured offset in the service log.
```

Whether drift is an authorized technical noun depends on the specified concept and field glossary; do not decide from the word alone.

</div>

</article>

<article class="rule-card" aria-labelledby="ste106" markdown="1">

## `STE106`: Nonlisted technical nouns {#ste106}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.6 (page 1-1-9–1-1-10). Use a word absent from the approved list only when it is a technical noun or part of one in this context. A word can be valid inside a technical term and unsuitable in ordinary prose. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
A second technician is available as snapshot.
```

**After**

```text
A second technician is available as a substitute.
```

The first use needs review because it does not identify a supported technical-noun sense; confirm the intended role and authorized terminology.

</div>

</article>

<article class="rule-card" aria-labelledby="ste107" markdown="1">

## `STE107`: Noun used as an action {#ste107}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.7 (page 1-1-10). Do not use a technical noun as a verb unless the same form is separately authorized as a technical verb. Keep the noun as a noun or modifier when that is its approved role. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Powder the guide rail before assembly.
```

**After**

```text
Apply powder to the guide rail before assembly.
```

This is a review candidate only if powder is authorized as a material noun but not as the action verb; verify the field vocabulary.

</div>

</article>

<article class="rule-card" aria-labelledby="ste108" markdown="1">

## `STE108`: Approved field terminology {#ste108}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.8 (page 1-1-11). Prefer the technical noun formally approved by the relevant company, industry, or subject field. Consult the governing glossary or official parts information rather than replacing a potentially controlled term with a generic synonym. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The control unit is listed as the actuator in the parts register. Later: remove the drive module.
```

**After**

```text
The control unit is listed as the actuator in the parts register. Later: remove the actuator.
```

The wording is inconsistent only if both names identify the same approved item; check the authoritative parts source first.

</div>

</article>

<article class="rule-card" aria-labelledby="ste109" markdown="1">

## `STE109`: Concise technical nouns {#ste109}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.9 (page 1-1-12). When no approved field term exists and a technical noun must be selected, prefer a short, readily understood term; the source sets a maximum of three words for that selected noun. Keep precision needed to distinguish components. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Remove the upper forward exterior access enclosure cover.
```

**After**

```text
Remove the access cover.
```

The shorter form is appropriate only if the drawing and surrounding text identify the same part unambiguously; never shorten a fixed official name.

</div>

</article>

<article class="rule-card" aria-labelledby="ste110" markdown="1">

## `STE110`: Regional and specialist jargon {#ste110}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.10 (page 1-1-12). Avoid regional, slang, or narrowly understood jargon as a technical noun when it is likely to confuse the intended readers. Prefer a familiar term only when it preserves the technical distinction. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Move your kit to the service bay.
```

**After**

```text
Move the specified tools to the service bay.
```

Kit may be local jargon for equipment; retain it if the project defines it and the audience understands it.

</div>

</article>

<article class="rule-card" aria-labelledby="ste111" markdown="1">

## `STE111`: Consistent item naming {#ste111}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.11 (page 1-1-13). Use the same approved technical noun for the same item throughout a document. First establish that two mentions refer to one item; distinct components must retain distinct names. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Disconnect the intake screen. Inspect the filter panel. Reinstall the mesh cover.
```

**After**

```text
Disconnect the intake screen. Inspect the intake screen. Reinstall the intake screen.
```

Normalize names only if the parts list confirms all three phrases refer to the same component.

</div>

</article>

<article class="rule-card" aria-labelledby="ste112" markdown="1">

## `STE112`: Technical verbs {#ste112}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.12 (page 1-1-13–1-1-15). A verb may be a technical verb when it names a specified process in a subject field. Use an accurate authorized verb; do not reject specialized verbs by rarity or approve them without the applicable glossary. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The instrument performs a numeric scan of the sample.
```

**After**

```text
The instrument scans the sample.
```

The direct verb is suitable only if scan is approved for this process and preserves the measurement meaning.

</div>

</article>

<article class="rule-card" aria-labelledby="ste113" markdown="1">

## `STE113`: Technical verb as a noun {#ste113}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.13 (page 1-1-16). Do not use a technical verb as a noun. Distinguish a true noun, an authorized participial adjective, and a noun form created from the action by checking syntax and the approved entry. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The width received a coat during processing.
```

**After**

```text
The operator coated the surface during processing.
```

Use an action verb when it expresses the intended operation; keep a legitimate technical noun or authorized adjective.

</div>

</article>

<article class="rule-card" aria-labelledby="ste114" markdown="1">

## `STE114`: American spelling default {#ste114}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

ASD-STE100 Issue 9, Part 1, Rule 1.14 (page 1-1-17). Use American English spelling unless an applicable official directive sets another variety. Preserve quoted text, official names, and mandated wording rather than normalizing them. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The centre unit controls output.
```

**After**

```text
The center unit controls output.
```

Use the American form in editable prose unless a directive specifies otherwise; preserve the exact spelling inside a quoted label.

</div>

</article>

</div>

## Rules 2.1–2.2

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste201" markdown="1">

## `STE201`: Short multi-word nouns {#ste201}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 2.1 (page 1-2-1–1-2-2). Keep a multi-word noun to three words or fewer where the intended term can be stated clearly. For a longer phrase, consider an explicit relation or a sentence construction instead of a dense modifier chain. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Check the pump seal location marker.
```

**After**

```text
Check the marker that identifies the pump-seal location.
```

Count and parse the noun phrase, but preserve a recognized indivisible technical name; the word limit is not a license to rename a component.

</div>

</article>

<article class="rule-card" aria-labelledby="ste202" markdown="1">

## `STE202`: Long official noun forms {#ste202}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

ASD-STE100 Issue 9, Part 1, Rule 2.2 (page 1-2-2–1-2-4). Write an official technical noun in full at first use. Later, define a clear shorter form or use hyphens only to join words that genuinely form one unit; do not invent groupings or obscure the name. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Install the thermal relay enclosure assembly. Then inspect the relay box.
```

**After**

```text
Install the thermal relay enclosure assembly (the relay assembly). Then inspect the relay assembly.
```

Use the shortened form only after its referent is explicit and approved; preserve official spelling and word grouping.

</div>

</article>

</div>

## Rules 3.1–3.7

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste301" markdown="1">

## `STE301`: Listed verb forms {#ste301}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.1 (page 1-3-1). Use only the forms specified for the applicable approved verb. Morphology alone cannot establish the permitted paradigm, especially for irregular forms; check the authoritative entry. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The technician gived the unit a visual check.
```

**After**

```text
The technician gave the unit a visual check.
```

The correction illustrates an irregular past form; confirm the form in the governing entry and retain the intended meaning.

</div>

</article>

<article class="rule-card" aria-labelledby="ste302" markdown="1">

## `STE302`: Permitted verb tenses {#ste302}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.2 (page 1-3-2). Use the infinitive, imperative, simple present, simple past, simple future, or a permitted past participle as an adjective. Avoid other tense or aspect constructions; do not mistake an authorized adjective or modal for one. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The operator has been checking the pressure.
```

**After**

```text
The operator checked the pressure.
```

The simple-past alternative is valid only if it preserves the time and completion facts of the original.

</div>

</article>

<article class="rule-card" aria-labelledby="ste303" markdown="1">

## `STE303`: Past participles as adjectives {#ste303}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.3 (page 1-3-2–1-3-3). Use a permitted past-participle form as an adjective to describe a condition, before a noun or after an appropriate linking verb. Verify that the entry allows the form; not every participle is an adjective. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Inspect the part that was sealed assembly.
```

**After**

```text
Inspect the sealed assembly.
```

The shorter modifier is valid only if sealed is authorized and describes the assembly's state, not a separate event.

</div>

</article>

<article class="rule-card" aria-labelledby="ste304" markdown="1">

## `STE304`: Complex auxiliary constructions {#ste304}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.4 (page 1-3-3). Avoid auxiliary combinations that create disallowed complex verb constructions, including unneeded perfect and passive forms. Keep allowed modal meaning and use active wording only when it preserves the agent and technical facts. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The setting has been adjusted by the operator.
```

**After**

```text
The operator adjusted the setting.
```

Use the active form only if the operator is the established agent and the perfect aspect is not technically important.

</div>

</article>

<article class="rule-card" aria-labelledby="ste305" markdown="1">

## `STE305`: Verb-ing forms {#ste305}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.5 (page 1-3-4–1-3-5). Use an -ing verb form only as a technical noun or as a modifier inside a technical noun. Do not treat every word ending in -ing as a verb: nouns, approved adjectives, prepositions, and established terms are exceptions. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
While opening the cabinet, check the indicator.
```

**After**

```text
Before you open the cabinet, check the indicator.
```

The first phrase describes an ongoing action; preserve -ing forms when they are authorized nouns or modifiers in a technical term.

</div>

</article>

<article class="rule-card" aria-labelledby="ste306" markdown="1">

## `STE306`: Active voice and known agents {#ste306}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.6 (page 1-3-5–1-3-8). Prefer active voice. In descriptive text, passive voice is appropriate only when the agent is unknown; do not invent an agent or change causation to force an active sentence. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The result is stored by the controller.
```

**After**

```text
The controller stores the result.
```

Use the active version only if the controller is the verified agent; an unknown agent can justify passive voice in descriptive text.

</div>

</article>

<article class="rule-card" aria-labelledby="ste307" markdown="1">

## `STE307`: Verbs for actions {#ste307}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 3.7 (page 1-3-9). Describe an action with an approved verb rather than an action noun or another part of speech when the verb states the same operation clearly. Check approval and preserve the original technical meaning. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Before panel removal, perform an isolation of the supply.
```

**After**

```text
Before you remove the panel, isolate the supply.
```

The direct actions are appropriate only if remove and isolate are authorized and do not alter a required instruction.

</div>

</article>

</div>

## Rules 4.1–4.5

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste401" markdown="1">

## `STE401`: Clear sentence structure {#ste401}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 4.1 (page 1-4-1–1-4-2). Write clearly and directly. In procedures, make the instruction and action easy to identify; in descriptive prose, keep one main subject or idea per sentence and build details gradually. Avoid unsupported abstraction, not useful technical qualification. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The unit provides a comprehensive indication of operating status across several areas.
```

**After**

```text
The unit shows the input voltage and the fault state.
```

Use concrete details only when supported by the source; do not invent specifications to make a sentence appear precise.

</div>

</article>

<article class="rule-card" aria-labelledby="ste402" markdown="1">

## `STE402`: Complete wording {#ste402}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 4.2 (page 1-4-3). Do not shorten a sentence by omitting words needed to identify its subject, action, object, or article, or by using a contraction. Distinguish genuine omissions from concise but grammatical technical labels and preserve verbatim text. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
If loose, don’t tighten.
```

**After**

```text
If the latch is loose, do not tighten it.
```

The revision is suitable only when the latch is the intended referent and the instruction's meaning is unchanged.

</div>

</article>

<article class="rule-card" aria-labelledby="ste403" markdown="1">

## `STE403`: Vertical-list structure {#ste403}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 4.3 (page 1-4-4–1-4-6). Use a vertical list for complex groups of items or actions. Connect the lead-in with a colon, identify each item, capitalize the start, and punctuate complete sentences differently from fragments; avoid trailing commas or semicolons and end the final item with a period. Keep procedure and description separate within a list; follow official layout directives. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Prepare the kit: tray, cable, guide, and clamp.
```

**After**

```text
Prepare the kit as follows:
- The tray
- The cable
- The guide
- The clamp.
```

A vertical layout helps only when the content is a complex list; list item grammar and publication-specific symbols still need review.

</div>

</article>

<article class="rule-card" aria-labelledby="ste404" markdown="1">

## `STE404`: Logical sentence connections {#ste404}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 4.4 (page 1-4-7). Use an appropriate connecting word or phrase when it clarifies how one sentence relates to the next. Choose a connector that accurately expresses addition, contrast, sequence, or result; do not add one mechanically. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The filter blocks dust. However, the downstream air is clean.
```

**After**

```text
The filter blocks dust. Thus, the downstream air is clean.
```

The causal connector is correct only if the filter explains the stated result; check the technical relationship and approved vocabulary.

</div>

</article>

<article class="rule-card" aria-labelledby="ste405" markdown="1">

## `STE405`: Articles and demonstratives {#ste405}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 4.5 (page 1-4-8–1-4-9). Where grammar and meaning require it, use an article or demonstrative before a noun or multi-word noun. Avoid omissions that obscure a specific referent; do not force articles into general or abstract statements. Do not put a definite article before a noun followed by an alphanumeric identifier. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Install gasket on the bracket.
```

**After**

```text
Install the gasket on the bracket.
```

The article is needed only if a specific gasket and bracket are intended; bare nouns can be correct in general statements.

</div>

</article>

</div>

## Rules 5.1–5.5

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste501" markdown="1">

## `STE501`: Procedural sentence length {#ste501}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 5.1 (page 1-5-1–1-5-2). Limit each procedural sentence, including safety instructions, to 20 words. Exclude notes, which have a separate limit. Apply the Section 8 counting conventions, including list lead-ins and items; do not use whitespace splitting as a substitute. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Before the scheduled service begins, make sure that every access panel is secured and the work area is clear of loose objects.
```

**After**

```text
Before service, secure every access panel. Clear loose objects from the work area.
```

The limit is 20 words per procedural sentence; classify the text and count using the applicable Section 8 conventions.

</div>

</article>

<article class="rule-card" aria-labelledby="ste502" markdown="1">

## `STE502`: One instruction per sentence {#ste502}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 5.2 (page 1-5-2–1-5-3). Normally give one instruction per sentence and separate actions into steps when they do not occur together. Multiple actions may share a sentence when simultaneous; a work step may use multiple sentences for simultaneous actions or an immediate result. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Open the guard and remove the insert.
```

**After**

```text
Open the guard. Remove the insert.
```

Separate actions only when they are sequential; preserve an established simultaneous operation or immediate result within its work step.

</div>

</article>

<article class="rule-card" aria-labelledby="ste503" markdown="1">

## `STE503`: Imperative instructions {#ste503}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 5.3 (page 1-5-3–1-5-4). Write a work instruction in the imperative form. Do not add must before the command except for an important safety instruction or important condition. Distinguish instructions from description and do not change legal force. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The blue key should be pressed to reset the display.
```

**After**

```text
Press the blue key to reset the display.
```

The command is suitable only if the text is a work instruction and not a descriptive or legally constrained statement.

</div>

</article>

<article class="rule-card" aria-labelledby="ste504" markdown="1">

## `STE504`: Condition before command {#ste504}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 5.4 (page 1-5-4). When a reader must know a condition before acting, state the condition first and separate it from the imperative command with a comma. Preserve clause scope because punctuation can change the meaning. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Release the latch when the indicator turns green.
```

**After**

```text
When the indicator turns green, release the latch.
```

Move the condition to the front only when the reader needs it before starting the action and the condition remains unchanged.

</div>

</article>

<article class="rule-card" aria-labelledby="ste505" markdown="1">

## `STE505`: Informational notes {#ste505}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

ASD-STE100 Issue 9, Part 1, Rule 5.5 (page 1-5-5–1-5-7). Use notes for information, not commands, requirements, limits, tolerances, or work-step results. Each note sentence is at most 25 words. A procedure must remain performable without its notes; place essential or safety information in the appropriate step. Use notes in descriptions only when they support an illustration or table. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
NOTE: Press the reset key before leaving the area.
```

**After**

```text
(Work step) Press the reset key before you leave the area.
```

The note contains a command; review the whole procedure and move required actions to a work step without losing safety context.

</div>

</article>

</div>

## Rules 6.1–6.6

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste601" markdown="1">

## `STE601`: Gradual descriptive flow {#ste601}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 6.1 (page 1-6-1–1-6-2). In descriptive text, introduce information progressively and keep each sentence focused on one subject or idea. Avoid imperative wording in descriptions; retain accurate detail and necessary qualifications. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The cabinet contains a fan, alarm, drain, backup supply, and controller, all of which react differently during a power loss.
```

**After**

```text
The cabinet contains a fan. The alarm signals a fault. The drain removes collected water. The controller manages the backup supply.
```

Split only where each sentence remains technically accurate and the system relationships are supported by source material.

</div>

</article>

<article class="rule-card" aria-labelledby="ste602" markdown="1">

## `STE602`: Key terms and logical flow {#ste602}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 6.2 (page 1-6-2–1-6-3). Use recurring key words or phrases to make relationships between ideas visible. Keep terminology stable, and use connecting words only when they express the actual logical relation. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The file is encrypted. This safeguard limits access. The protection is removed after review.
```

**After**

```text
The file is encrypted. This protection limits access. The protection is removed after review.
```

Repeat a term when it denotes the same concept; preserve a different term when the system defines a real distinction.

</div>

</article>

<article class="rule-card" aria-labelledby="ste603" markdown="1">

## `STE603`: Descriptive sentence length {#ste603}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 6.3 (page 1-6-4). Limit each descriptive sentence to 25 words. Use the Section 8 word-count conventions; do not apply this limit to procedural text, which has a separate threshold. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The controller records the room temperature, sends the reading to the display, stores a copy in memory, and updates the maintenance log after each routine measurement is complete.
```

**After**

```text
The controller records the room temperature. It sends the reading to the display and stores a copy in memory.
```

Count descriptive sentences with Section 8 conventions and split only if each new sentence preserves the stated facts.

</div>

</article>

<article class="rule-card" aria-labelledby="ste604" markdown="1">

## `STE604`: Related paragraph structure {#ste604}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

ASD-STE100 Issue 9, Part 1, Rule 6.4 (page 1-6-5). Use paragraph breaks to group related descriptive information and show its sequence. An opening topic sentence can orient the reader before details; do not split lists, tables, or other structured material as if they were prose paragraphs. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
A paragraph begins with sensor operation, then shifts without transition to access-badge replacement.
```

**After**

```text
Keep the sensor description together. Start a separate paragraph for access-badge replacement.
```

Choose a break where the subject changes; preserve supporting details that belong to the original topic.

</div>

</article>

<article class="rule-card" aria-labelledby="ste605" markdown="1">

## `STE605`: One topic per paragraph {#ste605}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 6.5 (page 1-6-6). Keep a descriptive paragraph focused on one topic. Its opening sentence should identify the topic and connect new information to the preceding text; following sentences develop that topic. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The meter records humidity. Its display uses three zones. Access badges must be returned at shift end.
```

**After**

```text
The meter records humidity. Its display uses three zones.

Return access badges at shift end.
```

The last sentence changes the subject; retain it in the paragraph if the surrounding document supplies a clear relationship.

</div>

</article>

<article class="rule-card" aria-labelledby="ste606" markdown="1">

## `STE606`: Paragraph sentence maximum {#ste606}

<div class="rule-card-meta" markdown="1">

Engine: `deterministic` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 6.6 (page 1-6-7). Keep a paragraph to no more than six sentences. Flag only a paragraph with seven or more; choose a split that preserves topic unity and respects abbreviations, lists, and structured content. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The case stores the adapter. It has a hinged lid. The hinge allows full opening. A seal reduces dust. Two clips hold the lid. The label shows the model. The label also gives the batch code.
```

**After**

```text
The case stores the adapter. It has a hinged lid. The hinge allows full opening. A seal reduces dust. Two clips hold the lid.

The label shows the model. The label also gives the batch code.
```

Six sentences are allowed; a seventh exceeds the cap, but the paragraph break still needs to respect the topic.

</div>

</article>

</div>

## Rules 7.1–7.3

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste701" markdown="1">

## `STE701`: Safety risk signal {#ste701}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 7.1 (page 1-7-2). Identify the risk level of a safety instruction promptly with the signal word or symbol required by the governing safety and publication standards. Risk classification requires a technical risk assessment. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
CAUTION: Isolate the supply before opening the enclosure. Unexpected energization can injure the operator.
```

**After**

```text
WARNING: Isolate the supply before opening the enclosure. Unexpected energization can injure the operator.
```

The label depends on the approved risk assessment; never down-classify a risk to fit a text rule or guess from wording alone.

</div>

</article>

<article class="rule-card" aria-labelledby="ste702" markdown="1">

## `STE702`: Safety instruction lead {#ste702}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 7.2 (page 1-7-3). Begin a safety instruction with an accurate command or with a condition the reader must know before acting. Keep any condition that must precede the work step in that position. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
WARNING: The enclosure presents an electrical hazard. Isolate its power before opening it.
```

**After**

```text
WARNING: Before opening the enclosure, isolate its power source.
```

Use the condition-first form only when supported by the safe procedure; do not invent or reorder a critical condition.

</div>

</article>

<article class="rule-card" aria-labelledby="ste703" markdown="1">

## `STE703`: Safety consequence {#ste703}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 7.3 (page 1-7-4). Where feasible, explain the credible harm or result that may occur if the safety instruction is not followed. Use the approved risk assessment; do not fabricate a hazard or consequence. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
WARNING: Keep clear of the moving carriage. This is important.
```

**After**

```text
WARNING: Keep clear of the moving carriage. It can strike a person during travel.
```

Include a consequence only when the technical risk assessment supports it; a generic emphasis sentence is not an explanation.

</div>

</article>

</div>

## Rules 8.1–8.7

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste801" markdown="1">

## `STE801`: Semicolon punctuation {#ste801}

<div class="rule-card-meta" markdown="1">

Engine: `deterministic` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.1 (page 1-8-1–1-8-2). Use standard English punctuation except for the semicolon, which is not permitted in editable STE prose. Preserve fixed quotations, labels, titles, and other immutable text. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Inspect the removed parts; replace damaged items.
```

**After**

```text
Inspect the removed parts. Replace damaged items.
```

A semicolon is directly detectable in visible prose; preserve protected source text and use a sentence boundary only when the meaning supports it.

</div>

</article>

<article class="rule-card" aria-labelledby="ste802" markdown="1">

## `STE802`: Hyphenated compounds {#ste802}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.2 (page 1-8-2). Use a hyphen where it accurately connects words or word parts that function together. Do not join unrelated words or alter an official term; distinguish hyphens from dashes. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Install the low speed sensor.
```

**After**

```text
Install the low-speed sensor.
```

Hyphenate only if low-speed is the intended unit and matches the approved technical term.

</div>

</article>

<article class="rule-card" aria-labelledby="ste803" markdown="1">

## `STE803`: Parenthetical uses {#ste803}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.3 (page 1-8-3–1-8-4). Use parentheses for supported functions such as references, identifiers, work-step labels, abbreviations, singular/plural forms, explanations, or alternatives. Preserve exact technical identifiers and official text. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The controller shows (very important) the measured value.
```

**After**

```text
The controller shows the measured value.
```

Parentheses are useful for specified references and explanations, not as a detached emphasis device.

</div>

</article>

<article class="rule-card" aria-labelledby="ste804" markdown="1">

## `STE804`: Vertical-list word counting {#ste804}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.4 (page 1-8-4). For word-count limits, treat the colon before a vertical list as the end of its lead-in sentence and count each following list item as a new sentence. Apply the procedural or descriptive limit to each part. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Count a vertical-list introduction and its items as one sentence.
```

**After**

```text
Count the introduction and each vertical-list item separately.
```

The colon ends the lead-in sentence; every item is a separate sentence for the relevant limit.

</div>

</article>

<article class="rule-card" aria-labelledby="ste805" markdown="1">

## `STE805`: Parenthetical word counting {#ste805}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.5 (page 1-8-5). Count parenthetical text as one word in the containing sentence. If it is itself a sentence, count that separately; do not count its internal words again in the outer sentence. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Check the seal (before startup) for damage.
```

**After**

```text
Check the seal before startup for damage.
```

The parenthetical span counts as one outer-sentence word; its own sentence, if any, has a separate count.

</div>

</article>

<article class="rule-card" aria-labelledby="ste806" markdown="1">

## `STE806`: Special word-count units {#ste806}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.6 (page 1-8-5–1-8-8). For sentence-length counts, treat numbers, number-plus-unit expressions, abbreviations, alphanumeric identifiers, quoted spans, titles/headings/label text, and covered proper nouns as one word each. Exclude paragraph and step numbers used only as numbering. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Check 24 V at connector J14 before the North Wing Service Display is reset.
```

**After**

```text
Check 24 volts at connector J14 before the North Wing Service Display is reset.
```

The number with its unit, identifier, title, and proper name each count as one word; retain their exact technical content.

</div>

</article>

<article class="rule-card" aria-labelledby="ste807" markdown="1">

## `STE807`: Hyphenated word counting {#ste807}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 8.7 (page 1-8-8). Count a hyphenated word as one word. This counting convention does not decide whether the term should be hyphenated; preserve approved spelling and distinguish dashes. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Count two-piece as two words.
```

**After**

```text
Count two-piece as one word.
```

The hyphenated token counts as one word; this convention does not determine whether the term should use a hyphen.

</div>

</article>

</div>

## Rules 9.1–9.4

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="ste901" markdown="1">

## `STE901`: Meaning-preserving recast {#ste901}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 9.1 (page 1-9-1–1-9-4). If a word-for-word replacement is unavailable or changes meaning, recast the sentence with approved words and grammar while preserving its intended information. Ask for the missing meaning rather than guessing. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The access code is unacceptable.
```

**After**

```text
The system does not accept the access code.
```

The recast is valid only if the system's behavior is the intended meaning; do not select a superficially similar but incorrect alternative.

</div>

</article>

<article class="rule-card" aria-labelledby="ste902" markdown="1">

## `STE902`: Word meaning and role {#ste902}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 9.2 (page 1-9-5–1-9-6). Use each approved word with the dictionary meaning and part of speech that fit the context. Check restricted senses and roles against the authorized entry; a spelling match does not establish correct use. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Use wear to mean that the bearing loses material through friction.
```

**After**

```text
Use the specified verb for material loss through friction.
```

The word's permitted role and sense require the official entry; preserve a known technical meaning rather than substituting by guess.

</div>

</article>

<article class="rule-card" aria-labelledby="ste903" markdown="1">

## `STE903`: Phrasal-verb meaning {#ste903}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, Rule 9.3 (page 1-9-7). Do not combine words into a phrasal verb whose meaning differs from the authorized meanings of its parts, unless that phrasal use is explicitly approved. Literal combinations and approved restricted uses are not violations. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
After you put out the fire, close the valve.
```

**After**

```text
After you extinguish the fire, close the valve.
```

Use extinguish only if it is authorized and preserves the required action; check whether the original phrase is literal or approved.

</div>

</article>

<article class="rule-card" aria-labelledby="ste904" markdown="1">

## `STE904`: Consistent wording {#ste904}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

ASD-STE100 Issue 9, Part 1, Rule 9.4 (page 1-9-8). Use the same terminology and phrasing for repeated items or actions when their context and meaning are the same. Preserve different wording when it represents a real technical distinction or changed condition. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Lubricate the fasteners with oil. Apply oil to the bolt threads.
```

**After**

```text
Lubricate the fasteners with oil. Lubricate the bolt threads with oil.
```

Standardize only if the phrases describe the same action and scope; the second may refer to a more specific surface.

</div>

</article>

</div>

## General recommendations (GR-1–GR-8)

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="stegr1" markdown="1">

## `STEGR1`: That for clause clarity {#stegr1}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, GR-1 (page 1-9-9). Consider including the conjunction that when it makes a subordinate-clause boundary easier to follow or supports translation. This is a recommendation, not a blanket insertion requirement. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The display confirms the cycle is complete after the controller reports the result.
```

**After**

```text
The display confirms that the cycle is complete after the controller reports the result.
```

Add that only if it clarifies the intended clause and does not make the sentence ungrammatical or change its reading.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr2" markdown="1">

## `STEGR2`: Ambiguous with {#stegr2}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, GR-2 (page 1-9-10). Review with for ambiguity between association, accompaniment, assistance, or means. Recast only when context leaves the intended relation unclear, and preserve the main action. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Attach the panel with the silver clips.
```

**After**

```text
Attach the panel using the two silver clips.
```

The rewrite selects an instrument reading; confirm that the clips are the means of attachment rather than a feature of the panel.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr3" markdown="1">

## `STEGR3`: Pronoun reference {#stegr3}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, GR-3 (page 1-9-11). Use pronouns allowed by the applicable dictionary and replace one whose possible antecedents make the intended reference unclear. Confirm authorization and referent rather than banning a pronoun by form alone. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Align the guide with the rail. It must remain level.
```

**After**

```text
Align the guide with the rail. The rail must remain level.
```

Name the intended referent only after checking which item must remain level and the approved pronoun inventory.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr4" markdown="1">

## `STEGR4`: Referent of this {#stegr4}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, GR-4 (page 1-9-11). Make the referent of this clear. Restate the relevant item, event, or condition when more than one interpretation is plausible; do not invent a cause. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Open the lid beside the sensor. This can cause a fault.
```

**After**

```text
Open the lid beside the sensor. An open lid can cause a sensor fault.
```

The explicit cause must be verified; retain the original wording if context shows another intended referent.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr5" markdown="1">

## `STEGR5`: False-friend review {#stegr5}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, GR-5 (page 1-9-12). For readers working across languages, check that a word has its intended English sense rather than a similar-looking word's meaning in another language. Ask for language and meaning context; do not infer an error from unfamiliar wording. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
The vendor's disposition is attached to the work order.
```

**After**

```text
The vendor's instructions are attached to the work order.
```

The replacement is correct only if disposition was intended to mean instructions; check the source-language context first.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr6" markdown="1">

## `STEGR6`: Latin abbreviation alternatives {#stegr6}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, GR-6 (page 1-9-12). Consider replacing Latin abbreviations such as e.g., i.e., or etc. with clear English words when readers may not know them. This is a recommendation; retain necessary, official, or protected forms. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Inspect the connectors, e.g., the blue and green leads.
```

**After**

```text
Inspect the connectors, for example, the blue and green leads.
```

Expand only when the English wording preserves the intended relationship and helps this audience.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr7" markdown="1">

## `STEGR7`: Inclusive wording {#stegr7}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

ASD-STE100 Issue 9, Part 1, GR-7 (page 1-9-13). Prefer neutral, non-discriminatory wording and gender-neutral language in ordinary technical prose. Review known gendered terms in context; follow applicable organizational and official guidance. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Each technician must return his access card to the supervisor.
```

**After**

```text
Each technician must return the access card to the supervisor.
```

Use neutral wording when it preserves the intended referent; retain gender-specific language when a necessary, supported context requires it.

</div>

</article>

<article class="rule-card" aria-labelledby="stegr8" markdown="1">

## `STEGR8`: Possessive form {#stegr8}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

ASD-STE100 Issue 9, Part 1, GR-8 (page 1-9-13). The possessive apostrophe form is permitted, but use it correctly. When its ownership or association is unclear, choose an explicit alternative only if it preserves the intended relationship. This is a recommendation, not a mandatory rule. The supplied Issue 9 PDF includes Part 2's controlled dictionary, but this catalog does not ingest its entries or project terminology. Use the authorized, applicable vocabulary when it determines review; do not guess or certify technical facts.

[Upstream source](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)

<div class="rule-example" markdown="1">

**Before**

```text
Return the inspectors key to the desk.
```

**After**

```text
Return the inspector's key to the desk.
```

The apostrophe changes singular/plural ownership; confirm which inspector or inspectors own the key before editing.

</div>

</article>

</div>

<!-- generated-rule-cards:end -->

Use deterministic checks without a provider:

```sh
style-audit draft.md --select STE606,STE801
```

`STE606` reports paragraphs with more than six sentences. `STE801` reports semicolons in visible prose while leaving masked quotations and code untouched. All other `STE` entries use contextual LLM review. Selecting one explicitly opts into review; chat completions use `openrouter/openrouter/free` unless overridden, while Decisions requires an explicit provider-supported model:

```sh
style-audit draft.md --select STE --model openrouter/openrouter/free
```

See [configuration](../configuration.md#selection-ignoring-and-llm-opt-in) for prefix and glob selection, ignore precedence, and per-file opt-in. Review calls send the selected scoped text to the configured provider. Masking is not sensitive-data redaction. The [LLM guide](../llm.md) describes request boundaries, validation, and privacy.

## Source and limitations

The rule summaries derive from ASD-STE100 Issue 9, Part 1, in the supplied PDF. ASD's [official Simplified Technical English page](https://www.asd-europe.org/standards-specifications/simplified-technical-english/) and [publication download page](https://www.asd-europe.org/standards-specifications/simplified-technical-english/download-asd-ste-100/) provide the publisher's current information. Each card cites the applicable Issue 9 rule and printed page.

These rules are review prompts, not an official compliance checker or a substitute for an authorized edition. The supplied PDF contains Part 2's controlled dictionary, but this linter does not parse its entries, approved forms, or project/company glossaries; risk assessments, publication specifications, and other applicable directives also remain external. It cannot certify lexical approval, terminology, safety classification, or regulatory correctness. Its LLM may request missing context but must not invent technical facts or silently alter prescribed text. Review findings against the source with the responsible technical authority. The PDF's copyright notice restricts reproduction; its availability in this workspace does not grant permission to republish dictionary entries.

The publication's notice reserves rights in the document and its contents. This project does not republish the supplied PDF, its dictionary, or its examples. The rule descriptions are original summaries and the sample pairs are original illustrations. Their citations identify provenance, not endorsement or permission to reproduce the standard. ASD-STE100 is an ASD publication and registered trademark. This project is independent and is not endorsed by ASD.

