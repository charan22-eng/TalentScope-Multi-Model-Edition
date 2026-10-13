import json
from pathlib import Path
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, "ml/src")
from epk.uncertainty import get_prediction_set

ROOT = Path(".")
MODELS = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]

def verify_conformal():
    conf_file = ROOT / "artifacts/v2/comparison/conformal.json"
    if not conf_file.exists():
        print(f"[FAIL] Missing {conf_file}")
        return False
        
    with open(conf_file, "r", encoding="utf-8") as f:
        stored = json.load(f)
        
    print("--- Independent Split-Conformal Coverage Replication ---")
    all_passed = True
    
    for key in MODELS:
        pred_file = ROOT / f"artifacts/v2/models/{key}/test_predictions.csv"
        if not pred_file.exists():
            continue
            
        df = pd.read_csv(pred_file)
        y_true = df["y_true"].values
        probs = df[["prob_low", "prob_med", "prob_high"]].values
        
        rep = stored.get(key, {})
        min_p = rep.get("min_prob_threshold", 0.0)
        rep_cov = rep.get("empirical_coverage", 0.0)
        rep_size = rep.get("avg_set_size", 0.0)
        
        # Conformal prediction set per sample via shared get_prediction_set function
        sets = [get_prediction_set(p, classes=[0, 1, 2], min_prob_threshold=min_p) for p in probs]
        set_sizes = [len(s) for s in sets]
        
        # Empirical coverage: true label in conformal set
        covered = [y in s for y, s in zip(y_true, sets)]
        calc_cov = round(float(np.mean(covered)), 4)
        calc_size = round(float(np.mean(set_sizes)), 3)
        
        cov_diff = abs(calc_cov - rep_cov)
        size_diff = abs(calc_size - rep_size)
        passed = (cov_diff <= 0.002 and size_diff <= 0.01)
        if not passed:
            all_passed = False
            
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] Model {key:7s}: calc_cov={calc_cov:.4f} (rep={rep_cov:.4f}), calc_size={calc_size:.3f} (rep={rep_size:.3f})")
        
    return all_passed

if __name__ == "__main__":
    success = verify_conformal()
    print("\nSummary:", "ALL PASSED" if success else "FAILURES DETECTED")
    exit(0 if success else 1)
