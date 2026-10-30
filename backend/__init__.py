"""TalentScope backend package bootstrap."""

from .runtime_env import load_local_env

load_local_env()

__all__ = ["load_local_env"]
