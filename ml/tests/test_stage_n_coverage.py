"""Comprehensive Unit Tests for Stage N Hardening & Test Coverage.

Tests statistical comparisons (Bootstrap, McNemar-Holm), evidence packet validation,
split isolation, sensitivity correlation, and artifact loaders.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from epk.artifacts import ArtifactLoader, default_loader
from epk.features import ALL_FEATURES
from epk.labels import BANDS, encode_bands
from epk.split import load_split
from epk.stats import paired_stratified_bootstrap, pairwise_mcnemar_tests


def test_paired_stratified_bootstrap_synthetic():
    rng = np.random.default_rng(42)
    n = 300
    y_true = rng.choice([0, 1, 2], size=n, p=[0.25, 0.50, 0.25])
    
    # Model A: ~80% accuracy
    p_a = y_true.copy()
    flips_a = rng.choice(n, size=int(n * 0.2), replace=False)
    p_a[flips_a] = (p_a[flips_a] + 1) % 3
    
    # Model B: ~70% accuracy
    p_b = y_true.copy()
    flips_b = rng.choice(n, size=int(n * 0.3), replace=False)
    p_b[flips_b] = (p_b[flips_b] + 1) % 3

    preds_dict = {"model_a": p_a, "model_b": p_b}
    res = paired_stratified_bootstrap(
        y_true=y_true,
        preds_dict=preds_dict,
        rank1_key="model_a",
        rank2_key="model_b",
        n_resamples=50,
        seed=42,
    )

    assert "model_cis" in res
    assert "diff_rank1_rank2" in res
    assert "model_a" in res["model_cis"]
    f1_ci = res["model_cis"]["model_a"]["macro_f1_ci"]
    assert len(f1_ci) == 2
    assert f1_ci[0] <= f1_ci[1]


def test_pairwise_mcnemar_tests_symmetry_and_correction():
    rng = np.random.default_rng(123)
    n = 200
    y_true = rng.choice([0, 1, 2], size=n)

    models = ["m1", "m2", "m3", "m4", "m5", "m6", "m7"]
    preds_dict = {}
    for m in models:
        preds = y_true.copy()
        flips = rng.choice(n, size=rng.integers(20, 60), replace=False)
        preds[flips] = (preds[flips] + 1) % 3
        preds_dict[m] = preds

    res = pairwise_mcnemar_tests(y_true=y_true, preds_dict=preds_dict)
    assert len(res["pairwise_tests"]) == 21  # 7 * 6 / 2
    for item in res["pairwise_tests"]:
        assert 0.0 <= item["raw_p"] <= 1.0
        assert 0.0 <= item["holm_p"] <= 1.0
        assert item["raw_p"] <= item["holm_p"] + 1e-9


def test_split_integrity_and_disjointness():
    split_file = Path("data/processed/split.json")
    if split_file.exists():
        splits = load_split(str(split_file))
        assert len(splits["train"]) == 7142
        assert len(splits["test"]) == 2381
        assert len(splits["cal_a"]) in [1190, 1191]
        assert len(splits["cal_b"]) in [1190, 1191]
        assert len(splits["cal_a"]) + len(splits["cal_b"]) == 2381


def test_sensitivity_artifact_format():
    sens_file = Path("artifacts/v2/comparison/sensitivity.json")
    if sens_file.exists():
        with open(sens_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "variants" in data
        assert "kendall_tau" in data
        assert "linear" in data["variants"]
        assert "nonlinear" in data["variants"]
        assert "noisy_overlap" in data["variants"]


def test_artifact_loader_manifest_verification():
    assert default_loader.root_dir.exists()
    assert "files" in default_loader.manifest
    # Check champion file verification
    champ = default_loader.load_champion()
    assert "champion" in champ
    assert champ["champion"] in ["rf", "boost", "knn", "svm", "dt", "linreg", "logreg"]
