"""Command-line entry point and path discovery."""

import argparse
import fnmatch
import os
import math
from pathlib import Path
import sys
from collections.abc import Sequence

from .config import AuditConfig, load_config
from .deterministic import analyze_deterministic
from .llm import judge_document
from .models import AuditError, Diagnostic, Rule
from .reporting import render_json, render_text, sort_diagnostics
from .rules import RULES, RULES_BY_CODE
from .text import TextDocument


def _csv(values: Sequence[str], option: str) -> tuple[str, ...]:
    parts = tuple(part.strip() for value in values for part in value.split(","))
    if any(not part for part in parts):
        raise AuditError(f"{option} requires non-empty rule IDs")
    return parts


def _expand(values: Sequence[str]) -> set[str]:
    selected: set[str] = set()
    for value in values:
        prefix = value[:-1] if value.endswith("*") else value
        if "*" in prefix:
            raise AuditError(f"invalid rule selector {value!r}; use a rule ID or prefix")
        matches = {code for code in RULES_BY_CODE if code.startswith(prefix)}
        if not matches:
            raise AuditError(f"unknown rule selector {value!r}")
        selected.update(matches)
    return selected


def _enabled_rules(config: AuditConfig, cli_select: Sequence[str], cli_ignore: Sequence[str]) -> tuple[Rule, ...]:
    selection = _csv(cli_select, "--select") if cli_select else config.select
    ignored_values = (*config.ignore, *_csv(cli_ignore, "--ignore"))
    enabled = _expand(selection) if selection else set(RULES_BY_CODE)
    enabled.difference_update(_expand(ignored_values))
    return tuple(rule for rule in RULES if rule.code in enabled)


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
        documents.append(TextDocument(stdin_name, stdin_text or ""))
    for path in targets:
        display_path = path.relative_to(cwd).as_posix() if path.is_relative_to(cwd) else str(path)
        try:
            documents.append(TextDocument(display_path, path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError) as exc:
            raise AuditError(f"cannot read UTF-8 text from {path}: {exc}") from exc
    return documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="style-audit",
        description="Find source-backed writing-style patterns without guessing who wrote the text.",
    )
    parser.add_argument("paths", nargs="*", help="UTF-8 text files, directories, or - for standard input (default: current directory)")
    parser.add_argument("--config", type=Path, help="read configuration from this pyproject.toml or directory")
    parser.add_argument("--select", action="append", default=[], metavar="RULE[,RULE]", help="select rules or rule-ID prefixes; replaces configured selection")
    parser.add_argument("--ignore", action="append", default=[], metavar="RULE[,RULE]", help="ignore rules or rule-ID prefixes")
    parser.add_argument("--format", choices=("text", "json"), help="output format (default: project setting or text)")
    parser.add_argument("--llm", action="store_true", help="explicitly enable LLM judgments")
    parser.add_argument("--model", help="LiteLLM model for enabled editorial judgments")
    parser.add_argument("--threshold", type=float, help="decision probability threshold from 0 to 1 (default: project setting or 0.8)")
    parser.add_argument("--stdin-filename", default="<stdin>", help="display name for standard input")
    parser.add_argument("--version", action="version", version="style-audit 0.1.0")
    return parser


def run(args: argparse.Namespace, stdin_text: str | None = None, cwd: Path | None = None) -> tuple[int, str]:
    working_directory = (cwd or Path.cwd()).resolve()
    config = load_config(working_directory, args.config)
    enabled = _enabled_rules(config, args.select, args.ignore)
    llm_rules = tuple(rule for rule in enabled if rule.engine == "llm")
    model = args.model or config.llm_model
    threshold = args.threshold if args.threshold is not None else config.llm_threshold
    if isinstance(threshold, bool) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise AuditError("--threshold must be a finite number between 0 and 1")
    llm_selected = any(rule.engine == "llm" for rule in enabled) and bool(args.select or config.select)
    use_llm = bool(llm_rules) and (config.llm_enabled or args.llm or args.model is not None or llm_selected)
    if use_llm and not model:
        raise AuditError("LLM judging requires an explicit model; configure [tool.style-audit.llm].model or pass --model")
    paths = args.paths or ["."]
    if "-" in paths and stdin_text is None:
        stdin_text = sys.stdin.read()
    documents = _collect(paths, config, stdin_text, args.stdin_filename, working_directory)

    findings: list[Diagnostic] = []
    deterministic_rules = tuple(rule for rule in enabled if rule.engine == "deterministic")
    for document in documents:
        if deterministic_rules:
            findings.extend(analyze_deterministic(document, deterministic_rules))
        if use_llm:
            findings.extend(judge_document(document, llm_rules, model or "", threshold=threshold))
    ordered = sort_diagnostics(findings)
    output_format = args.format or config.output
    rendered = render_json(ordered) if output_format == "json" else render_text(ordered)
    return (1 if ordered else 0), rendered


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        exit_code, stdout = run(args)
    except (AuditError, OSError) as exc:
        print(f"style-audit: error: {exc}", file=sys.stderr)
        return 2
    if stdout:
        sys.stdout.write(stdout)
    return exit_code
