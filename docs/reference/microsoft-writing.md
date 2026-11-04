# Microsoft Writing Style (general)

`MWG` adapts broadly applicable writing guidance from the [Microsoft Writing Style Guide](https://learn.microsoft.com/en-us/style-guide/). The rules use original summaries and examples. They exclude Microsoft brand-specific guidance, product names and terminology, UI procedures, and proprietary word lists. This project is independent and is not endorsed by Microsoft.

All rules use contextual LLM judgments. Selecting `MWG` opts into remote review and sends visible prose and rule guidance to the configured provider. Review the [LLM privacy and cost guidance](../llm.md) before enabling it. The default Markdown selection is unchanged.

<!-- generated-rule-cards:start -->

This ruleset contains 13 rules, rendered from `style_audit.rules.RULES`. Each entry includes its canonical scope and source.

Before/after pairs illustrate a possible revision in the stated context, not recorded model outcomes or automatic fixes. See [auditing rule prose and raw examples](../dogfooding.md#audit-the-generated-rule-catalog).

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="mwg001" markdown="1">

## `MWG001`: Reader-first message order {#mwg001}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Review whether the paragraph makes its most important reader-relevant point, result, or next step clear early. Flag only when needed information is buried beneath setup or repeated background. Preserve useful context, narrative sequence, suspense, emphasis, and uncertainty; do not force every paragraph to lead with a conclusion or invent actions.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice)

<div class="rule-example" markdown="1">

**Before**

```text
We compared the options with the team's needs, including operating costs and the expected migration work. The team recommends the hosted option.
```

**After**

```text
The team recommends the hosted option after weighing operating costs and expected migration work against its needs.
```

State the recommendation first, then give the factors that support it.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg002" markdown="1">

## `MWG002`: Plain, audience-fit wording {#mwg002}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Flag jargon, unnecessarily complex wording, or ambiguous common words only when a familiar precise word or a brief explanation would better fit the intended audience. Preserve necessary technical terms, established terminology, and expert vocabulary when they are accurate and clear in context. Do not treat rarity alone as a problem.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/word-choice/use-simple-words-concise-sentences)

<div class="rule-example" markdown="1">

**Before**

```text
The service facilitates the transfer of files.
```

**After**

```text
The service transfers files.
```

The direct verb names the action without obscuring it in a formal phrase.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg003" markdown="1">

## `MWG003`: Concision with meaning intact {#mwg003}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Flag repeated ideas, empty modifiers, or phrases that add no substance and delay the point. Suggest a shorter expression only when it preserves qualifications, reasoning, uncertainty, technical precision, and useful context. Brevity is not a goal by itself; preserve intentional emphasis and voice.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/word-choice/use-simple-words-concise-sentences)

<div class="rule-example" markdown="1">

**Before**

```text
At this point in time, we're currently reviewing every individual request separately.
```

**After**

```text
We're reviewing each request separately.
```

The opening and modifiers repeat information already expressed by currently and individually.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg004" markdown="1">

## `MWG004`: Natural, context-appropriate voice {#mwg004}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Flag wording that is needlessly stiff, impersonal, or distant when natural language would preserve the meaning and suit the audience. Prefer a warm, human, conversational tone when the context allows it. Do not force contractions, slang, jokes, cheerfulness, or informality; keep the author's voice and adapt to serious, expert, and formal contexts.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice)

<div class="rule-example" markdown="1">

**Before**

```text
We are pleased to inform you that the review has now been completed.
```

**After**

```text
We've completed the review.
```

The direct, natural sentence keeps the update without its ceremonial framing.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg005" markdown="1">

## `MWG005`: Clear sentence construction {#mwg005}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag only syntax that makes the actor, action, relationships, or modifiers hard to follow. Consider direct wording or active voice when it makes agency clearer, and simplify nested clauses or long modifier chains when they impede understanding. Preserve meaningful passive voice, technical precision, and long but clear sentences; do not require active voice universally or impose a word or verb count.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/grammar/grammar-and-parts-of-speech)

<div class="rule-example" markdown="1">

**Before**

```text
The committee's approval of the proposal was granted after review by the staff.
```

**After**

```text
The committee approved the proposal after the staff reviewed it.
```

The revision names the actors and actions directly without changing their order.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg006" markdown="1">

## `MWG006`: Consistent terms and useful acronyms {#mwg006}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

Check whether the same term is used consistently for the same concept and whether unfamiliar acronyms are introduced only when useful, defined on first use, and reused consistently. Avoid one-off abbreviations when spelling out the term is clearer. Preserve familiar acronyms, established domain vocabulary, proper names, quotations, and deliberate distinctions. Do not infer unfamiliarity from word frequency alone.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/checklists/acronyms-checklist)

<div class="rule-example" markdown="1">

**Before**

```text
The service-level objective guides alerts. The SLO also sets the alert target.
```

**After**

```text
The service-level objective (SLO) guides alerts. The SLO also sets the alert target.
```

Define a useful, audience-relevant abbreviation on its first occurrence.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg007" markdown="1">

## `MWG007`: Scannable section organization {#mwg007}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

Review whether this section is organized into meaningful, easy-to-scan parts. When dense material covers distinct topics, suggest a logical order, concise paragraphs, or descriptive hierarchical headings. Avoid redundant headings, empty structure, and breaking a short coherent passage into needless fragments. Keep key information easy to locate without imposing a fixed paragraph or section length.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/scannable-content/headings)

