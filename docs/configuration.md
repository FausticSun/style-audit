# Project configuration

The CLI reads `[tool.style-audit]` from the nearest `pyproject.toml` found by walking upward from the **current working directory**. It does not search from each input path. `--config PATH` bypasses discovery; `PATH` may be a TOML file or a directory containing `pyproject.toml`. Invalid TOML and invalid setting types fail with exit status `2`.

## Settings

```toml
[tool.style-audit]
include = ["*.md", "*.markdown", "*.rst", "*.txt"]
exclude = [".git", ".venv", "venv", "build", "dist", "__pycache__", "vendor/**"]
select = ["NAS001", "NAS002", "NAS003"]
ignore = []
output = "text"

[tool.style-audit.llm]
enabled = false
model = "microsoft/microsoft-decision-1"
threshold = 0.8
```

All settings are optional. Directory scanning defaults to `*.md`, `*.markdown`, `*.rst`, and `*.txt`. Explicit file paths bypass `include` filtering. Includes and excludes are arrays of non-empty strings; path matching uses Python filename-glob matching. A bare excluded directory name matches that component at any depth, and glob patterns can exclude directory subtrees. Supplying an `include` or `exclude` array replaces that default list; restate the defaults you still need. `output` is `text` or `json`.

The `llm` table accepts:

| Setting | Type and default | Effect |
| --- | --- | --- |
| `enabled` | Boolean, default `false` | Opt into judging selected LLM rules. |
| `model` | Non-empty string, no default model | Select the OpenRouter decision model or a LiteLLM chat model. |
| `threshold` | Finite number in `[0, 1]`, default `0.8` | Emit decision findings when probability is greater than or equal to this value. |

Use `microsoft/microsoft-decision-1` or its equivalent LiteLLM-qualified name `openrouter/microsoft/microsoft-decision-1` for decisions, with `OPENROUTER_API_KEY` in the environment. Other model names retain the LiteLLM chat backend; for example, `openai/gpt-4o-mini` requires its provider's configuration. Keep credentials out of TOML.

Enabling LLM review requires an explicit model. A configured model alone does not enable config-driven calls: `enabled` must be true, or an LLM rule must be explicitly selected. Command-line opt-ins are described below. See [LLM review and privacy](llm.md) for request content and backend differences.

TOML `threshold` accepts integers or floats, but rejects booleans, strings, nonfinite values (`nan` and `inf`), and values outside `[0, 1]`. `--threshold` overrides the configured value; its effective value must also be finite and in range. Invalid settings fail with exit `2`, not an empty successful audit. The threshold neither enables LLM review nor changes rule selection. It has no filtering effect on chat responses, which do not return decision probabilities.

## Selection, ignoring, and LLM opt-in

With no `select`, all registered rules in both catalogs are selected. A non-empty `select` array narrows the set; `ignore` removes from it. Entries may be exact IDs or prefixes. `"NAS"` selects no-ai-slop rules, `"NAS1"` matches `NAS101`–`NAS121`, and `"NAS00"` matches `NAS001`–`NAS003`. `"RDL"` selects the separate [readability ruleset](reference/readability.md); combine them with `select = ["NAS00", "RDL"]` for local source rules plus readability review. Matching is case-sensitive. `RDL` consists of LLM rules, so selecting it requires an explicit model and opts into judging.

Selection does not change a rule's scope. Every deterministic and LLM rule has a canonical sentence, paragraph, section, or document assignment in the generated [rule reference](reference/rules.md). There are no scope overrides in TOML or on the CLI. Both LLM backends group selected rules by that metadata, requesting only the matching-scope rules and masked text of each eligible unit. Selecting additional scopes can increase remote request volume; see [segmentation, privacy, and cost](llm.md#canonical-scopes-and-segmentation).

CLI `--select` replaces configured `select`, while CLI `--ignore` is combined with configured `ignore`. Unknown selectors are errors. Examples:

```sh
style-audit --select NAS001,NAS003 draft.md
style-audit --ignore NAS003 docs/
style-audit --select NAS101 --model microsoft/microsoft-decision-1 --threshold 0.9 draft.md
style-audit --select RDL --model microsoft/microsoft-decision-1 draft.md
```

LLM judging requires selected LLM rules **and** an explicit opt-in. The opt-in comes from `[tool.style-audit.llm].enabled = true`, `--llm`, `--model`, or explicitly selecting an LLM rule. `--llm` does not broaden `select`: if only deterministic rules are selected, no provider call is made. A command-line model selects the model and opts into judging selected LLM rules. Deterministic-only checks never send text remotely.

`AuditConfig` and `load_config()` in `style_audit.config` implement these settings. The parser accepts only the documented setting types; a broken `pyproject.toml` is not silently ignored.
