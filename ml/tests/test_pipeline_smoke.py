"""Comprehensive pipeline smoke and invariant tests for epk package.

Covers:
- train_all.py: Experiments logging and small training step
- final_eval.py: G6 Lock enforcement ("second run refused") and ECE metric
- stats.py: Statistical testing, conformal sets, and robustness
- evidence.py: Fact selection, packet building, forbidden keys scanning
- explain.py: Explanations, native model summaries, PCA projection, persona summaries
- sensitivity.py: Variant sensitivity evaluation
"""

import datetime
import hashlib
import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from epk.evidence import (
    scan_packet_for_forbidden_keys,
    select_facts,
)
from epk.explain import (
    explain,
    explain_model_native,
    find_counterfactuals,
    find_similar_cases,
    fit_pca_projection,
    generate_decision_landscape_grid,
    generate_persona_summaries,
    local_attribution,
)
from epk.features import ALL_FEATURES
from epk.final_eval import check_and_acquire_g6_lock, compute_ece
from epk.labels import encode_bands
from epk.models.registry import get_model_spec, list_model_specs
from epk.sensitivity import run_variant_sensitivity
from epk.split import create_frozen_split, load_split
from epk.stats import (
    compute_conformal_sets_cal_b,
    evaluate_robustness,
    paired_stratified_bootstrap,
    pairwise_mcnemar_tests,
)
from epk.train_all import log_experiment, run_training_pipeline
from epk.uncertainty import get_prediction_set, stability_score


@pytest.fixture
def sample_data():
    """Load small slice of existing cleaned dataset."""
    df = pd.read_csv("data/nonlinear/dataset.csv").head(100)
    return df


def test_g6_lock_second_run_refused(tmp_path):
    """Guard G6 invariant: Running final_eval a second time without --new-config must be REFUSED."""
    lock_file = tmp_path / "test_eval.lock"
    log_file = tmp_path / "test_eval_log.csv"

    variant = "nonlinear"
    data_hash = "mock_data_hash_12345"
    split_hash = "mock_split_hash_67890"

    # Run 1: Should acquire lock cleanly
    config_hash = check_and_acquire_g6_lock(
        lock_path=str(lock_file),
        log_path=str(log_file),
        variant=variant,
        dataset_hash=data_hash,
        split_hash=split_hash,
        new_config_reason=None,
    )
    assert lock_file.exists()
    with open(lock_file) as f:
        lock_data = json.load(f)
    assert lock_data["config_hash"] == config_hash

    # Run 2: Exact same configuration without reason -> MUST RAISE RuntimeError
    with pytest.raises(RuntimeError, match=r"\[G6 VIOLATION PREVENTED\]"):
        check_and_acquire_g6_lock(
            lock_path=str(lock_file),
            log_path=str(log_file),
            variant=variant,
            dataset_hash=data_hash,
            split_hash=split_hash,
            new_config_reason=None,
        )

    # Run 3: With --new-config reason -> MUST SUCCEED and log entry
    reason = "calibration audit retry"
    new_cfg_hash = check_and_acquire_g6_lock(
        lock_path=str(lock_file),
        log_path=str(log_file),
        variant=variant,
        dataset_hash=data_hash,
        split_hash=split_hash,
        new_config_reason=reason,
    )
    assert new_cfg_hash == config_hash
    assert log_file.exists()
    log_df = pd.read_csv(log_file)
    assert len(log_df) == 1
    assert log_df.iloc[0]["reason"] == reason


def test_train_all_log_experiment(tmp_path):
    """Verify experiment logger in train_all."""
    exp_csv = tmp_path / "experiments.csv"
    log_experiment(
        report_csv=str(exp_csv),
        run_id="test_run_1",
        phase="test_phase",
        model="rf",
        cv_macro_f1="0.8000 +- 0.0100",
        test_macro_f1="N/A",
        params={"n_estimators": 50},
        seed=42,
        data_checksum="checksum_abc",
        split_hash="split_xyz",
        profile="fast",
        notes="smoke test run",
    )
    assert exp_csv.exists()
    df = pd.read_csv(exp_csv)
    assert len(df) == 1
    assert df.iloc[0]["model"] == "rf"
    assert df.iloc[0]["run_id"] == "test_run_1"


def test_stats_and_bootstrap():
    """Verify statistical testing routines."""
    y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 1] * 10)
    preds_dict = {
        "m1": y_true.copy(),
        "m2": np.where(y_true == 2, 1, y_true),
    }
    # Stratified bootstrap
    boot = paired_stratified_bootstrap(y_true, preds_dict, "m1", "m2", n_resamples=50)
    assert "diff_rank1_rank2" in boot
    assert "model_cis" in boot

    # McNemar tests
    mcn = pairwise_mcnemar_tests(y_true, preds_dict)
    assert "pair_map" in mcn
    assert "m1_vs_m2" in mcn["pair_map"] or "m2_vs_m1" in mcn["pair_map"]


