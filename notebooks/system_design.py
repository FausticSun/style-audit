import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    from collections import Counter
    from pathlib import Path
    import tomllib

    import marimo as mo
    import style_audit
    from style_audit.rules import RULES

    repo_root = Path(style_audit.__file__).resolve().parents[2]
    with (repo_root / "pyproject.toml").open("rb") as project_file:
        project_data = tomllib.load(project_file)
    project = project_data["project"]
    metadata = {
        "name": project["name"],
        "version": project["version"],
        "python": project["requires-python"],
        "runtime_dependencies": project.get("dependencies", []),
        "dev_dependencies": project_data.get("dependency-groups", {}).get("dev", []),
    }
    families = tuple(dict.fromkeys(rule.code[:3] for rule in RULES))
    return Counter, RULES, families, metadata, mo


@app.cell
def _(metadata, mo):
    mo.md(
        f"""# {metadata['name']} — system design

    **Purpose.** A Python writing-style CLI that combines source-backed deterministic checks with optional, explicitly enabled editorial judgments. It reports reviewable findings; it does not rewrite prose or classify authorship.

    **Package:** `{metadata['version']}` · **Python:** `{metadata['python']}`  
    **Runtime dependencies:** {", ".join(f"`{item}`" for item in metadata['runtime_dependencies'])}  
    **Developer tools:** {", ".join(f"`{item}`" for item in metadata['dev_dependencies'])}

    Catalog counts and explorer choices come from `style_audit.rules.RULES` and `pyproject.toml` in this checkout.
    """
    )
    return


@app.cell
def _(mo):
    mo.mermaid(
        """flowchart TD
    CLI["CLI entry points"] --> CFG["TOML settings and rule plan"]
    CFG --> INPUT["Paths or standard input"]
    INPUT --> KIND{"Input kind"}
    KIND -->|Prose| DOC["TextDocument"]
    KIND -->|Python| AST{"Marimo app?"}
    AST -->|Yes| MD["AST mo.md Markdown extraction"]
    AST -->|No| DOCS["AST docstring extraction"]
    MD --> DOC
    DOCS --> DOC
    KIND -->|Gherkin| GH["Mask syntax and fixtures"]
    GH --> DOC
    DOC --> PLAN["Per-file rules and scoped units"]
    PLAN --> LOCAL["Deterministic checks"]
    PLAN --> OPT{"Selected LLM rules opted in?"}
    OPT -->|Yes| JUDGE["LiteLLM judge"]
    OPT -->|No| MERGE["Sort diagnostics"]
    JUDGE --> CHAT["Chat completions"]
    JUDGE --> DECISION["Decisions API"]
    CHAT --> MERGE
    DECISION --> MERGE
    LOCAL --> MERGE
    MERGE --> REPORT["Text or JSON report"]
    REPORT --> EXIT["Exit status 0, 1, or 2"]"""
    )
    return


@app.cell
def _(mo):
    mo.md("""
    ## Component responsibilities

    The CLI owns discovery, planning, orchestration, and exit status. The text layer owns segmentation and source-coordinate mapping. Rule modules declare policy; analyzers execute local checks or delegate selected scopes. Reporting is a terminal boundary, not part of rule evaluation.
    """)
    return


