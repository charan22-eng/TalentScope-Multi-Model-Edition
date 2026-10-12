"""Local LLM HTTP client with SSRF guard and model discovery."""

import ipaddress
import json
import socket
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from epk.llm.schema import VERDICT_SCHEMA


def assert_local(base_url: str, allow_remote: bool = False) -> None:
    """Refuse non-local LLM hosts unless explicitly allowed (SSRF and data-egress guard G10)."""
    if allow_remote:
        return

    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    if not host:
        raise ValueError(f"Invalid URL without hostname: {base_url!r}")

    # Allow literal 'localhost'
    if host.lower() == "localhost":
        return

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise ValueError(f"Cannot resolve LLM host {host!r}") from e

    for _fam, _t, _p, _c, sockaddr in infos:
        ip = ipaddress.ip_address(sockaddr[0])
        if not (ip.is_loopback or ip.is_private):
            raise ValueError(f"LLM host {host!r} resolves to a public/non-local address {ip}; refusing under G10 guard")


class LocalLLM:
    """Client for local LLMs via Ollama (/api/chat) or OpenAI-compatible (/v1/chat/completions).

    base_url has NO trailing /v1 (the client appends proper endpoints).
    """

    def __init__(
        self,
        provider: str = "ollama",
        base_url: str = "http://localhost:11434",
        model: str = "",
        timeout: float = 120.0,
        temperature: float = 0.0,
        seed: int = 42,
        num_ctx: int = 8192,
        allow_remote: bool = False,
    ):
        assert_local(base_url, allow_remote)
        self.provider = provider.lower()
        self.base = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.seed = seed
        self.num_ctx = num_ctx
        self.allow_remote = allow_remote

    def list_models(self) -> List[str]:
        """Discover available models from the local server."""
        if self.provider == "ollama":
            try:
                r = httpx.get(f"{self.base}/api/tags", timeout=10.0)
                r.raise_for_status()
                return [m["name"] for m in r.json().get("models", [])]
            except Exception as e:
                return []
        else:
            try:
                r = httpx.get(f"{self.base}/v1/models", timeout=10.0)
                r.raise_for_status()
                return [m["id"] for m in r.json().get("data", [])]
            except Exception as e:
                return []

    def chat_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 900,
    ) -> str:
        """Call LLM and return structured JSON response string."""
        if schema is None:
            schema = VERDICT_SCHEMA

        msgs = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        if self.provider == "ollama":
            body = {
                "model": self.model,
                "messages": msgs,
                "stream": False,
                "format": schema,
                "options": {
                    "temperature": self.temperature,
                    "seed": self.seed,
                    "num_ctx": self.num_ctx,
                    "num_predict": max_tokens,
                },
            }
            r = httpx.post(f"{self.base}/api/chat", json=body, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["message"]["content"]
        else:
            # OpenAI-compatible
            body = {
                "model": self.model,
                "messages": msgs,
                "temperature": self.temperature,
                "seed": self.seed,
                "max_tokens": max_tokens,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "verdict", "schema": schema, "strict": True},
                },
            }
            r = httpx.post(f"{self.base}/v1/chat/completions", json=body, timeout=self.timeout)
            if r.status_code == 400:
                # If json_schema is unsupported, fallback to json_object mode
                body["response_format"] = {"type": "json_object"}
                r = httpx.post(f"{self.base}/v1/chat/completions", json=body, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]


class FakeLLM:
    """Deterministic mock LLM for testing, evaluation harness, and CI offline environments."""

    def __init__(self, canned_response_or_func: Any = None, model: str = "fake-model"):
        self.canned = canned_response_or_func
        self.model = model
        self.call_count = 0
        self.last_prompt = ""

    def list_models(self) -> List[str]:
        return ["fake-llama3-8b", "fake-mistral-7b"]

    def chat_json(
        self,
        system: str,
        user: str,
        schema: Optional[Dict[str, Any]] = None,
        max_tokens: int = 900,
    ) -> str:
        self.call_count += 1
        self.last_prompt = user

        if callable(self.canned):
            res = self.canned(system, user, self.call_count)
            return json.dumps(res) if isinstance(res, dict) else str(res)

        if isinstance(self.canned, dict):
            return json.dumps(self.canned)
        elif isinstance(self.canned, str):
            return self.canned

        # Default minimal valid response
        return json.dumps({
            "headline": "Random Forest is recommended under the Balanced profile",
            "recommendation": {
                "model_key": "rf",
                "confidence": "marginal",
                "agreement": "agree",
            },
            "claims": [
                {"text": "Random Forest achieved strong performance.", "fact_ids": ["F1"]},
                {"text": "Model calibration was evaluated.", "fact_ids": ["F2"]},
            ],
            "tradeoffs": [
                {"text": "SVM has higher raw accuracy but Random forest offers better calibration.", "fact_ids": ["F1", "F2"]},
            ],
            "caveats": [
                {"text": "The data is synthetic (12,000 rows) and rankings depend on how it was generated.", "fact_ids": ["F90"]},
            ],
        })
