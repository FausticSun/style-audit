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
model = "openrouter/microsoft/microsoft-decision-1"
threshold = 0.8
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
| `model` | Optional non-empty string, no default | Required for LLM judging. A configured model alone does not enable global judging. |
| `threshold` | Finite number in `[0, 1]`, default `0.8` | Emit decision findings when probability is greater than or equal to this value. |

Use `azure-maas-judge/Decision-1` for Azure MaaS Decisions judging. The public selector syntax is `azure-maas-judge/<model-id>`. The OMP registry supplies defaults for its base URL and API key, while `[tool.style-audit.llm.litellm]` can override LiteLLM settings as described below. The registry's `api: openrouter-decisions` selects the Decisions interface, not the OpenRouter service.

Other model names use LiteLLM chat completions directly. If a Decisions-selected model rejects its first Decisions request as unsupported or unavailable on that endpoint, style-audit switches that model to chat completions; authentication and other failures remain errors. Chat findings do not use the probability threshold. For example, `openai/gpt-4o-mini` requires its provider's configuration. Never put raw credentials in project TOML.

For OpenRouter Microsoft Decision-1, set `OPENROUTER_API_KEY`. LiteLLM's `systemone` adapter sends typed judgments to `POST https://openrouter.ai/api/alpha/decisions`; this model does not use chat completions. No OMP registry or custom endpoint is needed. If overriding `api_base`, use the OpenRouter API root (`https://openrouter.ai/api`), not the chat `/api/v1` base.

LLM judging is off by default, including when the default Markdown selection contains RDL rules. A configured model alone does not enable it. Opt in through `[tool.style-audit.llm].enabled = true` (with a model), `--llm` or `--model`, or an explicit LLM-rule selection with a model. A matching per-file entry that selects LLM rules also opts that file in. See [LLM review and privacy](llm.md) for request content and backend differences.

### LiteLLM transport settings

The optional `[tool.style-audit.llm.litellm]` table supplies LiteLLM settings for chat and Decisions requests. `custom_llm_provider` selects LiteLLM's provider-specific Decisions adapter. OpenRouter Decision-1 uses `openrouter`; Microsoft Foundry project endpoints use `azure_ai`, and OpenAI-compatible endpoints use `openai`. Style-audit passes the configured base and key explicitly.

The OMP registry still uses `api: openrouter-decisions` for its legacy Azure MaaS model entry. That value identifies the Decisions interface and does not route requests through OpenRouter.

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
| `api_base` | Optional non-empty URL; OpenRouter Decisions default to `https://openrouter.ai/api`, and Azure MaaS can fall back to the OMP provider's `baseUrl` | Sets LiteLLM's API base, which requires HTTPS except for loopback HTTP and rejects embedded credentials, query strings, and fragments. |
| `api_key_env` | Optional environment-variable name | Uses that variable's value as the API key, which must be set. OpenRouter defaults to `OPENROUTER_API_KEY`; Azure MaaS otherwise checks `AZURE_MAAS_JUDGE_API_KEY` and then the OMP registry key. |
| `custom_llm_provider` | Optional non-empty string | Selects LiteLLM's Decisions adapter. OpenRouter Decision-1 requires `openrouter`; Azure MaaS defaults to `openai`, with `azure_ai` for Microsoft Foundry project endpoints. |
| `decision_model` | Optional non-empty string, or the CLI model ID when omitted | Selects the Decisions model ID. OpenRouter adds the `openrouter/` prefix when it is omitted; Azure MaaS validates IDs against the OMP model list when that registry is loaded. |
| `timeout` | Optional finite positive number of seconds | Overrides LiteLLM's request timeout. |
| `temperature` | Finite number in `[0, 2]`, default `0` | Sets chat-completion temperature. Decisions requests do not use it. |

Project values override matching Azure MaaS settings from the OMP registry. The registry supplies `baseUrl` and/or `apiKey` when those are not supplied by project settings or environment, and validates the selected model ID against its `models` list when loaded. A project `api_base` plus `api_key_env` can provide the full endpoint and credential source without registry lookup. OpenRouter calls use OpenRouter credentials and the Decisions endpoint directly; they do not read this registry. Never put a raw key in TOML. Use an environment-variable name or the user-level registry, and protect the registry file.

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

