"""Resolve provider settings for LiteLLM Decisions calls."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

import yaml

from .config import LiteLLMConfig, validate_api_base
from .models import AuditError

_PROVIDER = "azure-maas-judge"
_MODEL = "Decision-1"
_API = "openrouter-decisions"
_OPENROUTER_MODEL_PREFIX = "openrouter/"
_OPENROUTER_API_BASE = "https://openrouter.ai/api"
_OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"


@dataclass(frozen=True)
class DecisionAPISettings:
    api_base: str
    model: str
    custom_llm_provider: str
    api_key: str = field(repr=False)
    timeout: float | None = None


def _registry_paths() -> tuple[Path, ...]:
    home = Path.home()
    return (
        home / ".omp" / "agent" / "models.yml",
        home / ".omp" / "agents" / "models.yml",
    )


def _read_registry(registry_path: Path | None) -> dict[str, Any]:
    if registry_path is None:
        registry_path = next((path for path in _registry_paths() if path.is_file()), None)
        if registry_path is None:
            raise AuditError(
                "azure-maas-judge/Decision-1 requires ~/.omp/agent/models.yml "
                "or ~/.omp/agents/models.yml, unless all LiteLLM settings are configured in pyproject.toml"
            )
    else:
        registry_path = registry_path.expanduser().resolve()
    try:
        with registry_path.open(encoding="utf-8") as file:
            registry: Any = yaml.safe_load(file)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise AuditError("cannot read the configured Azure MaaS model registry") from exc
    if not isinstance(registry, dict):
        raise AuditError("the OMP model registry must contain a YAML table")
    providers = registry.get("providers")
    provider = providers.get(_PROVIDER) if isinstance(providers, dict) else None
    if not isinstance(provider, dict) or provider.get("api") != _API:
        raise AuditError("the OMP registry must define azure-maas-judge with the openrouter-decisions API")
    return provider




def load_decision_api(
    config: LiteLLMConfig = LiteLLMConfig(),
    requested_model: str = _MODEL,
    registry_path: Path | None = None,
) -> DecisionAPISettings:
    """Resolve OpenRouter directly or Azure MaaS through project/OMP settings."""
    if requested_model.startswith(_OPENROUTER_MODEL_PREFIX):
        env_name = config.api_key_env or _OPENROUTER_API_KEY_ENV
        api_key = os.environ.get(env_name)
        if not isinstance(api_key, str) or not api_key.strip():
            raise AuditError(f"OpenRouter Decisions judging requires API key environment variable {env_name!r}")
        if config.custom_llm_provider not in (None, "openrouter"):
            raise AuditError("OpenRouter Decisions models require custom_llm_provider = 'openrouter'")
        model_id = config.decision_model or requested_model
        model = model_id if model_id.startswith(_OPENROUTER_MODEL_PREFIX) else f"{_OPENROUTER_MODEL_PREFIX}{model_id}"
        base_url = config.api_base or os.environ.get("OPENROUTER_API_BASE") or _OPENROUTER_API_BASE
        return DecisionAPISettings(
            api_base=validate_api_base(base_url),
            model=model.strip(),
            custom_llm_provider="openrouter",
            api_key=api_key.strip(),
            timeout=config.timeout,
        )

    api_key = None
    env_name = config.api_key_env
    if env_name:
        api_key = os.environ.get(env_name)
        if not isinstance(api_key, str) or not api_key.strip():
            raise AuditError(f"LiteLLM API key environment variable {env_name!r} is not set")
    else:
        api_key = os.environ.get("AZURE_MAAS_JUDGE_API_KEY") or None

    needs_registry = config.api_base is None or (api_key is None and not env_name)
    provider = _read_registry(registry_path) if needs_registry else {}
    base_url = config.api_base or provider.get("baseUrl")
    model_id = config.decision_model or requested_model
    models = provider.get("models")
    if provider and (
        not isinstance(models, list)
        or not any(isinstance(item, dict) and item.get("id") == model_id for item in models)
    ):
        raise AuditError(f"Decision model {model_id!r} is not listed in the OMP azure-maas-judge provider")
    if not isinstance(model_id, str) or not model_id.strip():
        raise AuditError("LiteLLM decision_model must be a non-empty string")
    if api_key is None:
        api_key = provider.get("apiKey")
    if not isinstance(api_key, str) or not api_key.strip():
        raise AuditError("Azure MaaS Decision judging requires an API key in OMP models.yml or api_key_env")
    custom_llm_provider = config.custom_llm_provider or "openai"
    return DecisionAPISettings(
        api_base=validate_api_base(base_url),
        model=model_id.strip(),
        custom_llm_provider=custom_llm_provider,
        api_key=api_key.strip(),
        timeout=config.timeout,
    )
