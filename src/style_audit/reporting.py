"""Deterministic text and JSON diagnostic renderers."""

import json
from collections.abc import Sequence

from .models import ConfidenceScore, Diagnostic


def sort_diagnostics(findings: Sequence[Diagnostic]) -> list[Diagnostic]:
    return sorted(findings, key=lambda item: (item.path, item.line, item.column, item.code, item.end_line, item.end_column))


def sort_confidence_scores(scores: Sequence[ConfidenceScore]) -> list[ConfidenceScore]:
    return sorted(
        scores,
        key=lambda item: (item.path, item.line, item.column, item.code, item.end_line, item.end_column),
    )


def render_text(
    findings: Sequence[Diagnostic],
    *,
    confidence_scores: Sequence[ConfidenceScore] | None = None,
    threshold: float | None = None,
) -> str:
    lines: list[str] = []
    for item in sort_diagnostics(findings):
        lines.append(f"{item.path}:{item.line}:{item.column}: {item.code}: {item.message}")
        lines.append(f"  Evidence: {item.evidence}")
        if item.fix:
            lines.append(f"  Suggestion: {item.fix}")
    if confidence_scores is not None:
        if threshold is None:
            raise ValueError("confidence reports require the effective threshold")
        lines.append(f"Model confidence scores (threshold {threshold:.2f}):")
        for item in sort_confidence_scores(confidence_scores):
            status = "meets threshold" if item.meets_threshold else "below threshold"
            lines.append(
                f"{item.path}:{item.line}:{item.column}: {item.code}: "
                f"{item.probability:.2f} ({status})"
            )
            lines.append(f"  Evidence: {item.evidence}")
    return "\n".join(lines) + ("\n" if lines else "")


def render_json(
    findings: Sequence[Diagnostic],
    *,
    confidence_scores: Sequence[ConfidenceScore] | None = None,
    threshold: float | None = None,
) -> str:
    report = {
        "version": 1,
        "findings": [item.model_dump(mode="json") for item in sort_diagnostics(findings)],
    }
    if confidence_scores is not None:
        if threshold is None:
            raise ValueError("confidence reports require the effective threshold")
        report["confidence_threshold"] = threshold
        report["confidences"] = [
            item.model_dump(mode="json") for item in sort_confidence_scores(confidence_scores)
        ]
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"
