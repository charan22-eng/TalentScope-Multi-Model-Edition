"""Independent Calibration Audit for TalentScope Multi-Model Edition.

Computes ECE (10 equal-width bins, top label) and Brier BEFORE and AFTER calibration
for all seven models on both cal-B and test splits.
Verifies whether calibrators are applied to test_predictions.csv probabilities.
"""

import json
import os
import sys
from pathlib import Path

# Ensure ml/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml" / "src"))

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax

from epk.features import ALL_FEATURES
from epk.labels import encode_bands
from epk.split import load_split


def compute_ece(y_true: np.ndarray, probas: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) across multi-class predictions."""
    conf = np.max(probas, axis=1)
    preds = np.argmax(probas, axis=1)
    accs = (preds == y_true).astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for b_lo, b_hi in zip(bins[:-1], bins[1:]):
        in_bin = (conf > b_lo) & (conf <= b_hi)
        if np.any(in_bin):
            b_acc = np.mean(accs[in_bin])
            b_conf = np.mean(conf[in_bin])
            ece += np.sum(in_bin) / len(y_true) * np.abs(b_acc - b_conf)
    return float(ece)


def compute_brier(y_true: np.ndarray, probas: np.ndarray) -> float:
    """Compute multi-class Brier score."""
    n_classes = probas.shape[1]
    y_bin = np.zeros_like(probas)
    for c in range(n_classes):
        y_bin[:, c] = (y_true == c).astype(float)
    return float(np.mean(np.sum((probas - y_bin) ** 2, axis=1)))


def main():
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "nonlinear" / "dataset.csv"
    split_path = root / "data" / "processed" / "split.json"
    models_dir = root / "artifacts" / "v2" / "models"

    df = pd.read_csv(data_path)
    splits = load_split(str(split_path))

    cal_b_idx = splits["cal_b"]
    test_idx = splits["test"]

    X_cal_b = df.loc[cal_b_idx, ALL_FEATURES]
    y_cal_b = encode_bands(df.loc[cal_b_idx, "performance"])

    X_test = df.loc[test_idx, ALL_FEATURES]
    y_test = encode_bands(df.loc[test_idx, "performance"])

    models = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]

    results = {}
    print("=" * 88)
    print("INDEPENDENT CALIBRATION AUDIT: BEFORE vs AFTER CALIBRATION (cal-B & test)")
    print("=" * 88)

    for m in models:
        model_path = models_dir / m / "model.joblib"
        cal_model = joblib.load(model_path)
        base_model = cal_model.estimator

        # Pre-calibration probabilities
        if hasattr(base_model, "predict_proba"):
            p_cal_b_pre = base_model.predict_proba(X_cal_b)
            p_test_pre = base_model.predict_proba(X_test)
        elif hasattr(base_model, "decision_function"):
            p_cal_b_pre = softmax(base_model.decision_function(X_cal_b), axis=1)
            p_test_pre = softmax(base_model.decision_function(X_test), axis=1)
        else:
            raise ValueError(f"Cannot get pre-calibration probabilities for {m}")

        # Post-calibration probabilities
        p_cal_b_post = cal_model.predict_proba(X_cal_b)
        p_test_post = cal_model.predict_proba(X_test)

        # Cal-B metrics
        ece_cal_b_pre = compute_ece(y_cal_b, p_cal_b_pre)
        ece_cal_b_post = compute_ece(y_cal_b, p_cal_b_post)
        brier_cal_b_pre = compute_brier(y_cal_b, p_cal_b_pre)
        brier_cal_b_post = compute_brier(y_cal_b, p_cal_b_post)

        # Test metrics
        ece_test_pre = compute_ece(y_test, p_test_pre)
        ece_test_post = compute_ece(y_test, p_test_post)
        brier_test_pre = compute_brier(y_test, p_test_pre)
        brier_test_post = compute_brier(y_test, p_test_post)

        # Verification against test_predictions.csv
        pred_csv = pd.read_csv(models_dir / m / "test_predictions.csv")
        csv_probas = pred_csv[["prob_low", "prob_med", "prob_high"]].values
        max_diff = float(np.max(np.abs(csv_probas - np.round(p_test_post, 5))))
        matches_csv = bool(max_diff < 1e-4)

        results[m] = {
            "cal_b": {
                "ece_before": round(ece_cal_b_pre, 4),
                "ece_after": round(ece_cal_b_post, 4),
                "brier_before": round(brier_cal_b_pre, 4),
                "brier_after": round(brier_cal_b_post, 4),
            },
            "test": {
                "ece_before": round(ece_test_pre, 4),
                "ece_after": round(ece_test_post, 4),
                "brier_before": round(brier_test_pre, 4),
                "brier_after": round(brier_test_post, 4),
            },
            "test_predictions_csv_verified": matches_csv,
            "max_abs_diff_with_csv": max_diff,
        }

    # Print Formatted Markdown Tables
    print("\n### 1. Split: cal-B (N = 1,191)")
    print("| Model | ECE (Before) | ECE (After) | Brier (Before) | Brier (After) | Delta ECE | Delta Brier |")
    print("|---|---|---|---|---|---|---|")
    for m in models:
        cb = results[m]["cal_b"]
        d_ece = cb["ece_after"] - cb["ece_before"]
        d_brier = cb["brier_after"] - cb["brier_before"]
        print(f"| `{m}` | {cb['ece_before']:.4f} | {cb['ece_after']:.4f} | {cb['brier_before']:.4f} | {cb['brier_after']:.4f} | {d_ece:+.4f} | {d_brier:+.4f} |")

    print("\n### 2. Split: test (N = 2,381)")
    print("| Model | ECE (Before) | ECE (After) | Brier (Before) | Brier (After) | In test_predictions.csv | Max Abs Diff |")
    print("|---|---|---|---|---|---|---|")
    for m in models:
        t = results[m]["test"]
        print(f"| `{m}` | {t['ece_before']:.4f} | {t['ece_after']:.4f} | {t['brier_before']:.4f} | {t['brier_after']:.4f} | {'VERIFIED (Post)' if results[m]['test_predictions_csv_verified'] else 'MISMATCH'} | {results[m]['max_abs_diff_with_csv']:.1e} |")

    out_file = root / "reports" / "calibration_audit.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved raw audit data to: {out_file}")


if __name__ == "__main__":
    main()
