# CLI and output reference

Run `style-audit --help` for the installed parser's option summary and `style-audit --version` for the package version. The equivalent module entry point is `python -m style_audit`.

## Inputs and discovery

```sh
style-audit                       # scan the current directory
style-audit draft.md              # audit an explicit file
style-audit docs/                  # traverse matching files
cat draft.txt | style-audit -      # read standard input
```

Pass one or more paths. The literal `-` reads stdin once and may be combined with files. Set `--stdin-filename NAME` to change its diagnostic path. If no paths are given, `.` is used. Explicit files need not match the directory include patterns; they must be UTF-8 text. A directory scan matches configured `include` patterns and respects configured `exclude` patterns.

Configuration is discovered by walking upward from the current working directory for `pyproject.toml`. `--config PATH` selects an explicit `pyproject.toml` or a directory containing one. See [configuration](../configuration.md) for path and precedence details.

## Options

| Option | Effect |
| --- | --- |
| `--config PATH` | Read settings from this `pyproject.toml` or directory. |
| `--select RULE[,RULE]` | Select exact rule IDs or prefixes; replaces configured `select`. Repeatable. |
| `--ignore RULE[,RULE]` | Suppress selected IDs or prefixes; adds to configured `ignore`. Repeatable. |
| `--format text\|json` | Override configured report format. |
| `--llm` | Explicitly enable LLM rules among the currently selected rules. |
| `--model MODEL` | Select an OpenRouter decision model or LiteLLM chat model; also opts into judging selected LLM rules. |
| `--threshold FLOAT` | Override the decision-probability threshold (default `0.8`); must be finite and in `[0, 1]`. Does not enable judging. |
| `--stdin-filename NAME` | Set the displayed path for stdin. |
| `--version` | Print the package version. |
| `-h`, `--help` | Print help. |

IDs and prefixes are matched case-sensitively. `NAS` selects the no-ai-slop rules; `NAS1` selects `NAS101` through `NAS121`, and `NAS00` selects `NAS001`–`NAS003`. `RDL` selects the separate [readability ruleset](readability.md). Prefixes can be combined, such as `--select NAS00,RDL`. An unknown selector is an error. CLI `--select` replaces configured selection; CLI `--ignore` combines with configured ignores. An empty configured `select` means no selection filter, so both catalogs are selected before ignores.

Selecting an LLM rule explicitly enables the judge for that rule. `--llm` and `--model` enable only LLM rules that remain selected. A deterministic-only `select` does not start remote calls, even with `--llm`; selecting a model does not add unselected rules. See [LLM review and privacy](../llm.md).

Each rule's sentence, paragraph, section, or document scope is fixed registry metadata, shown in the generated [rule reference](rules.md); there is no scope option or configuration override. Both LLM APIs group selected rules by scope and request once per eligible unit using only that unit's masked text and matching-scope rules. Request count depends on the selected scopes and their unit counts; see [LLM segmentation and privacy](../llm.md#canonical-scopes-and-segmentation).

The exact models `microsoft/microsoft-decision-1` and `openrouter/microsoft/microsoft-decision-1` select OpenRouter decision judging and use `OPENROUTER_API_KEY`. Other model names use LiteLLM chat judging. An explicit model is required whenever selected LLM rules are judged; there is no default model. Example:

```sh
style-audit draft.md --select NAS106 --model microsoft/microsoft-decision-1 --threshold 0.9
```

`--threshold` overrides `[tool.style-audit.llm].threshold`. A decision probability equal to the threshold is included; below-threshold answers are excluded only after validation. Non-numeric, nonfinite, or out-of-range CLI values fail with exit `2`. The setting is validated but does not filter chat findings. See [configuration](../configuration.md) for TOML types.

## Output and exit status

Text output reports `path:line:column`, rule ID, explanation, exact evidence, and a suggestion when present. Start line and column positions are one-based; end positions are exclusive. Offsets count Python Unicode characters, not UTF-8 bytes.

JSON output is a versioned object with a `findings` array. Each finding contains `path`, `code`, `message`, `line`, `column`, `end_line`, `end_column`, `evidence`, and `fix`. Findings sort deterministically by path, start position, rule ID, and end position. Empty scans produce an empty text stream or a JSON object with an empty array.

Decision findings use the complete original logical unit as `evidence`, locate it by original source offsets, and include the scope, rule name, description, and probability in `message`. The source span may contain masked quotations or code as context, not judged prose; a document-scoped finding spans the trimmed document. Multiple matching-scope rules may produce findings for the same unit, and equal text in different units remains separately located. `fix` is empty because decision responses do not generate suggestions. No probability field or new JSON schema is added. Chat findings use validated exact contiguous visible quotes within the current unit, generated reasons, and optional fixes; quotes elsewhere in the input do not qualify. Deterministic findings retain exact token or emoji evidence within their rules' units.

| Exit status | Meaning |
| --- | --- |
| `0` | No findings. |
| `1` | One or more findings. |
| `2` | Invalid configuration or threshold, unknown rule, unreadable or missing input, or LLM/provider error (including malformed answers or unavailable credentials). |

Operational errors go to stderr. JSON mode never turns operational failures into an empty successful report.
