"""Artifact v2 Loader with model whitelist, lazy loading, and SHA-256 integrity verification (G2 / VM7.2)."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional, Set

import joblib

from epk.models.registry import MODEL_KEYS

ARTIFACTS_V2_DIR = Path(__file__).resolve().parent.parent.parent.parent / "artifacts" / "v2"


class ArtifactIntegrityError(Exception):
    """Raised when an artifact file fails SHA-256 checksum verification."""
    pass


class ModelKeyError(ValueError):
    """Raised when an unrecognized model key or potential path traversal is requested."""
    pass


class ArtifactLoader:
    """Secure, lazy, integrity-verified loader for TalentScope v2 artifacts."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or ARTIFACTS_V2_DIR
        self._manifest: Optional[Dict[str, Any]] = None
        self._loaded_models: Dict[str, Any] = {}
        self._loaded_metadata: Dict[str, Any] = {}
        self._loaded_comparisons: Dict[str, Dict[str, Any]] = {}
        self._loaded_champion: Optional[Dict[str, Any]] = None
        self._loaded_dataset_meta: Optional[Dict[str, Any]] = None

    def reset_cache(self) -> None:
        """Clear cached in-memory manifests, models, and JSON payloads."""
        self._manifest = None
        self._loaded_models.clear()
        self._loaded_metadata.clear()
        self._loaded_comparisons.clear()
        self._loaded_champion = None
        self._loaded_dataset_meta = None

    @property
    def manifest(self) -> Dict[str, Any]:
        """Lazy load and cache MANIFEST.json."""
        if self._manifest is None:
            m_path = self.root_dir / "MANIFEST.json"
            if not m_path.exists():
                raise FileNotFoundError(f"Artifact manifest not found at: {m_path}")
            with open(m_path, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)
        return self._manifest

    def verify_file(self, rel_path: str) -> None:
        """Verify that the file exists and its SHA-256 matches MANIFEST.json."""
        full_path = self.root_dir / rel_path
        if not full_path.is_file():
            raise FileNotFoundError(f"Artifact file not found: {rel_path}")

        files_map = self.manifest.get("files", {})
        if rel_path not in files_map:
            raise ArtifactIntegrityError(f"File '{rel_path}' is not registered in MANIFEST.json")

        expected_hash = files_map[rel_path]["sha256"]

        h = hashlib.sha256()
        with open(full_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_hash = h.hexdigest()

        if actual_hash != expected_hash:
            # Allow text files (e.g. .json, .csv) to match if discrepancy is CRLF vs LF line endings
            if full_path.suffix in [".json", ".csv", ".txt", ".md"]:
                content = full_path.read_bytes()
                norm_lf = hashlib.sha256(content.replace(b"\r\n", b"\n")).hexdigest()
                norm_crlf = hashlib.sha256(content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest()
                if expected_hash in (norm_lf, norm_crlf):
                    return
            raise ArtifactIntegrityError(
                f"Tampered or corrupted artifact: '{rel_path}' expected SHA-256 {expected_hash}, got {actual_hash}"
            )

    def load_model(self, model_key: str, force_reload: bool = False) -> Any:
        """Load fitted model pipeline with key whitelist and hash verification."""
        if model_key not in MODEL_KEYS:
            raise ModelKeyError(
                f"Invalid model key '{model_key}'. Allowed keys: {sorted(list(MODEL_KEYS))}"
            )

        if not force_reload and model_key in self._loaded_models:
            return self._loaded_models[model_key]

        rel_path = f"models/{model_key}/model.joblib"
        self.verify_file(rel_path)

        model_path = self.root_dir / rel_path
        model_obj = joblib.load(model_path)
        self._loaded_models[model_key] = model_obj
        return model_obj

    def load_model_metadata(self, model_key: str) -> Dict[str, Any]:
        """Load model metadata JSON with key validation."""
        if model_key not in MODEL_KEYS:
            raise ModelKeyError(f"Invalid model key '{model_key}'. Allowed keys: {sorted(list(MODEL_KEYS))}")

        if model_key in self._loaded_metadata:
            return self._loaded_metadata[model_key]

        rel_path = f"models/{model_key}/metadata.json"
        self.verify_file(rel_path)

        with open(self.root_dir / rel_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._loaded_metadata[model_key] = data
        return data

    def load_comparison_json(self, name: str) -> Dict[str, Any]:
        """Load comparison JSON (leaderboard, pairwise, mcda, etc.) with hash verification."""
        if not hasattr(self, "_loaded_comparisons"):
            self._loaded_comparisons = {}
        if name in self._loaded_comparisons:
            return self._loaded_comparisons[name]

        rel_path = f"comparison/{name}.json" if not name.endswith(".json") else f"comparison/{name}"
        self.verify_file(rel_path)
        with open(self.root_dir / rel_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._loaded_comparisons[name] = data
        return data

    def load_champion(self) -> Dict[str, Any]:
        """Load champion.json with hash verification."""
        if not hasattr(self, "_loaded_champion") or self._loaded_champion is None:
            self.verify_file("champion.json")
            with open(self.root_dir / "champion.json", "r", encoding="utf-8") as f:
                self._loaded_champion = json.load(f)
        return self._loaded_champion

    def load_dataset_meta(self) -> Dict[str, Any]:
        """Load dataset_meta.json with hash verification."""
        if not hasattr(self, "_loaded_dataset_meta") or self._loaded_dataset_meta is None:
            self.verify_file("dataset_meta.json")
            with open(self.root_dir / "dataset_meta.json", "r", encoding="utf-8") as f:
                self._loaded_dataset_meta = json.load(f)
        return self._loaded_dataset_meta


# Global default instance
default_loader = ArtifactLoader()
