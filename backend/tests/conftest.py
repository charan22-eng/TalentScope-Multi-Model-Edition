import os
import sys

# Tests must remain deterministic and must never call a developer's local
# Ollama server. The application still uses Ollama in the real demo process.
os.environ["LLM_ENABLED"] = "false"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
