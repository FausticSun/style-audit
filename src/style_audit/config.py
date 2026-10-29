"""Validated discovery of ``[tool.style-audit]`` settings."""

from dataclasses import dataclass
from pathlib import Path
import math
import tomllib
from typing import Any
from urllib.parse import urlsplit

from .models import AuditError

DEFAULT_INCLUDE = ("*.md", "*.markdown", "*.rst", "*.txt", "*.py", "*.pyi", "*.feature")
DEFAULT_EXCLUDE = (".git", ".venv", "venv", "build", "dist", "site", "__pycache__")


@dataclass(frozen=True)
class LiteLLMConfig:
    """Supported LiteLLM transport settings from ``pyproject.toml``."""

    api_base: str | None = None
    api_key_env: str | None = None
    custom_llm_provider: str | None = None
    decision_model: str | None = None
    timeout: float | None = None
    temperature: float = 0.0


@dataclass(frozen=True)
class AuditConfig:
    root: Path
    select: tuple[str, ...] = ()
    ignore: tuple[str, ...] = ()
    include: tuple[str, ...] = DEFAULT_INCLUDE
    exclude: tuple[str, ...] = DEFAULT_EXCLUDE
    output: str = "text"
    llm_enabled: bool = False
    llm_model: str | None = None
    llm_threshold: float = 0.8
    llm_litellm: LiteLLMConfig = LiteLLMConfig()
    per_file_select: tuple[tuple[str, tuple[str, ...]], ...] = ()
    nas_allowed_words: tuple[str, ...] = ()
    nas_disallowed_words: tuple[str, ...] = ()
    ste_allowed_words: tuple[str, ...] = ()
    ste_disallowed_words: tuple[str, ...] = ()


def _string_list(data: dict[str, Any], name: str, default: tuple[str, ...], *, section: str = "tool.style-audit") -> tuple[str, ...]:
    value = data.get(name)
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise AuditError(f"[{section}].{name} must be an array of non-empty strings")
    return tuple(item.strip() for item in value)


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


def _parse_litellm_config(llm: dict[str, Any]) -> LiteLLMConfig:
    data = llm.get("litellm", {})
    if not isinstance(data, dict):
        raise AuditError("[tool.style-audit.llm.litellm] must be a table")
    allowed = {
        "api_base", "api_key_env", "custom_llm_provider", "decision_model", "timeout", "temperature",
    }
    unknown = set(data) - allowed
    if unknown:
        raise AuditError(f"[tool.style-audit.llm.litellm] has unsupported setting(s): {', '.join(sorted(unknown))}")
    strings: dict[str, str | None] = {}
    for name in ("api_base", "api_key_env", "custom_llm_provider", "decision_model"):
        value = data.get(name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise AuditError(f"[tool.style-audit.llm.litellm].{name} must be a non-empty string")
        strings[name] = value.strip() if value else None
    if strings["api_base"] is not None:
        strings["api_base"] = validate_api_base(strings["api_base"])
    timeout = data.get("timeout")
    if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0):
        raise AuditError("[tool.style-audit.llm.litellm].timeout must be a finite positive number")
    temperature = data.get("temperature", 0.0)
    if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature) or not 0 <= temperature <= 2:
        raise AuditError("[tool.style-audit.llm.litellm].temperature must be a finite number between 0 and 2")
    return LiteLLMConfig(
        **strings,
        timeout=float(timeout) if timeout is not None else None,
        temperature=float(temperature),
    )


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
    llm = data.get("llm", {})
    if not isinstance(llm, dict):
        raise AuditError("[tool.style-audit.llm] must be a table")
    llm_litellm = _parse_litellm_config(llm)
    ste = data.get("ste", {})
    if not isinstance(ste, dict):
        raise AuditError("[tool.style-audit.ste] must be a table")
    no_ai_slop = data.get("no-ai-slop", {})
    if not isinstance(no_ai_slop, dict):
        raise AuditError("[tool.style-audit.no-ai-slop] must be a table")
    enabled = llm.get("enabled", False)
    model = llm.get("model")
    if not isinstance(enabled, bool):
        raise AuditError("[tool.style-audit.llm].enabled must be a boolean")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise AuditError("[tool.style-audit.llm].model must be a non-empty string")
    if enabled and model is None:
        raise AuditError("[tool.style-audit.llm].model is required when LLM judging is enabled")
    threshold = llm.get("threshold", 0.8)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise AuditError("[tool.style-audit.llm].threshold must be a finite number between 0 and 1")
    output = data.get("output", "text")
    if not isinstance(output, str) or output not in {"text", "json"}:
        raise AuditError("[tool.style-audit].output must be 'text' or 'json'")
    per_file = data.get("per-file-select", {})
    if not isinstance(per_file, dict):
        raise AuditError("[tool.style-audit.per-file-select] must be a table")
    if any(not pattern.strip() for pattern in per_file):
        raise AuditError("[tool.style-audit.per-file-select] requires non-empty file patterns")
    return AuditConfig(
        root=path.parent.resolve(),
        select=_string_list(data, "select", ()),
        ignore=_string_list(data, "ignore", ()),
        include=_string_list(data, "include", DEFAULT_INCLUDE),
        exclude=_string_list(data, "exclude", DEFAULT_EXCLUDE),
        output=output,
        llm_enabled=enabled,
        llm_model=model.strip() if model else None,
        llm_threshold=float(threshold),
        llm_litellm=llm_litellm,
        per_file_select=tuple(
            (pattern, _string_list(per_file, pattern, (), section="tool.style-audit.per-file-select"))
            for pattern in per_file
        ),
        nas_allowed_words=_string_list(no_ai_slop, "allowed-words", (), section="tool.style-audit.no-ai-slop"),
        nas_disallowed_words=_string_list(no_ai_slop, "disallowed-words", (), section="tool.style-audit.no-ai-slop"),
        ste_allowed_words=_string_list(ste, "allowed-words", (), section="tool.style-audit.ste"),
        ste_disallowed_words=_string_list(ste, "disallowed-words", (), section="tool.style-audit.ste"),
    )


def load_config(start: Path | None = None, config_path: Path | None = None) -> AuditConfig:
    """Load an explicit pyproject or the nearest project pyproject. Use defaults if none exists."""
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