Without a non-empty `select`, `.md` inputs with no matching per-file entry default to the `NAS` and `RDL` catalogs; other unmatched inputs retain all registered rules. This changes rule selection only; LLM judging remains opt-in. A non-empty global `select` or matching per-file entry overrides the Markdown default. `ignore` removes rules from the effective selection.

`"NAS"` selects no-ai-slop rules. `"NAS1"` matches `NAS101`–`NAS121`. `"NAS00"` selects `NAS001`–`NAS003`. `"NAS00?"` selects the three local rules. `"NAS00[13]"` selects `NAS001` and `NAS003`.

`"RDL"` selects readability rules. `"STE"` selects all 61 ASD-STE100 rules and recommendations. `"STE606"` selects the local six-sentence paragraph check, and `"STE801"` selects the local semicolon check. Combine them, for example, with `select = ["NAS00", "RDL", "STE606", "STE801"]`.

`*`, `?`, and bracket classes use Python `fnmatchcase` semantics. Entries without glob characters retain prefix matching. Matching is case-sensitive. Default `.md` selection does not enable remote review or choose a model; LLM rules require explicit opt-in and a model.

Selection does not change a rule's scope. Every deterministic and LLM rule has a canonical sentence, paragraph, section, or document assignment in the generated [rule reference](reference/rules.md). There are no scope overrides in TOML or on the CLI. Both LLM backends group selected rules by that metadata, requesting only the matching-scope rules and masked text of each eligible unit. Selecting additional scopes can increase remote request volume. See [segmentation, privacy, and cost](llm.md#canonical-scopes-and-segmentation).

CLI `--select` replaces both configured `select` and per-file selections, while CLI `--ignore` is combined with configured `ignore`. Unknown selectors in the effective global selection, ignores, or any per-file entry are errors. Per-file entries are validated even when unused or overridden by CLI selection. Quote CLI globs so the shell does not expand them. Examples:

```sh
style-audit --select NAS001,NAS003 draft.md
style-audit --ignore NAS003 docs/
style-audit --select NAS101 --model azure-maas-judge/Decision-1 --threshold 0.9 draft.md
style-audit --select RDL --model azure-maas-judge/Decision-1 draft.md
```

LLM judging remains off by default, including for default `.md` selections. It requires selected LLM rules and an explicit opt-in: `[tool.style-audit.llm].enabled = true` (which requires a configured model), `--llm`, `--model`, or explicitly selecting an LLM rule. A matching per-file entry selecting LLM rules opts that file in. Explicit CLI/model/rule-selection opt-ins still take precedence over `enabled = false`. `--llm` does not broaden `select`; deterministic-only checks never send text remotely.

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

1. Start with configured global `select` when non-empty. Otherwise, an unmatched `.md` input defaults to `NAS` and `RDL`; other inputs start with all rules.
2. If per-file patterns match, replace that selection with the **union** of their rule selectors. Declaration order and pattern specificity do not affect the result. An empty matching array selects no rules unless another matching entry contributes rules.
3. CLI `--select`, when supplied, replaces both global and per-file selection.
4. Remove global `ignore` and CLI `--ignore`. Ignored rules cannot be re-enabled by a file entry or CLI selection.

File mappings do not change discovery, `include`/`exclude`, or a rule's canonical scope. Explicit files also use the mappings. Every docstring in a Python file inherits the file's selection. `[]` disables rules but does not bypass UTF-8 reading or Python syntax checks.

Stdin uses `--stdin-filename` for matching. Relative names are resolved from the invocation directory, then made relative to the configuration root. Absolute names also work and need not exist. Unnamed stdin uses `<stdin>` and inherits the global selection unless a pattern matches that name.

A matching per-file entry that selects LLM rules opts that file into judging; other files follow their own selection policy. Unmatched entries do not require a model.

Global `llm.enabled`, `--llm`, and `--model` still opt into any LLM rules retained by each file's effective selection. Use a local global selection such as `NAS00` when other files must stay local. Model requirements are checked for all collected documents before any provider call. See [LLM review and privacy](llm.md).

The table requires non-empty file-pattern keys and arrays of non-empty rule-selector strings. Invalid entries fail with exit `2`, even when no file matches or CLI `--select` overrides them.
