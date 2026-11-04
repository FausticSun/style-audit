# Project configuration

The CLI reads `[tool.style-audit]` from the nearest `pyproject.toml` found by walking upward from the **current working directory**. It does not search from each input path. `--config PATH` bypasses discovery. `PATH` may be a TOML file or a directory containing `pyproject.toml`. Pydantic validates configuration values; invalid TOML, invalid setting types, and unsupported LiteLLM transport settings fail with exit status `2`.

## Settings

```toml
[tool.style-audit]
include = ["*.md", "*.markdown", "*.rst", "*.txt", "*.feature", "*.py", "*.pyi"]
exclude = [".git", ".venv", "venv", "build", "dist", "site", "__pycache__", "vendor/**"]
select = ["NAS001", "NAS002", "NAS003"]
ignore = []
output = "text"

[tool.style-audit.llm]
enabled = false
model = "openrouter/openrouter/free"
```

All settings are optional. Directory scanning defaults to `*.md`, `*.markdown`, `*.rst`, `*.txt`, `*.feature`, `*.py`, and `*.pyi`. Ordinary Python files audit docstrings; recognized Marimo `.py` apps audit direct Markdown cell literals.
`.feature` files receive a syntax-aware Gherkin pass that does not execute steps or load step definitions. It masks Gherkin keyword prefixes and full-line tags, comments, table rows, and docstring fixtures while keeping heading descriptions and step prose auditable. Explicit file paths bypass `include` filtering.
Directory scans exclude `AGENTS.md` and `SKILL.md` at any depth by default. Includes and excludes are arrays of non-empty strings; a bare excluded directory name matches that component at any depth, and glob patterns can exclude directory subtrees.
Supplying an `include` or `exclude` array replaces the corresponding default list. Restate the defaults you still need, including these file exclusions. `output` is `text` or `json`.

