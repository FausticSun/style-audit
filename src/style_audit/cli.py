"""Command-line entry point and path discovery."""

from collections.abc import Sequence
import fnmatch
import math
import os
import subprocess
from pathlib import Path
import sys

import click
from pydantic import BaseModel, ConfigDict

from .config import (
    DEFAULT_SELECT,
    AuditConfig,
    load_config,
)
from .deterministic import analyze_deterministic
from .docstrings import extract_docstrings
from .marimo_docs import extract_markdown_cells
from .llm import judge_document
from .models import AuditError, ConfidenceScore, Diagnostic, Rule
from .reporting import render_json, render_text, sort_diagnostics
from .rules import RULES
from .gherkin import document_from_feature
from .text import TextDocument


def _csv(values: Sequence[str], option: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for value in values for part in value.split(","))
    if any(not part for part in parts):
        raise AuditError(f"{option} requires non-empty rule IDs")
    return parts


def _expand(values: Sequence[str], rule_codes: Sequence[str]) -> set[str]:
    selected: set[str] = set()
    for value in values:
        if any(char in value for char in "*?["):
            matches = {code for code in rule_codes if fnmatch.fnmatchcase(code, value)}
        else:
            matches = {code for code in rule_codes if code.startswith(value)}
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
    return [TextDocument(
        path=path,
        text=text,
    )]

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


def _commit_message_documents(revision: str, cwd: Path) -> list[TextDocument]:
    if not revision or revision.startswith("-"):
        raise AuditError("--commit-messages requires a Git revision or range")
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--no-color",
                "--encoding=UTF-8",
                "--format=%H%x00%B%x00",
                revision,
            ],
            cwd=cwd,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise AuditError(f"cannot read Git commit messages: {exc}") from exc
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise AuditError(
            f"cannot read Git commit messages for {revision!r}: {detail or 'git log failed'}"
        )

    fields = result.stdout.split(b"\0")
    if len(fields) % 2 != 1:
        raise AuditError("Git returned malformed commit-message output")
    documents: list[TextDocument] = []
    for index in range(0, len(fields) - 1, 2):
        commit = fields[index].strip()
        if not commit:
            continue
        try:
            commit_id = commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise AuditError("Git returned an invalid commit ID") from exc
        try:
            message = fields[index + 1].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AuditError(f"commit {commit_id} has a message that is not valid UTF-8") from exc
        documents.append(TextDocument(path=f"commit/{commit_id}.txt", text=message))
    return documents


def _validate_cli_threshold(
    ctx: click.Context,
    param: click.Parameter,
    value: float | None,
) -> float | None:
    if value is not None and (not math.isfinite(value) or not 0 <= value <= 1):
        raise click.BadParameter("must be a finite number from 0 to 1", ctx=ctx, param=param)
    return value


class CLIOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    paths: tuple[str, ...]
    config: Path | None
    select: tuple[str, ...]
    ignore: tuple[str, ...]
    format: str | None
    llm: bool
    model: str | None
    commit_messages: str | None = None
    threshold: float | None = None
    show_confidences: bool = False
    stdin_filename: str


