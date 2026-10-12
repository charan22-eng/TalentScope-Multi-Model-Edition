"""SHA-256 caching and persistence for LLM verdicts (F4/VM6.12)."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "v2" / "verdicts"


class VerdictCache:
    """Persistent cache for LLM verdicts keyed by SHA-256 hash of inputs."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_key(
        packet_hash: str,
        prompt_version: str,
        model: str,
        audience: str,
        mode: str,
        profile_name: str,
    ) -> str:
        """Generate SHA-256 cache key from input tuple."""
        key_str = f"{packet_hash}:{prompt_version}:{model}:{audience}:{mode}:{profile_name}"
        return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve verdict record from cache if present."""
        path = self.cache_dir / f"{cache_key}.json"
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def put(
        self,
        cache_key: str,
        packet_hash: str,
        prompt_version: str,
        model: str,
        audience: str,
        mode: str,
        source: str,
        output: Dict[str, Any],
        validation_history: Any,
        attempts: int = 1,
        latency_s: float = 0.0,
    ) -> Dict[str, Any]:
        """Save verdict record to disk cache."""
        record = {
            "cache_key": cache_key,
            "packet_hash": packet_hash,
            "prompt_version": prompt_version,
            "model": model,
            "audience": audience,
            "mode": mode,
            "source": source,
            "attempts": attempts,
            "output": output,
            "validation_history": validation_history,
            "latency_s": round(latency_s, 3),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        path = self.cache_dir / f"{cache_key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        return record
