# Project configuration

The CLI reads `[tool.style-audit]` from the nearest `pyproject.toml` found by walking upward from the **current working directory**. It does not search from each input path. `--config PATH` bypasses discovery. `PATH` may be a TOML file or a directory containing `pyproject.toml`. Invalid TOML and invalid setting types fail with exit status `2`.

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
model = "azure-maas-judge/Decision-1"
threshold = 0.8
```

All settings are optional. Directory scanning defaults to `*.md`, `*.markdown`, `*.rst`, `*.txt`, `*.feature`, `*.py`, and `*.pyi`. Python files audit docstrings only.
`.feature` files receive a syntax-aware Gherkin pass that does not execute steps or load step definitions. It masks Gherkin keyword prefixes and full-line tags, comments, table rows, and docstring fixtures while keeping heading descriptions and step prose auditable. Explicit file paths bypass `include` filtering.

Includes and excludes are arrays of non-empty strings. Path matching uses Python filename-glob matching. A bare excluded directory name matches that component at any depth, and glob patterns can exclude directory subtrees. Supplying an `include` or `exclude` array replaces that default list. Restate the defaults you still need. `output` is `text` or `json`.

For docstrings only during directory traversal, use `include = ["*.py", "*.pyi"]`. To retain a prose-files-only scan including Gherkin features, use `include = ["*.md", "*.markdown", "*.rst", "*.txt", "*.feature"]`. Existing LLM opt-ins also apply to unmasked Gherkin feature prose and newly included Python docstrings. Narrow includes if those inputs must not be reviewed remotely. See [Python inputs](reference/cli.md#python-docstrings) and [Gherkin feature files](reference/cli.md#gherkin-feature-files).

The `llm` table accepts:

| Setting | Type and default | Effect |
| --- | --- | --- |
| `enabled` | Boolean, default `false` | Opt into judging selected LLM rules. |
| `model` | Non-empty string, no default model | Select the configured Azure MaaS Decision-1 model or a LiteLLM chat model. |
| `threshold` | Finite number in `[0, 1]`, default `0.8` | Emit decision findings when probability is greater than or equal to this value. |

Use `azure-maas-judge/Decision-1` for Azure MaaS Decisions judging. The public selector syntax is `azure-maas-judge/<model-id>`. The OMP registry supplies defaults for its base URL and API key, while `[tool.style-audit.llm.litellm]` can override LiteLLM settings as described below. The registry's `api: openrouter-decisions` selects the Decisions interface, not the OpenRouter service.

Other model names retain the LiteLLM chat backend. For example, `openai/gpt-4o-mini` requires its provider's configuration. Never put raw credentials in project TOML.

Enabling LLM review requires an explicit model. A configured model alone does not enable config-driven calls: `enabled` must be true, or an LLM rule must be explicitly selected. Command-line opt-ins are described below. See [LLM review and privacy](llm.md) for request content and backend differences.

### LiteLLM transport settings

The optional `[tool.style-audit.llm.litellm]` table supplies LiteLLM settings for chat and Decision-1 requests. `custom_llm_provider` selects LiteLLM's provider-specific Decisions adapter. For Microsoft Foundry project endpoints, configure `azure_ai` with the project `api_base`. For an OpenAI-compatible endpoint ending `/openai/v1`, configure `openai`. Style-audit passes the configured base and key explicitly.

The OMP registry still uses `api: openrouter-decisions` for this model entry. That value identifies the Decisions interface and does not route requests through OpenRouter.

```toml
[tool.style-audit.llm.litellm]
api_base = "https://<your-foundry-host>.services.ai.azure.com/api/projects/<project>"
custom_llm_provider = "azure_ai"
decision_model = "Decision-1"
timeout = 120
temperature = 0
```

| Setting | Type and default | Effect |
| --- | --- | --- |
| `api_base` | Optional non-empty URL, with Decision-1 falling back to the OMP provider's `baseUrl` | Sets LiteLLM's API base, which requires HTTPS except for loopback HTTP and rejects embedded credentials, query strings, and fragments. |
| `api_key_env` | Optional environment-variable name | Uses that variable's value as the API key, which must be set and does not fall back to the registry key. If omitted, `AZURE_MAAS_JUDGE_API_KEY` overrides the OMP key. |
| `custom_llm_provider` | Optional non-empty string, defaulting to `openai` for Decision-1 | Selects LiteLLM's Decisions adapter and is passed through to LiteLLM. Use `azure_ai` for Microsoft Foundry project endpoints or `openai` for OpenAI-compatible endpoints. Style-audit does not restrict the provider name. |
| `decision_model` | Optional non-empty string, or the CLI model ID when omitted | Selects the Decisions model ID, which must be listed by the provider when the OMP registry is loaded (the documented default is `Decision-1`). |
| `timeout` | Optional finite positive number of seconds | Overrides LiteLLM's request timeout. |
| `temperature` | Finite number in `[0, 2]`, default `0` | Sets chat-completion temperature. Decisions requests do not use it. |

Project values override matching Azure MaaS settings from the OMP registry. The registry supplies `baseUrl` and/or `apiKey` when those are not supplied by project settings or environment, and validates the selected model ID against its `models` list when loaded. A project `api_base` plus `api_key_env` can provide the full endpoint and credential source without registry lookup. Never put a raw key in TOML. Use an environment-variable name or the user-level registry, and protect the registry file.

TOML `threshold` accepts integers or floats, but rejects booleans, strings, nonfinite values (`nan` and `inf`), and values outside `[0, 1]`. `--threshold` overrides the configured value. Its effective value must also be finite and in range. Invalid settings fail with exit `2`, not an empty successful audit. The threshold neither enables LLM review nor changes rule selection. It has no filtering effect on chat responses, which do not return decision probabilities.

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


## Selection, ignoring, and LLM opt-in

With no `select`, all registered rules from the `NAS`, `RDL`, and `STE` catalogs are selected. A non-empty `select` array narrows the set. `ignore` removes rules from it. Entries may be exact IDs, prefixes, or filename-style globs.

`"NAS"` selects no-ai-slop rules. `"NAS1"` matches `NAS101`–`NAS121`. `"NAS00"` selects `NAS001`–`NAS003`. `"NAS00?"` selects the three local rules. `"NAS00[13]"` selects `NAS001` and `NAS003`.

`"RDL"` selects readability rules. `"STE"` selects all 61 ASD-STE100 rules and recommendations. `"STE606"` selects the local six-sentence paragraph check, and `"STE801"` selects the local semicolon check. Combine them, for example, with `select = ["NAS00", "RDL", "STE606", "STE801"]`.

`*`, `?`, and bracket classes use Python `fnmatchcase` semantics. Entries without glob characters retain prefix matching. Matching is case-sensitive. Selecting LLM rules requires an explicit model and opts into judging.

Selection does not change a rule's scope. Every deterministic and LLM rule has a canonical sentence, paragraph, section, or document assignment in the generated [rule reference](reference/rules.md). There are no scope overrides in TOML or on the CLI. Both LLM backends group selected rules by that metadata, requesting only the matching-scope rules and masked text of each eligible unit. Selecting additional scopes can increase remote request volume. See [segmentation, privacy, and cost](llm.md#canonical-scopes-and-segmentation).

CLI `--select` replaces both configured `select` and per-file selections, while CLI `--ignore` is combined with configured `ignore`. Unknown selectors in the effective global selection, ignores, or any per-file entry are errors. Per-file entries are validated even when unused or overridden by CLI selection. Quote CLI globs so the shell does not expand them. Examples:

```sh
style-audit --select NAS001,NAS003 draft.md
style-audit --ignore NAS003 docs/
style-audit --select NAS101 --model azure-maas-judge/Decision-1 --threshold 0.9 draft.md
style-audit --select RDL --model azure-maas-judge/Decision-1 draft.md
```

LLM judging requires selected LLM rules **and** an explicit opt-in. The opt-in comes from `[tool.style-audit.llm].enabled = true`, `--llm`, `--model`, or explicitly selecting an LLM rule. `--llm` does not broaden `select`: if only deterministic rules are selected, no provider call is made. A command-line model selects the model and opts into judging selected LLM rules. Deterministic-only checks never send text remotely.

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
model = "azure-maas-judge/Decision-1"
```

