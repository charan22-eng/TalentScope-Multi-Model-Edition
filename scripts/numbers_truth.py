#!/usr/bin/env python3
"""numbers_truth.py — Independent metrics truth table from test_predictions.csv.

Computes from raw CSVs (numpy, pandas, scipy, scikit-learn only):
  accuracy, macro_f1, qwk, brier, ece (10 equal-width bins, top-label),
  balanced_accuracy, mcc, roc_auc_ovr, log_loss, confusion_matrix,
  per-class precision/recall/f1/support, exact/adjacent/extreme shares.

Compares field-by-field with leaderboard.json.
Outputs JSON truth table to stdout.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize


MODELS_DIR = Path("artifacts/v2/models")
LEADERBOARD_PATH = Path("artifacts/v2/comparison/leaderboard.json")
MODEL_KEYS = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]


def compute_ece(y_true: np.ndarray, probas: np.ndarray, n_bins: int = 10) -> float:
    """ECE: 10 equal-width bins, top-label confidence."""
    confidences = np.max(probas, axis=1)
    predictions = np.argmax(probas, axis=1)
    accuracies = (predictions == y_true).astype(float)
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for bin_lower, bin_upper in zip(bin_boundaries[:-1], bin_boundaries[1:]):
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = float(np.mean(in_bin))
        if prop_in_bin > 0:
            acc_in_bin = float(np.mean(accuracies[in_bin]))
            conf_in_bin = float(np.mean(confidences[in_bin]))
            ece += np.abs(conf_in_bin - acc_in_bin) * prop_in_bin
    return float(ece)


def compute_brier_multiclass(y_true: np.ndarray, probas: np.ndarray) -> float:
    """Multiclass Brier: mean of sum-of-squared differences per row."""
    y_bin = label_binarize(y_true, classes=[0, 1, 2])
    return float(np.mean(np.sum((probas - y_bin) ** 2, axis=1)))


def compute_metrics_from_csv(csv_path: Path) -> dict:
    """Compute all metrics from a test_predictions.csv file."""
    df = pd.read_csv(csv_path)
    y_true = df["y_true"].to_numpy(dtype=int)
    y_pred = df["y_pred"].to_numpy(dtype=int)
    probas = df[["prob_low", "prob_med", "prob_high"]].to_numpy(dtype=float)
    y_bin = label_binarize(y_true, classes=[0, 1, 2])
    n = len(y_true)

    # Core metrics
    acc = round(float(accuracy_score(y_true, y_pred)), 4)
    bal_acc = round(float(balanced_accuracy_score(y_true, y_pred)), 4)
    macro_f1 = round(float(f1_score(y_true, y_pred, average="macro")), 4)
    qwk = round(float(cohen_kappa_score(y_true, y_pred, weights="quadratic")), 4)
    mcc = round(float(matthews_corrcoef(y_true, y_pred)), 4)

    # Probabilistic
    ll = round(float(log_loss(y_true, probas, labels=[0, 1, 2])), 4)
    brier = round(compute_brier_multiclass(y_true, probas), 4)
    ece = round(compute_ece(y_true, probas, n_bins=10), 4)
    roc_ovr = round(float(roc_auc_score(y_bin, probas, multi_class="ovr", average="macro")), 4)

    # Ordinal error
    diff = np.abs(y_true - y_pred)
    exact_share = round(float(np.mean(diff == 0)), 4)
    adjacent_share = round(float(np.mean(diff == 1)), 4)
    extreme_share = round(float(np.mean(diff == 2)), 4)

    # Per-class
    INT_TO_BAND = {0: "Low", 1: "Medium", 2: "High"}
    p_c, r_c, f_c, sup_c = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1, 2])
    per_class = {}
    for c in range(3):
        per_class[INT_TO_BAND[c]] = {
            "precision": round(float(p_c[c]), 4),
            "recall": round(float(r_c[c]), 4),
            "f1": round(float(f_c[c]), 4),
            "support": int(sup_c[c]),
        }

    cm = confusion_matrix(y_true, y_pred).tolist()

    return {
        "test_samples": n,
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "macro_f1": macro_f1,
        "qwk": qwk,
        "mcc": mcc,
        "roc_auc_ovr": roc_ovr,
        "log_loss": ll,
        "brier": brier,
        "ece": ece,
        "exact_share": exact_share,
        "adjacent_share": adjacent_share,
        "extreme_share": extreme_share,
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def diff_fields(computed: dict, leaderboard_entry: dict, key: str) -> list:
    """Compare computed metrics against leaderboard entry, return list of differences."""
    diffs = []
    COMPARE_FIELDS = [
        "test_samples", "accuracy", "balanced_accuracy", "macro_f1", "qwk",
        "mcc", "roc_auc_ovr", "log_loss", "brier", "ece",
        "exact_share", "adjacent_share", "extreme_share",
    ]
    for field in COMPARE_FIELDS:
        cv = computed.get(field)
        lv = leaderboard_entry.get(field)
        if cv != lv:
            diffs.append({
                "model": key,
                "field": field,
                "computed": cv,
                "leaderboard": lv,
            })

    # Compare confusion matrix
    if computed.get("confusion_matrix") != leaderboard_entry.get("confusion_matrix"):
        diffs.append({
            "model": key,
            "field": "confusion_matrix",
            "computed": computed["confusion_matrix"],
            "leaderboard": leaderboard_entry.get("confusion_matrix"),
        })

    # Compare per-class
    for cls_name in ["Low", "Medium", "High"]:
        for metric in ["precision", "recall", "f1", "support"]:
            cv = computed.get("per_class", {}).get(cls_name, {}).get(metric)
            lv = leaderboard_entry.get("per_class", {}).get(cls_name, {}).get(metric)
            if cv != lv:
                diffs.append({
                    "model": key,
                    "field": f"per_class.{cls_name}.{metric}",
                    "computed": cv,
                    "leaderboard": lv,
                })

    return diffs


def main():
    # Load leaderboard
    with open(LEADERBOARD_PATH) as f:
        lb = json.load(f)
    lb_by_key = {m["key"]: m for m in lb["metrics"]}

    all_computed = {}
    all_diffs = []

    print("=" * 80)
    print("NUMBERS TRUTH TABLE — Independent computation from test_predictions.csv")
    print("=" * 80)

    for key in MODEL_KEYS:
        csv_path = MODELS_DIR / key / "test_predictions.csv"
        if not csv_path.exists():
            print(f"[MISSING] {csv_path}")
            continue

        computed = compute_metrics_from_csv(csv_path)
        all_computed[key] = computed

        lb_entry = lb_by_key.get(key, {})
        diffs = diff_fields(computed, lb_entry, key)
        all_diffs.extend(diffs)

        print(f"\n--- {key} ---")
        print(f"  accuracy:      {computed['accuracy']}")
        print(f"  macro_f1:      {computed['macro_f1']}")
        print(f"  qwk:           {computed['qwk']}")
        print(f"  brier:         {computed['brier']}")
        print(f"  ece:           {computed['ece']}")
        print(f"  roc_auc_ovr:   {computed['roc_auc_ovr']}")
        print(f"  log_loss:      {computed['log_loss']}")
        if diffs:
            print(f"  ** {len(diffs)} DIFFERENCES vs leaderboard **")
            for d in diffs:
                print(f"    {d['field']}: computed={d['computed']} vs leaderboard={d['leaderboard']}")
        else:
            print(f"  OK All fields match leaderboard")

    print(f"\n{'=' * 80}")
    print(f"TOTAL DIFFERENCES: {len(all_diffs)}")
    print(f"{'=' * 80}")

    # Dump full results as JSON to a file
    output = {
        "computed_metrics": all_computed,
        "differences": all_diffs,
        "total_differences": len(all_diffs),
    }
    out_path = Path("reports/numbers_truth.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results written to {out_path}")


if __name__ == "__main__":
    main()
