import os
import sys
import pytest

# Tests must remain deterministic and must never call a developer's local
# Ollama server. The application still uses Ollama in the real demo process.
os.environ["LLM_ENABLED"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True, scope="session")
def setup_database_session():
    """Ensure database schema and standard roles are seeded for all backend tests."""
    from backend.db.migrate import run_migrations

    run_migrations()