@app.cell
def _(mo):
    module_rows = [
        {"Layer": "Entry", "Modules": "__init__.py, __main__.py, cli.py", "Contract": "Console and module entry points; discover inputs; resolve each file's rule plan; map operational failures to exit 2."},
        {"Layer": "Configuration", "Modules": "config.py", "Contract": "Discover and validate [tool.style-audit]; hold global/per-file selectors, local vocabularies, LLM opt-in, thresholds, and transport settings."},
        {"Layer": "Input adapters", "Modules": "docstrings.py, marimo_docs.py, gherkin.py", "Contract": "Extract Python docstrings and Marimo Markdown without executing code; mask Gherkin syntax and fixtures without running scenarios."},
        {"Layer": "Text model", "Modules": "text.py", "Contract": "Represent visible prose, masks, source maps, logical units, spans, and original-source evidence."},
        {"Layer": "Policy", "Modules": "rules/no-ai-slop.yaml, rules/readability.yaml, rules/technical-english.yaml, rule_catalog.py, rules/__init__.py", "Contract": "Canonical validated ruleset YAML metadata, prompts, detectors, scope, source citations, and examples."},
        {"Layer": "Execution", "Modules": "deterministic.py, llm.py, decision_api.py", "Contract": "Run selected local checks; call LiteLLM chat or Decisions judging by scope; validate provider responses."},
        {"Layer": "Output", "Modules": "models.py, reporting.py", "Contract": "Carry immutable Rule/Diagnostic values; sort findings; render versioned JSON or text."},
    ]
    mo.ui.table(module_rows, pagination=False, selection=None)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Input normalization and source locations

    - Markdown, reStructuredText, and plain text become prose documents. `TextDocument` masks code and quotations without splitting a logical unit into visible fragments.
    - Python files are parsed with the AST, never imported or run. Ordinary `.py` and `.pyi` inputs expose docstrings; recognized Marimo `.py` apps expose direct `mo.md()` strings and static f-string text. The extractor omits f-string expressions. A `SourceMap` maps decoded Markdown to its source positions and spelling.
    - `.feature` files use a syntax-aware text pass. Gherkin keyword prefixes, tags, comments, table rows, docstrings, and fenced fixtures are masked. Heading descriptions and step prose remain auditable; scenarios and step definitions are not executed or loaded.

    Sentence, paragraph, section, and document scopes are declared in rule metadata. The segmenter uses punctuation and structural boundaries; it is intentionally not a full linguistic parser. The selected scope controls both what text is sent remotely and the diagnostic span returned locally.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Rule catalog

    Rule IDs, engine, and scope are runtime metadata. The summary and explorer below read the canonical `style_audit.rules.RULES` catalog.
    """)
    return


@app.cell
def _(Counter, RULES, families, mo):
    summary_rows = []
    for family in families:
        family_rules = [rule for rule in RULES if rule.code.startswith(family)]
        engines = Counter(rule.engine for rule in family_rules)
        scopes = Counter(rule.scope for rule in family_rules)
        summary_rows.append(
            {
                "Ruleset": family,
                "Registered rules": len(family_rules),
                "Deterministic": engines["deterministic"],
                "LLM": engines["llm"],
                "Scopes": ", ".join(
                    f"{scope}: {scopes[scope]}"
                    for scope in ("sentence", "paragraph", "section", "document")
                    if scopes[scope]
                ),
            }
        )
    mo.ui.table(summary_rows, pagination=False, selection=None)
    return


@app.cell
def _(families, mo):
    family_picker = mo.ui.dropdown(
        options=list(families),
        value=families[-1],
        label="Explore registered rules",
        full_width=True,
    )
    family_picker
    return (family_picker,)


@app.cell
def _(RULES, family_picker):
    selected_family = family_picker.value
    selected_rules = [rule for rule in RULES if rule.code.startswith(selected_family)]
    return selected_family, selected_rules


@app.cell
def _(mo, selected_family):
    family_context = {
        "NAS": "NAS combines explicit local pattern checks with context-sensitive editorial judgments.",
        "RDL": "RDL adapts readability research as sentence-scoped LLM judgments; it does not compute the paper's corpus metrics.",
        "STE": "STE606 counts sentences in visible paragraphs and STE801 checks semicolons locally. Other STE entries require contextual review. The supplied PDF includes Part 2's controlled dictionary, but this catalog does not parse its entries or certify vocabulary compliance.",
    }[selected_family]
    mo.md(
        f"""### {selected_family} rule details

    Each entry carries its diagnostic ID, engine, canonical scope, upstream source, and contextual examples. {family_context}"""
    )
    return


@app.cell
def _(mo, selected_rules):
    rule_rows = [
        {
            "ID": rule.code,
            "Name": rule.name,
            "Engine": rule.engine,
            "Scope": rule.scope,
        }
        for rule in selected_rules
    ]
    mo.ui.table(rule_rows, pagination=True, page_size=12, selection=None)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Selection and execution policy

    `config.load_config()` discovers the nearest `pyproject.toml` from the current working directory; `--config` selects an explicit file or directory. Exact IDs, prefixes, and case-sensitive filename-style globs select rules. Matching per-file selections are unioned and replace the global selection for that file; ignores always remove rules. CLI `--select` replaces configured global and per-file selection.

    Local rules run without a provider. LLM review requires selected subjective rules plus an explicit opt-in (`llm.enabled`, `--llm`, `--model`, or explicit selection) and a model. A deterministic-only selection never initiates a remote call. The registered scope groups rules so each request contains only its matching rules and one eligible masked unit.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Remote judging and trust boundaries

    Chat models use LiteLLM chat completions and must return structured findings with exact visible evidence quotes inside the current unit. Azure MaaS Decision-1 uses LiteLLM's Decisions `systemone` API; answers must match the requested rule IDs and contain finite probabilities in `[0, 1]`. Decision findings use the inclusive configured threshold. Provider or validation failures are operational errors, not clean results.

    The Decisions base, provider, and model can be overridden in project TOML; otherwise the OMP `azure-maas-judge` registry supplies defaults. A configured `api_key_env` is mandatory when selected; otherwise `AZURE_MAAS_JUDGE_API_KEY` overrides the registry key. Requests are synchronous and per eligible scope unit. The application has no cache, retry, or backend fallback.

    **Privacy boundary:** deterministic checks stay local. Opted-in LLM rules send visible prose from the selected masked unit. Python comments and executable code, Gherkin fixtures, and masked code/quotes are excluded from model input, but masking is not sensitive-data redaction. Visible docstring and Gherkin prose can still contain private information.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Diagnostics, failures, and verification

    A `Diagnostic` carries path, rule ID, message, one-based start/end positions, evidence, and an optional fix. Reporting sorts diagnostics before rendering text or version-1 JSON.

    | Exit status | Meaning |
    | --- | --- |
    | `0` | No findings |
    | `1` | Findings reported |
    | `2` | Configuration, input, provider, or response-validation error |

    The suite combines focused unit tests with pytest-bdd acceptance scenarios. Tests use controlled providers; the Decision adapter also has a local HTTP route smoke test. No test requires provider credentials. The installed command is `style-audit`; `python -m style_audit` exposes the same CLI.

    Run or export this report from the repository root:

    ```sh
    uv run marimo edit notebooks/system_design.py
    uv run marimo run notebooks/system_design.py
    uv run marimo export html notebooks/system_design.py -o /tmp/style-audit-system-design.html
    ```

    **Implementation references:** `src/style_audit/cli.py`, `config.py`, `docstrings.py`, `marimo_docs.py`, `gherkin.py`, `text.py`, `rules/no-ai-slop.yaml`, `rules/readability.yaml`, `rules/technical-english.yaml`, `rule_catalog.py`, `src/style_audit/rules/__init__.py`, `deterministic.py`, `llm.py`, `decision_api.py`, `models.py`, and `reporting.py`. The checked-in [architecture guide](../docs/architecture.md) records the package contracts.
    """)
    return


if __name__ == "__main__":
    app.run()
