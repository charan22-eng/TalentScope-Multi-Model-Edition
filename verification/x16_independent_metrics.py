import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score, confusion_matrix
from scipy.stats import chi2

MODELS = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]
ROOT = Path(".")

def compute_metrics(y_true, y_pred):
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "qwk": float(cohen_kappa_score(y_true, y_pred, weights="quadratic")),
    }

def paired_bootstrap_ci(y_true, y_pred, n_bootstraps=2000, seed=42):
    rng = np.random.RandomState(seed)
    n = len(y_true)
    f1_boots = np.empty(n_bootstraps)
    for i in range(n_bootstraps):
        idx = rng.randint(0, n, n)
        f1_boots[i] = f1_score(y_true[idx], y_pred[idx], average="macro")
    
    ci_lower = float(np.percentile(f1_boots, 2.5))
    ci_upper = float(np.percentile(f1_boots, 97.5))
    return round(ci_lower, 4), round(ci_upper, 4)

def mcnemar_p_value(y_true, y_pred_a, y_pred_b):
    correct_a = (y_pred_a == y_true)
    correct_b = (y_pred_b == y_true)
    b = np.sum(correct_a & ~correct_b)  # A right, B wrong
    c = np.sum(~correct_a & correct_b)  # A wrong, B right
    
    if b + c == 0:
        return 1.0
    # McNemar with Edwards continuity correction
    stat = (abs(b - c) - 1.0) ** 2 / (b + c)
    p_val = float(1.0 - chi2.cdf(stat, df=1))
    return p_val, int(b), int(c)

def verify_all_metrics():
    results = {}
    mismatches = []
    
    leaderboard_file = ROOT / "artifacts/v2/comparison/leaderboard.json"
    if not leaderboard_file.exists():
        print(f"[FAIL] Leaderboard file missing: {leaderboard_file}")
        return False, {"error": "leaderboard missing"}
    
    with open(leaderboard_file, "r", encoding="utf-8") as f:
        leaderboard_data = json.load(f)
    
    reported_by_key = {m["key"]: m for m in leaderboard_data.get("metrics", [])}
    preds = {}
    
    for key in MODELS:
        pred_file = ROOT / f"artifacts/v2/models/{key}/test_predictions.csv"
        if not pred_file.exists():
            mismatches.append(f"Missing predictions file: {pred_file}")
            continue
        
        df = pd.read_csv(pred_file)
        y_true = df["y_true"].values
        y_pred = df["y_pred"].values
        preds[key] = (y_true, y_pred)
        
        m = compute_metrics(y_true, y_pred)
        reported = reported_by_key.get(key, {})
        rep_f1 = reported.get("macro_f1")
        f1_diff = abs(m["macro_f1"] - rep_f1) if rep_f1 is not None else 999
        
        passed = (f1_diff <= 0.0002)
        if not passed:
            mismatches.append(f"Model {key}: reported f1={rep_f1} vs calc f1={m['macro_f1']:.4f}")
        
        results[key] = {
            "calculated": m,
            "reported": {"accuracy": reported.get("accuracy"), "macro_f1": rep_f1, "qwk": reported.get("qwk")},
            "passed": passed
        }
        print(f"[{'PASS' if passed else 'FAIL'}] Model {key:7s}: calc_f1={m['macro_f1']:.4f}, rep_f1={rep_f1}, delta={f1_diff:.5f}")

    # Bootstrap CIs for rf and boost
    print("\n--- Paired Bootstrap 95% CIs (2,000 resamples) ---")
    for key in ["boost", "rf", "svm"]:
        y_true, y_pred = preds[key]
        low, high = paired_bootstrap_ci(y_true, y_pred, n_bootstraps=2000, seed=42)
        rep_low = reported_by_key[key].get("macro_f1_ci_lower")
        rep_high = reported_by_key[key].get("macro_f1_ci_upper")
        print(f"Model {key:7s} CI: [{low}, {high}] (Reported: [{rep_low}, {rep_high}])")

    # McNemar test between rf and boost
    y_true_all = preds["rf"][0]
    p_val, b, c = mcnemar_p_value(y_true_all, preds["rf"][1], preds["boost"][1])
    print(f"\n--- McNemar Test rf vs boost ---")
    print(f"Discordant pairs: rf correct only = {b}, boost correct only = {c}")
    print(f"McNemar p-value = {p_val:.4f} (>= 0.05 indicates no statistically significant difference)")

    all_passed = len(mismatches) == 0 and len(results) == 7
    return all_passed, {"results": results, "mismatches": mismatches}

if __name__ == "__main__":
    success, data = verify_all_metrics()
    print("\nSummary:", "ALL PASSED" if success else f"FAILURES: {data['mismatches']}")
    exit(0 if success else 1)
