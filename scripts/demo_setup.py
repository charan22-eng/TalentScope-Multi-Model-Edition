"""Prepare a repeatable local TalentScope review demo.

The setup is intentionally local-only: it creates a development .env file when
needed, selects an installed Ollama text model, verifies the checked-in V2
artifacts, and seeds the SQLite database. It never downloads models or touches
production configuration.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
OLLAMA_URL = "http://localhost:11434"
PREFERRED_MODELS = (
    "llama3.1:latest",
    "qwen2.5:7b",
    "qwen2.5:3b",
    "llama3.2:latest",
)
MODEL_KEYS = ("boost", "dt", "knn", "linreg", "logreg", "rf", "svm")


def parse_env(lines: Iterable[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_env(path: Path) -> tuple[list[str], dict[str, str]]:
    if not path.exists():
        return [], {}
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines, parse_env(lines)


def discover_ollama_models(base_url: str = OLLAMA_URL) -> list[str]:
    try:
        with urllib.request.urlopen(
            f"{base_url.rstrip('/')}/api/tags", timeout=3
        ) as response:
            payload = response.read().decode("utf-8")
        return [
            str(item["name"])
            for item in __import__("json").loads(payload).get("models", [])
        ]
    except (OSError, ValueError, KeyError, urllib.error.URLError):
        return []


def choose_model(existing: str, available: list[str]) -> str:
    if existing and existing in available:
        return existing
    for candidate in PREFERRED_MODELS:
        if candidate in available:
            return candidate
    return existing or PREFERRED_MODELS[0]


def update_env_file(path: Path, updates: dict[str, str]) -> None:
    lines, existing = read_env(path)
    if not lines:
        lines = [
            "# Generated for local TalentScope review only; do not use in production.",
            "",
        ]

    seen: set[str] = set()
    output: list[str] = []
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        output.append(raw_line)

    missing = [key for key in updates if key not in seen and key not in existing]
    if missing:
        if output and output[-1].strip():
            output.append("")
        output.append("# Local demo defaults")
        output.extend(f"{key}={updates[key]}" for key in missing)

    path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")


def load_into_environment(path: Path) -> dict[str, str]:
    _, values = read_env(path)
    for key, value in values.items():
        os.environ[key] = value
    return values


def check_artifacts() -> list[str]:
    required = [
        ROOT / "artifacts" / "v2" / "MANIFEST.json",
        ROOT / "artifacts" / "v2" / "champion.json",
        ROOT / "artifacts" / "v2" / "comparison" / "leaderboard.json",
    ]
    required.extend(
        ROOT / "artifacts" / "v2" / "models" / key / "model.joblib"
        for key in MODEL_KEYS
    )
    return [str(path.relative_to(ROOT)) for path in required if not path.exists()]


def run_migrations() -> None:
    sys.path.insert(0, str(ROOT))
    from backend.db.migrate import run_migrations

    run_migrations()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-migrate",
        action="store_true",
        help="Prepare .env and artifacts without initializing the database",
    )
    parser.add_argument(
        "--ollama-url",
        default=os.getenv("LLM_BASE_URL", OLLAMA_URL),
        help="Local Ollama URL used for model discovery",
    )
    args = parser.parse_args()

    os.chdir(ROOT)
    available_models = discover_ollama_models(args.ollama_url)
    _, existing = read_env(ENV_PATH)
    selected_model = choose_model(existing.get("LLM_MODEL", ""), available_models)

    jwt_secret = existing.get("JWT_SECRET_KEY", "")
    if len(jwt_secret) < 32 or jwt_secret.startswith("replace-with-"):
        jwt_secret = f"talentscope-local-{secrets.token_urlsafe(32)}"

    updates = {
        "ENVIRONMENT": "development",
        "DATABASE_URL": "sqlite:///./hr_insights.db",
        "POSTGRES_USER": "talentscope",
        "POSTGRES_PASSWORD": "talentscope_dev_pass",
        "POSTGRES_DB": "talentscope",
        "JWT_SECRET_KEY": jwt_secret,
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        "LLM_ENABLED": "true",
        "LLM_PROVIDER": "ollama",
        "LLM_BASE_URL": args.ollama_url.rstrip("/"),
        "OLLAMA_BASE_URL": args.ollama_url.rstrip("/"),
        "DOCKER_OLLAMA_BASE_URL": "http://host.docker.internal:11434",
        "LLM_MODEL": selected_model,
        "LLM_TEMPERATURE": "0.0",
        "LLM_SEED": "42",
        "LLM_NUM_CTX": "8192",
        "LLM_TIMEOUT_S": "120.0",
        "LLM_MAX_RETRIES": "2",
        "LLM_ALLOW_REMOTE": "false",
    }
    update_env_file(ENV_PATH, updates)
    load_into_environment(ENV_PATH)

    missing_artifacts = check_artifacts()
    if missing_artifacts:
        print("ERROR: required V2 artifacts are missing:")
        for item in missing_artifacts:
            print(f"  - {item}")
        return 1

    if not args.skip_migrate:
        run_migrations()

    print("TalentScope local demo setup complete.")
    print(f"  Environment: {ENV_PATH}")
    print("  Database: SQLite at ./hr_insights.db")
    print(
        f"  Ollama: {args.ollama_url} ({'online' if available_models else 'offline'})"
    )
    if available_models:
        print(f"  Installed models: {', '.join(available_models)}")
        print(f"  Selected demo model: {selected_model}")
    else:
        print(
            f"  Selected model: {selected_model} (template fallback remains available)"
        )
    print(
        "  Backend: uv run uvicorn backend.app.main:app --reload "
        "--reload-dir backend --reload-dir ml/src --port 8000"
    )
    print("  Frontend: cd frontend && npm run dev")
    print("  Smoke test: uv run python scripts/demo_smoke.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
