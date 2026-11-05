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

### Default LLM review

With no global or matching per-file `select`, style-audit applies all `NAS` and `RDL` rules to supported inputs and judges their LLM rules by default. Chat completions use `openrouter/openrouter/free` and OpenRouter's `OPENROUTER_API_KEY`; Decisions mode requires a provider-supported model. Never put raw credentials in project TOML.

This invocation combines local NAS checks with readability review:

```sh
uv run style-audit draft.md --select NAS00,RDL
```

`--select` replaces the local-only selection from the earlier example. `NAS00` runs deterministic no-ai-slop checks and `RDL` enables readability judgments. Use `--select NAS,RDL` to include no-ai-slop LLM judgments too. `--model` overrides the default model and force-enables judging for selected LLM rules.

For project-wide selection, **replace** the earlier `[tool.style-audit]` table with this block; do not add a second table with the same name:

```toml
[tool.style-audit]
select = ["NAS", "RDL"]
output = "text"

[tool.style-audit.llm]
model = "openrouter/openrouter/free"

[tool.style-audit.llm.litellm]
api_key_env = "OPENROUTER_API_KEY"
custom_llm_provider = "openrouter"
```

The default ruleset selection already enables LLM judging; `model` selects its LiteLLM backend. Set `enabled = false` to disable judging unless the CLI explicitly force-enables it with `--llm` or `--model`. The optional `[tool.style-audit.llm.litellm]` table can override the API base, API-key environment variable, provider, timeout, and temperature for other chat models; see [LiteLLM transport settings](configuration.md#litellm-transport-settings).

Selected LLM rules send masked document units to the configured provider and can incur charges. Masking is not sensitive-data redaction.

### Other checkouts and CI

Commit your application's `pyproject.toml` and `uv.lock`. This installation uses a relative local source: collaborators and CI must also provide the `style-audit` checkout at `../style-audit`. The lockfile locks resolved dependencies but does not pin the contents of an editable checkout. Use the same tool revision on those machines. Running `uv sync` inside the tool's checkout alone does not add it to your application's environment.

For a local-only CI check, run from the application root with that sibling checkout present:

```sh
uv sync --locked --group dev
uv run --no-sync style-audit --select NAS00
```

The explicit local selection keeps CI local even when default LLM judging is active or the project config enables it. Exit status `1` or `2` should fail the check. Installing with `--no-dev` omits the linter, so include the `dev` group in the environment used for auditing.

## Install from a checkout

```sh
uv sync
uv run style-audit --help
```

`uv sync` installs the project, its LiteLLM runtime dependency, and the `style-audit` console entry point. Marimo is an optional extra for running the interactive system-design notebook: use `uv sync --extra marimo`. Static Marimo source auditing only parses `.py` files and does not require Marimo to be installed. To install documentation dependencies as well, use `uv sync --group docs`.

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
