"""Load the repository-local .env before modules read process settings."""

from __future__ import annotations

import os
from pathlib import Path


def load_local_env() -> None:
    """Load simple KEY=VALUE entries from the repository .env if present.

    Environment variables already supplied by the shell always win. This small
    loader keeps the local demo self-contained without requiring a dotenv CLI or
    relying on import order between database, security, and application modules.
    """

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


# Importing this module is the bootstrap hook used by the API and migration
# entrypoints, so settings are available before database/security modules load.
load_local_env()
