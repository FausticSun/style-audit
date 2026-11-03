# No AI slop

`NAS` adapts [Peter Yang's no-ai-slop guidance](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md), pinned to commit `000650b`, under the [MIT license](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/LICENSE). The repository includes its license notice in `third_party/no-ai-slop-LICENSE`.

The rules combine narrow local patterns with contextual editorial judgments. Preserve personal voice, useful uncertainty, and intentional cadence rather than rewriting every unusual phrase. Each card identifies its engine and canonical audit scope.

<!-- generated-rule-cards:start -->

This ruleset contains 24 rules, rendered from `style_audit.rules.RULES`. Each entry includes its canonical scope and source.

Before/after pairs illustrate a possible revision in the stated context, not recorded model outcomes or automatic fixes. See [auditing rule prose and raw examples](../dogfooding.md#audit-the-generated-rule-catalog).

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="nas001" markdown="1">

## `NAS001`: Banned outright words and phrases {#nas001}

<div class="rule-card-meta" markdown="1">

Engine: `deterministic` · Scope: `sentence`

</div>

Flags exact matches for terms the source explicitly lists as banned outright.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#words-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
We utilize the parser.
```

**After**

```text
We use the parser.
```

The listed verb can be replaced without changing the action.

</div>

</article>

<article class="rule-card" aria-labelledby="nas002" markdown="1">

## `NAS002`: Emoji in headings {#nas002}

<div class="rule-card-meta" markdown="1">

Engine: `deterministic` · Scope: `section`

</div>

Flags emoji decorating Markdown headings.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
# 🚀 Launch
```

**After**

```text
# Launch
```

The emoji decorates the heading rather than adding information.

</div>

</article>

<article class="rule-card" aria-labelledby="nas003" markdown="1">

## `NAS003`: Weak verb phrases {#nas003}

<div class="rule-card-meta" markdown="1">

Engine: `deterministic` · Scope: `sentence`

</div>

Flags the source's explicit examples 'serves as', 'made a decision', and 'has the ability to'.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#editing-principles)

<div class="rule-example" markdown="1">

**Before**

```text
The service has the ability to audit drafts.
```

**After**

```text
The service can audit drafts.
```

The direct modal verb preserves the stated capability.

</div>

</article>

<article class="rule-card" aria-labelledby="nas101" markdown="1">

## `NAS101`: Binary contrasts {#nas101}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect formulaic 'not X, but Y' contrasts when stating Y directly would be clearer.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The question isn't whether to use retries. It's how many retries to allow.
```

**After**

```text
How many retries should we allow?
```

The point is the retry count; the contrast adds no separate constraint. Keep contrasts that convey a relevant correction.

</div>

</article>

<article class="rule-card" aria-labelledby="nas102" markdown="1">

## `NAS102`: Throat-clearing openers {#nas102}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect generic opening phrases that delay the point; preserve personal context that earns its place.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
Here's the thing: the build passed.
```

**After**

```text
The build passed.
```

The opener delays the result without supplying personal context.

</div>

</article>

<article class="rule-card" aria-labelledby="nas103" markdown="1">

## `NAS103`: Faux-insight setups {#nas103}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Detect claims that flatter the writer as uniquely insightful without adding substance.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
Here's what nobody tells you: backups need restore tests.
```

**After**

```text
Backups need restore tests.
```

The exclusivity claim supplies no evidence and is not needed to state the point.

</div>

</article>

<article class="rule-card" aria-labelledby="nas104" markdown="1">

## `NAS104`: Colon reveals {#nas104}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Detect lowercase dramatic reveals after a colon; allow lists, labels, quotations, titles, code, and grammatical capitalization.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The best part: it keeps your drafts.
```

**After**

```text
It keeps your drafts.
```

The lowercase reveal supplies a dramatic label, not a grammatical need for the colon. Ordinary labels and lists remain valid.

</div>

</article>

<article class="rule-card" aria-labelledby="nas105" markdown="1">

## `NAS105`: Superficial analysis {#nas105}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Detect trailing -ing clauses that claim significance without explaining a concrete mechanism or consequence.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The release adds file search, highlighting the team's commitment to better workflows.
```

**After**

```text
The release adds file search.
```

The trailing clause asserts significance without explaining a mechanism; the revision keeps the stated feature.

</div>

</article>

<article class="rule-card" aria-labelledby="nas106" markdown="1">

## `NAS106`: Importance puffery {#nas106}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Detect inflated claims of importance in place of concrete facts.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The company launched its first paid plan, marking a pivotal moment.
```

**After**

```text
The company launched its first paid plan.
```

The first paid plan is already a concrete fact. Remove the importance claim rather than inventing evidence for it.

</div>

</article>

<article class="rule-card" aria-labelledby="nas107" markdown="1">

## `NAS107`: Interpretive metadiscourse {#nas107}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect redundant instructions about what to notice or how to interpret a point.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The queue stopped losing jobs. That last part matters more than it sounds.
```

**After**

```text
The queue stopped losing jobs.
```

The second sentence tells readers how to react but gives them no additional reason.

</div>

</article>

<article class="rule-card" aria-labelledby="nas108" markdown="1">

## `NAS108`: Weasel attribution {#nas108}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect vague appeals to unnamed experts, studies, or reports; do not require attribution for ordinary supported statements.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
Experts agree that caching reduces latency. In our test, caching cut latency from 8 ms to 2 ms.
```

**After**

```text
In our test, caching cut latency from 8 ms to 2 ms.
```

The named test and its measurements are already in the draft; the unnamed experts add no verifiable support.

</div>

</article>

<article class="rule-card" aria-labelledby="nas109" markdown="1">

## `NAS109`: Fake-strong verbs {#nas109}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Detect inflated verb phrases where a direct verb or plain 'is'/'has' is clearer.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The service serves as a tracker for invoices.
```

**After**

```text
The service tracks invoices.
```

The direct verb states the same function without the inflated construction.

</div>

</article>

<article class="rule-card" aria-labelledby="nas110" markdown="1">

## `NAS110`: Synonym cycling {#nas110}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

Detect repeated renaming of the same subject solely to avoid repeating a clear term.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The agent reviews the draft. The assistant scores the piece. The tool suggests fixes.
```

**After**

```text
The agent reviews the draft, scores it, and suggests fixes.
```

Here all three subject labels refer to the same agent, and both object labels refer to the same draft. Keep the identities consistent.

</div>

</article>

<article class="rule-card" aria-labelledby="nas111" markdown="1">

## `NAS111`: Negative listing {#nas111}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect stacked 'not X, not Y, but Z' fragments that can state Z directly.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
Not a dashboard. Not a spreadsheet. A queue.
```

**After**

```text
A queue.
```

For a component label, the negative list adds drama rather than a relevant distinction. Keep exclusions that readers actually need.

</div>

</article>

<article class="rule-card" aria-labelledby="nas112" markdown="1">

## `NAS112`: Dramatic fragmentation {#nas112}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect stacked dramatic fragments or empty repeated endings; preserve intentional voice and useful cadence.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The migration finished. Quietly. Completely. No loose ends.
```

**After**

```text
The migration finished quietly and completely.
```

Combine the stacked emphasis while preserving the manner and completion claim. A deliberate single fragment is not automatically wrong.

</div>

</article>

<article class="rule-card" aria-labelledby="nas113" markdown="1">

## `NAS113`: Robotic rhythm {#nas113}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

Detect conspicuously repeated sentence or paragraph shapes and uniform punchy cadence.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
We opened the file.

We read the code.

We found the bug.

We fixed the bug.

We ran the suite.

We shipped the patch.
```

**After**

```text
After opening the file and reading the code, we found and fixed the bug.

We ran the suite and shipped the patch.
```

In narrative prose, six identically shaped micro-paragraphs obscure the sequence. Group related actions without claiming that the suite passed; a parallel checklist could be appropriate instead.

</div>

</article>

<article class="rule-card" aria-labelledby="nas114" markdown="1">

## `NAS114`: Rhetorical setups {#nas114}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `paragraph`

</div>

Detect empty rhetorical teasers or self-answered question-and-answer pairs.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
What if I told you the test caught a race? Plot twist: it did.
```

**After**

```text
The test caught a race.
```

The self-answered teaser withholds a result that can be stated directly.

</div>

</article>

<article class="rule-card" aria-labelledby="nas115" markdown="1">

## `NAS115`: Fake-profound kickers {#nas115}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

Detect a final aphorism or cute metaphor that restates or dilutes the preceding concrete point.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The queue processed all 12 jobs. In the end, every storm is just a doorway.
```

**After**

```text
The queue processed all 12 jobs.
```

The final metaphor supplies no clear takeaway about the observed result.

</div>

</article>

<article class="rule-card" aria-labelledby="nas116" markdown="1">

## `NAS116`: Summary-recap endings {#nas116}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

Detect a conclusion that merely repeats the preceding text instead of adding a takeaway or next action.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The parser now handles empty files. It also preserves line numbers.

In conclusion, the parser handles empty files and preserves line numbers.
```

**After**

```text
The parser now handles empty files and preserves line numbers.
```

The ending repeats both facts without adding a takeaway or next action.

</div>

</article>

<article class="rule-card" aria-labelledby="nas117" markdown="1">

## `NAS117`: Formatting slop {#nas117}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

Detect decorative formatting that impairs the content: mid-sentence bold emphasis, bullets better expressed as prose, and headers for tiny sections. Ignore code and examples.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
## Result

- The test **passed**.
- The build **passed**.
```

**After**

```text
The test and build passed.
```

For this two-item status note, a heading, bullets, and bold emphasis add structure the content does not need. Longer status lists may warrant that structure.

</div>

</article>

<article class="rule-card" aria-labelledby="nas118" markdown="1">

## `NAS118`: Em dash overuse {#nas118}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `document`

</div>

Detect decorative or clustered em dashes used as a rhythm crutch; short copy should normally avoid them and long copy should use at most a few when useful.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#patterns-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
The test passed — finally — and the build completed — without errors.
```

**After**

```text
The test finally passed, and the build completed without errors.
```

Three decorative dashes crowd a short sentence; the revision retains both results and the emphasis on finally.

</div>

</article>

<article class="rule-card" aria-labelledby="nas119" markdown="1">

## `NAS119`: Abstraction and concreteness {#nas119}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `section`

</div>

Flag generic, portable claims or inflated abstractions when the draft provides no concrete fact, mechanism, consequence, name, number, date, or example to support them. Do not invent missing facts.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#editing-principles)

<div class="rule-example" markdown="1">

**Before**

```text
The update transforms the experience. We do not yet have measurements of its effect on review time.
```

**After**

```text
We do not yet have measurements of the update's effect on review time.
```

The draft supplies no support for the benefit claim and acknowledges uncertainty. Keep that uncertainty rather than inventing measurements.

</div>

</article>

<article class="rule-card" aria-labelledby="nas120" markdown="1">

## `NAS120`: Voice-preserving clarity {#nas120}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag only genuinely tangled sentences, needless passive constructions with no human actor, or empty qualifiers. Preserve useful uncertainty, spoken rhythm, humor, edge, deliberate fragments, and personal context.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#editing-principles)

<div class="rule-example" markdown="1">

**Before**

```text
The report, which the team had revised after the incident that occurred during the release, was shared by the team.
```

**After**

```text
The team revised the report after the release incident and then shared it.
```

The team and the event order already appear in the original. Unnest the clauses and make the team explicit without deleting useful uncertainty or voice.

</div>

</article>

<article class="rule-card" aria-labelledby="nas121" markdown="1">

## `NAS121`: Filler phrases {#nas121}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag a listed filler phrase only when it delays the point in this specific sentence; retain useful spoken rhythm or emphasis.

[Upstream source](https://github.com/petergyang/no-ai-slop/blob/000650b156983f5159695b441477f4e63b25dc85/skills/no-ai-slop/SKILL.md#words-to-cut)

<div class="rule-example" markdown="1">

**Before**

```text
It's worth noting that the service uses port 8003.
```

**After**

```text
The service uses port 8003.
```

Here the filler adds neither emphasis nor context; removing it leaves the fact intact.

</div>

</article>

</div>

<!-- generated-rule-cards:end -->

## Usage

Run only the deterministic rules, without contacting a provider:

```sh
style-audit draft.md --select NAS00
```

To include the no-ai-slop LLM rules, select the ruleset and provide a model explicitly:

```sh
style-audit draft.md --select NAS --model openai/gpt-4o-mini
```

`NAS1` selects only its LLM rules. Combine rulesets with `--select NAS00,RDL` for local no-ai-slop checks plus [readability review](readability.md). See [selection and ignore precedence](../configuration.md#selection-ignoring-and-llm-opt-in), [LLM review and privacy](../llm.md), and the [ruleset overview](rules.md).
