"""Comparison Science: Bootstrap, McNemar, Conformal Prediction, Robustness, Fairness.

Implements rigorous statistical comparisons across all 7 models:
- D1: Paired Stratified Bootstrap (2,000 resamples) for CIs and difference CIs.
- D2: McNemar tests across all 21 pairs with Holm-Bonferroni correction.
- D3: Split-conformal sets fitted on cal-B (alpha=0.10) with test coverage & set sizes.
- D4: Robustness stress-testing (noise, missingness) and audit fairness disparity ratios.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy.stats import binom, chi2
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score
from sklearn.preprocessing import label_binarize

from epk.features import ALL_FEATURES, NUMERIC_FEATURES
from epk.labels import encode_bands
from epk.models.registry import MODEL_KEYS
from epk.split import load_split


def paired_stratified_bootstrap(
    y_true: np.ndarray,
    preds_dict: Dict[str, np.ndarray],
    rank1_key: str,
    rank2_key: str,
    n_resamples: int = 2000,
    seed: int = 42,
) -> Dict[str, Any]:
    """Paired stratified bootstrap with identical resamples across all models."""
    rng = np.random.default_rng(seed)
    n_samples = len(y_true)
    classes = np.unique(y_true)
    class_indices = {c: np.where(y_true == c)[0] for c in classes}

    boot_results = {k: {"macro_f1": [], "accuracy": [], "qwk": []} for k in preds_dict}
    diff_f1_list = []

    for _ in range(n_resamples):
        # Sample with replacement within each class to preserve exact class distribution
        sample_idx_parts = [
            rng.choice(idx_list, size=len(idx_list), replace=True)
            for idx_list in class_indices.values()
        ]
        sample_idx = np.concatenate(sample_idx_parts)

        y_boot = y_true[sample_idx]

        for k, preds in preds_dict.items():
            p_boot = preds[sample_idx]
            f1 = f1_score(y_boot, p_boot, average="macro")
            acc = accuracy_score(y_boot, p_boot)
            qwk = cohen_kappa_score(y_boot, p_boot, weights="quadratic")

            boot_results[k]["macro_f1"].append(f1)
            boot_results[k]["accuracy"].append(acc)
            boot_results[k]["qwk"].append(qwk)

        diff = (
            boot_results[rank1_key]["macro_f1"][-1]
            - boot_results[rank2_key]["macro_f1"][-1]
        )
        diff_f1_list.append(diff)

    cis = {}
    for k in preds_dict:
        cis[k] = {
            "macro_f1_ci": [
                round(float(np.percentile(boot_results[k]["macro_f1"], 2.5)), 4),
                round(float(np.percentile(boot_results[k]["macro_f1"], 97.5)), 4),
            ],
            "accuracy_ci": [
                round(float(np.percentile(boot_results[k]["accuracy"], 2.5)), 4),
                round(float(np.percentile(boot_results[k]["accuracy"], 97.5)), 4),
            ],
            "qwk_ci": [
                round(float(np.percentile(boot_results[k]["qwk"], 2.5)), 4),
                round(float(np.percentile(boot_results[k]["qwk"], 97.5)), 4),
            ],
        }

    diff_ci = [
        round(float(np.percentile(diff_f1_list, 2.5)), 4),
        round(float(np.percentile(diff_f1_list, 97.5)), 4),
    ]

    return {
        "model_cis": cis,
        "diff_rank1_rank2": {
            "rank1": rank1_key,
            "rank2": rank2_key,
            "diff_ci_95": diff_ci,
            "excludes_zero": bool(diff_ci[0] > 0),
        },
    }


def pairwise_mcnemar_tests(
    y_true: np.ndarray,
    preds_dict: Dict[str, np.ndarray],
) -> Dict[str, Any]:
    """McNemar tests with exact binomial calculation for small counts and Holm correction."""
    keys = list(preds_dict.keys())
    pairs = []

    # Compute raw p-values for all 21 pairs
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            m1, m2 = keys[i], keys[j]
            corr1 = preds_dict[m1] == y_true
            corr2 = preds_dict[m2] == y_true

            # b: m1 wrong, m2 correct
            b = int(np.sum((~corr1) & corr2))
            # c: m1 correct, m2 wrong
            c = int(np.sum(corr1 & (~corr2)))

            total_discordant = b + c
            if total_discordant == 0:
                p_val = 1.0
                stat = 0.0
            elif total_discordant < 25:
                # Exact two-sided binomial test
                k = min(b, c)
                p_val = float(min(1.0, 2.0 * binom.cdf(k, total_discordant, 0.5)))
                stat = float(total_discordant)
            else:
                # Edwards continuity-corrected McNemar chi-square
                chi2_stat = float(((abs(b - c) - 1.0) ** 2) / total_discordant)
                p_val = float(1.0 - chi2.cdf(chi2_stat, df=1))
                stat = chi2_stat

            pairs.append({
                "model_a": m1,
                "model_b": m2,
                "b_discordant": b,
                "c_discordant": c,
                "stat": round(stat, 3),
                "raw_p": p_val,
            })

    # Holm-Bonferroni step-down correction
    pairs.sort(key=lambda x: x["raw_p"])
    m = len(pairs)
    cum_max = 0.0

    for idx, item in enumerate(pairs):
        adjusted = min(1.0, item["raw_p"] * (m - idx))
        cum_max = max(cum_max, adjusted)
        item["holm_p"] = round(float(cum_max), 5)
        item["significant"] = bool(item["holm_p"] < 0.05)
        item["raw_p"] = round(item["raw_p"], 5)

    pair_map = {f"{p['model_a']}_vs_{p['model_b']}": p for p in pairs}
    return {
        "pairwise_tests": pairs,
        "pair_map": pair_map,
    }


def compute_conformal_sets_cal_b(
    cal_b_df: pd.DataFrame,
    test_df: pd.DataFrame,
    models_dict: Dict[str, Any],
    alpha: float = 0.10,
) -> Dict[str, Any]:
    """Fit conformal prediction threshold on cal-B and evaluate coverage on test."""
    y_cal_b = encode_bands(cal_b_df["performance"])
    y_test = encode_bands(test_df["performance"])
    X_cal_b = cal_b_df[ALL_FEATURES]
    X_test = test_df[ALL_FEATURES]
    n_cal_b = len(cal_b_df)

    results = {}

    for key, model in models_dict.items():
        # Predict class probabilities on cal-B
        p_cal_b = model.predict_proba(X_cal_b)
        # Non-conformity score: 1 - P(true class)
        true_class_probs = p_cal_b[np.arange(n_cal_b), y_cal_b]
        nonconformity = 1.0 - true_class_probs

        # Conformal quantile: ceil((n+1)(1-alpha)) / n
        q_level = float(np.ceil((n_cal_b + 1) * (1.0 - alpha)) / n_cal_b)
        q_level = min(1.0, q_level)
        threshold = float(np.quantile(nonconformity, q_level))

        # Evaluate on test set
        p_test = model.predict_proba(X_test)
        # Prediction set: classes with non-conformity <= threshold <=> prob >= 1 - threshold
        min_prob_threshold = max(0.0, 1.0 - threshold)
        sets = [np.where(p_test[i] >= min_prob_threshold)[0] for i in range(len(test_df))]

        # Guarantee non-empty sets if required (or measure empty share)
        set_sizes = np.array([len(s) for s in sets])
        coverages = np.array([y_test[i] in sets[i] for i in range(len(test_df))])

        results[key] = {
            "alpha": alpha,
            "threshold": round(threshold, 4),
            "min_prob_threshold": round(min_prob_threshold, 4),
            "empirical_coverage": round(float(np.mean(coverages)), 4),
            "avg_set_size": round(float(np.mean(set_sizes)), 3),
            "single_label_share": round(float(np.mean(set_sizes == 1)), 4),
            "multi_label_share": round(float(np.mean(set_sizes > 1)), 4),
            "empty_share": round(float(np.mean(set_sizes == 0)), 4),
        }

    return results


def evaluate_robustness(
    test_df: pd.DataFrame,
    models_dict: Dict[str, Any],
    seed: int = 42,
) -> Dict[str, Any]:
    """Evaluate performance drop under 5% Gaussian noise and 10% missing features."""
    rng = np.random.default_rng(seed)
    y_test = encode_bands(test_df["performance"])
    X_test = test_df[ALL_FEATURES].copy()

    # 1. 5% Gaussian noise on numeric columns
    X_noisy = X_test.copy()
    for col in NUMERIC_FEATURES:
        vals = X_noisy[col].to_numpy(dtype=float)
        std_val = np.nanstd(vals)
        noise = rng.normal(0, 0.05 * std_val, size=len(vals))
        X_noisy[col] = vals + noise

    # 2. 10% MCAR missingness across all features
    X_missing = X_test.copy()
    mask = rng.uniform(0, 1, size=X_missing.shape) < 0.10
    X_missing = X_missing.mask(mask)

    robustness = {}
    for key, model in models_dict.items():
        base_f1 = f1_score(y_test, model.predict(X_test), average="macro")
        noisy_f1 = f1_score(y_test, model.predict(X_noisy), average="macro")
        missing_f1 = f1_score(y_test, model.predict(X_missing), average="macro")

        drop_noise = max(0.0, base_f1 - noisy_f1)
        drop_missing = max(0.0, base_f1 - missing_f1)
        mean_drop = (drop_noise + drop_missing) / 2.0
        robustness_score = round(max(0.0, 1.0 - mean_drop), 4)

        robustness[key] = {
            "baseline_f1": round(float(base_f1), 4),
            "noisy_f1": round(float(noisy_f1), 4),
            "missing_f1": round(float(missing_f1), 4),
            "drop_noise": round(float(drop_noise), 4),
            "drop_missing": round(float(drop_missing), 4),
            "robustness_score": robustness_score,
        }

    return robustness


def evaluate_fairness(
    row_indices: np.ndarray,
    preds_dict: Dict[str, np.ndarray],
    protected_csv_path: str = "data/nonlinear/protected.csv",
) -> Dict[str, Any]:
    """Evaluate audit disparity ratio of High-selection rate across audit groups."""
    prot_df = pd.read_csv(protected_csv_path).iloc[row_indices].reset_index(drop=True)

    fairness_results = {}

    for key, preds in preds_dict.items():
        is_high = (preds == 2).astype(float)  # 2 corresponds to High

        group_rates = {}
        # Audit attributes: gender, age_band
        for attr in ["gender", "age_band"]:
            if attr in prot_df.columns:
                for grp in prot_df[attr].unique():
                    grp_mask = (prot_df[attr] == grp).to_numpy()
                    if np.sum(grp_mask) >= 30:  # Minimum group size threshold
                        rate = float(np.mean(is_high[grp_mask]))
                        group_rates[f"{attr}_{grp}"] = max(1e-4, rate)

        if group_rates:
            min_rate = min(group_rates.values())
            max_rate = max(group_rates.values())
            disparity_ratio = min_rate / max_rate if max_rate > 0 else 1.0
        else:
            disparity_ratio = 1.0

        fairness_results[key] = {
            "disparity_ratio": round(float(disparity_ratio), 4),
            "group_rates": {k: round(v, 4) for k, v in group_rates.items()},
        }

    return fairness_results
