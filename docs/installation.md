# Installation and first scan

The package requires Python 3.12 or newer and uses [uv](https://docs.astral.sh/uv/) for dependency and environment management.

## Use in a new Python/uv project

This walkthrough installs the current repository from a local checkout as a development dependency of your application. It does not assume a PyPI release. Keep the checkout in a directory named `style-audit`. The new `writing-project` directory will sit beside it.

### 1. Create the project and add the tool

Start in the directory **containing** the `style-audit` checkout, not inside the checkout:

```sh
uv init --python 3.12 writing-project
cd writing-project
uv add --dev --editable ../style-audit
uv run style-audit --help
```

The example creates a Python 3.12 project. The tool requires Python 3.12 or newer. It cannot be added to a project environment that must support an older Python version.

`uv add` installs the console command and LiteLLM dependency, updates `uv.lock`, and adds these sections to your application's `pyproject.toml`:

```toml
[dependency-groups]
dev = ["style-audit"]

[tool.uv.sources]
style-audit = { path = "../style-audit", editable = true }
```

Let uv create or merge those sections. Keep your existing application dependencies and build settings. The `dev` group is installed by default with `uv sync` and `uv run`. An editable installation uses the checkout's Python source directly, so changes there are available to later CLI invocations without reinstalling the tool. No provider credentials are needed for local checks.

### 2. Configure local checks in pyproject.toml

Append this table to the new project's `pyproject.toml`, alongside the sections uv maintains:

```toml
[tool.style-audit]
select = ["NAS00"]
output = "text"
```

`NAS00` selects the three deterministic no-ai-slop rules, `NAS001`–`NAS003`. This configuration runs locally and never sends document text to a model provider. Browse the [no-ai-slop rule cards](reference/no-ai-slop.md) for their criteria and examples.

Run commands from your application's root. Configuration discovery starts at the current working directory and walks upward to the nearest `pyproject.toml`. It does not start from the input file's location. Use `--config PATH` when running from elsewhere. See [project configuration](configuration.md) for includes, excludes, ignoring rules, and CLI overrides.

### 3. Run the audit and fix a finding

Create a draft with a deliberately banned term:

```sh
printf '%s\n' 'We utilize the parser.' > draft.md
uv run style-audit draft.md
```

Expect `NAS001` at line 1, column 4, with exit status `1`. That status means findings were reported, not an installation failure. Replace the term and scan again:

```sh
printf '%s\n' 'We use the parser.' > draft.md
uv run style-audit draft.md
```

The revised draft produces no findings and exit status `0`. To scan the project, name files explicitly, request JSON, or read standard input:

```sh
uv run style-audit
uv run style-audit README.md draft.md
uv run style-audit draft.md --format json
cat draft.md | uv run style-audit -
```

The default directory scan checks `.md`, `.markdown`, `.rst`, `.txt`, `.feature`, `.py`, and `.pyi` files. Ordinary Python files audit docstrings; recognized Marimo `.py` apps audit direct Markdown cell literals without executing the app.

Gherkin `.feature` files are processed as text without executing scenarios. Syntax prefixes, full-line tags, comments, table rows, and docstring fixtures are masked. Heading descriptions and step prose remain auditable.

Virtual environments, Git metadata, build output, generated `site/` output, and Python caches are excluded. The [CLI reference](reference/cli.md) describes Gherkin handling, diagnostic fields, and input handling. Exit status `2` means a configuration, input, or provider error. Inspect stderr rather than treating it as a clean scan.

### 4. Audit Python docstrings

Save this working function in `example.py`:

```python
def parse_count(value: str) -> int:
    """Use a robust count parser."""
    return int(value)
```

Run `uv run style-audit example.py`: the local configuration reports `NAS001` at line 2, column 14. Change the docstring to `"""Parse an integer count."""` and rerun for a clean result. Comments and non-docstring strings do not affect this audit. A Python file with invalid syntax fails with exit `2`. It is never audited as raw prose.

Audit an existing source tree with `uv run style-audit src/`, or pipe Python code with `cat example.py | uv run style-audit - --stdin-filename example.py`. The filename is needed to select Python extraction on stdin. `.py` Marimo apps expose literal Markdown cells; ordinary `.py` files and `.pyi` stubs expose docstrings. [Python inputs](reference/cli.md#python-docstrings) covers scope, decoding, and source locations.

### Optional: enable LLM review

Configure the Azure MaaS Decision-1 provider in the OMP model registry. Style-audit looks first at `~/.omp/agent/models.yml`, then falls back to `~/.omp/agents/models.yml` if the first file is absent:

```yaml
providers:
  azure-maas-judge:
    api: openrouter-decisions
    baseUrl: "https://<your-azure-maas-host>/openai/v1"
    apiKey: "<your-secret-api-key>"
    models:
      - id: Decision-1
```

The registry's `baseUrl` supplies LiteLLM's `api_base` unless project configuration overrides it. `custom_llm_provider` selects LiteLLM's provider-specific Decisions adapter.

For a Microsoft Foundry project endpoint, set it to `azure_ai`. LiteLLM constructs `/providers/microsoft/v1/systemone`. For an OpenAI-compatible base ending `/openai/v1`, set it to `openai`. LiteLLM constructs `/openai/v1/decisions`. The required OMP value `api: openrouter-decisions` identifies the Decisions interface but does not use the OpenRouter service. Style-audit passes the configured base URL and API key explicitly.

The registry `apiKey` is a secret. Restrict access to this user-level YAML file and do not commit or share it. Unless a different `api_key_env` is configured in TOML, `AZURE_MAAS_JUDGE_API_KEY` overrides the registry key. The `api_key_env` value names an environment variable, not its secret value. The named variable must be set and does not fall back to the registry key. See [LiteLLM transport settings](configuration.md#litellm-transport-settings) for project overrides and validation.

This invocation opts into readability review:

```sh
uv run style-audit draft.md --select NAS00,RDL --model azure-maas-judge/Decision-1 --threshold 0.8
```

`--select` replaces the local-only configured selection. The command runs the local checks plus the LLM-based [readability rules](reference/readability.md). Use `--select NAS,RDL` to include no-ai-slop editorial judgments too. A model flag alone does not broaden a deterministic-only selection.

For project-wide opt-in, **replace** the earlier `[tool.style-audit]` table with the following block. Do not add a second table with the same name.

```toml
[tool.style-audit]
select = ["NAS00", "RDL"]
output = "text"

[tool.style-audit.llm]
enabled = true
model = "azure-maas-judge/Decision-1"
threshold = 0.8

[tool.style-audit.llm.litellm]
api_base = "https://<your-foundry-host>.services.ai.azure.com/api/projects/<project>"
custom_llm_provider = "azure_ai"
decision_model = "Decision-1"
```

This example uses the OMP registry's `apiKey`. The project `api_base` overrides its `baseUrl`. Never put a raw key in TOML. An optional `api_key_env` can select a different environment variable, which must be set and does not fall back to the registry.

Subsequent `uv run style-audit` commands use this project configuration and the OMP registry for the model entry and key. Unless `api_key_env` is configured, `AZURE_MAAS_JUDGE_API_KEY` overrides the registry `apiKey`. When that variable is unset, style-audit uses the registry key.

Selected LLM rules send masked document units to the configured provider and can incur charges. Adding rule scopes can increase request volume. The threshold applies to Decision-1 finding probabilities, not to LiteLLM chat-model responses.

A previous audit of `wages-report/report.md` through the OpenAI Decisions adapter returned LiteLLM `ServiceUnavailableError`. After switching to the Foundry route, one document-scoped `NAS113` check on that file completed with no findings; the full `wages-report` NAS/RDL audit remains unrun. The separate Marimo system-design audit exited `1` with three `NAS117` findings and no `RDL` findings. See the [dogfooding record](dogfooding.md#observed-marimo-system-design-audit).

### Other checkouts and CI

Commit your application's `pyproject.toml` and `uv.lock`. This installation uses a relative local source: collaborators and CI must also provide the `style-audit` checkout at `../style-audit`. The lockfile locks resolved dependencies but does not pin the contents of an editable checkout. Use the same tool revision on those machines. Running `uv sync` inside the tool's checkout alone does not add it to your application's environment.

For a local-only CI check, run from the application root with that sibling checkout present:

```sh
uv sync --locked --group dev
uv run --no-sync style-audit --select NAS00
```

The explicit selection keeps CI local even if the optional LLM table is enabled. Exit status `1` or `2` should fail the check. Installing with `--no-dev` omits the linter, so include the `dev` group in the environment used for auditing.

## Install from a checkout

```sh
uv sync
uv run style-audit --help
```

`uv sync` installs the project, its LiteLLM runtime dependency, and the `style-audit` console entry point. To install documentation dependencies as well, use `uv sync --group docs`.

An installed package can also be invoked as a module:

```sh
uv run python -m style_audit --help
```

## Audit prose

```sh
uv run style-audit README.md
uv run style-audit docs/ notes.txt
cat draft.txt | uv run style-audit -
uv run style-audit docs/ --format json
```

With no paths, the CLI scans the current directory. Directory scans include `.md`, `.markdown`, `.rst`, `.txt`, `.feature`, `.py`, and `.pyi` files by default. Python inputs audit docstrings only. Gherkin feature headings and step text are treated as prose after syntax masking, and scenarios are never executed.

An explicitly named file may use any extension, but must be readable UTF-8 text. Directories named `.git`, `.venv`, `venv`, `build`, `dist`, `site`, and `__pycache__` are excluded by default.

Only local deterministic rules run by default. No document text is sent to a provider. Findings produce exit status `1`, a clean scan `0`, and configuration, input, or provider errors `2`. See the [CLI reference](reference/cli.md) and [configuration guide](configuration.md) for selection, output, and model-review options.
