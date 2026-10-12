"""Environment configuration for the Local LLM Verdict Engine."""

import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool = True
    provider: Literal["ollama", "openai_compat"] = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = ""
    temperature: float = 0.0
    seed: int = 42
    num_ctx: int = 8192
    timeout_s: float = 120.0
    max_retries: int = 2
    allow_remote: bool = False


def get_llm_config() -> LLMConfig:
    """Read LLM configuration from environment variables."""
    enabled_str = os.getenv("LLM_ENABLED", "true").lower()
    enabled = enabled_str in ("true", "1", "yes")

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider not in ("ollama", "openai_compat"):
        provider = "ollama"

    base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
    model = os.getenv("LLM_MODEL", "")

    try:
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    except ValueError:
        temperature = 0.0

    try:
        seed = int(os.getenv("LLM_SEED", "42"))
    except ValueError:
        seed = 42

    try:
        num_ctx = int(os.getenv("LLM_NUM_CTX", "8192"))
    except ValueError:
        num_ctx = 8192

    try:
        timeout_s = float(os.getenv("LLM_TIMEOUT_S", "120.0"))
    except ValueError:
        timeout_s = 120.0

    try:
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))
    except ValueError:
        max_retries = 2

    allow_remote_str = os.getenv("LLM_ALLOW_REMOTE", "false").lower()
    allow_remote = allow_remote_str in ("true", "1", "yes")

    return LLMConfig(
        enabled=enabled,
        provider=provider,  # type: ignore
        base_url=base_url,
        model=model,
        temperature=temperature,
        seed=seed,
        num_ctx=num_ctx,
        timeout_s=timeout_s,
        max_retries=max_retries,
        allow_remote=allow_remote,
    )
