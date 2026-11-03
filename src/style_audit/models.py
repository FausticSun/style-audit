"""Shared rule metadata and source-located diagnostics."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

RuleScope = Literal["sentence", "paragraph", "section", "document"]


class AuditError(Exception):
    """An operational failure, never a successful clean audit."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RuleExample(_FrozenModel):
    """An illustrative revision with its intended context and reasoning."""

    before: str
    after: str
    explanation: str


class Rule(_FrozenModel):
    code: str
    name: str
    engine: Literal["deterministic", "llm"]
    description: str
    source: str
    scope: RuleScope
    examples: tuple[RuleExample, ...]


class Diagnostic(_FrozenModel):
    path: str
    code: str
    message: str
    line: int
    column: int
    end_line: int
    end_column: int
    evidence: str
    fix: str
