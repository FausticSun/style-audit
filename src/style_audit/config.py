"""Validated discovery of ``[tool.style-audit]`` settings."""

import math
import tomllib
from pathlib import Path
from typing import ClassVar, Literal
from urllib.parse import urlsplit

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from .models import AuditError, Rule
from .rule_catalog import (
    load_project_rule_catalogs,
    load_project_rule_overrides,
    load_rule_catalog,
)

DEFAULT_INCLUDE = ("*.md", "*.markdown", "*.rst", "*.txt", "*.py", "*.pyi", "*.feature")
DEFAULT_EXCLUDE = (
    ".git", ".venv", "venv", "build", "dist", "site", "__pycache__", "AGENTS.md", "SKILL.md",
)

DEFAULT_SELECT = ("NAS", "RDL")

DEFAULT_LLM_MODEL = "openrouter/openrouter/free"


def validate_api_base(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuditError("LiteLLM api_base must be a non-empty URL")
    value = value.strip()
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise AuditError("LiteLLM api_base must be an absolute URL") from exc
    local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not local_http:
        raise AuditError("LiteLLM api_base must use HTTPS (HTTP is allowed only for localhost)")
    if not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise AuditError("LiteLLM api_base must be an absolute URL without embedded credentials or query data")
    return value.rstrip("/")


class LiteLLMConfig(BaseModel):
    """Supported LiteLLM transport settings from ``pyproject.toml``."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    api_base: str | None = None
    api_key_env: str | None = None
    custom_llm_provider: str | None = None
    timeout: float | None = None
    temperature: float = 0.0

    @model_validator(mode="before")
    @classmethod
    def reject_unsupported_settings(cls, value: object) -> object:
        if not isinstance(value, dict):
            raise ValueError("[tool.style-audit.llm.litellm] must be a table")
        unknown = set(value) - set(cls.model_fields)
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise ValueError(f"[tool.style-audit.llm.litellm] has unsupported setting(s): {names}")
        return value

    @field_validator("api_base", mode="before")
    @classmethod
    def validate_api_base_value(cls, value: object) -> str | None:
        if value is None:
            return None
        try:
            return validate_api_base(value)
        except AuditError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("api_key_env", "custom_llm_provider", mode="before")
    @classmethod
    def validate_optional_strings(cls, value: object, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"[tool.style-audit.llm.litellm].{info.field_name} must be a non-empty string")
        return value.strip()

    @field_validator("timeout", mode="before")
    @classmethod
    def validate_timeout(cls, value: object) -> float | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("[tool.style-audit.llm.litellm].timeout must be a finite positive number")
        try:
            number = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError("[tool.style-audit.llm.litellm].timeout must be a finite positive number") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError("[tool.style-audit.llm.litellm].timeout must be a finite positive number")
        return number

    @field_validator("temperature", mode="before")
    @classmethod
    def validate_temperature(cls, value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("[tool.style-audit.llm.litellm].temperature must be a finite number between 0 and 2")
        try:
            number = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError("[tool.style-audit.llm.litellm].temperature must be a finite number between 0 and 2") from exc
        if not math.isfinite(number) or not 0 <= number <= 2:
            raise ValueError("[tool.style-audit.llm.litellm].temperature must be a finite number between 0 and 2")
        return number


class AuditConfig(BaseModel):
    """Fully normalized project settings used by the CLI and analyzers."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    root: Path
    select: tuple[str, ...] = ()
    ignore: tuple[str, ...] = ()
    include: tuple[str, ...] = DEFAULT_INCLUDE
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE
    output: Literal["text", "json"] = "text"
    llm_enabled: bool | None = None
    llm_model: str | None = None
    llm_litellm: LiteLLMConfig = Field(default_factory=LiteLLMConfig)
    llm_api: Literal["completion", "decisions"] = "completion"
    llm_threshold: float = 0.82
    per_file_select: tuple[tuple[str, tuple[str, ...]], ...] = ()
    project_rules: tuple[Rule, ...] = ()
    overridden_rules: tuple[Rule, ...] = ()
    nas_allowed_words: tuple[str, ...] = ()
    nas_disallowed_words: tuple[str, ...] = ()
    ste_allowed_words: tuple[str, ...] = ()
    ste_disallowed_words: tuple[str, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def default_completion_model(cls, values: object) -> object:
        if not isinstance(values, dict):
            return values
        normalized = dict(values)
        if (
            normalized.get("llm_api", "completion") == "completion"
            and normalized.get("llm_model") is None
        ):
            normalized["llm_model"] = DEFAULT_LLM_MODEL
        return normalized


def _string_list(value: object, name: str, default: tuple[str, ...], *, section: str) -> tuple[str, ...]:
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f"[{section}].{name} must be an array of non-empty strings")
    return tuple(item.strip() for item in value)


class _WordSettings(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    _section: ClassVar[str]

    allowed_words: tuple[str, ...] = Field(default=(), alias="allowed-words")
    disallowed_words: tuple[str, ...] = Field(default=(), alias="disallowed-words")

    @field_validator("allowed_words", "disallowed_words", mode="before")
    @classmethod
    def validate_words(cls, value: object, info: ValidationInfo) -> tuple[str, ...]:
        name = info.field_name.replace("_", "-")
        return _string_list(value, name, (), section=cls._section)


class _NASWordSettings(_WordSettings):
    _section: ClassVar[str] = "tool.style-audit.no-ai-slop"


class _STEWordSettings(_WordSettings):
    _section: ClassVar[str] = "tool.style-audit.ste"


class _LLMSettings(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    enabled: bool | None = None
    model: str | None = None
    litellm: LiteLLMConfig = Field(default_factory=LiteLLMConfig)
    api: Literal["completion", "decisions"] = "completion"
    threshold: float = 0.82

    @field_validator("enabled", mode="before")
    @classmethod
    def validate_enabled(cls, value: object) -> bool | None:
        if value is None:
            return None
        if not isinstance(value, bool):
            raise ValueError("[tool.style-audit.llm].enabled must be a boolean")
        return value

    @field_validator("model", mode="before")
    @classmethod
    def validate_model(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError("[tool.style-audit.llm].model must be a non-empty string")
        return value.strip()

    @field_validator("threshold", mode="before")
    @classmethod
    def validate_threshold(cls, value: object) -> float:
        message = "[tool.style-audit.llm].threshold must be a finite number from 0 to 1"
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(message)
        try:
            number = float(value)
        except (OverflowError, ValueError) as exc:
            raise ValueError(message) from exc
        if not math.isfinite(number) or not 0 <= number <= 1:
            raise ValueError(message)
        return number


    @field_validator("litellm", mode="before")
    @classmethod
    def validate_litellm_table(cls, value: object) -> object:
        if isinstance(value, (dict, LiteLLMConfig)):
            return value
        raise ValueError("[tool.style-audit.llm.litellm] must be a table")

    @model_validator(mode="after")
    def validate_api_settings(self) -> "_LLMSettings":
        if self.api == "decisions" and self.litellm.temperature != 0:
            raise ValueError("[tool.style-audit.llm.litellm].temperature applies only to completion judging")
        return self


class _ProjectSettings(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    select: tuple[str, ...] = ()
    ignore: tuple[str, ...] = ()
    include: tuple[str, ...] = DEFAULT_INCLUDE
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE
    output: Literal["text", "json"] = "text"
    llm: _LLMSettings = Field(default_factory=_LLMSettings)
    per_file_select: tuple[tuple[str, tuple[str, ...]], ...] = Field(default=(), alias="per-file-select")
    rule_catalogs: tuple[str, ...] = Field(default=(), alias="rule-catalogs")
    rule_overrides: tuple[str, ...] = Field(default=(), alias="rule-overrides")
    no_ai_slop: _NASWordSettings = Field(default_factory=_NASWordSettings, alias="no-ai-slop")
    ste: _STEWordSettings = Field(default_factory=_STEWordSettings)

    @field_validator("select", "ignore", "include", "exclude", mode="before")
    @classmethod
    def validate_rule_lists(cls, value: object, info: ValidationInfo) -> tuple[str, ...]:
        defaults = {"select": (), "ignore": (), "include": DEFAULT_INCLUDE, "exclude": DEFAULT_EXCLUDE}
        return _string_list(value, info.field_name, defaults[info.field_name], section="tool.style-audit")

    @field_validator("rule_catalogs", mode="before")
    @classmethod
    def validate_rule_catalogs(cls, value: object) -> tuple[str, ...]:
        return _string_list(value, "rule-catalogs", (), section="tool.style-audit")

    @field_validator("rule_overrides", mode="before")
    @classmethod
    def validate_rule_overrides(cls, value: object) -> tuple[str, ...]:
        return _string_list(value, "rule-overrides", (), section="tool.style-audit")

    @field_validator("output", mode="before")
    @classmethod
    def validate_output(cls, value: object) -> Literal["text", "json"]:
        if not isinstance(value, str) or value not in {"text", "json"}:
            raise ValueError("[tool.style-audit].output must be 'text' or 'json'")
        return value

    @field_validator("llm", "no_ai_slop", "ste", mode="before")
    @classmethod
    def validate_tables(cls, value: object, info: ValidationInfo) -> object:
        if isinstance(value, dict):
            return value
        section = {
            "llm": "tool.style-audit.llm",
            "no_ai_slop": "tool.style-audit.no-ai-slop",
            "ste": "tool.style-audit.ste",
        }[info.field_name]
        raise ValueError(f"[{section}] must be a table")

    @field_validator("per_file_select", mode="before")
    @classmethod
    def validate_per_file_select(cls, value: object) -> tuple[tuple[str, tuple[str, ...]], ...]:
        if not isinstance(value, dict):
            raise ValueError("[tool.style-audit.per-file-select] must be a table")
        selections: list[tuple[str, tuple[str, ...]]] = []
        for pattern, rules in value.items():
            if not isinstance(pattern, str) or not pattern.strip():
                raise ValueError("[tool.style-audit.per-file-select] requires non-empty file patterns")
            selections.append((pattern, _string_list(rules, pattern, (), section="tool.style-audit.per-file-select")))
        return tuple(selections)


def _validation_message(error: ValidationError) -> str:
    messages: list[str] = []
    for item in error.errors(include_url=False, include_input=False):
        cause = (item.get("ctx") or {}).get("error")
        if isinstance(cause, ValueError):
            messages.append(str(cause))
            continue
        location = ".".join(str(part) for part in item["loc"])
        messages.append(f"{location}: {item['msg']}")
    return "; ".join(messages) or "invalid style-audit configuration"


def _parse_config(path: Path) -> AuditConfig:
    try:
        with path.open("rb") as file:
            document = tomllib.load(file)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise AuditError(f"cannot load configuration {path}: {exc}") from exc
    tools = document.get("tool", {})
    if not isinstance(tools, dict):
        raise AuditError(f"[tool] in {path} must be a table")
    data = tools.get("style-audit", {})
    if not isinstance(data, dict):
        raise AuditError(f"[tool.style-audit] in {path} must be a table")
    try:
        settings = _ProjectSettings.model_validate(data)
        project_rules = ()
        overridden_rules = ()
        bundled_rules = load_rule_catalog() if settings.rule_catalogs or settings.rule_overrides else ()
        if settings.rule_catalogs:
            project_rules = load_project_rule_catalogs(
                path.parent,
                settings.rule_catalogs,
                existing_codes=(rule.code for rule in bundled_rules),
            )
        if settings.rule_overrides:
            overridden_rules = load_project_rule_overrides(
                path.parent,
                settings.rule_overrides,
                (*bundled_rules, *project_rules),
            )
        return AuditConfig(
            root=path.parent.resolve(),
            select=settings.select,
            ignore=settings.ignore,
            include=settings.include,
            exclude=settings.exclude,
            output=settings.output,
            llm_enabled=settings.llm.enabled,
            llm_model=settings.llm.model,
            llm_litellm=settings.llm.litellm,
            llm_api=settings.llm.api,
            llm_threshold=settings.llm.threshold,
            per_file_select=settings.per_file_select,
            project_rules=project_rules,
            overridden_rules=overridden_rules,
            nas_allowed_words=settings.no_ai_slop.allowed_words,
            nas_disallowed_words=settings.no_ai_slop.disallowed_words,
            ste_allowed_words=settings.ste.allowed_words,
            ste_disallowed_words=settings.ste.disallowed_words,
        )
    except ValidationError as exc:
        raise AuditError(_validation_message(exc)) from exc


def load_config(start: Path | None = None, config_path: Path | None = None) -> AuditConfig:
    """Load an explicit project or the nearest project ``pyproject.toml``."""
    if config_path is not None:
        path = config_path.expanduser().resolve()
        if path.is_dir():
            path /= "pyproject.toml"
        return _parse_config(path)
    current = (start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent
    for directory in (current, *current.parents):
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return _parse_config(candidate)
    return AuditConfig(root=current)
