"""Shared rule metadata and source-located diagnostics."""

import re
from string import Formatter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RuleScope = Literal["sentence", "paragraph", "section", "document"]


class AuditError(Exception):
    """An operational failure, never a successful clean audit."""


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class RegexDetector(_FrozenModel):
    kind: Literal["regex"]
    pattern: str
    flags: tuple[Literal["ignorecase"], ...] = ()
    target: Literal["unit", "heading"] = "unit"
    message: str
    fix: str

    @model_validator(mode="after")
    def validate_pattern(self) -> "RegexDetector":
        regex_flags = re.IGNORECASE if "ignorecase" in self.flags else 0
        try:
            re.compile(self.pattern, regex_flags)
            for _, field, format_spec, conversion in Formatter().parse(self.message):
                if field is not None and field != "evidence":
                    raise ValueError("message may interpolate only {evidence}")
                if format_spec or conversion not in (None, "r"):
                    raise ValueError("message supports only the !r conversion for evidence")
        except re.error as exc:
            raise ValueError(f"invalid Python regular expression: {exc}") from exc
        except ValueError as exc:
            raise ValueError(f"invalid regex diagnostic message: {exc}") from exc
        return self


class SentenceCountDetector(_FrozenModel):
    kind: Literal["sentence_count"]
    max_sentences: int = Field(gt=0)
    skip_markdown_tables: bool = False


Detector = Annotated[RegexDetector | SentenceCountDetector, Field(discriminator="kind")]

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

    detector: Detector | None = None
    additional_terms: tuple[str, ...] = ()

    @field_validator("additional_terms")
    @classmethod
    def validate_additional_terms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not term.strip() for term in value):
            raise ValueError("additional terms must be non-empty strings")
        return tuple(term.strip() for term in value)

    @model_validator(mode="after")
    def validate_detector(self) -> "Rule":
        if self.engine == "deterministic" and self.detector is None:
            raise ValueError("deterministic rules require a detector")
        if self.engine == "llm" and self.detector is not None:
            raise ValueError("LLM rules cannot define a deterministic detector")
        if isinstance(self.detector, SentenceCountDetector) and self.scope != "paragraph":
            raise ValueError("sentence-count detectors require paragraph scope")
        if isinstance(self.detector, RegexDetector) and self.detector.target == "heading" and self.scope != "section":
            raise ValueError("heading regex detectors require section scope")
        if self.additional_terms and not isinstance(self.detector, RegexDetector):
            raise ValueError("additional terms require a regex detector")
        return self


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


class ConfidenceScore(_FrozenModel):
    """A source-located Decisions probability, including below-threshold results."""

    path: str
    code: str
    scope: RuleScope
    probability: float
    meets_threshold: bool
    line: int
    column: int
    end_line: int
    end_column: int
    evidence: str