def test_stats_robustness_and_conformal(sample_data):
    """Verify robustness and conformal prediction set generation."""
    cal_b_df = sample_data.iloc[:50].copy()
    test_df = sample_data.iloc[50:].copy()

    class MockModel:
        def predict(self, X):
            return np.zeros(len(X), dtype=int)
        def predict_proba(self, X):
            p = np.full((len(X), 3), 1.0 / 3.0)
            return p

    models_dict = {"mock": MockModel()}
    conf = compute_conformal_sets_cal_b(cal_b_df, test_df, models_dict, alpha=0.10)
    assert "mock" in conf
    assert "empirical_coverage" in conf["mock"]
    assert "avg_set_size" in conf["mock"]

    # Robustness evaluation
    rob = evaluate_robustness(test_df, models_dict)
    assert "mock" in rob
    assert "robustness_score" in rob["mock"]


def test_evidence_packet_inspection():
    """Verify evidence packet inspection, selection, and forbidden key scanning."""
    packet_path = Path("artifacts/v2/comparison/evidence_packet.json")
    assert packet_path.exists(), "artifacts/v2/comparison/evidence_packet.json not found"

    with open(packet_path, "r", encoding="utf-8") as f:
        packet = json.load(f)

    assert packet["deterministic_winner"] == "boost"
    assert "facts" in packet
    assert len(packet["facts"]) >= 10

    # Test fact selection
    facts = select_facts(packet)
    assert len(facts) >= 2

    # Test forbidden keys scanning on clean packet
    leaks = scan_packet_for_forbidden_keys(packet)
    assert leaks == []

    # Inject forbidden key and verify refusal
    dirty_packet = dict(packet)
    dirty_packet["employee_id"] = "EMP0001"
    leaks_dirty = scan_packet_for_forbidden_keys(dirty_packet)
    assert len(leaks_dirty) > 0


def test_explain_functions(sample_data):
    """Verify explainers, native model summaries, PCA projection, and landscapes."""
    X = sample_data[ALL_FEATURES]
    y = encode_bands(sample_data["performance"])

    # Test fit PCA projection with complete sample_data containing performance
    pca_dict = fit_pca_projection(sample_data)
    assert "explained_variance_ratio" in pca_dict
    assert "components" in pca_dict
    assert len(pca_dict["background_points"]) > 0

    class DummyClf:
        def predict(self, data):
            return np.ones(len(data), dtype=int)
        def predict_proba(self, data):
            p = np.zeros((len(data), 3))
            p[:, 1] = 1.0
            return p

    # Test decision landscape grid
    grid = generate_decision_landscape_grid(
        DummyClf(),
        X,
        feature_x="prev_score",
        feature_y="attendance",
        grid_size=10,
    )
    assert "feature_x" in grid
    assert "grid_predictions" in grid

    # Test persona summaries
    personas = generate_persona_summaries(
        key="rf",
        label="Random Forest",
        pred_band="Medium",
        proba=[0.1, 0.8, 0.1],
        attribution={"prev_score": 0.25, "attendance": -0.10},
        counterfactuals=[{"changes": {"attendance": 95.0}}],
        stability=0.95,
    )
    assert "hr_summary" in personas
    assert "datascience_summary" in personas

    # Test find similar cases
    row = X.iloc[[0]]
    sim = find_similar_cases(
        train_df=sample_data,
        train_labels=sample_data["performance"],
        x_row=row,
        model_key="rf",
        k=3,
    )
    assert "cases" in sim or "neighbors" in sim or isinstance(sim, dict)

    # Test find counterfactuals
    class DummyClfWithClasses:
        classes_ = np.array([0, 1, 2])
        def predict(self, data):
            return np.ones(len(data), dtype=int)
        def predict_proba(self, data):
            p = np.zeros((len(data), 3))
            p[:, 1] = 1.0
            return p

    cf = find_counterfactuals(DummyClfWithClasses(), row, target_band="High")
    assert isinstance(cf, list)


def test_explain_all_native_models():
    """Verify explain_model_native extracts interpretability payloads for all 7 models."""
    from epk.artifacts import default_loader
    for key in ["rf", "boost", "linreg", "svm", "knn", "dt", "logreg"]:
        m = default_loader.load_model(key)
        exp = explain_model_native(m, key)
        assert exp["key"] == key
        assert "explanation_type" in exp


def test_local_attribution_and_helpers(sample_data):
    """Verify local attribution calculation and legacy explain helpers."""
    from epk.artifacts import default_loader
    from epk.explain import counterfactual, explain, summarise
    rf_model = default_loader.load_model("rf")
    row = sample_data[ALL_FEATURES].iloc[[0]]
    medians = sample_data[ALL_FEATURES].median(numeric_only=True)
    attr = local_attribution(rf_model, row, medians)
    assert len(attr) > 0

    nb_df, votes = explain(rf_model, sample_data[ALL_FEATURES], sample_data["performance"], row, k=2)
    assert len(nb_df) == 2
    assert isinstance(votes, dict)

    summary = summarise({"label": "High", "confidence": 0.95})
    assert "High" in summary


