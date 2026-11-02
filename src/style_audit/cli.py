"""Command-line entry point and path discovery."""

from collections.abc import Sequence
from dataclasses import dataclass
import fnmatch
import math
import os
from pathlib import Path
import sys

import click

from .config import AuditConfig, load_config
from .deterministic import analyze_deterministic
from .docstrings import extract_docstrings
from .marimo_docs import extract_markdown_cells
from .llm import judge_document
from .models import AuditError, Diagnostic, Rule
from .reporting import render_json, render_text, sort_diagnostics
from .rules import RULES, RULES_BY_CODE
from .gherkin import document_from_feature
from .text import TextDocument


def _csv(values: Sequence[str], option: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for value in values for part in value.split(","))
    if any(not part for part in parts):
        raise AuditError(f"{option} requires non-empty rule IDs")
    return parts


def _expand(values: Sequence[str]) -> set[str]:
    selected: set[str] = set()
    for value in values:
        if any(char in value for char in "*?["):
            matches = {code for code in RULES_BY_CODE if fnmatch.fnmatchcase(code, value)}
        else:
            matches = {code for code in RULES_BY_CODE if code.startswith(value)}
        if not matches:
            raise AuditError(f"unknown rule selector {value!r}")
        selected.update(matches)
    return selected


def _excluded(relative: str, patterns: Sequence[str]) -> bool:
    parts = relative.split("/")
    for pattern in patterns:
        if fnmatch.fnmatchcase(relative, pattern) or any(part == pattern for part in parts):
            return True
        if fnmatch.fnmatchcase(relative.rstrip("/") + "/__style_audit_child__", pattern):
            return True
    return False


def _matches_include(relative: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(relative, pattern) or Path(relative).match(pattern) for pattern in patterns)


def _walk(directory: Path, config: AuditConfig, cwd: Path) -> list[Path]:
    discovered: list[Path] = []
    errors: list[OSError] = []
    try:
        root = directory.resolve()
    except OSError as exc:
        raise AuditError(f"cannot resolve input directory {directory}: {exc}") from exc

    def on_error(error: OSError) -> None:
        errors.append(error)

    for current, names, filenames in os.walk(root, topdown=True, onerror=on_error, followlinks=False):
        current_path = Path(current)
        relative_dir = current_path.relative_to(cwd).as_posix() if current_path.is_relative_to(cwd) else current_path.as_posix()
        names[:] = sorted(name for name in names if not _excluded((Path(relative_dir) / name).as_posix(), config.exclude))
        for filename in sorted(filenames):
            path = current_path / filename
            relative = path.relative_to(cwd).as_posix() if path.is_relative_to(cwd) else path.as_posix()
            if not _excluded(relative, config.exclude) and _matches_include(relative, config.include):
                discovered.append(path)
    if errors:
        first = errors[0]
        raise AuditError(f"cannot traverse {directory}: {first}")
    return discovered


def _documents(path: str, text: str) -> list[TextDocument]:
    suffix = Path(path).suffix.lower()
    if suffix in {".py", ".pyi"}:
        if suffix == ".py" and "marimo" in text:
            documents = extract_markdown_cells(path, text)
            if documents is not None:
                return documents
        return extract_docstrings(path, text)
    if suffix == ".feature":
        return [document_from_feature(path, text)]
    return [TextDocument(path, text)]

def _collect(paths: Sequence[str], config: AuditConfig, stdin_text: str | None, stdin_name: str, cwd: Path) -> list[TextDocument]:
    if paths.count("-") > 1:
        raise AuditError("standard input ('-') may be specified only once")
    targets: list[Path] = []
    for value in paths:
        if value == "-":
            continue
        path = Path(value).expanduser()
        if not path.exists():
            raise AuditError(f"input path does not exist: {value}")
        if path.is_file():
            targets.append(path.resolve())
        elif path.is_dir():
            targets.extend(_walk(path, config, cwd))
        else:
            raise AuditError(f"input is not a regular file or directory: {value}")
    targets = sorted(set(targets), key=lambda path: path.as_posix())

    documents: list[TextDocument] = []
    if "-" in paths:
        documents.extend(_documents(stdin_name, stdin_text or ""))
    for path in targets:
        display_path = path.relative_to(cwd).as_posix() if path.is_relative_to(cwd) else str(path)
        try:
            with path.open(encoding="utf-8", newline="") as file:
                documents.extend(_documents(display_path, file.read()))
        except (OSError, UnicodeError) as exc:
            raise AuditError(f"cannot read UTF-8 text from {path}: {exc}") from exc
    return documents


@dataclass(frozen=True)
class CLIOptions:
    paths: tuple[str, ...]
    config: Path | None
    select: tuple[str, ...]
    ignore: tuple[str, ...]
    format: str | None
    llm: bool
    model: str | None
    threshold: float | None
    stdin_filename: str


