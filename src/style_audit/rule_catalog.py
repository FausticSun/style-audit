"""Loading bundled and project-defined YAML ruleset catalogs."""

import json
from collections.abc import Iterable, Sequence
from importlib.resources import files
from pathlib import Path, PureWindowsPath
from typing import Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .models import AuditError, Detector, RegexDetector, Rule, RuleExample, RuleScope


class _CatalogModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class _RuleRecord(_CatalogModel):
    code: str
    name: str
    engine: Literal["deterministic", "llm"]
    scope: RuleScope
    source: str
    examples: tuple[RuleExample, ...]
    prompt: str | None = None
    description: str | None = None
    detector: Detector | None = None
    additional_terms: tuple[str, ...] = Field(default=(), alias="additional-terms")

    @model_validator(mode="after")
    def validate_engine_fields(self) -> "_RuleRecord":
        if self.engine == "llm":
            if not self.prompt or not self.prompt.strip():
                raise ValueError("LLM rule records require a non-empty prompt")
            if self.description is not None:
                raise ValueError("LLM rule records use prompt, not description")
            if self.detector is not None:
                raise ValueError("LLM rule records cannot define deterministic detectors")
        else:
            if not self.description or not self.description.strip():
                raise ValueError("deterministic rule records require a non-empty description")
            if self.prompt is not None:
                raise ValueError("deterministic rule records use description, not prompt")
            if self.detector is None:
                raise ValueError("deterministic rule records require a detector")
        return self

    def to_rule(self) -> Rule:
        return Rule(
            code=self.code,
            name=self.name,
            engine=self.engine,
            description=self.prompt if self.prompt is not None else self.description or "",
            source=self.source,
            scope=self.scope,
            examples=self.examples,
            detector=self.detector,
            additional_terms=self.additional_terms,
        )


class _RuleOverrideRecord(_CatalogModel):
    code: str
    name: str | None = None
    scope: RuleScope | None = None
    source: str | None = None
    prompt: str | None = None
    description: str | None = None
    examples: tuple[RuleExample, ...] | None = None
    detector: dict[str, object] | None = None
    additional_terms: tuple[str, ...] | None = Field(default=None, alias="additional-terms")

    @field_validator("name", "source", "prompt", "description", mode="before")
    @classmethod
    def validate_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("rule override text fields must be non-empty strings")
        return value.strip()

    @field_validator("detector", mode="before")
    @classmethod
    def validate_detector_mapping(cls, value: object) -> dict[str, object] | None:
        if value is None:
            return None
        if not isinstance(value, dict) or not value:
            raise ValueError("detector overrides must be non-empty tables")
        return value

    @field_validator("additional_terms", mode="before")
    @classmethod
    def validate_additional_terms(cls, value: object) -> tuple[str, ...] | None:
        if value is None:
            return None
        if (
            not isinstance(value, (list, tuple))
            or not value
            or not all(isinstance(term, str) and term.strip() for term in value)
        ):
            raise ValueError("additional-terms must be a non-empty array of non-empty strings")
        return tuple(term.strip() for term in value)

    @model_validator(mode="after")
    def validate_override_fields(self) -> "_RuleOverrideRecord":
        fields = self.model_fields_set - {"code"}
        if not fields:
            raise ValueError("each rule override must specify at least one field")
        if any(getattr(self, name) is None for name in fields):
            raise ValueError("rule override fields cannot be null")
        if self.prompt is not None and self.description is not None:
            raise ValueError("an override cannot specify both prompt and description")
        if self.examples is not None and not self.examples:
            raise ValueError("examples overrides must contain at least one example")
        return self


class _RuleOverrides(_CatalogModel):
    schema_version: Literal[1]
    overrides: tuple[_RuleOverrideRecord, ...]

    @model_validator(mode="after")
    def validate_unique_codes(self) -> "_RuleOverrides":
        codes = [override.code for override in self.overrides]
        if not codes:
            raise ValueError("the rule override file must contain at least one override")
        if len(codes) != len(set(codes)):
            raise ValueError("each rule ID can be overridden only once per file")
        return self


class _RuleCatalog(_CatalogModel):
    schema_version: Literal[1]
    rules: tuple[_RuleRecord, ...]

    @model_validator(mode="after")
    def validate_unique_codes(self) -> "_RuleCatalog":
        codes = [rule.code for rule in self.rules]
        if not codes:
            raise ValueError("the rule catalog must contain at least one rule")
        if len(codes) != len(set(codes)):
            raise ValueError("rule IDs must be unique")
        return self


