# CLI and output reference

Run `style-audit --help` for the installed parser's option summary and `style-audit --version` for the package version. The equivalent module entry point is `python -m style_audit`.

## Inputs and discovery

```sh
style-audit                       # scan the current directory
style-audit draft.md              # audit an explicit file
style-audit docs/                  # traverse matching files
cat draft.txt | style-audit -      # read standard input
```

Pass one or more paths. The literal `-` reads stdin once and may be combined with files. `--stdin-filename NAME` sets its diagnostic path. It selects Python docstring extraction for `.py` or `.pyi`, or Gherkin processing for `.feature`. Other names retain prose input. If no paths are given, `.` is used.

Explicit files need not match the directory include patterns, but they must be UTF-8 text.

Default directory includes are `*.md`, `*.markdown`, `*.rst`, `*.txt`, `*.feature`, `*.py`, and `*.pyi`. Configured `include` and `exclude` patterns retain their existing matching semantics.

Configuration is discovered by walking upward from the current working directory for `pyproject.toml`. `--config PATH` selects an explicit `pyproject.toml` or a directory containing one. See [configuration](../configuration.md) for path and precedence details.

## Python docstrings

Inputs ending in `.py` or `.pyi` are parsed with the running Python interpreter. Only AST-recognized module, class, function, async-function, and nested-definition docstrings are audited. Comments, assigned literals (including assignments to `__doc__`), later standalone strings, bytes, f-strings, and template strings are excluded. Input code is never executed or imported. Invalid Python produces a located error on stderr and exit status `2`, not a raw-source fallback or a successful empty audit.

Each docstring becomes a separate logical document. Its Python string value is decoded, including escaped characters and adjacent literal concatenation, then cleaned like `inspect.cleandoc`: tabs expand, common continuation-line indentation is removed, and blank outer lines are trimmed. Existing quotation and Markdown-code masks still exempt examples within the docstring. Sentence, paragraph, section, and document scopes never combine separate docstrings or include surrounding executable code.

```sh
style-audit src/ tests/ --select NAS00
style-audit module.py --select NAS00 --format json
cat module.py | style-audit - --stdin-filename module.py --select NAS00
style-audit module.py --select NAS00,RDL --model azure-maas-judge/Decision-1
```

No new rule IDs or configuration toggle are needed. The same selection, ignores, LLM opt-in, and exit codes apply. Files without docstrings produce no findings or provider requests. Source positions count original Unicode characters, and UTF-8 BOM and physical newlines are retained in the source mapping.

Evidence is the original source spelling, not the cleaned model input. A span can contain escape sequences, indentation, or the quote/whitespace/comment separators between concatenated literals. Those separators are source context, not audited prose or remote-request content.

## Gherkin feature files

`.feature` files use a syntax-aware, text-only Gherkin pass. The CLI does not load step definitions or execute scenarios. The pass masks the keyword prefixes for `Feature`, `Rule`, `Background`, `Scenario`, `Scenario Outline`, and `Examples`, and for the English step keywords `Given`, `When`, `Then`, `And`, `But`, or `*`. Text after those prefixes—including Gherkin heading descriptions and step wording—remains auditable prose.

Full-line tags, comments, table rows, Gherkin docstring delimiters and contents, and fenced code blocks marked with triple backticks are masked. Headings and steps establish segmentation boundaries, and original source positions are preserved. Masking is not sensitive-data redaction. If LLM rules are opted in, visible heading and step prose is eligible for remote review.

```sh
style-audit tests/bdd/features/
cat checkout.feature | style-audit - --stdin-filename checkout.feature
```

## Options

| Option | Effect |
| --- | --- |
| `--config PATH` | Read settings from this `pyproject.toml` or directory. |
| `--select RULE[,RULE]` | Select rule IDs, prefixes, or globs and replace global and per-file selections. Repeatable. |
| `--ignore RULE[,RULE]` | Suppress IDs, prefixes, or globs and add them to configured `ignore`. Repeatable. |
| `--format text\|json` | Override configured report format. |
| `--llm` | Explicitly enable LLM rules among the currently selected rules. |
| `--model MODEL` | Select the configured Azure MaaS Decision-1 model or a LiteLLM chat model and opt into judging selected LLM rules. |
| `--threshold FLOAT` | Override the decision-probability threshold (default `0.8`). The value must be finite and in `[0, 1]`. It does not enable judging. |
| `--stdin-filename NAME` | Set the stdin path for per-file selection and select Python docstring extraction for `.py` and `.pyi` names or Gherkin processing for `.feature` names. |
| `--version` | Print the package version. |
| `-h`, `--help` | Print help. |