def build_cli() -> click.Command:
    @click.command(
        name="style-audit",
        help=(
            "Find source-backed writing-style patterns without guessing who wrote the text. "
            "Without a global or matching per-file selection, it applies all NAS and RDL "
            "rules and sends eligible prose to the configured LLM provider by default. "
            "Set [tool.style-audit.llm].enabled = false or select deterministic-only rules "
            "to avoid remote judging."
        ),
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
    @click.option(
        "--commit-messages",
        metavar="REVISION",
        help="audit commit messages reachable from this Git revision or range",
    )
    @click.option("--llm", is_flag=True, help="force-enable LLM judgments for selected rules")
    @click.option(
        "--model",
        help="LiteLLM model for judging (completion default: openrouter/openrouter/free; required for Decisions)",
    )
    @click.option(
        "--threshold",
        type=float,
        callback=_validate_cli_threshold,
        metavar="PROBABILITY",
        help="override the configured Decisions threshold in [0, 1]",
    )
    @click.option(
        "--show-confidences",
        is_flag=True,
        help="include all Decisions probabilities in the report, including below-threshold scores",
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
        commit_messages: str | None,
        threshold: float | None,
        show_confidences: bool,
        stdin_filename: str,
    ) -> int:
        options = CLIOptions(
            paths=paths,
            config=config,
            select=select,
            ignore=ignore,
            format=format,
            llm=llm,
            model=model,
            commit_messages=commit_messages,
            threshold=threshold,
            show_confidences=show_confidences,
            stdin_filename=stdin_filename,
        )
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
    if args.commit_messages is not None and args.paths:
        raise AuditError("--commit-messages cannot be combined with input paths")
    if args.threshold is not None:
        if not math.isfinite(args.threshold) or not 0 <= args.threshold <= 1:
            raise AuditError("--threshold must be a finite number from 0 to 1")
        if config.llm_api != "decisions":
            raise AuditError("--threshold is available only with the Decisions API")
    if args.show_confidences and config.llm_api != "decisions":
        raise AuditError("--show-confidences requires [tool.style-audit.llm].api = 'decisions'")
    effective_threshold = args.threshold if args.threshold is not None else config.llm_threshold
    rules_by_code = {rule.code: rule for rule in (*RULES, *config.project_rules)}
    rules_by_code.update({rule.code: rule for rule in config.overridden_rules})
    rules = tuple(rules_by_code.values())
    rule_codes = tuple(rules_by_code)
    selection = _csv(args.select, "--select") if args.select else config.select
    ignored = _expand((*config.ignore, *_csv(args.ignore, "--ignore")), rule_codes)
    enabled = _expand(selection or DEFAULT_SELECT, rule_codes) - ignored
    per_file = tuple(
        (pattern, _expand(values, rule_codes) - ignored)
        for pattern, values in config.per_file_select
    )
    if args.select:
        per_file = ()
    model = args.model or config.llm_model
    if args.commit_messages is not None:
        documents = _commit_message_documents(args.commit_messages, working_directory)
    else:
        paths = args.paths or ["."]
        if "-" in paths and stdin_text is None:
            stdin_text = sys.stdin.read()
        documents = _collect(paths, config, stdin_text, args.stdin_filename, working_directory)
    rule_plans: dict[str, tuple[tuple[Rule, ...], tuple[Rule, ...], str | None]] = {}
    for document in documents:
        if document.path in rule_plans:
            continue
        relative = (
            document.path
            if args.commit_messages is not None
            else Path(os.path.relpath(working_directory / document.path, config.root)).as_posix()
        )
        matches = [codes for pattern, codes in per_file if fnmatch.fnmatchcase(relative, pattern)]
        if matches:
            codes = set().union(*matches)
        else:
            codes = enabled
        selected_rules = tuple(rule for rule in rules if rule.code in codes)
        deterministic_rules = tuple(rule for rule in selected_rules if rule.engine == "deterministic")
        llm_rules = tuple(rule for rule in selected_rules if rule.engine == "llm")
        if config.ste_disallowed_words and any(rule.code == "STE101" for rule in selected_rules):
            deterministic_rules += (rules_by_code["STE101"],)
        use_llm = bool(llm_rules) and (
            config.llm_enabled is not False or args.llm or args.model is not None
        )
        document_model = model
        if use_llm and document_model is None:
            raise AuditError("LLM judging requires a model; configure [tool.style-audit.llm].model or pass --model")
        rule_plans[document.path] = deterministic_rules, llm_rules if use_llm else (), document_model

    if args.threshold is not None or args.show_confidences:
        if not any(llm_rules for _, llm_rules, _ in rule_plans.values()):
            raise AuditError(
                "--threshold and --show-confidences require selected LLM rules "
                "with judging enabled"
            )
    confidence_scores: list[ConfidenceScore] | None = [] if args.show_confidences else None
    findings: list[Diagnostic] = []
    for document in documents:
        deterministic_rules, llm_rules, document_model = rule_plans[document.path]
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
                document_model or "",
                api=config.llm_api,
                threshold=effective_threshold,
                litellm_config=config.llm_litellm,
                ste_allowed_words=config.ste_allowed_words,
                ste_disallowed_words=config.ste_disallowed_words,
                confidence_scores=confidence_scores,
            ))
    ordered = sort_diagnostics(findings)
    output_format = args.format or config.output
    if output_format == "json":
        rendered = render_json(ordered, confidence_scores=confidence_scores, threshold=effective_threshold)
    else:
        rendered = render_text(ordered, confidence_scores=confidence_scores, threshold=effective_threshold)
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
