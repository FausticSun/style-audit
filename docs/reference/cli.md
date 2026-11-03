# CLI and output reference

Run `style-audit --help` for the installed command's option summary and `style-audit --version` for the package version. The equivalent module entry point is `python -m style_audit`.

## Inputs and discovery

```sh
style-audit                       # scan the current directory
style-audit draft.md              # audit an explicit file
style-audit docs/                  # traverse matching files
cat draft.txt | style-audit -      # read standard input
```

Pass one or more paths. The literal `-` reads stdin once and may be combined with files. `--stdin-filename NAME` sets its diagnostic path. It selects Python extraction for `.py` and `.pyi` (Marimo Markdown cells or ordinary Python docstrings), or Gherkin processing for `.feature`. Other names retain prose input. If no paths are given, `.` is used.

Explicit files need not match the directory include patterns, but they must be UTF-8 text. Default excludes apply during directory discovery; passing a named file explicitly remains an intentional override.

Default directory includes are `*.md`, `*.markdown`, `*.rst`, `*.txt`, `*.feature`, `*.py`, and `*.pyi`. Directory scans exclude `AGENTS.md` and `SKILL.md` at any depth by default; configured `include` and `exclude` patterns retain their existing matching semantics.

Configuration is discovered by walking upward from the current working directory for `pyproject.toml`. `--config PATH` selects an explicit `pyproject.toml` or a directory containing one. See [configuration](../configuration.md) for path and precedence details.

## Python docstrings

Inputs ending in `.py` or `.pyi` are parsed with the running Python interpreter and never executed or imported. A recognized Marimo `.py` app is handled as described below. Other `.py` files and `.pyi` stubs audit only AST-recognized module, class, function, async-function, and nested-definition docstrings. Comments, assigned literals (including assignments to `__doc__`), later standalone strings, bytes, f-strings, and template strings are excluded from ordinary Python docstring extraction. Invalid Python produces a located error on stderr and exit status `2`, not a raw-source fallback or a successful empty audit.

Each ordinary Python docstring becomes a separate logical document. Its Python string value is decoded, including escaped characters and adjacent literal concatenation, then cleaned like `inspect.cleandoc`: tabs expand, common continuation-line indentation is removed, and blank outer lines are trimmed. Existing quotation and Markdown-code masks still exempt examples within the docstring. Sentence, paragraph, section, and document scopes never combine separate docstrings or include surrounding executable code.

```sh
style-audit src/ tests/ --select NAS00
style-audit module.py --select NAS00 --format json
cat module.py | style-audit - --stdin-filename module.py --select NAS00
style-audit module.py --select NAS00,RDL --model openai/gpt-4o-mini
```

No new rule IDs or configuration toggle are needed. The same selection, ignores, LLM opt-in, and exit codes apply. Files without extracted prose produce no findings or provider requests. Source positions count original Unicode characters, and UTF-8 BOM and physical newlines are retained in the source mapping.

Evidence is the original source spelling, not the cleaned model input. A span can contain escape sequences, indentation, or the quote/whitespace/comment separators between concatenated literals. Those separators are source context, not audited prose or remote-request content.

### Marimo Markdown cells

A `.py` file is treated as a Marimo app when it imports Marimo and constructs `App` (including an imported `App` alias). Only direct `mo.md()` calls with string-literal arguments are extracted; ordinary and raw strings are decoded, and f-strings contribute only their static text. Interpolation expressions and nonliteral arguments are not evaluated. Each Markdown call becomes a separate document with source-mapped findings. Comments, cell code, generated widget values, and `mo.mermaid()` diagrams are excluded.

```sh
style-audit notebooks/system_design.py --select NAS00 --format json
style-audit notebooks/system_design.py --select NAS,RDL --model openai/gpt-4o-mini
```

Selecting LLM rules sends only the current extracted Markdown unit after normal code and quotation masking. Visible private prose remains eligible for transmission; extraction is not redaction.

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
| `--model MODEL` | Select a LiteLLM `provider/model` name and opt into judging selected LLM rules using the API configured in `[tool.style-audit.llm].api` (chat completions by default). |
| `--stdin-filename NAME` | Set the stdin path for per-file selection; `.py` selects Marimo Markdown cells or Python docstrings, `.pyi` selects docstrings, and `.feature` selects Gherkin processing. |
| `--version` | Print the package version. |
| `-h`, `--help` | Print help. |

IDs, prefixes, and filename-style rule globs are matched case-sensitively. `NAS` selects no-ai-slop rules. `NAS1` selects `NAS101` through `NAS121`. `NAS00` selects `NAS001`–`NAS003`. `RDL` selects readability rules.

CLI `--select` replaces configured global and per-file selections, and CLI `--ignore` combines with configured ignores. Without a global selection or matching per-file entry, `.md` inputs default to `NAS` and `RDL`; other inputs select all catalogs. An empty per-file selection disables rules for matching files. See [per-file rule selection](../configuration.md#per-file-rule-selection).

Default `.md` selection chooses `NAS` and `RDL` but does not enable remote judging. LLM review requires selected LLM rules, a model, and an opt-in through `enabled = true`, explicit LLM selection, `--llm`, or `--model`. Supply the standard credentials required by the selected LiteLLM provider; for `openai/gpt-4o-mini`, set `OPENAI_API_KEY`. A deterministic-only effective selection does not start remote calls. See [LLM review and privacy](../llm.md).

`STE` selects all 61 ASD-STE100 entries, including recommendations. `STE606` and `STE801` are the local paragraph-count and semicolon rules. Markdown table blocks are not paragraphs and do not count toward the STE606 six-sentence limit. STE801 still checks semicolons in table cells. Combine selectors with `--select NAS00,RDL,STE606,STE801`, or quote globs such as `--select 'NAS00?'` and `--ignore 'NAS00[23]'`. Every selector must match a registered rule.


Example:

```sh
style-audit draft.md --select NAS106 --model openai/gpt-4o-mini
```


## Output and exit status

Text output reports `path:line:column`, rule ID, explanation, exact evidence, and a suggestion when present. Start line and column positions are one-based, while end positions are exclusive. Offsets count Python Unicode characters, not UTF-8 bytes.

JSON output is a versioned object with a `findings` array. Each finding contains `path`, `code`, `message`, `line`, `column`, `end_line`, `end_column`, `evidence`, and `fix`. Findings sort deterministically by path, start position, rule ID, and end position. Empty scans produce an empty text stream or a JSON object with an empty array.

Completion findings use exact contiguous visible quotes within the current unit, generated reasons, and optional fixes. Decisions findings use the full visible unit as evidence and include the configured probability threshold; they do not include generated rationales or fixes. Deterministic findings retain exact token or emoji evidence within their rules' units.


| Exit status | Meaning |
| --- | --- |
| `0` | No findings. |
| `1` | One or more findings. |
| `2` | Invalid configuration, unknown rule, unreadable or missing input, or LLM/provider error (including malformed answers or unavailable credentials). |

Operational errors go to stderr. JSON mode never turns operational failures into an empty successful report.
