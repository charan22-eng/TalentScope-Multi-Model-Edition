"""Orchestrator for Local LLM verdict generation with validation and template fallback."""

import json
import time
from typing import Any, Dict, List, Literal, Optional

from epk.llm.cache import VerdictCache
from epk.llm.client import LocalLLM
from epk.llm.fallback import generate_template_verdict
from epk.llm.prompts import PROMPT_VERSION, SYSTEM_PROMPT, format_user_prompt
from epk.llm.validator import validate_verdict


def generate_verdict(
    llm: Optional[LocalLLM],
    packet: Dict[str, Any],
    audience: str = "HR",
    profile: Optional[Dict[str, Any]] = None,
    mode: Literal[
        "verdict", "why_not", "second_opinion", "audience_rewrite"
    ] = "verdict",
    focus_model: Optional[str] = None,
    prior_verdict: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    max_retries: int = 2,
    cache: Optional[VerdictCache] = None,
) -> Dict[str, Any]:
    """Generate validated verdict using local LLM, with retry feedback and deterministic fallback."""
    start_time = time.perf_counter()

    if profile is None:
        packet_profile = packet.get("profile")
        profile = (
            packet_profile if isinstance(packet_profile, dict) else {"name": "Balanced"}
        )
    profile_name = profile.get("name", "Custom")

    packet_hash = packet.get("checksum", "unknown_hash")
    model_name = getattr(llm, "model", "none") if llm else "none"

    if cache is None:
        cache = VerdictCache()

    cache_key = cache.compute_key(
        packet_hash=packet_hash,
        prompt_version=PROMPT_VERSION,
        model=model_name,
        audience=audience,
        mode=mode,
        profile_name=profile_name,
    )

    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            cached_output = cached.get("output")
            if isinstance(cached_output, dict) and not validate_verdict(
                cached_output, packet
            ):
                return cached

    # If LLM is not provided or disabled, return template fallback immediately
    if llm is None:
        tpl_output = generate_template_verdict(packet, audience=audience)
        record = cache.put(
            cache_key=cache_key,
            packet_hash=packet_hash,
            prompt_version=PROMPT_VERSION,
            model="template",
            audience=audience,
            mode=mode,
            source="template",
            output=tpl_output,
            validation_history=[
                ["LLM runtime not configured or disabled; template fallback used"]
            ],
            latency_s=time.perf_counter() - start_time,
        )
        return record

    violations: List[str] = []
    history: List[List[str]] = []
    parsed_output: Optional[Dict[str, Any]] = None

    for attempt in range(max_retries + 1):
        user_prompt = format_user_prompt(
            packet=packet,
            audience=audience,
            profile=profile,
            mode=mode,
            focus_model=focus_model,
            prior_verdict=prior_verdict,
            violations=violations if violations else None,
        )

        try:
            raw_json = llm.chat_json(
                system=SYSTEM_PROMPT.format(audience=audience),
                user=user_prompt,
            )
            parsed_output = json.loads(raw_json)
        except Exception as e:
            violations = [f"{type(e).__name__}: {str(e)[:120]}"]
            history.append(violations)
            continue

        if not isinstance(parsed_output, dict):
            violations = ["LLM output was not a JSON object"]
            history.append(violations)
            continue
        violations = validate_verdict(parsed_output, packet)
        history.append(violations)

        if not violations:
            record = cache.put(
                cache_key=cache_key,
                packet_hash=packet_hash,
                prompt_version=PROMPT_VERSION,
                model=model_name,
                audience=audience,
                mode=mode,
                source="llm",
                output=parsed_output,
                validation_history=history,
                attempts=attempt + 1,
                latency_s=time.perf_counter() - start_time,
            )
            return record

    # Exceeded max retries -> use deterministic fallback
    tpl_output = generate_template_verdict(packet, audience=audience)
    record = cache.put(
        cache_key=cache_key,
        packet_hash=packet_hash,
        prompt_version=PROMPT_VERSION,
        model=model_name,
        audience=audience,
        mode=mode,
        source="template",
        output=tpl_output,
        validation_history=history,
        attempts=max_retries + 1,
        latency_s=time.perf_counter() - start_time,
    )
    return record
