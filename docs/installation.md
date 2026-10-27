# Installation and first scan

The package requires Python 3.14 or newer and uses [uv](https://docs.astral.sh/uv/) for dependency and environment management.

## Use in a new Python/uv project

This walkthrough installs the current repository from a local checkout as a development dependency of your application. It does not assume a PyPI release. Keep the checkout in a directory named `style-audit`; the new `writing-project` directory will sit beside it.

### 1. Create the project and add the tool

Start in the directory **containing** the `style-audit` checkout, not inside the checkout:

```sh
uv init --python 3.14 writing-project
cd writing-project
uv add --dev --editable ../style-audit
uv run style-audit --help
```

The example creates a Python 3.14 project. The tool requires Python 3.14 or newer; it cannot be added to a project environment that must support an older Python version.

`uv add` installs the console command and LiteLLM dependency, updates `uv.lock`, and adds these sections to your application's `pyproject.toml`:

```toml
[dependency-groups]
dev = ["style-audit"]

[tool.uv.sources]
style-audit = { path = "../style-audit", editable = true }
```

Let uv create or merge those sections; keep your existing application dependencies and build settings. The `dev` group is installed by default with `uv sync` and `uv run`. An editable installation uses the checkout's Python source directly, so changes there are available to later CLI invocations without reinstalling the tool. No provider credentials are needed for local checks.

### 2. Configure local checks in pyproject.toml

Append this table to the new project's `pyproject.toml`, alongside the sections uv maintains:

```toml
[tool.style-audit]
select = ["NAS00"]
output = "text"
```

`NAS00` selects the three deterministic no-ai-slop rules, `NAS001`–`NAS003`. This configuration runs locally and never sends document text to a model provider. Browse the [no-ai-slop rule cards](reference/no-ai-slop.md) for their criteria and examples.

Run commands from your application's root. Configuration discovery starts at the current working directory and walks upward to the nearest `pyproject.toml`; it does not start from the input file's location. Use `--config PATH` when running from elsewhere. See [project configuration](configuration.md) for includes, excludes, ignoring rules, and CLI overrides.

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

The default directory scan checks `.md`, `.markdown`, `.rst`, and `.txt` files, not Python source files. Virtual environments, Git metadata, build output, and Python caches are excluded. The [CLI reference](reference/cli.md) describes diagnostic fields and input handling. Exit status `2` means a configuration, input, or provider error; inspect stderr rather than treating it as a clean scan.

### Optional: enable LLM review

Provide `OPENROUTER_API_KEY` in the process environment through your shell or CI secret store. Do not put the key in `pyproject.toml` or commit it to the repository. This example opts into readability review for one invocation:

```sh
uv run style-audit draft.md --select NAS00,RDL --model microsoft/microsoft-decision-1 --threshold 0.8
```

`--select` replaces the local-only configured selection. The command runs the local checks plus the LLM-based [readability rules](reference/readability.md). Use `--select NAS,RDL` to include no-ai-slop editorial judgments too. A model flag alone does not broaden a deterministic-only selection.

For project-wide opt-in, **replace** the earlier `[tool.style-audit]` table with the following block; do not add a second table with the same name:

```toml
[tool.style-audit]
select = ["NAS00", "RDL"]
output = "text"

[tool.style-audit.llm]
enabled = true
model = "microsoft/microsoft-decision-1"
threshold = 0.8
```

Subsequent `uv run style-audit` commands use that review configuration and need the provider key. Selected LLM rules send masked document units to the provider and can incur charges; adding rule scopes can increase request volume. The threshold applies to this decision model's finding probabilities, not to LiteLLM chat-model responses. Read [LLM review and privacy](llm.md) before enabling it for private documents.

### Other checkouts and CI

Commit your application's `pyproject.toml` and `uv.lock`. This installation uses a relative local source: collaborators and CI must also provide the `style-audit` checkout at `../style-audit`. The lockfile locks resolved dependencies but does not pin the contents of an editable checkout; use the same tool revision on those machines. Running `uv sync` inside the tool's checkout alone does not add it to your application's environment.

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

With no paths, the CLI scans the current directory. Directory scans include `.md`, `.markdown`, `.rst`, and `.txt` files by default. An explicitly named file may use any extension, but must be readable UTF-8 text. Directories named `.git`, `.venv`, `venv`, `build`, `dist`, and `__pycache__` are excluded by default.

Only local deterministic rules run by default; no document text is sent to a provider. Findings produce exit status `1`, a clean scan `0`, and configuration, input, or provider errors `2`. See the [CLI reference](reference/cli.md) and [configuration guide](configuration.md) for selection, output, and model-review options.
