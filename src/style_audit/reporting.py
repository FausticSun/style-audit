"""Deterministic text and JSON diagnostic renderers."""

import json
from collections.abc import Sequence

from .models import Diagnostic


def sort_diagnostics(findings: Sequence[Diagnostic]) -> list[Diagnostic]:
    return sorted(findings, key=lambda item: (item.path, item.line, item.column, item.code, item.end_line, item.end_column))


def render_text(findings: Sequence[Diagnostic]) -> str:
    lines: list[str] = []
    for item in sort_diagnostics(findings):
        lines.append(f"{item.path}:{item.line}:{item.column}: {item.code}: {item.message}")
        lines.append(f"  Evidence: {item.evidence}")
        if item.fix:
            lines.append(f"  Suggestion: {item.fix}")
    return "\n".join(lines) + ("\n" if lines else "")


def render_json(findings: Sequence[Diagnostic]) -> str:
    return json.dumps(
        {"version": 1, "findings": [item.model_dump(mode="json") for item in sort_diagnostics(findings)]},
        ensure_ascii=False,
        indent=2,
    ) + "\n"
