"""Unit tests for MCDA ranking, decision strength, and evidence packet builder."""

import pytest
import numpy as np
import pandas as pd

from epk.mcda import (
    PROFILES,
    compute_decision_strength,
    mcda_rank,
    minmax_normalise,
    rank_probability,
    run_mcda_pipeline,
)
from epk.evidence import (
    scan_packet_for_forbidden_keys,
    select_facts,
)


def test_minmax_normalise():
    df = pd.DataFrame({
        "a": [10, 20, 30],
        "b": [100, 200, 300],
    })
    hib = {"a": True, "b": False}
    norm = minmax_normalise(df, hib)

    np.testing.assert_allclose(norm["a"], [0.0, 0.5, 1.0])
    np.testing.assert_allclose(norm["b"], [1.0, 0.5, 0.0])


def test_mcda_ranking_synthetic():
    df = pd.DataFrame({
        "macro_f1": [0.85, 0.80, 0.70],
        "qwk": [0.85, 0.80, 0.70],
        "calibration": [0.95, 0.90, 0.85],
        "robustness": [0.90, 0.85, 0.80],
        "fairness": [0.90, 0.85, 0.80],
        "stability": [0.95, 0.90, 0.85],
        "latency": [100.0, 95.0, 1.0],
        "train_cost": [300.0, 290.0, 1.0],
        "explainability": [0.3, 0.6, 1.0],
    }, index=["svm", "rf", "dt"])

    res = mcda_rank(df, PROFILES["Accuracy-first"])
    assert res.loc["svm", "rank"] == 1

    res_speed = mcda_rank(df, PROFILES["Speed-first"])
    assert res_speed.loc["dt", "rank"] == 1


def test_rank_probability_dirichlet():
    df = pd.DataFrame({
        "macro_f1": [0.85, 0.80, 0.70],
        "qwk": [0.85, 0.80, 0.70],
        "calibration": [0.95, 0.90, 0.85],
        "robustness": [0.90, 0.85, 0.80],
        "fairness": [0.90, 0.85, 0.80],
        "stability": [0.95, 0.90, 0.85],
        "latency": [20.0, 10.0, 5.0],
        "train_cost": [30.0, 20.0, 5.0],
        "explainability": [0.3, 0.6, 1.0],
    }, index=["svm", "rf", "dt"])

    probs = rank_probability(df, PROFILES["Accuracy-first"], n_draws=1000)
    assert len(probs) == 3
    assert np.isclose(probs.sum(), 1.0, rtol=1e-3)
    assert probs["svm"] > 0.80


def test_decision_strength_rule():
    # Clear: diff excludes zero, mcnemar p < 0.05, p_rank1 >= 0.80
    assert compute_decision_strength(True, 0.01, 0.85) == "clear"

    # Marginal: some but not all hold
    assert compute_decision_strength(False, 0.01, 0.85) == "marginal"
    assert compute_decision_strength(True, 0.12, 0.85) == "marginal"
    assert compute_decision_strength(True, 0.01, 0.65) == "marginal"

    # None: none hold
    assert compute_decision_strength(False, 0.20, 0.50) == "none"


def test_forbidden_key_scanner():
    clean_packet = {
        "dataset": {"name": "test_ds", "variant": "nonlinear"},
        "models": [{"key": "svm", "macro_f1": 0.81}],
        "facts": [{"id": "F1", "text": "Score 0.81"}],
    }
    assert len(scan_packet_for_forbidden_keys(clean_packet)) == 0

    dirty_packet = {
        "dataset": {"name": "test_ds"},
        "records": [{"employee_id": "EMP001", "salary": 50000}],
    }
    violations = scan_packet_for_forbidden_keys(dirty_packet)
    assert len(violations) >= 2


def test_select_facts_contains_caveat():
    mock_packet = {
        "synthetic_caveat_fact": "F90",
        "deterministic_winner": "svm",
        "models": [{"key": "svm"}, {"key": "boost"}, {"key": "rf"}, {"key": "dt"}],
        "facts": [
            {"id": "F1", "model_key": "svm", "text": "SVM fact"},
            {"id": "F2", "model_key": "dt", "text": "DT fact"},
            {"id": "F90", "model_key": "global", "text": "Synthetic caveat"},
        ],
    }
    selected = select_facts(mock_packet, mode="verdict")
    fact_ids = {f["id"] for f in selected}
    assert "F90" in fact_ids
    assert "F1" in fact_ids
    assert "F2" not in fact_ids  # dt is rank 4, excluded from top-3 in verdict mode
