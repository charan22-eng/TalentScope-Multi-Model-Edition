"""Single test-split evaluation harness with G6 lock for TalentScope Multi-Model Edition.

The held-out test split is evaluated ONCE per final configuration.
Writes reports/test_eval.lock and refuses to run again for the same key.
Enforces Guard G6:
- Only this file reads test_indices
- Refuses repeat runs without --new-config "<reason>"
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure ml/src is on sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import joblib
import numpy as np
import pandas as pd
from scipy.special import softmax
from scipy.stats import spearmanr
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    log_loss,
    matthews_corrcoef,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_fscore_support,
    r2_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize

from epk.features import ALL_FEATURES
from epk.labels import BANDS, INT_TO_BAND, decode_bands, encode_bands
from epk.models.registry import MODEL_KEYS, get_model_spec
from epk.split import load_split


def compute_ece(y_true: np.ndarray, probas: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) across multi-class predictions."""
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


def check_and_acquire_g6_lock(
    lock_path: str = "reports/test_eval.lock",
    log_path: str = "reports/test_eval_log.csv",
    variant: str = "nonlinear",
    dataset_hash: str = "",
    split_hash: str = "",
    new_config_reason: str = None,
) -> str:
    """Enforce G6 Test-Set-Once lock invariant."""
    lock_file = Path(lock_path)
    config_hash = hashlib.sha256(f"{variant}:{dataset_hash}:{split_hash}".encode("utf-8")).hexdigest()

    if lock_file.exists():
        with open(lock_file, "r") as f:
            existing_lock = json.load(f)

        is_same_config = (
            existing_lock.get("variant") == variant
            and existing_lock.get("dataset_hash") == dataset_hash
            and existing_lock.get("split_hash") == split_hash
        )

        if is_same_config and not new_config_reason:
            raise RuntimeError(
                f"[G6 VIOLATION PREVENTED] Test evaluation has ALREADY been executed for this configuration "
                f"(variant={variant}, timestamp={existing_lock.get('utc_time')}). "
                f"The test set must never be evaluated twice without an explicit --new-config '<reason>'."
            )

        if new_config_reason:
            log_file = Path(log_path)
            log_entry = {
                "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "variant": variant,
                "config_hash": config_hash,
                "reason": new_config_reason,
            }
            log_df = pd.DataFrame([log_entry])
            if log_file.exists():
                prev_log = pd.read_csv(log_file)
                combined = pd.concat([prev_log, log_df], ignore_index=True)
            else:
                combined = log_df
            combined.to_csv(log_file, index=False, lineterminator="\n")
            print(f"[G6] Re-evaluating test split under --new-config reason: '{new_config_reason}'")

    # Write new lock
    lock_data = {
        "variant": variant,
        "config_hash": config_hash,
        "dataset_hash": dataset_hash,
        "split_hash": split_hash,
        "utc_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file, "w") as f:
        json.dump(lock_data, f, indent=2)

    return config_hash


def run_final_evaluation(
    variant: str = "nonlinear",
    data_path: str = None,
    split_path: str = "data/processed/split.json",
    models_dir: str = "artifacts/v2/models",
    new_config: str = None,
) -> Dict[str, Any]:
    """Perform single test-split evaluation for all 7 models."""
    if data_path is None:
        data_path = f"data/{variant}/dataset.csv"

    print(f"\n============================================================")
    print(f"TALENTSCOPE FINAL TEST EVALUATION [make final, variant={variant}]")
    print(f"============================================================")

    # 1. Load dataset & split
    df = pd.read_csv(data_path)
    with open(data_path, "rb") as f:
        dataset_hash = hashlib.sha256(f.read()).hexdigest()

    split_info = load_split(split_path)
    test_indices = split_info["test"]
    split_hash = split_info["split_hash"]

    # 2. Enforce G6 lock
    config_hash = check_and_acquire_g6_lock(
        variant=variant,
        dataset_hash=dataset_hash,
        split_hash=split_hash,
        new_config_reason=new_config,
    )

    X_test = df[ALL_FEATURES].iloc[test_indices].reset_index(drop=True)
    y_test_band = encode_bands(df["performance"].iloc[test_indices])
    y_test_score = df["performance_score"].iloc[test_indices].to_numpy(dtype=float)
    y_bin = label_binarize(y_test_band, classes=[0, 1, 2])
    n_test = len(test_indices)

    print(f"Test split size: {n_test} rows")
    results = {}

    for key in MODEL_KEYS:
        model_path = Path(models_dir) / key / "model.joblib"
        tuning_path = Path(models_dir) / key / "tuning.json"

        if not model_path.exists():
            raise FileNotFoundError(f"Missing trained model for '{key}' at {model_path}. Run make train first.")

        model = joblib.load(model_path)
        spec = get_model_spec(key)

        with open(tuning_path, "r") as f:
            tuning_meta = json.load(f)

        # Predict (calibrated)
        y_pred = model.predict(X_test)
        probas = model.predict_proba(X_test)

        # Unwrapped raw estimator for dual reporting
        if hasattr(model, "calibrated_classifiers_"):
            raw_pipe = model.calibrated_classifiers_[0].estimator
        elif hasattr(model, "estimator") and not hasattr(model, "named_steps"):
            raw_pipe = model.estimator
        else:
            raw_pipe = model

        raw_pred = raw_pipe.predict(X_test)
        if hasattr(raw_pipe, "predict_proba"):
            raw_probas = raw_pipe.predict_proba(X_test)
        elif hasattr(raw_pipe, "decision_function"):
            df_dec = raw_pipe.decision_function(X_test)
            if df_dec.ndim == 1:
                df_dec = np.vstack([-df_dec, df_dec]).T
            raw_probas = softmax(df_dec, axis=1)
        else:
            raw_probas = probas

        raw_acc = float(accuracy_score(y_test_band, raw_pred))
        raw_macro_f1 = float(f1_score(y_test_band, raw_pred, average="macro"))
        raw_ll = float(log_loss(y_test_band, raw_probas, labels=[0, 1, 2]))
        raw_brier = float(np.mean(np.sum((raw_probas - y_bin) ** 2, axis=1)))
        raw_ece = compute_ece(y_test_band, raw_probas, n_bins=10)

        # G3 invariant assertion: classes_ == [0, 1, 2]
        assert hasattr(model, "classes_"), f"Model {key} lacks classes_"
        np.testing.assert_array_equal(model.classes_, np.array([0, 1, 2]))

        # Metrics calculation
        acc = float(accuracy_score(y_test_band, y_pred))
        bal_acc = float(balanced_accuracy_score(y_test_band, y_pred))
        macro_f1 = float(f1_score(y_test_band, y_pred, average="macro"))
        qwk = float(cohen_kappa_score(y_test_band, y_pred, weights="quadratic"))
        mcc = float(matthews_corrcoef(y_test_band, y_pred))

        # Precision, recall, f1 per class
        p_c, r_c, f_c, sup_c = precision_recall_fscore_support(y_test_band, y_pred, labels=[0, 1, 2])
        per_class = {
            INT_TO_BAND[c]: {
                "precision": round(float(p_c[c]), 4),
                "recall": round(float(r_c[c]), 4),
                "f1": round(float(f_c[c]), 4),
                "support": int(sup_c[c]),
            }
            for c in range(3)
        }

        # Prepare test_predictions DataFrame with exact precision
        preds_df = pd.DataFrame({
            "row_index": test_indices,
            "y_true": y_test_band,
            "y_pred": y_pred,
            "prob_low": np.round(probas[:, 0], 5),
            "prob_med": np.round(probas[:, 1], 5),
            "prob_high": np.round(probas[:, 2], 5),
        })
        probas_eval = preds_df[["prob_low", "prob_med", "prob_high"]].to_numpy()

        # Probabilistic metrics on exact exported values
        ll = float(log_loss(y_test_band, probas_eval, labels=[0, 1, 2]))
        brier = float(np.mean(np.sum((probas_eval - y_bin) ** 2, axis=1)))
        ece = compute_ece(y_test_band, probas_eval, n_bins=10)
        roc_ovr = float(roc_auc_score(y_bin, probas_eval, multi_class="ovr", average="macro"))

        # Ordinal error breakdown
        diff = np.abs(y_test_band - y_pred)
        exact_err = float(np.mean(diff == 0))
        adj_err = float(np.mean(diff == 1))
        ext_err = float(np.mean(diff == 2))

        # Latency benchmarking
        sample_rows = X_test.iloc[:100]
        single_times = []
        for i in range(100):
            row_df = sample_rows.iloc[[i]]
            t_start = time.perf_counter()
            _ = model.predict(row_df)
            single_times.append((time.perf_counter() - t_start) * 1000.0)

        latency_p50 = float(np.percentile(single_times, 50))
        latency_p95 = float(np.percentile(single_times, 95))

        # Batch 5000 latency
        repeats = int(np.ceil(5000 / len(X_test)))
        batch_5000 = pd.concat([X_test] * repeats, ignore_index=True).iloc[:5000]
        t_batch_start = time.perf_counter()
        _ = model.predict(batch_5000)
        batch_5000_ms = float((time.perf_counter() - t_batch_start) * 1000.0)

        model_size_bytes = int(os.path.getsize(model_path))

        # Check for regression metrics if linreg
        pred_scores = None
        regression_metrics = {}
        if spec.task == "score_to_band":
            # Extract underlying regressor score prediction
            underlying = model.estimator if hasattr(model, "estimator") else model
            prep_pipe = underlying.named_steps["prep"]
            stb_est = underlying.named_steps["model"]
            prep_X = prep_pipe.transform(X_test)
            pred_scores = stb_est.predict_score(prep_X)

            mae = float(mean_absolute_error(y_test_score, pred_scores))
            rmse = float(np.sqrt(mean_squared_error(y_test_score, pred_scores)))
            r2 = float(r2_score(y_test_score, pred_scores))
            spearman_corr = float(spearmanr(y_test_score, pred_scores).correlation)

            regression_metrics = {
                "mae": round(mae, 4),
                "rmse": round(rmse, 4),
                "r2": round(r2, 4),
                "spearman": round(spearman_corr, 4),
            }

        # Quality dimensions
        stability_std = tuning_meta.get("stability_std", 0.0)
        explain_tier = spec.explain_tier
        explain_score = {"native": 1.0, "partial": 0.6, "post_hoc": 0.3}.get(explain_tier, 0.3)

        metric_data = {
            "key": key,
            "label": spec.label,
            "family": spec.family,
            "task": spec.task,
            "variant": variant,
            "test_samples": n_test,
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "macro_f1": round(macro_f1, 4),
            "qwk": round(qwk, 4),
            "mcc": round(mcc, 4),
            "roc_auc_ovr": round(roc_ovr, 4),
            "log_loss": round(ll, 4),
            "brier": round(brier, 4),
            "ece": round(ece, 4),
            "raw_accuracy": round(raw_acc, 4),
            "raw_macro_f1": round(raw_macro_f1, 4),
            "raw_log_loss": round(raw_ll, 4),
            "raw_brier": round(raw_brier, 4),
            "raw_ece": round(raw_ece, 4),
            "calibration_temperature": round(getattr(model, "temperature_", 1.0), 4),
            "exact_share": round(exact_err, 4),
            "adjacent_share": round(adj_err, 4),
            "extreme_share": round(ext_err, 4),
            "per_class": per_class,
            "confusion_matrix": confusion_matrix(y_test_band, y_pred).tolist(),
            "latency_single_p50_ms": round(latency_p50, 3),
            "latency_single_p95_ms": round(latency_p95, 3),
            "latency_batch_5000_ms": round(batch_5000_ms, 2),
            "model_size_bytes": model_size_bytes,
            "tuning_time_sec": tuning_meta.get("tuning_time_sec", 0.0),
            "stability_std": stability_std,
            "explain_tier": explain_tier,
            "explain_score": explain_score,
            "regression_track": regression_metrics,
        }

        # Save metrics.json
        with open(Path(models_dir) / key / "metrics.json", "w") as f:
            json.dump(metric_data, f, indent=2)

        # Save test_predictions.csv
        if pred_scores is not None:
            preds_df["pred_score"] = np.round(pred_scores, 2)

        preds_df.to_csv(Path(models_dir) / key / "test_predictions.csv", index=False, lineterminator="\n")
        results[key] = metric_data

        # Sanity check: G7 leakage check (any metric >= 0.97 means investigate leakage)
        if macro_f1 >= 0.97:
            print(f"[ALERT - POSSIBLE LEAKAGE] Model {key} has test Macro-F1 = {macro_f1} >= 0.97!")

        print(f"[{key:7s}] Macro-F1: {macro_f1:.4f} | QWK: {qwk:.4f} | ECE: {ece:.4f} | Latency p95: {latency_p95:.2f}ms")

    # Generate reports/v2_final.md
    generate_v2_final_report(results, variant, n_test)

    print("\n[make final] Final test evaluation completed successfully.")
    return results


def generate_v2_final_report(results: Dict[str, Any], variant: str, n_test: int):
    """Write comprehensive reports/v2_final.md."""
    report_file = Path("reports/v2_final.md")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    sorted_models = sorted(results.values(), key=lambda x: x["macro_f1"], reverse=True)

    lines = [
        f"# TalentScope Multi-Model Final Evaluation Report (v2)",
        f"",
        f"**Variant Evaluated**: `{variant}` | **Holdout Test Set Size**: {n_test:,} rows",
        f"**Generated**: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"",
        f"## 1. Classification Leaderboard (Sorted by Primary Metric: Macro-F1)",
        f"",
        f"| Rank | Model Key | Label | Family | Macro-F1 | Accuracy | QWK | MCC | ROC-AUC | Log-Loss | ECE |",
        f"|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for rank, m in enumerate(sorted_models, 1):
        lines.append(
            f"| {rank} | `{m['key']}` | {m['label']} | {m['family']} | "
            f"**{m['macro_f1']:.4f}** | {m['accuracy']:.4f} | {m['qwk']:.4f} | "
            f"{m['mcc']:.4f} | {m['roc_auc_ovr']:.4f} | {m['log_loss']:.4f} | {m['ece']:.4f} |"
        )

    lines.extend([
        f"",
        f"## 2. Efficiency and Latency Benchmarks",
        f"",
        f"| Model Key | Single-Row p50 (ms) | Single-Row p95 (ms) | Batch 5,000 (ms) | Model Size (KB) | Tuning Time (s) |",
        f"|---|---|---|---|---|---|",
    ])

    for m in sorted_models:
        lines.append(
            f"| `{m['key']}` | {m['latency_single_p50_ms']:.2f} | {m['latency_single_p95_ms']:.2f} | "
            f"{m['latency_batch_5000_ms']:.1f} | {m['model_size_bytes'] / 1024:.1f} | {m['tuning_time_sec']:.1f} |"
        )

    lines.extend([
        f"",
        f"## 3. Error Breakdown (Exact vs Adjacent vs Extreme)",
        f"",
        f"| Model Key | Exact Agreement (%) | Adjacent Error (+-1 Band) (%) | Extreme Error (Low <-> High) (%) |",
        f"|---|---|---|---|",
    ])

    for m in sorted_models:
        lines.append(
            f"| `{m['key']}` | {m['exact_share']*100:.1f}% | {m['adjacent_share']*100:.1f}% | {m['extreme_share']*100:.2f}% |"
        )

    lines.extend([
        "",
        "## 4. Calibration Analysis (ADR-014 Multinomial Temperature Scaling vs Raw)",
        "",
        "| Model Key | Temperature (T) | Calibrated ECE | Raw ECE | Calibrated Brier | Raw Brier | Calibrated Log-Loss | Raw Log-Loss |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for m in sorted_models:
        lines.append(
            f"| `{m['key']}` | {m.get('calibration_temperature', 1.0):.4f} | "
            f"**{m['ece']:.4f}** | {m.get('raw_ece', m['ece']):.4f} | "
            f"**{m['brier']:.4f}** | {m.get('raw_brier', m['brier']):.4f} | "
            f"**{m['log_loss']:.4f}** | {m.get('raw_log_loss', m['log_loss']):.4f} |"
        )

    # Check for linreg regression track
    if "linreg" in results and results["linreg"].get("regression_track"):
        reg = results["linreg"]["regression_track"]
        lines.extend([
            f"",
            f"## 5. Regression Track (Continuous Performance Score)",
            f"",
            f"| Model | MAE | RMSE | R2 | Spearman rho |",
            f"|---|---|---|---|---|",
            f"| `linreg` (ScoreToBand) | {reg['mae']:.2f} | {reg['rmse']:.2f} | {reg['r2']:.4f} | {reg['spearman']:.4f} |",
        ])

    lines.extend([
        f"",
        f"## 6. Decision Support & Ethics Disclaimer",
        f"",
        f"> **Notice**: Model rankings depend on the synthetic data-generating process and variant parameters.",
        f"> Protected attributes (gender, age_band) are strictly excluded from all training and inference feature sets.",
        f"> Output bands and probabilities are designed strictly for decision support and human review.",
    ])

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Final single test evaluation with G6 lock")
    parser.add_argument("--variant", choices=["linear", "nonlinear", "noisy_overlap"], default="nonlinear")
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--split-path", type=str, default="data/processed/split.json")
    parser.add_argument("--models-dir", type=str, default="artifacts/v2/models")
    parser.add_argument("--new-config", type=str, default=None, help="Explicit reason if re-evaluating test set")
    args = parser.parse_args()

    run_final_evaluation(
        variant=args.variant,
        data_path=args.data_path,
        split_path=args.split_path,
        models_dir=args.models_dir,
        new_config=args.new_config,
    )