File patterns match case-sensitive, slash-separated paths **relative to the directory containing the selected `pyproject.toml`**, not the invocation directory. Running from a nested directory or supplying `--config` preserves that root. Paths outside it contain `../` components. Both file and rule globs use Python `fnmatchcase`: `*` spans directory separators, so `"*.py"` matches Python files at any depth and `"docs/*.md"` includes nested Markdown files.

`**` has no special zero-directory meaning. Use `"*.md"`, not `"**/*.md"`, to include root-level Markdown too. `?` matches one character, and `[12]` matches either listed character.

Selection order:

1. Start with global `select`, or all rules when it is absent or empty.
2. If any per-file patterns match, replace that selection with the **union** of their rule selectors. Declaration order and pattern specificity do not affect the result. An empty matching array selects no rules unless another matching entry contributes rules.
3. CLI `--select`, when supplied, replaces both global and per-file selection.
4. Remove global `ignore` and CLI `--ignore`. Ignored rules cannot be re-enabled by a file entry or CLI selection.

File mappings do not change discovery, `include`/`exclude`, or a rule's canonical scope. Explicit files also use the mappings. Every docstring in a Python file inherits the file's selection. `[]` disables rules but does not bypass UTF-8 reading or Python syntax checks.

Stdin uses `--stdin-filename` for matching. Relative names are resolved from the invocation directory, then made relative to the configuration root. Absolute names also work and need not exist. Unnamed stdin uses `<stdin>` and inherits the global selection unless a pattern matches that name.

A matching entry that explicitly selects LLM rules opts into judging **that file only** and requires a model. It does not enable LLM review of other files merely because their default selection contains LLM rules. Unmatched entries do not require a model.

Global `llm.enabled`, `--llm`, and `--model` still opt into any LLM rules retained by each file's effective selection. Use a local global selection such as `NAS00` when other files must stay local. Model requirements are checked for all collected documents before any provider call. See [LLM review and privacy](llm.md).

The table requires non-empty file-pattern keys and arrays of non-empty rule-selector strings. Invalid entries fail with exit `2`, even when no file matches or CLI `--select` overrides them.