def test_artifact_loader_methods():
    """Verify ArtifactLoader loads champion, dataset_meta, and errors on invalid keys."""
    from epk.artifacts import default_loader, ModelKeyError
    assert default_loader.load_champion()["champion"] == "boost"
    assert "variants" in default_loader.load_dataset_meta()
    assert "metrics" in default_loader.load_comparison_json("leaderboard")
    meta = default_loader.load_model_metadata("rf")
    assert meta["key"] == "rf"

    with pytest.raises(ModelKeyError):
        default_loader.load_model("unknown_key")
    with pytest.raises(ModelKeyError):
        default_loader.load_model_metadata("unknown_key")


def test_variant_sensitivity(tmp_path):
    """Verify run_variant_sensitivity executes across all 3 variants."""
    out_file = tmp_path / "sensitivity.json"
    res = run_variant_sensitivity(output_path=str(out_file))
    assert out_file.exists()
    assert "variants" in res
    assert "kendall_tau" in res


def test_build_comparison_suite(tmp_path):
    """Verify build_comparison_suite builds all artifacts and evidence packet."""
    from epk.evidence import build_comparison_suite
    comp_dir = tmp_path / "comp"
    packet = build_comparison_suite(comparison_dir=str(comp_dir), n_resamples=10)
    assert packet["deterministic_winner"] == "boost"
    assert (comp_dir / "leaderboard.json").exists()
    assert (comp_dir / "pairwise.json").exists()
    assert (comp_dir / "conformal.json").exists()
    assert (comp_dir / "mcda.json").exists()
    assert (comp_dir / "evidence_packet.json").exists()


def test_create_frozen_split(tmp_path):
    """Verify create_frozen_split generates disjoint partitions."""
    out_split = tmp_path / "split.json"
    data = create_frozen_split(data_path="data/nonlinear/dataset.csv", out_path=str(out_split))
    assert out_split.exists()
    assert "train_indices" in data
    assert "cal_a_indices" in data
    assert "cal_b_indices" in data
    assert "test_indices" in data
    assert data["n_rows"] == 11904


def test_train_all_smoke_pipeline(tmp_path, monkeypatch):
    """Verify train_all_models and final_eval run end-to-end on a tiny fixture under smoke profile."""
    split_info = load_split("data/processed/split.json")
    mini_split = {
        "seed": 42,
        "n_rows": 11904,
        "train_indices": [int(i) for i in split_info["train"][:150]],
        "cal_a_indices": [int(i) for i in split_info["cal_a"][:30]],
        "cal_b_indices": [int(i) for i in split_info["cal_b"][:30]],
        "test_indices": [int(i) for i in split_info["test"][:105]],
        "split_hash": "mini_split_hash",
    }
    split_path = tmp_path / "split.json"
    with open(split_path, "w") as f:
        json.dump(mini_split, f)

    out_models = tmp_path / "models"
    res = run_training_pipeline(
        profile="smoke",
        variant="nonlinear",
        split_path=str(split_path),
        output_dir=str(out_models),
    )
    assert len(res) == 7
    for k in ["rf", "boost", "linreg", "svm", "knn", "dt", "logreg"]:
        assert (out_models / k / "model.joblib").exists()
        assert (out_models / k / "tuning.json").exists()

    # Now test run_final_evaluation with monkeypatched lock and report generator
    from epk import final_eval
    monkeypatch.setattr(
        final_eval,
        "check_and_acquire_g6_lock",
        lambda **kwargs: "mock_eval_hash",
    )
    monkeypatch.setattr(
        final_eval,
        "generate_v2_final_report",
        lambda results, variant, n_test: None,
    )
    eval_res = final_eval.run_final_evaluation(
        variant="nonlinear",
        data_path="data/nonlinear/dataset.csv",
        split_path=str(split_path),
        models_dir=str(out_models),
        new_config="test smoke evaluation",
    )
    assert len(eval_res) == 7
    for k in ["rf", "boost", "linreg", "svm", "knn", "dt", "logreg"]:
        assert (out_models / k / "metrics.json").exists()
        assert (out_models / k / "test_predictions.csv").exists()


def test_final_eval_ece_and_report(tmp_path):
    """Verify ECE calculation edge cases and final report generation."""
    from epk.final_eval import generate_v2_final_report
    # ECE perfect calibration
    y_true = np.array([0, 1, 2, 0])
    probas = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
    ])
    assert compute_ece(y_true, probas) == 0.0

    # Test report generation
    with open("artifacts/v2/comparison/leaderboard.json") as f:
        lb = json.load(f)
    results = {m["key"]: m for m in lb["metrics"]}
    generate_v2_final_report(results, variant="nonlinear", n_test=2381)
    assert Path("reports/v2_final.md").exists()

