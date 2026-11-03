"""Strict loading of bundled, editable ruleset catalogs."""

import json
from importlib.resources import files
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from .models import AuditError, Detector, Rule, RuleExample, RuleScope


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
        )


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


_RULESET_CATALOGS = (
    "no-ai-slop.yaml",
    "readability.yaml",
    "technical-english.yaml",
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