class _UniqueKeySafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader: _UniqueKeySafeLoader, node: yaml.MappingNode, deep: bool = False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def parse_rule_catalog(content: str, *, source: str = "<memory>") -> tuple[Rule, ...]:
    """Parse YAML records into validated immutable rules."""
    try:
        value = yaml.load(content, Loader=_UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        raise AuditError(f"cannot parse rule catalog {source}: {exc}") from exc
    try:
        json_value = json.dumps(value, ensure_ascii=False)
        catalog = _RuleCatalog.model_validate_json(json_value)
    except (TypeError, ValueError, ValidationError) as exc:
        raise AuditError(f"invalid rule catalog {source}: {exc}") from exc
    return tuple(record.to_rule() for record in catalog.rules)


def parse_rule_overrides(
    content: str,
    *,
    source: str = "<memory>",
) -> tuple[_RuleOverrideRecord, ...]:
    """Parse strict partial overrides for registered rules."""
    try:
        value = yaml.load(content, Loader=_UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        raise AuditError(f"cannot parse rule overrides {source}: {exc}") from exc
    try:
        json_value = json.dumps(value, ensure_ascii=False)
        catalog = _RuleOverrides.model_validate_json(json_value)
    except (TypeError, ValueError, ValidationError) as exc:
        raise AuditError(f"invalid rule overrides {source}: {exc}") from exc
    return catalog.overrides


_RULESET_CATALOGS = (
    "no-ai-slop.yaml",
    "readability.yaml",
    "technical-english.yaml",
    "microsoft-writing.yaml",
)


def load_rule_catalog() -> tuple[Rule, ...]:
    """Load bundled rulesets in stable order, independent of the working directory."""
    ruleset_directory = files("style_audit").joinpath("rules")
    rules: list[Rule] = []
    for filename in _RULESET_CATALOGS:
        source = f"rules/{filename}"
        try:
            content = ruleset_directory.joinpath(filename).read_text(encoding="utf-8")
        except (OSError, UnicodeError, ModuleNotFoundError) as exc:
            raise AuditError(
                f"cannot read the bundled YAML rule catalog {source}"
            ) from exc
        rules.extend(parse_rule_catalog(content, source=source))
    codes = [rule.code for rule in rules]
    if len(codes) != len(set(codes)):
        raise AuditError("rule IDs must be unique across bundled rulesets")
    return tuple(rules)


def _read_project_yaml(root: Path, filename: str, *, kind: str) -> str:
    project_root = root.resolve()
    relative_path = Path(filename)
    windows_path = PureWindowsPath(filename)
    if (
        "\x00" in filename
        or relative_path.is_absolute()
        or windows_path.is_absolute()
        or ".." in relative_path.parts
        or ".." in windows_path.parts
    ):
        raise AuditError(
            f"project {kind} path {filename!r} must be project-relative to {project_root}"
        )
    try:
        path = (project_root / relative_path).resolve()
        path.relative_to(project_root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise AuditError(
            f"project {kind} path {filename!r} must resolve inside {project_root}"
        ) from exc
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise AuditError(f"cannot read project YAML {kind} {filename!r}: {exc}") from exc


def load_project_rule_catalogs(
    root: Path,
    filenames: Sequence[str],
    *,
    existing_codes: Iterable[str] = (),
) -> tuple[Rule, ...]:
    """Load project YAML catalogs without allowing paths outside the project root."""
    codes = set(existing_codes)
    rules: list[Rule] = []
    for filename in filenames:
        content = _read_project_yaml(root, filename, kind="rule catalog")
        for rule in parse_rule_catalog(content, source=filename):
            if rule.code in codes:
                raise AuditError(
                    f"rule ID {rule.code!r} is defined more than once across bundled and project rulesets"
                )
            codes.add(rule.code)
            rules.append(rule)
    return tuple(rules)


def load_project_rule_overrides(
    root: Path,
    filenames: Sequence[str],
    rules: Sequence[Rule],
) -> tuple[Rule, ...]:
    """Load and validate project overrides, returning only replaced immutable rules."""
    rules_by_code = {rule.code: rule for rule in rules}
    if len(rules_by_code) != len(rules):
        raise AuditError("rule IDs must be unique before project overrides are applied")
    seen_codes: set[str] = set()
    overridden: dict[str, Rule] = {}
    for filename in filenames:
        content = _read_project_yaml(root, filename, kind="rule override catalog")
        for override in parse_rule_overrides(content, source=filename):
            if override.code in seen_codes:
                raise AuditError(f"rule {override.code!r} is overridden in more than one project file")
            seen_codes.add(override.code)
            rule = rules_by_code.get(override.code)
            if rule is None:
                raise AuditError(f"rule override {override.code!r} in {filename!r} refers to an unknown rule")
            if override.prompt is not None and rule.engine != "llm":
                raise AuditError(f"prompt can only override an LLM rule ({override.code})")
            if override.description is not None and rule.engine != "deterministic":
                raise AuditError(f"description can only override a deterministic rule ({override.code})")

            detector = rule.detector
            if override.detector is not None:
                if detector is None:
                    raise AuditError(f"detector cannot be overridden for an LLM rule ({override.code})")
                detector_data = detector.model_dump(mode="json")
                detector_data.update(override.detector)
                try:
                    detector = type(detector).model_validate_json(
                        json.dumps(detector_data, ensure_ascii=False)
                    )
                except (TypeError, ValueError, ValidationError) as exc:
                    raise AuditError(
                        f"invalid detector override for {override.code} in {filename!r}: {exc}"
                    ) from exc
            if override.additional_terms is not None and not isinstance(detector, RegexDetector):
                raise AuditError(
                    f"additional-terms can only override a regex rule ({override.code})"
                )

            description = rule.description
            if override.prompt is not None:
                description = override.prompt
            elif override.description is not None:
                description = override.description
            try:
                overridden[override.code] = Rule(
                    code=rule.code,
                    name=override.name if override.name is not None else rule.name,
                    engine=rule.engine,
                    description=description,
                    source=override.source if override.source is not None else rule.source,
                    scope=override.scope if override.scope is not None else rule.scope,
                    examples=override.examples if override.examples is not None else rule.examples,
                    detector=detector,
                    additional_terms=rule.additional_terms + (override.additional_terms or ()),
                )
            except ValidationError as exc:
                raise AuditError(f"invalid rule override {override.code} in {filename!r}: {exc}") from exc

    return tuple(overridden[rule.code] for rule in rules if rule.code in overridden)
