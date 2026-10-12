"""Model Registry for TalentScope Multi-Model Edition.

Defines the ModelSpec dataclass and registry of seven models.
Adding an eighth model requires only adding a new spec file under ml/src/epk/models/specs/.
"""

import importlib
import pkgutil
from typing import Dict, List

from .spec_base import ModelSpec
from .score_to_band import ScoreToBand
from . import specs

# Build the registry by loading all spec files in the specs package
REGISTRY: Dict[str, ModelSpec] = {}

for module_info in pkgutil.iter_modules(specs.__path__):
    mod = importlib.import_module(f".specs.{module_info.name}", package="epk.models")
    if hasattr(mod, "SPEC") and isinstance(mod.SPEC, ModelSpec):
        REGISTRY[mod.SPEC.key] = mod.SPEC

MODEL_KEYS: List[str] = list(REGISTRY.keys())


def get_model_spec(key: str) -> ModelSpec:
    """Retrieve ModelSpec by key with whitelist safety."""
    if key not in REGISTRY:
        raise ValueError(f"Unknown model key '{key}'. Supported models: {MODEL_KEYS}")
    return REGISTRY[key]


def list_model_specs() -> List[ModelSpec]:
    """List all registered ModelSpec instances."""
    return list(REGISTRY.values())


__all__ = [
    "ModelSpec",
    "ScoreToBand",
    "REGISTRY",
    "MODEL_KEYS",
    "get_model_spec",
    "list_model_specs",
]
