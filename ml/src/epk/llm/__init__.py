"""Local LLM Verdict Engine for TalentScope Multi-Model Edition."""

from epk.llm.config import LLMConfig, get_llm_config
from epk.llm.client import LocalLLM, assert_local
from epk.llm.schema import VERDICT_SCHEMA
from epk.llm.prompts import SYSTEM_PROMPT, PROMPT_VERSION, format_user_prompt
from epk.llm.validator import validate_verdict
from epk.llm.fallback import generate_template_verdict
from epk.llm.cache import VerdictCache
from epk.llm.orchestrator import generate_verdict

__all__ = [
    "LLMConfig",
    "get_llm_config",
    "LocalLLM",
    "assert_local",
    "VERDICT_SCHEMA",
    "SYSTEM_PROMPT",
    "PROMPT_VERSION",
    "format_user_prompt",
    "validate_verdict",
    "generate_template_verdict",
    "VerdictCache",
    "generate_verdict",
]
