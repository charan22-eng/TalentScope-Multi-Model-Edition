"""TalentScope Multi-Model Training Harness (train_all.py).

Trains, tunes, calibrates, and evaluates stability for all seven models
under an identical, fair comparison protocol.
Enforces Guard G7: cal-A and cal-B are never accessed in tuning code.
The test partition is strictly locked for single evaluation via make final.
"""

import argparse
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import f1_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

from epk.features import ALL_FEATURES, build_preprocessor
from epk.labels import encode_bands
from epk.models.registry import REGISTRY, list_model_specs, get_model_spec
from epk.split import load_split


PROFILE_CONFIGS = {
    "smoke": {"n_iter": 1, "n_repeats": 1},
    "fast": {"n_iter": 10, "n_repeats": 3},
    "standard": {"n_iter": 30, "n_repeats": 5},
    "thorough": {"n_iter": 60, "n_repeats": 10},
}


def log_experiment(
    report_csv: str,
    run_id: str,
    phase: str,
    model: str,
    cv_macro_f1: str,
    test_macro_f1: str,
    params: str,
    seed: int,
    data_checksum: str,
    split_hash: str,
    profile: str,
    notes: str,
):
    """Append run to reports/experiments.csv preserving full schema."""
    out_path = Path(report_csv)
    cols = [
        "run_id",
        "phase",
        "model",
        "cv_macro_f1",
        "test_macro_f1",
        "params",
        "seed",
        "data_checksum",
        "split_hash",
        "profile",
        "notes",
    ]
    row = {
        "run_id": run_id,
        "phase": phase,
        "model": model,
        "cv_macro_f1": cv_macro_f1,
        "test_macro_f1": test_macro_f1,
        "params": json.dumps(params) if isinstance(params, dict) else str(params),
        "seed": seed,
        "data_checksum": data_checksum,
        "split_hash": split_hash,
        "profile": profile,
        "notes": notes,
    }
    df_row = pd.DataFrame([row])
    if out_path.exists():
        existing = pd.read_csv(out_path)
        # Ensure all columns exist
        for c in cols:
            if c not in existing.columns:
                existing[c] = ""
        for c in cols:
            if c not in df_row.columns:
                df_row[c] = ""
        combined = pd.concat([existing[cols], df_row[cols]], ignore_index=True)
    else:
        combined = df_row[cols]
    combined.to_csv(out_path, index=False, lineterminator="\n")