IDs, prefixes, and filename-style rule globs are matched case-sensitively. `NAS` selects no-ai-slop rules. `NAS1` selects `NAS101` through `NAS121`. `NAS00` selects `NAS001`–`NAS003`. `RDL` selects readability rules.

CLI `--select` replaces configured global and per-file selections, and CLI `--ignore` combines with configured ignores. An empty global `select` means all three catalogs are selected before ignores. An empty per-file selection disables rules for matching files unless another matching entry adds rules. See [per-file rule selection](../configuration.md#per-file-rule-selection).

Selecting an LLM rule explicitly enables the judge for that file, including through a matching per-file entry. `--llm` and `--model` enable only LLM rules that remain selected for each file. A deterministic-only effective selection does not start remote calls, even with `--llm`. Selecting a model does not add unselected rules. See [LLM review and privacy](../llm.md).

`STE` selects all 61 ASD-STE100 entries, including recommendations. `STE606` and `STE801` are the local paragraph-count and semicolon rules. Markdown table blocks are not paragraphs and do not count toward the STE606 six-sentence limit. STE801 still checks semicolons in table cells. Combine selectors with `--select NAS00,RDL,STE606,STE801`, or quote globs such as `--select 'NAS00?'` and `--ignore 'NAS00[23]'`. Every selector must match a registered rule.

Use `azure-maas-judge/Decision-1` for Azure MaaS Decisions judging. Configure its API base and provider in the OMP model registry or override them with `[tool.style-audit.llm.litellm]`. API keys come from the registry or a named environment variable, never a raw TOML value. Other model names use LiteLLM chat judging. An explicit model is required whenever selected LLM rules are judged. There is no default model.

Example:

```sh
style-audit draft.md --select NAS106 --model azure-maas-judge/Decision-1 --threshold 0.9
```

`--threshold` overrides `[tool.style-audit.llm].threshold`. A decision probability equal to the threshold is included, and below-threshold answers are excluded only after validation. Non-numeric, nonfinite, or out-of-range CLI values fail with exit `2`. The setting is validated but does not filter chat findings. See [configuration](../configuration.md) for TOML types.

## Output and exit status

Text output reports `path:line:column`, rule ID, explanation, exact evidence, and a suggestion when present. Start line and column positions are one-based, while end positions are exclusive. Offsets count Python Unicode characters, not UTF-8 bytes.

JSON output is a versioned object with a `findings` array. Each finding contains `path`, `code`, `message`, `line`, `column`, `end_line`, `end_column`, `evidence`, and `fix`. Findings sort deterministically by path, start position, rule ID, and end position. Empty scans produce an empty text stream or a JSON object with an empty array.

Decision findings use the complete original logical unit as `evidence`, locate it by original source offsets, and include the scope, rule name, description, and probability in `message`. The source span may contain masked quotations or code as context, not judged prose. A document-scoped finding spans the trimmed document. Multiple matching-scope rules may produce findings for the same unit, and equal text in different units remains separately located. `fix` is empty because decision responses do not generate suggestions. No probability field or new JSON schema is added.

Chat findings use validated exact contiguous visible quotes within the current unit, generated reasons, and optional fixes. Quotes elsewhere in the input do not qualify. Deterministic findings retain exact token or emoji evidence within their rules' units.

| Exit status | Meaning |
| --- | --- |
| `0` | No findings. |
| `1` | One or more findings. |
| `2` | Invalid configuration or threshold, unknown rule, unreadable or missing input, or LLM/provider error (including malformed answers or unavailable credentials). |

Operational errors go to stderr. JSON mode never turns operational failures into an empty successful report.
