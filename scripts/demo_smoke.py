"""Exercise the local review-demo flow against a running TalentScope API."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

SAMPLE_FEATURES = {
    "attendance": 90,
    "experience_years": 5,
    "training_hours": 100,
    "projects_completed": 5,
    "weekly_hours": 40,
    "prev_score": 3.0,
    "department": "Sales",
    "job_level": "Junior",
    "peer_feedback": 3.8,
    "tasks_on_time_pct": 85,
    "certifications": 2,
}


def request_json(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: Any = None,
    token: str | None = None,
    form: dict[str, str] | None = None,
    timeout: float = 180.0,
) -> tuple[int, Any]:
    headers = {"Accept": "application/json"}
    body = None
    if form is not None:
        body = urllib.parse.urlencode(form).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", data=body, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            details = json.loads(raw)
        except json.JSONDecodeError:
            details = raw
        return exc.code, details


def require_ok(name: str, status: int, payload: Any) -> None:
    if status >= 400:
        raise RuntimeError(f"{name} failed with HTTP {status}: {payload}")
    print(f"[PASS] {name}: HTTP {status}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default="admin@test.com")
    parser.add_argument("--password", default="AdminPassword123!")
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()

    status, payload = request_json(args.base_url, "/health")
    require_ok("health", status, payload)
    status, payload = request_json(args.base_url, "/ready")
    require_ok("ready", status, payload)
    if payload.get("status") != "ready":
        raise RuntimeError(f"API is not ready: {payload}")

    status, login = request_json(
        args.base_url,
        "/login",
        method="POST",
        form={"username": args.email, "password": args.password},
    )
    require_ok("login", status, login)
    token = login["access_token"]

    status, models = request_json(args.base_url, "/api/v2/models", token=token)
    require_ok("model catalog", status, models)
    champion = next((item for item in models if item.get("is_champion")), models[0])
    champion_key = champion["key"]
    print(f"       champion: {champion_key}")

    status, predictions = request_json(
        args.base_url,
        "/api/v2/predict/all",
        method="POST",
        payload=SAMPLE_FEATURES,
        token=token,
    )
    require_ok("multi-model prediction", status, predictions)
    print(
        f"       consensus: {predictions['consensus_band']} "
        f"({predictions['agreement_rate']:.0%} agreement)"
    )

    status, explanation = request_json(
        args.base_url,
        "/api/v2/explain",
        method="POST",
        payload={"model_key": champion_key, "features": SAMPLE_FEATURES},
        token=token,
    )
    require_ok("explanation", status, explanation)
    print(f"       explanation type: {explanation['explanation_type']}")

    status, health = request_json(args.base_url, "/api/v2/llm/health", token=token)
    require_ok("LLM health", status, health)
    print(
        f"       LLM status: {health.get('status')} / {health.get('model', 'configured')}"
    )

    if not args.skip_llm:
        status, verdict = request_json(
            args.base_url,
            "/api/v2/llm/verdict",
            method="POST",
            payload={"allow_fallback": True, "profile": "Balanced", "audience": "HR"},
            token=token,
            timeout=180.0,
        )
        require_ok("LLM verdict", status, verdict)
        print(f"       verdict source: {verdict.get('source')}")

    print("Local demo smoke test passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError, urllib.error.URLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