def run_training_pipeline(
    profile: str = "fast",
    variant: str = "nonlinear",
    data_path: str = None,
    split_path: str = "data/processed/split.json",
    seed: int = 42,
    output_dir: str = "artifacts/v2/models",
) -> Dict[str, Any]:
    """Execute tuning, calibration, and stability runs for all models."""
    if profile not in PROFILE_CONFIGS:
        raise ValueError(f"Unknown profile: {profile}. Choices: {list(PROFILE_CONFIGS.keys())}")

    cfg = PROFILE_CONFIGS[profile]
    n_iter_default = cfg["n_iter"]
    n_repeats = cfg["n_repeats"]

    if data_path is None:
        data_path = f"data/{variant}/dataset.csv"

    print(f"=== TalentScope Model Training [Profile={profile}, Variant={variant}] ===")
    print(f"Data: {data_path}")
    print(f"Split: {split_path}")

    # Load dataset
    df = pd.read_csv(data_path)
    with open(data_path, "rb") as f:
        data_checksum = hashlib.sha256(f.read()).hexdigest()

    X = df[ALL_FEATURES]
    y_score = df["performance_score"].to_numpy(dtype=float)
    y_band = encode_bands(df["performance"])

    # Load split (Train and Cal-A only! Test is NEVER touched here)
    split_info = load_split(split_path)
    train_idx = split_info["train"]
    cal_a_idx = split_info["cal_a"]
    split_hash = split_info["split_hash"]

    # Invariant check: G7
    assert len(set(train_idx) & set(cal_a_idx)) == 0, "Train and Cal-A overlap"

    X_train = X.iloc[train_idx].reset_index(drop=True)
    y_train_band = y_band[train_idx]
    y_train_score = y_score[train_idx]

    X_cal_a = X.iloc[cal_a_idx].reset_index(drop=True)
    y_cal_a_band = y_band[cal_a_idx]

    all_specs = list_model_specs()
    summary = {}

    for spec in all_specs:
        key = spec.key
        print(f"\n--- Training {key} ({spec.label}) ---")
        t0 = time.time()

        prep = build_preprocessor(spec)
        raw_est = spec.make()
        base_pipe = Pipeline([("prep", prep), ("model", raw_est)])

        best_params: Dict[str, Any] = {}
        cv_mean = 0.0
        cv_std = 0.0

        if spec.task == "score_to_band":
            # Direct fit for ScoreToBand (linreg)
            # Evaluate CV macro-F1 across 5 folds
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            cv_scores = []
            for tr_k, val_k in skf.split(X_train, y_train_band):
                p_k = Pipeline([("prep", build_preprocessor(spec)), ("model", spec.make())])
                p_k.fit(X_train.iloc[tr_k], y_train_score[tr_k])
                val_preds = p_k.predict(X_train.iloc[val_k])
                cv_scores.append(f1_score(y_train_band[val_k], val_preds, average="macro"))

            cv_mean = float(np.mean(cv_scores))
            cv_std = float(np.std(cv_scores))
            best_pipe = base_pipe.fit(X_train, y_train_score)
            best_params = {}
            tuning_time = time.time() - t0
        else:
            # Random search with equal budget across classification models
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            n_iter = 1 if len(spec.search_space) == 0 else min(n_iter_default, spec.n_iter)
            search = RandomizedSearchCV(
                base_pipe,
                param_distributions=spec.search_space,
                n_iter=n_iter,
                scoring="f1_macro",
                cv=skf,
                random_state=seed,
                n_jobs=1 if profile == "smoke" else -1,
                error_score="raise",
            )
            search.fit(X_train, y_train_band)
            cv_mean = float(search.best_score_)
            cv_std = float(search.cv_results_["std_test_score"][search.best_index_])
            best_pipe = search.best_estimator_
            best_params = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
            tuning_time = time.time() - t0

        print(f"CV Macro-F1: {cv_mean:.4f} ± {cv_std:.4f} (tuning time: {tuning_time:.2f}s)")

        # C4: Probability Calibration on Cal-A via Platt scaling (sigmoid) per ADR-008
        cal_start = time.time()
        calibrated_model = CalibratedClassifierCV(
            estimator=best_pipe,
            method="sigmoid",
            cv="prefit",
        )
        calibrated_model.fit(X_cal_a, y_cal_a_band)
        cal_time = time.time() - cal_start
        print(f"Calibrated on Cal-A ({len(X_cal_a)} rows) in {cal_time:.2f}s")

        # C5: Stability evaluation over repeated development splits
        repeat_scores = []
        for rep in range(n_repeats):
            rep_seed = seed + rep * 100
            skf_rep = StratifiedKFold(n_splits=5, shuffle=True, random_state=rep_seed)
            rep_tr, rep_val = next(skf_rep.split(X_train, y_train_band))
            p_rep = Pipeline([("prep", build_preprocessor(spec)), ("model", spec.make())])
            if spec.task == "score_to_band":
                p_rep.fit(X_train.iloc[rep_tr], y_train_score[rep_tr])
            else:
                if best_params:
                    # Apply best params
                    p_rep.named_steps["model"].set_params(**best_params)
                p_rep.fit(X_train.iloc[rep_tr], y_train_band[rep_tr])
            val_preds = p_rep.predict(X_train.iloc[rep_val])
            repeat_scores.append(f1_score(y_train_band[rep_val], val_preds, average="macro"))

        stability_mean = float(np.mean(repeat_scores))
        stability_std = float(np.std(repeat_scores))
        print(f"Stability across {n_repeats} splits: {stability_mean:.4f} ± {stability_std:.4f}")

        # Persist model artifact
        model_dir = Path(output_dir) / key
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "model.joblib"
        joblib.dump(calibrated_model, model_path)

        meta = {
            "key": key,
            "label": spec.label,
            "family": spec.family,
            "task": spec.task,
            "needs_scaling": spec.needs_scaling,
            "explain_tier": spec.explain_tier,
            "best_params": best_params,
            "cv_macro_f1_mean": round(cv_mean, 4),
            "cv_macro_f1_std": round(cv_std, 4),
            "stability_mean": round(stability_mean, 4),
            "stability_std": round(stability_std, 4),
            "tuning_time_sec": round(tuning_time, 2),
            "calibration_method": "sigmoid",
            "profile": profile,
            "seed": seed,
            "variant": variant,
        }
        with open(model_dir / "tuning.json", "w") as f:
            json.dump(meta, f, indent=2)

        # Log to reports/experiments.csv
        log_experiment(
            report_csv="reports/experiments.csv",
            run_id=f"train_{profile}_{key}_{variant}",
            phase="MM-S3",
            model=key,
            cv_macro_f1=f"{cv_mean:.4f} +- {cv_std:.4f}",
            test_macro_f1="N/A (untouched)",
            params=best_params,
            seed=seed,
            data_checksum=data_checksum,
            split_hash=split_hash,
            profile=profile,
            notes=f"Tuned ({n_iter_default} iters), calibrated on cal-A, stability_std={stability_std:.4f}",
        )

        summary[key] = meta

    print("\n=== Training Complete for All 7 Models ===")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and tune all 7 models")
    parser.add_argument("--profile", choices=["fast", "standard", "thorough"], default="fast")
    parser.add_argument("--variant", choices=["linear", "nonlinear", "noisy_overlap"], default="nonlinear")
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--split-path", type=str, default="data/processed/split.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=str, default="artifacts/v2/models")
    args = parser.parse_args()

    run_training_pipeline(
        profile=args.profile,
        variant=args.variant,
        data_path=args.data_path,
        split_path=args.split_path,
        seed=args.seed,
        output_dir=args.output_dir,
    )
