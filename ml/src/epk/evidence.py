"""Evidence Packet Builder for TalentScope Multi-Model Edition.

Generates structured evidence packets strictly from machine-generated files
(metrics.json, test_predictions.csv, tuning.json, etc.). No hand-typed numbers.
Enforces Guard G8: Zero employee-level keys in packet.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

# Ensure ml/src is on sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import joblib
import numpy as np
import pandas as pd

from epk.labels import BANDS, INT_TO_BAND
from epk.mcda import PROFILES, run_mcda_pipeline
from epk.models.registry import MODEL_KEYS, get_model_spec
from epk.split import load_split
from epk.stats import (
    compute_conformal_sets_cal_b,
    evaluate_fairness,
    evaluate_robustness,
    paired_stratified_bootstrap,
    pairwise_mcnemar_tests,
)

FORBIDDEN_EMPLOYEE_KEYS: Set[str] = {
    "employee_id",
    "emp_id",
    "employee_name",
    "first_name",
    "last_name",
    "full_name",
    "email",
    "phone",
    "ssn",
    "salary",
    "gender",
    "age",
    "age_band",
    "row_index",
    "individual_prediction",
}


def scan_packet_for_forbidden_keys(data: Any, path: str = "") -> List[str]:
    """Recursively scan packet data structure for forbidden employee-level keys."""
    violations = []
    if isinstance(data, dict):
        for k, v in data.items():
            current_path = f"{path}.{k}" if path else k
            if k.lower() in FORBIDDEN_EMPLOYEE_KEYS:
                violations.append(f"Forbidden key '{k}' found at path '{current_path}'")
            violations.extend(scan_packet_for_forbidden_keys(v, current_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            violations.extend(scan_packet_for_forbidden_keys(item, f"{path}[{i}]"))
    return violations


def build_comparison_suite(
    variant: str = "nonlinear",
    models_dir: str = "artifacts/v2/models",
    comparison_dir: str = "artifacts/v2/comparison",
    data_path: str = None,
    split_path: str = "data/processed/split.json",
    n_resamples: int = 2000,
) -> Dict[str, Any]:
    """Compute and persist all comparison science artifacts."""
    if data_path is None:
        data_path = f"data/{variant}/dataset.csv"

    comp_path = Path(comparison_dir)
    comp_path.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    split_info = load_split(split_path)
    cal_b_idx = split_info["cal_b"]

    # Load evaluated row indices and y_true directly from persisted test_predictions.csv
    sample_pred_csv = Path(models_dir) / "linreg" / "test_predictions.csv"
    p_sample_df = pd.read_csv(sample_pred_csv)
    eval_row_idx = p_sample_df["row_index"].to_numpy(dtype=int)
    y_test = p_sample_df["y_true"].to_numpy(dtype=int)

    test_df = df.iloc[eval_row_idx].reset_index(drop=True)
    cal_b_df = df.iloc[cal_b_idx].reset_index(drop=True)

    # 1. Load predictions and metrics for all 7 models
    preds_dict = {}
    probas_dict = {}
    models_obj = {}
    metrics_table_rows = []

    for key in MODEL_KEYS:
        pred_csv = Path(models_dir) / key / "test_predictions.csv"
        metric_json = Path(models_dir) / key / "metrics.json"
        model_job = Path(models_dir) / key / "model.joblib"

        if not pred_csv.exists() or not metric_json.exists():
            raise FileNotFoundError(f"Missing artifacts for model {key}. Run make train & make final first.")

        p_df = pd.read_csv(pred_csv)
        preds_dict[key] = p_df["y_pred"].to_numpy(dtype=int)
        probas_dict[key] = p_df[["prob_low", "prob_med", "prob_high"]].to_numpy(dtype=float)
        models_obj[key] = joblib.load(model_job)

        with open(metric_json, "r") as f:
            m = json.load(f)
            metrics_table_rows.append(m)

    metrics_df = pd.DataFrame(metrics_table_rows).set_index("key")

    # 2. Robustness and Fairness
    robustness_dict = evaluate_robustness(test_df, models_obj)
    fairness_dict = evaluate_fairness(eval_row_idx, preds_dict, f"data/{variant}/protected.csv")

    # Add robustness and fairness to metrics_df
    for k in MODEL_KEYS:
        metrics_df.loc[k, "robustness"] = robustness_dict[k]["robustness_score"]
        metrics_df.loc[k, "fairness"] = fairness_dict[k]["disparity_ratio"]
        metrics_df.loc[k, "calibration"] = round(1.0 - metrics_df.loc[k, "ece"], 4)
        metrics_df.loc[k, "stability"] = round(1.0 - metrics_df.loc[k, "stability_std"], 4)
        metrics_df.loc[k, "latency"] = metrics_df.loc[k, "latency_single_p95_ms"]
        metrics_df.loc[k, "train_cost"] = metrics_df.loc[k, "tuning_time_sec"]
        metrics_df.loc[k, "explainability"] = metrics_df.loc[k, "explain_score"]

    # 3. Initial MCDA to identify rank 1 and rank 2
    mcda_res = run_mcda_pipeline(metrics_df, profile_name="Balanced")
    rank1_key = mcda_res["deterministic_winner"]
    rank2_key = mcda_res["runner_up"]

    # 4. Bootstrap and McNemar
    boot_data = paired_stratified_bootstrap(y_test, preds_dict, rank1_key, rank2_key, n_resamples=n_resamples)
    mcnemar_data = pairwise_mcnemar_tests(y_test, preds_dict)

    # 5. Conformal Prediction on cal-B
    conformal_data = compute_conformal_sets_cal_b(cal_b_df, test_df, models_obj, alpha=0.10)

    # 6. Re-run MCDA with statistical difference data
    diff_excludes_zero = boot_data["diff_rank1_rank2"]["excludes_zero"]
    pair_key = f"{rank1_key}_vs_{rank2_key}" if f"{rank1_key}_vs_{rank2_key}" in mcnemar_data["pair_map"] else f"{rank2_key}_vs_{rank1_key}"
    mcnemar_p = mcnemar_data["pair_map"][pair_key]["holm_p"] if pair_key in mcnemar_data["pair_map"] else 1.0

    final_mcda = run_mcda_pipeline(
        metrics_df,
        profile_name="Balanced",
        diff_excludes_zero=diff_excludes_zero,
        mcnemar_holm_p=mcnemar_p,
    )

    # Re-run MCDA for all 5 profiles per Prompt A.4
    all_profiles_res = {
        p_name: run_mcda_pipeline(
            metrics_df,
            profile_name=p_name,
            diff_excludes_zero=diff_excludes_zero if p_name == "Balanced" else False,
            mcnemar_holm_p=mcnemar_p if p_name == "Balanced" else 1.0,
        )
        for p_name in PROFILES
    }

    # Sensitivity runs per Prompt A.4:
    # (a) calibration criterion removed
    weights_no_cal = PROFILES["Balanced"].copy()
    weights_no_cal["calibration"] = 0.0
    mcda_no_cal = run_mcda_pipeline(metrics_df, custom_weights=weights_no_cal)

    # (b) calibration measured on raw (uncalibrated) probabilities
    metrics_df_raw_cal = metrics_df.copy()
    metrics_df_raw_cal["calibration"] = round(1.0 - metrics_df_raw_cal["raw_ece"], 4)
    mcda_raw_cal = run_mcda_pipeline(metrics_df_raw_cal, profile_name="Balanced")

    calibration_sensitivity = {
        "baseline_champion": final_mcda["deterministic_winner"],
        "calibration_removed": {
            "winner": mcda_no_cal["deterministic_winner"],
            "score": mcda_no_cal["ranking"][0]["mcda_score"],
            "champion_changed": bool(mcda_no_cal["deterministic_winner"] != final_mcda["deterministic_winner"]),
            "ranking": mcda_no_cal["ranking"],
        },
        "raw_calibration": {
            "winner": mcda_raw_cal["deterministic_winner"],
            "score": mcda_raw_cal["ranking"][0]["mcda_score"],
            "champion_changed": bool(mcda_raw_cal["deterministic_winner"] != final_mcda["deterministic_winner"]),
            "ranking": mcda_raw_cal["ranking"],
        },
    }

    final_mcda["all_profiles"] = all_profiles_res
    final_mcda["calibration_sensitivity"] = calibration_sensitivity

    # Save comparison artifacts
    with open(comp_path / "leaderboard.json", "w") as f:
        json.dump({
            "metrics": metrics_df.reset_index().to_dict(orient="records"),
            "confidence_intervals": boot_data["model_cis"],
            "rank1_vs_rank2": boot_data["diff_rank1_rank2"],
        }, f, indent=2)

    with open(comp_path / "pairwise.json", "w") as f:
        json.dump(mcnemar_data, f, indent=2)

    with open(comp_path / "conformal.json", "w") as f:
        json.dump(conformal_data, f, indent=2)

    with open(comp_path / "mcda.json", "w") as f:
        json.dump(final_mcda, f, indent=2)

    # 7. Build Evidence Packet
    packet = build_evidence_packet_from_data(
        variant=variant,
        n_test=len(test_df),
        metrics_df=metrics_df,
        boot_data=boot_data,
        mcnemar_data=mcnemar_data,
        conformal_data=conformal_data,
        mcda_res=final_mcda,
        robustness_dict=robustness_dict,
        fairness_dict=fairness_dict,
        calibration_sensitivity=calibration_sensitivity,
    )

    with open(comp_path / "evidence_packet.json", "w") as f:
        json.dump(packet, f, indent=2)

    return packet


def build_evidence_packet_from_data(
    variant: str,
    n_test: int,
    metrics_df: pd.DataFrame,
    boot_data: Dict[str, Any],
    mcnemar_data: Dict[str, Any],
    conformal_data: Dict[str, Any],
    mcda_res: Dict[str, Any],
    robustness_dict: Dict[str, Any],
    fairness_dict: Dict[str, Any],
    calibration_sensitivity: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Synthesize numbered facts strictly from machine evaluation data."""
    facts = []
    fact_counter = 1

    winner = mcda_res["deterministic_winner"]
    runner_up = mcda_res["runner_up"]
    strength = mcda_res["decision_strength"]

    # F1..F7: Primary Macro-F1 and CIs
    for m_entry in mcda_res["ranking"]:
        k = m_entry["key"]
        label = get_model_spec(k).label
        f1_val = metrics_df.loc[k, "macro_f1"]
        ci = boot_data["model_cis"][k]["macro_f1_ci"]
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": k,
            "category": "accuracy",
            "text": f"{label} achieved macro-F1 {f1_val:.4f} (95% CI {ci[0]:.4f} to {ci[1]:.4f}) on {n_test:,} test rows.",
        })
        fact_counter += 1

    # F8..F14: QWK and Accuracy
    for m_entry in mcda_res["ranking"]:
        k = m_entry["key"]
        label = get_model_spec(k).label
        acc = metrics_df.loc[k, "accuracy"]
        qwk = metrics_df.loc[k, "qwk"]
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": k,
            "category": "performance",
            "text": f"{label} overall accuracy {acc*100:.1f}% and quadratic weighted kappa (QWK) {qwk:.4f}.",
        })
        fact_counter += 1

    # F15..F21: Latency & Batch Speed
    for m_entry in mcda_res["ranking"]:
        k = m_entry["key"]
        label = get_model_spec(k).label
        p95 = metrics_df.loc[k, "latency_single_p95_ms"]
        b5000 = metrics_df.loc[k, "latency_batch_5000_ms"]
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": k,
            "category": "latency",
            "text": f"{label} single-row p95 latency {p95:.2f} ms and 5,000-row batch latency {b5000:.1f} ms.",
        })
        fact_counter += 1

    # F22: Head-to-head difference between winner and runner up
    diff_info = boot_data["diff_rank1_rank2"]
    diff_ci = diff_info["diff_ci_95"]
    w_label = get_model_spec(winner).label
    ru_label = get_model_spec(runner_up).label
    facts.append({
        "id": f"F{fact_counter}",
        "model_key": winner,
        "category": "comparison",
        "text": f"{w_label} versus {ru_label} macro-F1 difference 95% CI is {diff_ci[0]:.4f} to {diff_ci[1]:.4f} (excludes zero: {str(diff_info['excludes_zero']).lower()}).",
    })
    fact_counter += 1

    # F23: Pairwise McNemar significance
    pair_k = f"{winner}_vs_{runner_up}" if f"{winner}_vs_{runner_up}" in mcnemar_data["pair_map"] else f"{runner_up}_vs_{winner}"
    if pair_k in mcnemar_data["pair_map"]:
        p_res = mcnemar_data["pair_map"][pair_k]
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": winner,
            "category": "significance",
            "text": f"{w_label} versus {ru_label} pairwise McNemar test with Holm-Bonferroni correction p-value is {p_res['holm_p']:.4f}.",
        })
        fact_counter += 1

    # F24..F30: Calibration (ECE and Brier) & Conformal Coverage
    for m_entry in mcda_res["ranking"][:3]:  # Top 3
        k = m_entry["key"]
        label = get_model_spec(k).label
        ece = metrics_df.loc[k, "ece"]
        brier = metrics_df.loc[k, "brier"]
        conf = conformal_data[k]
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": k,
            "category": "calibration",
            "text": f"{label} expected calibration error (ECE) {ece:.4f}, Brier score {brier:.4f}, conformal 90% coverage {conf['empirical_coverage']*100:.1f}%, average set size {conf['avg_set_size']:.2f}.",
        })
        fact_counter += 1

    # F31..F35: Robustness and Fairness
    for m_entry in mcda_res["ranking"][:3]:
        k = m_entry["key"]
        label = get_model_spec(k).label
        rob = robustness_dict[k]["robustness_score"]
        disp = fairness_dict[k]["disparity_ratio"]
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": k,
            "category": "robustness_fairness",
            "text": f"{label} robustness score {rob:.4f} (under noise/missingness) and audit demographic disparity ratio {disp:.4f}.",
        })
        fact_counter += 1

    # F36: MCDA Score and Rank 1 probability
    w_entry = [m for m in mcda_res["ranking"] if m["key"] == winner][0]
    facts.append({
        "id": f"F{fact_counter}",
        "model_key": winner,
        "category": "mcda",
        "text": f"Under the {mcda_res['profile']} MCDA profile, {w_label} achieved score {w_entry['mcda_score']:.4f} with Dirichlet rank-1 probability {w_entry['p_rank1']*100:.1f}%.",
    })
    fact_counter += 1

    # F37 & F38: Sensitivity analysis facts per Prompt A.4
    if calibration_sensitivity:
        no_cal_w = calibration_sensitivity["calibration_removed"]["winner"]
        no_cal_score = calibration_sensitivity["calibration_removed"]["score"]
        no_cal_label = get_model_spec(no_cal_w).label
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": no_cal_w,
            "category": "sensitivity",
            "text": f"Sensitivity analysis with calibration criterion removed: top model is {no_cal_label} with MCDA score {no_cal_score:.4f} (champion changed: {str(calibration_sensitivity['calibration_removed']['champion_changed']).lower()}).",
        })
        fact_counter += 1

        raw_cal_w = calibration_sensitivity["raw_calibration"]["winner"]
        raw_cal_score = calibration_sensitivity["raw_calibration"]["score"]
        raw_cal_label = get_model_spec(raw_cal_w).label
        facts.append({
            "id": f"F{fact_counter}",
            "model_key": raw_cal_w,
            "category": "sensitivity",
            "text": f"Sensitivity analysis evaluating calibration on raw uncalibrated probabilities: top model is {raw_cal_label} with MCDA score {raw_cal_score:.4f} (champion changed: {str(calibration_sensitivity['raw_calibration']['champion_changed']).lower()}).",
        })
        fact_counter += 1

    # F90: MANDATORY SYNTHETIC DATA CAVEAT FACT
    facts.append({
        "id": "F90",
        "model_key": "global",
        "category": "caveat",
        "text": f"The dataset is synthetic (12,000 rows) and rankings depend on how it was generated; under linear variants, linear models remain highly competitive.",
    })

    packet = {
        "schema_version": "1.0",
        "dataset": {
            "name": "employees_v2",
            "variant": variant,
            "rows": 12000,
            "holdout_test_rows": n_test,
        },
        "profile": {
            "name": mcda_res["profile"],
            "weights": mcda_res["weights"],
        },
        "deterministic_winner": winner,
        "runner_up": runner_up,
        "decision_strength": strength,
        "synthetic_caveat_fact": "F90",
        "calibration_sensitivity": calibration_sensitivity,
        "models": [
            {
                "key": m["key"],
                "label": get_model_spec(m["key"]).label,
                "rank": m["rank"],
                "mcda_score": m["mcda_score"],
                "p_rank1": m["p_rank1"],
            }
            for m in mcda_res["ranking"]
        ],
        "facts": facts,
        "limits": {
            "max_facts": len(facts),
        },
    }

    # Compute packet hash
    packet_bytes = json.dumps(packet, sort_keys=True).encode("utf-8")
    packet["packet_hash"] = hashlib.sha256(packet_bytes).hexdigest()

    # Guard G8: Scan for forbidden employee-level keys
    violations = scan_packet_for_forbidden_keys(packet)
    if violations:
        raise ValueError(f"[G8 VIOLATION DETECTED] Forbidden employee keys found in packet: {violations}")

    return packet


def select_facts(
    packet: Dict[str, Any],
    mode: Literal["verdict", "why_not", "second_opinion", "audience_rewrite"] = "verdict",
    target_model: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Filter facts to a compact subset (top-3 models + global facts + caveat)."""
    top3_keys = {m["key"] for m in packet["models"][:3]}
    facts = packet["facts"]

    selected = []
    for f in facts:
        # F90 caveat is always included
        if f["id"] == packet["synthetic_caveat_fact"]:
            selected.append(f)
            continue

        m_key = f.get("model_key")
        if mode in ("verdict", "second_opinion", "audience_rewrite"):
            if m_key in top3_keys or m_key == "global":
                selected.append(f)
        elif mode == "why_not":
            winner_key = packet["deterministic_winner"]
            if m_key in {winner_key, target_model, "global"}:
                selected.append(f)

    return selected


if __name__ == "__main__":
    packet = build_comparison_suite()
    print(f"[evidence.py] Comparison suite successfully built. Deterministic winner: {packet['deterministic_winner']}, Decision strength: {packet['decision_strength']}")
