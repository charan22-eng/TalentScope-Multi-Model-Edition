import json
from pathlib import Path
import numpy as np

ROOT = Path(".")

PROFILES = {
    "Balanced": {
        "macro_f1": 0.30, "qwk": 0.10, "calibration": 0.10, "robustness": 0.10,
        "fairness": 0.10, "stability": 0.05, "latency": 0.05, "train_cost": 0.05, "explainability": 0.15
    },
    "Accuracy-first": {
        "macro_f1": 0.50, "qwk": 0.15, "calibration": 0.10, "robustness": 0.10,
        "fairness": 0.05, "stability": 0.05, "latency": 0.02, "train_cost": 0.01, "explainability": 0.02
    },
    "Explainability-first": {
        "macro_f1": 0.20, "qwk": 0.05, "calibration": 0.10, "robustness": 0.05,
        "fairness": 0.10, "stability": 0.05, "latency": 0.05, "train_cost": 0.05, "explainability": 0.35
    },
    "Speed-first": {
        "macro_f1": 0.20, "qwk": 0.05, "calibration": 0.05, "robustness": 0.05,
        "fairness": 0.05, "stability": 0.05, "latency": 0.30, "train_cost": 0.20, "explainability": 0.05
    },
    "Fairness-first": {
        "macro_f1": 0.20, "qwk": 0.05, "calibration": 0.10, "robustness": 0.10,
        "fairness": 0.35, "stability": 0.05, "latency": 0.05, "train_cost": 0.05, "explainability": 0.05
    }
}

CRITERIA_DIRECTION = {
    "macro_f1": "maximize", "qwk": "maximize", "calibration": "maximize",
    "robustness": "maximize", "fairness": "maximize", "stability": "maximize",
    "latency": "minimize", "train_cost": "minimize", "explainability": "maximize"
}

def verify_mcda():
    leaderboard_file = ROOT / "artifacts/v2/comparison/leaderboard.json"
    if not leaderboard_file.exists():
        print(f"[FAIL] Missing {leaderboard_file}")
        return False

    with open(leaderboard_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    models_data = data.get("metrics", [])
    keys = [m["key"] for m in models_data]
    
    # Extract criteria matrix
    raw_matrix = {}
    for crit in CRITERIA_DIRECTION:
        vals = []
        for m in models_data:
            val = m.get(crit, 0.0)
            vals.append(float(val))
        raw_matrix[crit] = np.array(vals)

    # Normalize criteria
    norm_matrix = {}
    for crit, direction in CRITERIA_DIRECTION.items():
        v = raw_matrix[crit]
        v_min, v_max = float(v.min()), float(v.max())
        denom = v_max - v_min if (v_max - v_min) > 1e-9 else 1.0
        if direction == "maximize":
            norm_matrix[crit] = (v - v_min) / denom
        else:
            norm_matrix[crit] = (v_max - v) / denom

    print("--- Independent 5-Profile MCDA Rankings ---")
    all_ranks = {}
    for prof_name, weights in PROFILES.items():
        w_sum = sum(weights.values())
        scores = np.zeros(len(keys))
        for crit, w in weights.items():
            scores += (w / w_sum) * norm_matrix[crit]
        
        # Sort descending
        ranked_indices = np.argsort(-scores)
        ranked_keys = [keys[i] for i in ranked_indices]
        winner = ranked_keys[0]
        runner_up = ranked_keys[1]
        all_ranks[prof_name] = ranked_keys
        print(f"Profile {prof_name:20s}: Winner={winner:7s} (Score={scores[ranked_indices[0]]:.4f}), Runner-up={runner_up:7s} (Score={scores[ranked_indices[1]]:.4f})")

    # Load stored mcda.json for Balanced profile
    stored_mcda_file = ROOT / "artifacts/v2/comparison/mcda.json"
    if stored_mcda_file.exists():
        with open(stored_mcda_file, "r", encoding="utf-8") as f:
            stored_mcda = json.load(f)
        rep_winner = stored_mcda.get("deterministic_winner")
        rep_ranks = [r["key"] for r in stored_mcda.get("ranking", [])]
        calc_ranks = all_ranks["Balanced"]
        match = (rep_ranks == calc_ranks)
        print(f"\n[Balanced Profile Verification]:")
        print(f"Reported Ranks : {rep_ranks}")
        print(f"Calculated Ranks: {calc_ranks}")
        print(f"Rank Match: {'PASS' if match else 'FAIL'}")
        return match
    return True

if __name__ == "__main__":
    success = verify_mcda()
    exit(0 if success else 1)
