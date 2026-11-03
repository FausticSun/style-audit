# Readability

`RDL` reviews interpretation difficulty in English sentences, not AI authorship or a readability score. All its rules use sentence-scoped LLM judgments. With the default chat-completion API, review uses `openrouter/openrouter/free` and requires the OpenRouter credential; override the model as needed. Decisions mode requires a model supported by the provider. The [source and measurement limitations](#source-and-measurements) distinguish these editorial judgments from the paper's corpus statistics.

<!-- generated-rule-cards:start -->

This ruleset contains 7 rules, rendered from `style_audit.rules.RULES`. Each entry includes its canonical scope and source.

Before/after pairs illustrate a possible revision in the stated context, not recorded model outcomes or automatic fixes. See [auditing rule prose and raw examples](../dogfooding.md#audit-the-generated-rule-catalog).

<div class="rule-cards" markdown="1">

<article class="rule-card" aria-labelledby="rdl101" markdown="1">

## `RDL101`: Long syntactic dependencies {#rdl101}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag a syntactic dependency only when intervening clauses or modifiers make it difficult to connect a subject, verb, object, or modifier to its partner. Identify the separated partners and the processing burden; suggest bringing them closer or splitting the sentence without losing meaning. Do not flag a sentence merely for its word count, or invent a numeric dependency-length cutoff.

[Upstream source](https://arxiv.org/html/2610.29162v1#A2)

<div class="rule-example" markdown="1">

**Before**

```text
The report that the manager whom the consultant the board hired advised approved disappeared.
```

**After**

```text
The board hired the consultant, who advised the manager. The manager approved the report. The report disappeared.
```

Nested clauses delay the main verb and make it hard to track the report, board, consultant, and manager. The revision makes each participant and action explicit.

</div>

</article>

<article class="rule-card" aria-labelledby="rdl102" markdown="1">

## `RDL102`: Difficult object relative clauses {#rdl102}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag an object relative clause, with or without an overt relativizer, only when its noncanonical word order, embedding, or competing participants makes the roles hard to follow. In an object relative the modified noun is the relative clause's object, not its subject. Preserve clear, familiar constructions such as 'the book I read'; do not flag subject relatives or prescribe passive voice universally.

[Upstream source](https://arxiv.org/html/2610.29162v1#A2.SS1)

<div class="rule-example" markdown="1">

**Before**

```text
The intern the editor the manager praised hired left.
```

**After**

```text
The manager praised the editor, who hired the intern. The intern left.
```

The intern is the object of hired, and the editor is the object of praised. Unnest the object relatives so their roles are explicit; clear short object relatives remain valid.

</div>

</article>

<article class="rule-card" aria-labelledby="rdl103" markdown="1">

## `RDL103`: Ambiguous omitted clause markers {#rdl103}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag omission of an optional 'that' in an object relative or complement clause, including 'so (that)' and 'sure (that)', only when it causes a garden path, obscures the clause boundary, or forces rereading that an explicit marker would avoid. Explain the competing parses without inventing the intended meaning. Keep clear short omissions; do not lengthen every syntactic alternation or treat optional words as mandatory.

[Upstream source](https://arxiv.org/html/2610.29162v1#A3.T3)

<div class="rule-example" markdown="1">

**Before**

```text
The coach knew the players assigned to train with the reserve team missed practice.
```

**After**

```text
The coach knew that the players assigned to train with the reserve team missed practice.
```

The intended meaning here is knowledge that the players missed practice, not acquaintance with the players. That marks the complement boundary before a long modifier invites the direct-object reading.

</div>

</article>

<article class="rule-card" aria-labelledby="rdl104" markdown="1">

## `RDL104`: Opaque stacked noun compounds {#rdl104}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag a compound of three or more nouns in a noun-modifier relationship only when its grouping or the relations between nouns are unclear. Identify the noun stack and explain the ambiguous relations; suggest explicit prepositions or a clause without inventing facts. Do not count ordinary adjective sequences as noun stacks, and preserve familiar, unambiguous terms and necessary domain terminology.

[Upstream source](https://arxiv.org/html/2610.29162v1#A2.SS1)

<div class="rule-example" markdown="1">

**Before**

```text
The team changed the customer account access exception review policy.
```

**After**

```text
The team changed the policy for reviewing exceptions to access rules for customer accounts.
```

Here the policy governs reviews of exceptions to customer-account access rules. Stating those relationships resolves the noun grouping; do not assume this interpretation for a real draft without context.

</div>

</article>

<article class="rule-card" aria-labelledby="rdl105" markdown="1">

## `RDL105`: Unfamiliar denominal verbs {#rdl105}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag an ad-hoc verb formed from a noun only when the reader must infer an unclear action or noun-to-verb conversion obscures the meaning. Identify the converted noun and the interpretation burden; prefer an explicit action when supported by the sentence. Preserve conventional verbs such as 'bottle', 'email', and 'park', understandable domain usage, and deliberate wordplay. Do not classify unfamiliar words by rarity alone.

[Upstream source](https://arxiv.org/html/2610.29162v1#A2.SS1)

<div class="rule-example" markdown="1">

**Before**

```text
Please spreadsheet the complaint.
```

**After**

```text
Please record the complaint in the spreadsheet.
```

Here the intended action is recording the complaint, not calculating or analyzing it. State that action; conventional verbs such as email do not need replacement.

</div>

</article>

<article class="rule-card" aria-labelledby="rdl106" markdown="1">

## `RDL106`: Confusing inanimate-agent mismatches {#rdl106}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag an inanimate subject with an active verb that normally requires an animate agent only when the mismatch makes agency or the intended action hard to understand. Identify the subject, verb, and resulting confusion. Preserve conventional metonymy such as 'the paper argues', clear technical idioms, and intentional personification or metaphor. Do not ban all inanimate subjects, all active verbs, or invent an unnamed human actor.

[Upstream source](https://arxiv.org/html/2610.29162v1#A2.SS1)

<div class="rule-example" markdown="1">

**Before**

```text
In the approval procedure, the invoice hopes the reviewer forgives its missing approval.
```

**After**

```text
In the approval procedure, the reviewer might accept the invoice despite its missing approval.
```

For literal procedural copy, state whether the reviewer might accept the invoice rather than attributing human feelings to a document. This revision retains the intended uncertainty; deliberate personification could be valid in another context.

</div>

</article>

<article class="rule-card" aria-labelledby="rdl107" markdown="1">

## `RDL107`: Hard-to-interpret word combinations {#rdl107}

<div class="rule-card-meta" markdown="1">

Engine: `llm` · Scope: `sentence`

</div>

Flag an unexpected word pair or short word sequence only when its combination makes the local meaning hard to predict or reconstruct; explain the interpretation burden and suggest a clearer equivalent only when the meaning is supported. This is a qualitative readability judgment, not a measurement of corpus attestation, n-gram probability, surprisal, or perplexity. Do not invent frequency statistics or penalize proper names, precise technical vocabulary, useful novelty, or clear creative language merely for being uncommon.

[Upstream source](https://arxiv.org/html/2610.29162v1#A2.SS2)

<div class="rule-example" markdown="1">

**Before**

```text
The instructions omit the deadline, collateralizing instruction latency against deadline intent.
```

**After**

```text
The instructions omit the deadline.
```

The financial word combination supplies no reconstructable mechanism. Keep the omission already stated rather than inventing another claim; unusual but clear metaphors remain valid.

</div>

</article>

</div>

<!-- generated-rule-cards:end -->

## Usage

All readability rules use the LLM engine and sentence scope. They share one request per eligible sentence, using existing masking, provider opt-in, and evidence validation. No parser model or reference corpus is downloaded. Plain local checks remain local. Selecting `RDL` explicitly opts into judging; chat completions use the default model unless overridden, while Decisions requires an explicit provider-supported model.

```sh
style-audit draft.md --select RDL --model openrouter/openrouter/free
style-audit draft.md --select NAS00,RDL --model openrouter/openrouter/free
```

Project configuration:

```toml
[tool.style-audit]
select = ["RDL"]
output = "json"

[tool.style-audit.llm]
enabled = true
model = "openrouter/openrouter/free"
```

`RDL` uses sentence-scoped LLM judgments with either LiteLLM chat completions or its provider-neutral Decisions API, as selected in [configuration](../configuration.md#settings). Completion returns validated structured findings; Decisions returns sentence-level probability findings at the configured threshold. See [LLM review and privacy](../llm.md) for request boundaries and evidence limits.

## Interpreting findings

The paper associates constructions with processing costs at the corpus level. Their presence is not sufficient evidence that a particular sentence is difficult. The rules require an identifiable interpretation burden and preserve clear, familiar constructions, necessary technical terms, deliberate wordplay, and useful voice. A long sentence is not automatically a violation. An adjective sequence is not a stack of nouns.

For example, “The book I read was useful” is a clear short object relative without a marker. “We bottled the whiskey” uses a conventional denominal verb. “The paper argues that shorter dependencies help readers” uses conventional metonymy. None should be flagged merely for the corresponding construction. By contrast, an opaque stack such as “customer account access exception review escalation policy” may need its noun relationships made explicit. These are editorial examples, not recorded model outcomes.

Object-relative difficulty and omitted-marker ambiguity can coexist, so multiple rules may flag the same sentence for different reasons. Optional markers are not universally required. The length-penalty experiment supports examining whether compression obscures a clause boundary. It does not justify adding words to every short alternation or preferring passive voice everywhere.

## Source and measurements

`RDL` is a separate English-readability ruleset adapted from **Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald, “Why is AI-generated language so hard to understand?”**, [arXiv:2610.29162v1](https://arxiv.org/html/2610.29162v1), 21 October 2026. The paper is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This adaptation turns its processing-difficulty mechanisms into contextual editorial judgments. It does not reproduce the experiments or classify AI authorship.

The paper's unattested-bigram and trigram-perplexity measures inform the single qualitative word-combination rule. Without a genre-matched reference corpus and n-gram model, the judge cannot establish attestation, frequency, surprisal, or perplexity. Findings must not claim measured corpus rarity. Proper names and uncommon but precise terminology are not readability errors merely because they are rare.

The paper's [feature detection and dependency standardization](https://arxiv.org/html/2610.29162v1#A2) use spaCy dependency parses, human reference corpora, corpus-specific baselines, and an external classifier for some candidates. This tool does not calculate those metrics, apply the paper's classifier cutoff, or use its sentence-length exclusions as lint limits.

The study analyzes English, a limited set of models and conversational seeds, and genre-dependent aggregate differences. These rules are a research-informed review aid, not a validated readability score, a grade-level formula, an AI detector, or a guarantee of reader comprehension. Sentence-scoped judging cannot use definitions or context elsewhere in the document. See [LLM limitations and privacy](../llm.md#limitations-and-evidence).

For generated output, build or preview the site with the commands in [Contributing](../contributing.md).
