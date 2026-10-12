"""Golden-input regression tests across all seven models (G3 / VM7.7 / VM7.2)."""

import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from epk.artifacts import ArtifactIntegrityError, ArtifactLoader, ModelKeyError, default_loader
from epk.models.registry import MODEL_KEYS


@pytest.fixture
def golden_employees():
    """Three canonical test employees representing Low, Medium, and High performance profiles."""
    return pd.DataFrame([
        # Low profile
        {
            "department": "Engineering",
            "job_level": "Junior",
            "attendance": 72.0,
            "experience_years": 1.0,
            "training_hours": 15.0,
            "projects_completed": 1,
            "weekly_hours": 36.0,
            "prev_score": 42.0,
            "peer_feedback": 2.1,
            "tasks_on_time_pct": 58.0,
            "certifications": 0,
        },
        # Medium profile
        {
            "department": "Sales",
            "job_level": "Mid",
            "attendance": 89.0,
            "experience_years": 4.5,
            "training_hours": 45.0,
            "projects_completed": 6,
            "weekly_hours": 42.0,
            "prev_score": 68.0,
            "peer_feedback": 3.6,
            "tasks_on_time_pct": 82.0,
            "certifications": 1,
        },
        # High profile
        {
            "department": "Engineering",
            "job_level": "Lead",
            "attendance": 98.0,
            "experience_years": 10.0,
            "training_hours": 95.0,
            "projects_completed": 14,
            "weekly_hours": 48.0,
            "prev_score": 92.0,
            "peer_feedback": 4.7,
            "tasks_on_time_pct": 96.0,
            "certifications": 4,
        },
    ])


@pytest.mark.parametrize("model_key", sorted(list(MODEL_KEYS)))
def test_golden_prediction_probabilities(model_key, golden_employees):
    """Verify predict_proba and predict for all 7 models."""
    model = default_loader.load_model(model_key)
    preds = model.predict(golden_employees)
    probas = model.predict_proba(golden_employees)

    # Check shapes
    assert len(preds) == 3
    assert probas.shape == (3, 3)

    # Check probabilities sum to 1.0
    row_sums = probas.sum(axis=1)
    np.testing.assert_allclose(row_sums, [1.0, 1.0, 1.0], atol=1e-4)

    # Check probabilities are in [0, 1]
    assert (probas >= 0.0).all() and (probas <= 1.0).all()

    # The high profile employee should have higher High probability than low profile
    assert probas[2, 2] > probas[0, 2]


def test_loader_whitelist_refusal():
    """Verify loader strictly enforces model key whitelist (VM8.9 / G11)."""
    loader = default_loader

    with pytest.raises(ModelKeyError):
        loader.load_model("../evil_path")

    with pytest.raises(ModelKeyError):
        loader.load_model("neural_network")

    with pytest.raises(ModelKeyError):
        loader.load_model("unknown_model")


def test_loader_tamper_detection(tmp_path):
    """Verify loader detects corrupted/tampered files and refuses to load (VM7.2)."""
    # Create a sandbox copy of artifacts
    v2_dir = default_loader.root_dir
    test_dir = tmp_path / "artifacts" / "v2"
    test_dir.mkdir(parents=True)

    # Copy MANIFEST.json and champion.json
    shutil.copy2(v2_dir / "MANIFEST.json", test_dir / "MANIFEST.json")
    shutil.copy2(v2_dir / "champion.json", test_dir / "champion.json")

    # Tamper with champion.json
    with open(test_dir / "champion.json", "a", encoding="utf-8") as f:
        f.write(" ")  # Change byte count / content

    tampered_loader = ArtifactLoader(root_dir=test_dir)
    with pytest.raises(ArtifactIntegrityError, match="Tampered or corrupted artifact"):
        tampered_loader.load_champion()
