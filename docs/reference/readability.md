# Readability

`RDL` reviews interpretation difficulty in English sentences, not AI authorship or a readability score. All its rules use sentence-scoped LLM judgments; review requires an explicit model. The [source and measurement limitations](#source-and-measurements) distinguish these editorial judgments from the paper's corpus statistics.

<!-- rule-cards -->

## Usage

All readability rules use the LLM engine and sentence scope. They share one request per eligible sentence, using the existing masking, provider opt-in, evidence validation, and decision threshold. No parser model or reference corpus is downloaded. Plain local checks remain local; selecting `RDL` explicitly opts into judging and requires an explicit model.

```sh
style-audit draft.md --select RDL --model microsoft/microsoft-decision-1 --threshold 0.8
style-audit draft.md --select NAS00,RDL --model microsoft/microsoft-decision-1
```

Project configuration:

```toml
[tool.style-audit]
select = ["RDL"]
output = "json"

[tool.style-audit.llm]
enabled = true
model = "microsoft/microsoft-decision-1"
threshold = 0.8
```

Exact IDs and prefixes use the existing [selection and ignore precedence](../configuration.md#selection-ignoring-and-llm-opt-in). `NAS` continues to select only [no-ai-slop rules](no-ai-slop.md); `RDL` selects only readability rules. With no selection filter, both catalogs are selected, but remote review still requires an opt-in and model. The other supported LiteLLM chat models also judge `RDL`; their findings are not probability-filtered.

## Interpreting findings

The paper associates constructions with processing costs at the corpus level. Their presence is not sufficient evidence that a particular sentence is difficult. The rules require an identifiable interpretation burden and preserve clear, familiar constructions, necessary technical terms, deliberate wordplay, and useful voice. A long sentence is not automatically a violation; an adjective sequence is not a stack of nouns.

For example, “The book I read was useful” is a clear short object relative without a marker; “We bottled the whiskey” uses a conventional denominal verb; “The paper argues that shorter dependencies help readers” uses conventional metonymy. None should be flagged merely for the corresponding construction. By contrast, an opaque stack such as “customer account access exception review escalation policy” may need its noun relationships made explicit. These are editorial examples, not recorded model outcomes.

Object-relative difficulty and omitted-marker ambiguity can coexist, so multiple rules may flag the same sentence for different reasons. Optional markers are not universally required. The length-penalty experiment supports examining whether compression obscures a clause boundary; it does not justify adding words to every short alternation or preferring passive voice everywhere.

## Source and measurements

`RDL` is a separate English-readability ruleset adapted from **Thomas Hikaru Clark, Matias B. Martin, and Kyle Mahowald, “Why is AI-generated language so hard to understand?”**, [arXiv:2610.29162v1](https://arxiv.org/html/2610.29162v1), 21 October 2026. The paper is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This adaptation turns its processing-difficulty mechanisms into contextual editorial judgments; it does not reproduce the experiments or classify AI authorship.

The paper's unattested-bigram and trigram-perplexity measures inform the single qualitative word-combination rule. Without a genre-matched reference corpus and n-gram model, the judge cannot establish attestation, frequency, surprisal, or perplexity. Findings must not claim measured corpus rarity. Proper names and uncommon but precise terminology are not readability errors merely because they are rare.

The paper's [feature detection and dependency standardization](https://arxiv.org/html/2610.29162v1#A2) use spaCy dependency parses, human reference corpora, corpus-specific baselines, and an external classifier for some candidates. This tool does not calculate those metrics, apply the paper's classifier cutoff, or use its sentence-length exclusions as lint limits. The default decision threshold is the application's existing setting, not a paper-derived readability cutoff or calibrated comprehension probability.

The study analyzes English, a limited set of models and conversational seeds, and genre-dependent aggregate differences. These rules are a research-informed review aid, not a validated readability score, a grade-level formula, an AI detector, or a guarantee of reader comprehension. Sentence-scoped judging cannot use definitions or context elsewhere in the document. See [LLM limitations and privacy](../llm.md#limitations-and-evidence).

For generated output, build or preview the site with the commands in [Contributing](../contributing.md).
