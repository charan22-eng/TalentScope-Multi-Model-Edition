"""Unit tests for multi-model explainability, counterfactuals, and surfaces."""

import numpy as np
import pandas as pd
import pytest

from epk.explain import (
    ACTIONABLE_LEVERS,
    compute_performance_index,
    compute_stability_score,
    explain_model_native,
    find_counterfactuals,
    find_similar_cases,
    fit_pca_projection,
    generate_decision_landscape_grid,
    generate_persona_summaries,
    local_attribution,
)
from epk.features import ALL_FEATURES, NUMERIC_FEATURES


@pytest.fixture
def sample_row():
    return pd.DataFrame([{
        "department": "Engineering",
        "job_level": "Mid",
        "attendance": 90.0,
        "experience_years": 4.0,
        "training_hours": 35.0,
        "projects_completed": 7,
        "weekly_hours": 42.0,
        "prev_score": 72.0,
        "peer_feedback": 3.8,
        "tasks_on_time_pct": 82.0,
        "certifications": 1,
    }])


@pytest.fixture
def sample_dataset():
    rng = np.random.default_rng(42)
    n = 100
    df = pd.DataFrame({
        "department": rng.choice(["Engineering", "Sales", "HR", "Finance"], size=n),
        "job_level": rng.choice(["Junior", "Mid", "Senior", "Lead"], size=n),
        "attendance": rng.uniform(75, 99, size=n),
        "experience_years": rng.uniform(1, 15, size=n),
        "training_hours": rng.uniform(10, 80, size=n),
        "projects_completed": rng.integers(1, 15, size=n),
        "weekly_hours": rng.uniform(35, 50, size=n),
        "prev_score": rng.uniform(40, 95, size=n),
        "peer_feedback": rng.uniform(2, 5, size=n),
        "tasks_on_time_pct": rng.uniform(60, 99, size=n),
        "certifications": rng.integers(0, 4, size=n),
        "performance": rng.choice(["Low", "Medium", "High"], size=n),
    })
    return df


def test_similar_cases_banner_labeling(sample_dataset, sample_row):
    train_labels = sample_dataset["performance"]
    
    # KNN model check (Native)
    knn_res = find_similar_cases(sample_dataset, train_labels, sample_row, model_key="knn", k=5)
    assert knn_res["is_native_reasoning"] is True
    assert "Native" in knn_res["banner"]
    assert len(knn_res["neighbors"]) == 5

    # Non-KNN model check (E3 requirement: Not how this model decided)
    rf_res = find_similar_cases(sample_dataset, train_labels, sample_row, model_key="rf", k=5)
    assert rf_res["is_native_reasoning"] is False
    assert "Not how this model decided" in rf_res["banner"]
    assert len(rf_res["neighbors"]) == 5


def test_stability_score():
    s_high = compute_stability_score(np.array([0.1, 0.2, 0.7]))
    assert s_high == pytest.approx(0.5, abs=0.01)

    s_low = compute_stability_score(np.array([0.05, 0.48, 0.47]))
    assert s_low == pytest.approx(0.01, abs=0.01)


def test_fit_pca_projection(sample_dataset):
    pca_meta = fit_pca_projection(sample_dataset, max_background_samples=50)
    assert len(pca_meta["explained_variance_ratio"]) == 3
    assert len(pca_meta["background_points"]) == 50
    assert "pc1" in pca_meta["background_points"][0]
    assert "pc2" in pca_meta["background_points"][0]
    assert "pc3" in pca_meta["background_points"][0]


def test_persona_summaries():
    summaries = generate_persona_summaries(
        key="rf",
        label="Random Forest",
        pred_band="High",
        proba=[0.05, 0.15, 0.80],
        attribution={"projects_completed": 0.25, "attendance": -0.06},
        counterfactuals=[],
        stability=0.65,
    )
    assert "hr_summary" in summaries
    assert "datascience_summary" in summaries
    assert "Random Forest" in summaries["hr_summary"]
    assert "projects completed" in summaries["hr_summary"]
    assert "Low: 0.050" in summaries["datascience_summary"]