def build_cli() -> click.Command:
    @click.command(
        name="style-audit",
        help="Find source-backed writing-style patterns without guessing who wrote the text.",
        context_settings={"help_option_names": ["-h", "--help"]},
    )
    @click.argument("paths", nargs=-1)
    @click.option(
        "--config",
        type=click.Path(path_type=Path),
        help="read configuration from this pyproject.toml or directory",
    )
    @click.option(
        "--select",
        multiple=True,
        metavar="RULE[,RULE]",
        help="select rule IDs, prefixes, or globs; replaces configured global and per-file selection",
    )
    @click.option(
        "--ignore",
        multiple=True,
        metavar="RULE[,RULE]",
        help="ignore rule IDs, prefixes, or globs",
    )
    @click.option(
        "--format",
        type=click.Choice(("text", "json")),
        help="output format (default: project setting or text)",
    )
    @click.option("--llm", is_flag=True, help="explicitly enable LLM judgments")
    @click.option("--model", help="LiteLLM model for enabled editorial judgments")
    @click.option(
        "--threshold",
        type=click.FloatRange(min=0, max=1),
        help="decision probability threshold from 0 to 1 (default: project setting or 0.8)",
    )
    @click.option(
        "--stdin-filename",
        default="<stdin>",
        show_default=True,
        help="input name for stdin; .py extracts Marimo Markdown cells or Python docstrings, "
        ".pyi extracts docstrings, and .feature parses Gherkin",
    )
    @click.version_option(
        version="0.1.0",
        prog_name="style-audit",
        message="%(prog)s %(version)s",
    )
    def command(
        paths: tuple[str, ...],
        config: Path | None,
        select: tuple[str, ...],
        ignore: tuple[str, ...],
        format: str | None,
        llm: bool,
        model: str | None,
        threshold: float | None,
        stdin_filename: str,
    ) -> int:
        options = CLIOptions(paths, config, select, ignore, format, llm, model, threshold, stdin_filename)
        try:
            exit_code, rendered = run(options)
        except (AuditError, OSError) as exc:
            click.echo(f"style-audit: error: {exc}", err=True)
            return 2
        if rendered:
            click.echo(rendered, nl=False)
        return exit_code

    return command


def run(args: CLIOptions, stdin_text: str | None = None, cwd: Path | None = None) -> tuple[int, str]:
    working_directory = (cwd or Path.cwd()).resolve()
    config = load_config(working_directory, args.config)
    selection = _csv(args.select, "--select") if args.select else config.select
    ignored = _expand((*config.ignore, *_csv(args.ignore, "--ignore")))
    enabled = (_expand(selection) if selection else set(RULES_BY_CODE)) - ignored
    per_file = tuple((pattern, _expand(values) - ignored) for pattern, values in config.per_file_select)
    if args.select:
        per_file = ()
    model = args.model or config.llm_model
    threshold = args.threshold if args.threshold is not None else config.llm_threshold
    if isinstance(threshold, bool) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise AuditError("--threshold must be a finite number between 0 and 1")
    paths = args.paths or ["."]
    if "-" in paths and stdin_text is None:
        stdin_text = sys.stdin.read()
    documents = _collect(paths, config, stdin_text, args.stdin_filename, working_directory)
    rule_plans: dict[str, tuple[tuple[Rule, ...], tuple[Rule, ...]]] = {}
    for document in documents:
        if document.path in rule_plans:
            continue
        relative = Path(os.path.relpath(working_directory / document.path, config.root)).as_posix()
        matches = [codes for pattern, codes in per_file if fnmatch.fnmatchcase(relative, pattern)]
        codes = set().union(*matches) if matches else enabled
        rules = tuple(rule for rule in RULES if rule.code in codes)
        deterministic_rules = tuple(rule for rule in rules if rule.engine == "deterministic")
        llm_rules = tuple(rule for rule in rules if rule.engine == "llm")
        if config.ste_disallowed_words and any(rule.code == "STE101" for rule in rules):
            deterministic_rules += (RULES_BY_CODE["STE101"],)
        llm_selected = bool(args.select or config.select or matches)
        use_llm = bool(llm_rules) and (config.llm_enabled or args.llm or args.model is not None or llm_selected)
        if use_llm and not model:
            raise AuditError("LLM judging requires an explicit model; configure [tool.style-audit.llm].model or pass --model")
        rule_plans[document.path] = deterministic_rules, llm_rules if use_llm else ()

    findings: list[Diagnostic] = []
    for document in documents:
        deterministic_rules, llm_rules = rule_plans[document.path]
        if deterministic_rules:
            findings.extend(analyze_deterministic(
                document,
                deterministic_rules,
                nas_allowed_words=config.nas_allowed_words,
                nas_disallowed_words=config.nas_disallowed_words,
                ste_disallowed_words=config.ste_disallowed_words,
            ))
        if llm_rules:
            findings.extend(judge_document(
                document,
                llm_rules,
                model or "",
                threshold=threshold,
                litellm_config=config.llm_litellm,
                ste_allowed_words=config.ste_allowed_words,
                ste_disallowed_words=config.ste_disallowed_words,
            ))
    ordered = sort_diagnostics(findings)
    output_format = args.format or config.output
    rendered = render_json(ordered) if output_format == "json" else render_text(ordered)
    return (1 if ordered else 0), rendered


def main(argv: Sequence[str] | None = None) -> int:
    command = build_cli()
    try:
        result = command.main(
            args=list(argv) if argv is not None else None,
            prog_name="style-audit",
            standalone_mode=False,
        )
    except click.ClickException as exc:
        exc.show()
        return exc.exit_code
    except click.exceptions.Exit as exc:
        return exc.exit_code
    return int(result or 0)