<div class="rule-example" markdown="1">

**Before**

```text
## Service update
A stale certificate caused 12 minutes of downtime. The team replaced the certificate. It added an expiry alert. The team published a recovery checklist.
```

**After**

```text
## Cause
A stale certificate caused 12 minutes of downtime.
## Recovery
The team replaced the certificate.
## Prevention
The team added an expiry alert and published a recovery checklist.
```

Separate the cause, recovery, and prevention details so readers can scan for the information they need.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg008" markdown="1">

## `MWG008`: Clear, consistent headings {#mwg008}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

Check whether headings are specific, concise, and parallel with headings at the same level. For this style, use sentence-style capitalization by default and omit a final period or colon. Preserve proper nouns, established names, cited titles, and meaningful question marks. Do not demand headings for short content or change a title merely to impose uniformity.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/scannable-content/headings)

<div class="rule-example" markdown="1">

**Before**

```text
## Reviewing Drafts:
```

**After**

```text
## Reviewing drafts
```

The heading uses sentence-style capitalization and does not end in punctuation.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg009" markdown="1">

## `MWG009`: Purposeful, parallel lists {#mwg009}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

Review lists in this section for a clear purpose and lead-in. Use numbering when order or priority matters and bullets for unordered related items. Keep comparable items grammatically parallel and their capitalization and ending punctuation consistent with whether they are fragments or complete sentences. Prefer prose when a list does not improve scanning. Do not impose a fixed item-count limit.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/scannable-content/lists)

<div class="rule-example" markdown="1">

**Before**

```text
The review includes:
- Drafting the proposal - The budget is checked - Confirming the dates
```

**After**

```text
The review includes:
- Draft the proposal. - Check the budget. - Confirm the dates.
```

The list items are parallel commands with consistent sentence punctuation.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg010" markdown="1">

## `MWG010`: Clear, consistent punctuation {#mwg010}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Review punctuation for clarity and consistency with this guide's broad conventions: use the serial comma, one space after sentence punctuation, and no spaces around em dashes; use a colon for a list introduced by a phrase. Use exclamation points and rhetorical questions sparingly, and prefer simpler punctuation when a sentence is overloaded. Respect quotations, code, literal text, and contexts with a different convention; flag a variation only when it causes clear inconsistency or confusion.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/checklists/punctuation-checklist)

<div class="rule-example" markdown="1">

**Before**

```text
We invited editors, designers and translators.
```

**After**

```text
We invited editors, designers, and translators.
```

The serial comma makes the final list boundary explicit and follows this style's convention.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg011" markdown="1">

## `MWG011`: Consistent number style {#mwg011}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

In ordinary prose, spell out zero through nine and sentence-initial numbers; use numerals for 10 and above. Use a consistent format for numbers in the same category when one requires numerals, while separate categories can use their appropriate formats. Use numerals for measurements, percentages, dates, times, dimensions, and exact values when they improve clarity. Preserve quoted values, code, mathematics, and text readers must reproduce; never change a number's value or reformat data.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/checklists/numbers-checklist)

<div class="rule-example" markdown="1">

**Before**

```text
We reviewed 8 samples before publication.
```

**After**

```text
We reviewed eight samples before publication.
```

In ordinary prose, spell out a single-digit count when no numeric-format exception applies.

</div>

<div class="rule-example" markdown="1">

**Before**

```text
We reviewed eight drafts and 14 responses.
```

**After**

```text
We reviewed eight drafts and 14 responses.
```

These counts refer to separate categories, so each follows the ordinary format for its value rather than forcing the same format across both.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg012" markdown="1">

## `MWG012`: Inclusive, respectful language {#mwg012}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Flag clear cases of generic gendered pronouns, stereotyping, unsupported generalizations, or demeaning language that excludes or disrespects people. Use respectful language; generally use people-first wording for disability, while honoring a person's or community's stated identity language and preferences. Mention identity or disability only when relevant. Preserve direct quotations, real people's pronouns, and contexts where identity is relevant. Do not infer identities or flag a term in isolation.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/bias-free-communication)

<div class="rule-example" markdown="1">

**Before**

```text
Each reviewer should upload his notes.
```

**After**

```text
Each reviewer should upload their notes.
```

Singular they avoids assigning a gender to a reviewer whose identity is unknown.

</div>

</article>

<article class="rule-card" aria-labelledby="mwg013" markdown="1">

## `MWG013`: Accessible references {#mwg013}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Check whether links and references make sense to readers without relying on nearby visual layout or directional-only cues. Prefer descriptive link wording that identifies the destination and name the relevant content instead of using unexplained 'here', 'above', or 'below'. Keep necessary sequence or location descriptions when they add useful context. Judge only visible wording; do not assume the link destination or visual design beyond what the text shows.

[Upstream source](https://learn.microsoft.com/en-us/style-guide/accessibility/writing-all-abilities)

<div class="rule-example" markdown="1">

**Before**

```text
The migration checklist is here.
```

**After**

```text
Read the migration checklist for next steps.
```

The revised reference names the resource instead of depending on the reader to interpret a contextless link.

</div>

</article>

</div>

<!-- generated-rule-cards:end -->