Use `include = ["*.py", "*.pyi"]` to scan Python source only. Ordinary files contribute docstrings; recognized Marimo apps contribute direct Markdown cell literals. Use `include = ["*.md", "*.markdown", "*.rst", "*.txt", "*.feature"]` for prose files and Gherkin without Python source. Existing LLM opt-ins also apply to unmasked Gherkin prose and extracted Python prose. Narrow includes if those inputs must not be reviewed remotely. See [Python inputs](reference/cli.md#python-docstrings) and [Gherkin feature files](reference/cli.md#gherkin-feature-files).

The `llm` table accepts:

| Setting | Type and default | Effect |
| --- | --- | --- |
| `enabled` | Boolean, default `false` | Opts selected LLM rules into judging; it never adds rules to the effective selection. |
| `model` | Optional non-empty string; defaults to `openrouter/openrouter/free` for `completion`, with no default for `decisions` | LiteLLM `provider/model` name. Decisions mode needs a provider-supported model; configure it here or with `--model`. A model never enables global judging by itself. |
| `api` | `completion` or `decisions`, default `completion` | Selects LiteLLM chat completions with quoted findings, or the provider-neutral Decisions API with probability findings. |
| `threshold` | Finite number in `[0, 1]`, default `0.82` | Decisions mode only; emits findings when the returned predicate probability is at least this value. CLI `--threshold` overrides it for one run. |

For chat-completion judging, the default `openrouter/openrouter/free` model uses OpenRouter's `OPENROUTER_API_KEY`; set it in the environment. This free-model route does not support OpenRouter's Decisions API. Decisions mode requires a model supported by the selected provider's Decisions endpoint. Never put raw credentials in project TOML.

LLM judging is off by default, including when the default Markdown selection contains RDL rules. A model alone does not enable it. Opt in through `[tool.style-audit.llm].enabled = true`, `--llm` or `--model`, explicit LLM-rule selection, or a matching per-file entry that selects LLM rules. A matching per-file entry opts only that file in. See [LLM review and privacy](llm.md) for request content and provider behavior.

To use the Decisions API, set `api = "decisions"`, provide a model supported by that provider's endpoint, and set the probability threshold. CLI `--threshold` overrides the configured value for one run. OpenRouter's Decisions API supports TypeSafe Jev models such as `openrouter/typesafe/jev-1.14`; the free-model router is not compatible. See [LiteLLM's OpenRouter Decisions documentation](https://docs.litellm.ai/docs/providers/openrouter#decisions-jev).

```toml
[tool.style-audit.llm]
enabled = true
model = "openrouter/typesafe/jev-1.14"
api = "decisions"
threshold = 0.82
```


### LiteLLM transport settings

The optional `[tool.style-audit.llm.litellm]` table supplies transport settings for LiteLLM completions or Decisions. LiteLLM uses the model's provider prefix and standard credentials unless these settings override them.

```toml
[tool.style-audit.llm.litellm]
api_key_env = "OPENROUTER_API_KEY"
timeout = 120
temperature = 0
```

| Setting | Type and default | Effect |
| --- | --- | --- |
| `api_base` | Optional non-empty URL | Overrides the API base passed to LiteLLM. It must use HTTPS except for loopback HTTP and cannot contain embedded credentials, query strings, or fragments. |
| `api_key_env` | Optional environment-variable name | Uses that variable's value as the API key; the named variable must be set. If omitted, LiteLLM uses the provider's standard credential configuration. |
| `custom_llm_provider` | Optional non-empty string | Overrides the provider inferred from the model name. |
| `timeout` | Optional finite positive number of seconds | Overrides LiteLLM's request timeout. |
| `temperature` | Finite number in `[0, 2]`, default `0` | Sets chat-completion temperature. It is not sent to the Decisions API; nonzero values are rejected when `api = "decisions"`. |

Never put a raw key in TOML. Set the provider's standard credential variable or choose one with `api_key_env`; its value must be present in the environment.

## Rule-specific word lists

`no-ai-slop` and `ste` each accept optional arrays of non-empty strings:

```toml
[tool.style-audit.no-ai-slop]
allowed-words = ["robust"]
disallowed-words = ["synergy"]

[tool.style-audit.ste]
allowed-words = ["actuator"]
disallowed-words = ["snapshot"]
```

For NAS001, `allowed-words` exempts matching built-in discouraged terms. `disallowed-words` adds project-specific terms. Disallowed entries take precedence if the same term appears in both arrays. NAS matching is case-insensitive and uses whole-term boundaries.

For STE Rule 1.1 (STE101), `disallowed-words` also produces local findings when STE101 is selected, without requiring a model. `allowed-words` and `disallowed-words` are supplied to the LLM as lexical-authorization context when STE101 is judged remotely. They do not constitute an official ASD-STE100 dictionary, automatically approve another part of speech or sense, or cause every unlisted word to be flagged. Merely configuring either list does not enable LLM calls. See [LLM review and privacy](llm.md).

Local lexical checks scan visible prose, not masked quotations or code, and apply case-insensitive whole-term boundaries to entries. A list may contain a word or a multiword term. Invalid tables, scalar values, and empty entries fail configuration loading with exit status `2`.


## Project-defined rulesets

Declare one or more UTF-8 YAML catalogs in `[tool.style-audit]`. Each catalog may contain multiple custom rules:

```toml
[tool.style-audit]
rule-catalogs = ["rules/team-style.yaml"]
select = ["TEAM"]
```

Catalog paths are relative to the `pyproject.toml` that declares them. Absolute paths, `..` traversal, and symlinks resolving outside that project are rejected. Missing, unreadable, or invalid catalogs fail with exit status `2`. Rule IDs must be unique across bundled and project catalogs.

Each file uses catalog schema version `1` and a non-empty `rules` array. Every record requires `code`, `name`, `engine`, `scope`, `source`, and at least one `examples` entry with `before`, `after`, and `explanation`. Use `engine = deterministic` with a `description` and a typed `detector`, or `engine = llm` with a `prompt`:

```yaml
schema_version: 1
rules:
  - code: TEAM001
    name: Weak intensifier
    engine: deterministic
    scope: sentence
    source: https://example.com/team-style#intensifiers
    description: Flag the weak intensifier very.
    detector:
      kind: regex
      pattern: '(?<!\w)very(?!\w)'
      target: unit
      message: Replace {evidence!r} with a specific description.
      fix: State the measurable property directly.
    examples:
      - before: The service is very fast.
        after: The service is fast.
        explanation: Replace the vague intensifier with a direct claim.
```

Regex detector fields and scopes use the same validated schema as the packaged catalogs. Select custom rules by ID or prefix in `select`, `per-file-select`, or `--select`; ignore and glob selectors apply to them too. Custom catalogs do not change the default Markdown selection of `NAS` and `RDL`, so add custom prefixes to `select` or a matching per-file entry to run them on Markdown. LLM rules follow the normal opt-in and privacy contract: an explicit selection plus a model can send selected rule prompts, examples, and audited prose to the configured provider. See [LLM review and privacy](llm.md).

## Per-rule overrides

Use one or more UTF-8 YAML override catalogs to change fields on bundled or project-defined rules:

```toml
[tool.style-audit]
rule-overrides = ["rules/local-overrides.yaml"]
```

Each file uses schema version `1` and a non-empty `overrides` array. A record identifies an existing rule by `code` and supplies at least one field to replace:

```yaml
schema_version: 1
overrides:
  - code: NAS001
    additional-terms:
      - circle back
      - low-hanging fruit
  - code: NAS106
    prompt: >-
      Flag claims that a routine change marks a pivotal moment. Preserve concrete outcomes.
    examples:
      - before: The update marks a pivotal moment.
        after: The update adds export support.
        explanation: Describe the concrete change without ranking its importance.
```

Overrides are partial: omitted fields retain their catalog values. `name`, `source`, `scope`, and `examples` apply to either engine; `prompt` applies only to LLM rules, while `description` applies only to deterministic rules. `examples` replaces the rule's stored examples and is included in LLM requests as contextual reference data, not as instructions or verified facts. The LLM rule's `prompt` remains its rule guidance.

`detector` accepts a partial table for a deterministic rule and merges its keys into that rule's existing typed detector. This can change a regex rule's `pattern`, `flags`, `target`, `message`, or `fix` without replacing unrelated detector fields; it cannot change the detector kind. `additional-terms` adds case-insensitive whole-term matches to any regex rule, including custom regex rules. Each term may contain multiple words. It is additive and cannot be used with sentence-count or LLM rules.

Override paths follow the same project-relative and symlink-containment rules as [rule catalogs](#project-defined-rulesets). Rule IDs may appear only once across all configured override files. Unknown rules, duplicate overrides, unsupported fields, invalid detector values, and unreadable files fail configuration with exit status `2`. Overrides change rule metadata and execution but not rule selection; `select`, `per-file-select`, and CLI selection still use the original rule ID.


## Selection, ignoring, and LLM opt-in

Without a non-empty `select`, `.md` inputs with no matching per-file entry default to the `NAS` and `RDL` catalogs; other unmatched inputs retain all registered rules. This changes rule selection only; LLM judging remains opt-in. A non-empty global `select` or matching per-file entry overrides the Markdown default. `ignore` removes rules from the effective selection.

`"NAS"` selects no-ai-slop rules. `"NAS1"` matches `NAS101`–`NAS121`. `"NAS00"` selects `NAS001`–`NAS003`. `"NAS00?"` selects the three local rules. `"NAS00[13]"` selects `NAS001` and `NAS003`.

`"RDL"` selects readability rules. `"STE"` selects all 61 ASD-STE100 rules and recommendations. `"MWG"` selects the general Microsoft Writing Style judgments. `"STE606"` selects the local six-sentence paragraph check, and `"STE801"` selects the local semicolon check. Combine them, for example, with `select = ["NAS00", "RDL", "STE606", "STE801", "MWG"]`.

Default `.md` selection does not enable remote review. For `api = "completion"`, the model defaults to `openrouter/openrouter/free`; Decisions mode has no model default and needs a provider-supported model when LLM rules are judged.

LLM rules share one synchronous request per eligible unit and scope in completion mode. Decisions mode uses the same scope units and sends up to 128 predicate questions per request; larger scopes of selected rules are split into multiple requests. See [segmentation, privacy, and cost](llm.md#canonical-scopes-and-segmentation).

CLI `--select` replaces both configured `select` and per-file selections, while CLI `--ignore` is combined with configured `ignore`. Unknown selectors in the effective global selection, ignores, or any per-file entry are errors. Per-file entries are validated even when unused or overridden by CLI selection. Quote CLI globs so the shell does not expand them. Examples:

```sh
style-audit --select NAS001,NAS003 draft.md
style-audit --ignore NAS003 docs/
style-audit --select NAS101 --model openrouter/openrouter/free draft.md
style-audit --select RDL --model openrouter/openrouter/free draft.md
```

LLM judging remains off by default, including for default `.md` selections. It requires selected LLM rules and an explicit opt-in: `[tool.style-audit.llm].enabled = true`, `--llm`, `--model`, or explicitly selecting an LLM rule. A matching per-file entry selecting LLM rules opts that file in. Explicit CLI/model/rule-selection opt-ins still take precedence over `enabled = false`. `--llm` does not broaden `select`; deterministic-only checks never send text remotely.

`AuditConfig` and `load_config()` in `style_audit.config` implement these settings. The parser accepts only the documented setting types. A broken `pyproject.toml` is not silently ignored.

## Per-file rule selection

Map file patterns to rule selectors in `[tool.style-audit.per-file-select]`:

```toml
[tool.style-audit]
select = ["NAS00"]
ignore = ["NAS003"]

[tool.style-audit.per-file-select]
"docs/**" = ["NAS*", "RDL1??", "STE801"]
"src/*.py" = ["NAS00?"]
"src/*.pyi" = ["NAS00?"]
"generated/**" = []

[tool.style-audit.llm]
model = "openrouter/openrouter/free"
```

File patterns match case-sensitive, slash-separated paths **relative to the directory containing the selected `pyproject.toml`**, not the invocation directory. Running from a nested directory or supplying `--config` preserves that root. Paths outside it contain `../` components. Both file and rule globs use Python `fnmatchcase`: `*` spans directory separators, so `"*.py"` matches Python files at any depth and `"docs/*.md"` includes nested Markdown files.

`**` has no special zero-directory meaning. Use `"*.md"`, not `"**/*.md"`, to include root-level Markdown too. `?` matches one character, and `[12]` matches either listed character.

Selection order:

1. Start with configured global `select` when non-empty. Otherwise, an unmatched `.md` input defaults to `NAS` and `RDL`; other inputs start with all rules.
2. If per-file patterns match, replace that selection with the **union** of their rule selectors. Declaration order and pattern specificity do not affect the result. An empty matching array selects no rules unless another matching entry contributes rules.
3. CLI `--select`, when supplied, replaces both global and per-file selection.
4. Remove global `ignore` and CLI `--ignore`. Ignored rules cannot be re-enabled by a file entry or CLI selection.

File mappings do not change discovery, `include`/`exclude`, or a rule's canonical scope. Explicit files also use the mappings. Every docstring in a Python file inherits the file's selection. `[]` disables rules but does not bypass UTF-8 reading or Python syntax checks.

Stdin uses `--stdin-filename` for matching. Relative names are resolved from the invocation directory, then made relative to the configuration root. Absolute names also work and need not exist. Unnamed stdin uses `<stdin>` and inherits the global selection unless a pattern matches that name.

A matching per-file entry that selects LLM rules opts that file into judging; other files follow their own selection policy. Unmatched entries do not require a model.

Global `llm.enabled`, `--llm`, and `--model` still opt into any LLM rules retained by each file's effective selection. Use a local global selection such as `NAS00` when other files must stay local. Model requirements are checked for all collected documents before any provider call. See [LLM review and privacy](llm.md).

The table requires non-empty file-pattern keys and arrays of non-empty rule-selector strings. Invalid entries fail with exit `2`, even when no file matches or CLI `--select` overrides them.
