"""Validated discovery of ``[tool.style-audit]`` settings."""

from dataclasses import dataclass
from pathlib import Path
import math
import tomllib
from typing import Any

from .models import AuditError

DEFAULT_INCLUDE = ("*.md", "*.markdown", "*.rst", "*.txt")
DEFAULT_EXCLUDE = (".git", ".venv", "venv", "build", "dist", "__pycache__")


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


def _string_list(data: dict[str, Any], name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = data.get(name)
    if value is None:
        return default
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise AuditError(f"[tool.style-audit].{name} must be an array of non-empty strings")
    return tuple(item.strip() for item in value)


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
    )


def load_config(start: Path | None = None, config_path: Path | None = None) -> AuditConfig:
    """Load an explicit pyproject or the nearest project pyproject; otherwise defaults."""
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
