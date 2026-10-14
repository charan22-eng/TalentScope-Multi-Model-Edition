"""run_sensitivity_profiles.py — Execute omitted sensitivity runs across all 5 profiles per FF4 Item 4.

Scenarios:
(a) Calibration criterion removed (weight = 0.0, re-normalised)
(b) Calibration measured on raw probabilities (raw ECE)

Across all 5 profiles: Balanced, Accuracy-first, Explainability-first, Speed-first, Fairness-first.
Updates sensitivity.json and evidence_packet.json.
"""

import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml" / "src"))

from epk.mcda import PROFILES, HIGHER_IS_BETTER, mcda_rank, rank_probability, compute_decision_strength

def main():
    lb_path = ROOT / "artifacts" / "v2" / "comparison" / "leaderboard.json"
    with open(lb_path, "r", encoding="utf-8") as f:
        lb_data = json.load(f)

    metrics_list = lb_data["metrics"]
    df = pd.DataFrame(metrics_list).set_index("key")

    criteria = [
        "macro_f1", "qwk", "calibration", "robustness", "fairness",
        "stability", "latency", "train_cost", "explainability"
    ]

    base_table = df[criteria].copy()

    # Raw calibration table
    raw_cal_table = base_table.copy()
    raw_cal_table["calibration"] = 1.0 - df["raw_ece"]

    print("=" * 90)
    print("OMITTED SENSITIVITY RUNS ACROSS ALL 5 PROFILES")
    print("Statement: boost and svm are statistically tied under default balanced; winner depends on priorities.")
    print("=" * 90)

    results = {
        "statement": "boost and svm are statistically tied under default balanced (composite margin 0.0090, decision strength none); the winner depends on organizational priorities.",
        "profiles": {},
    }

    for prof_name, base_w in PROFILES.items():
        print(f"\n--- Profile: {prof_name} ---")

        # 1. Baseline
        base_ranks = mcda_rank(base_table, base_w)
        base_p_r1 = rank_probability(base_table, base_w, seed=42)
        base_merged = base_ranks.join(base_p_r1).sort_values("rank")
        base_winner = base_merged.index[0]
        base_score = float(base_merged.loc[base_winner, "mcda_score"])
        base_pr1 = float(base_merged.loc[base_winner, "p_rank1"])

        # 2. Scenario (a): Calibration removed (weight = 0)
        no_cal_w = base_w.copy()
        no_cal_w["calibration"] = 0.0
        no_cal_ranks = mcda_rank(base_table, no_cal_w)
        no_cal_p_r1 = rank_probability(base_table, no_cal_w, seed=42)
        no_cal_merged = no_cal_ranks.join(no_cal_p_r1).sort_values("rank")
        no_cal_winner = no_cal_merged.index[0]
        no_cal_runner = no_cal_merged.index[1]
        no_cal_score = float(no_cal_merged.loc[no_cal_winner, "mcda_score"])
        no_cal_runner_score = float(no_cal_merged.loc[no_cal_runner, "mcda_score"])
        no_cal_pr1 = float(no_cal_merged.loc[no_cal_winner, "p_rank1"])
        no_cal_changed = bool(no_cal_winner != base_winner)

        # 3. Scenario (b): Raw calibration ECE
        raw_cal_ranks = mcda_rank(raw_cal_table, base_w)
        raw_cal_p_r1 = rank_probability(raw_cal_table, base_w, seed=42)
        raw_cal_merged = raw_cal_ranks.join(raw_cal_p_r1).sort_values("rank")
        raw_cal_winner = raw_cal_merged.index[0]
        raw_cal_runner = raw_cal_merged.index[1]
        raw_cal_score = float(raw_cal_merged.loc[raw_cal_winner, "mcda_score"])
        raw_cal_runner_score = float(raw_cal_merged.loc[raw_cal_runner, "mcda_score"])
        raw_cal_pr1 = float(raw_cal_merged.loc[raw_cal_winner, "p_rank1"])
        raw_cal_changed = bool(raw_cal_winner != base_winner)

        print(f"  Baseline           : Winner = {base_winner:7s} ({base_score:.4f}) | Rank-1 Prob = {base_pr1*100:5.1f}%")
        print(f"  (a) Cal Removed    : Winner = {no_cal_winner:7s} ({no_cal_score:.4f}) | Runner = {no_cal_runner:7s} ({no_cal_runner_score:.4f}) | Rank-1 Prob = {no_cal_pr1*100:5.1f}% | Changed = {no_cal_changed}")
        print(f"  (b) Raw Calibrated : Winner = {raw_cal_winner:7s} ({raw_cal_score:.4f}) | Runner = {raw_cal_runner:7s} ({raw_cal_runner_score:.4f}) | Rank-1 Prob = {raw_cal_pr1*100:5.1f}% | Changed = {raw_cal_changed}")

        results["profiles"][prof_name] = {
            "baseline": {
                "winner": base_winner,
                "score": base_score,
                "rank1_probability": base_pr1,
                "ranking": [
                    {"key": k, "rank": int(base_merged.loc[k, "rank"]), "mcda_score": float(base_merged.loc[k, "mcda_score"]), "p_rank1": float(base_merged.loc[k, "p_rank1"])}
                    for k in base_merged.index
                ]
            },
            "calibration_removed": {
                "winner": no_cal_winner,
                "score": no_cal_score,
                "runner_up": no_cal_runner,
                "runner_up_score": no_cal_runner_score,
                "rank1_probability": no_cal_pr1,
                "champion_changed": no_cal_changed,
                "ranking": [
                    {"key": k, "rank": int(no_cal_merged.loc[k, "rank"]), "mcda_score": float(no_cal_merged.loc[k, "mcda_score"]), "p_rank1": float(no_cal_merged.loc[k, "p_rank1"])}
                    for k in no_cal_merged.index
                ]
            },
            "raw_calibration": {
                "winner": raw_cal_winner,
                "score": raw_cal_score,
                "runner_up": raw_cal_runner,
                "runner_up_score": raw_cal_runner_score,
                "rank1_probability": raw_cal_pr1,
                "champion_changed": raw_cal_changed,
                "ranking": [
                    {"key": k, "rank": int(raw_cal_merged.loc[k, "rank"]), "mcda_score": float(raw_cal_merged.loc[k, "mcda_score"]), "p_rank1": float(raw_cal_merged.loc[k, "p_rank1"])}
                    for k in raw_cal_merged.index
                ]
            }
        }

    # Update sensitivity.json
    sens_path = ROOT / "artifacts" / "v2" / "comparison" / "sensitivity.json"
    with open(sens_path, "r", encoding="utf-8") as f:
        sens_data = json.load(f)

    sens_data["calibration_sensitivity"] = {
        "statement": results["statement"],
        "baseline_champion": "boost",
        "profiles": results["profiles"],
        # Backwards compatible shortcuts for Balanced profile
        "calibration_removed": results["profiles"]["Balanced"]["calibration_removed"],
        "raw_calibration": results["profiles"]["Balanced"]["raw_calibration"],
    }

    with open(sens_path, "w", encoding="utf-8") as f:
        json.dump(sens_data, f, indent=2)
    print(f"\nUpdated {sens_path}")

    # Update evidence_packet.json
    ev_path = ROOT / "artifacts" / "v2" / "comparison" / "evidence_packet.json"
    with open(ev_path, "r", encoding="utf-8") as f:
        ev_data = json.load(f)

    ev_data["calibration_sensitivity"] = {
        "statement": results["statement"],
        "baseline_champion": "boost",
        "profiles": results["profiles"],
        "calibration_removed": results["profiles"]["Balanced"]["calibration_removed"],
        "raw_calibration": results["profiles"]["Balanced"]["raw_calibration"],
    }

    with open(ev_path, "w", encoding="utf-8") as f:
        json.dump(ev_data, f, indent=2)
    print(f"Updated {ev_path}")

if __name__ == "__main__":
    main()
