"""Shared rule metadata and source-located diagnostics."""

from dataclasses import dataclass
from typing import Literal

RuleScope = Literal["sentence", "paragraph", "section", "document"]


class AuditError(Exception):
    """An operational failure, never a successful clean audit."""


@dataclass(frozen=True)
class RuleExample:
    """An illustrative revision with its intended context and reasoning."""

    before: str
    after: str
    explanation: str


@dataclass(frozen=True)
class Rule:
    code: str
    name: str
    engine: Literal["deterministic", "llm"]
    description: str
    source: str
    scope: RuleScope
    examples: tuple[RuleExample, ...]


@dataclass(frozen=True)
class Diagnostic:
    path: str
    code: str
    message: str
    line: int
    column: int
    end_line: int
    end_column: int
    evidence: str
    fix: str
