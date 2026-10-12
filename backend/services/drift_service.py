"""Drift Monitoring Service (Stage L5).

Computes Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) tests
across numeric features for production batches vs reference distributions.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
from scipy import stats


def compute_psi(expected: np.ndarray, actual: np.ndarray, num_bins: int = 10) -> float:
    """Calculate Population Stability Index (PSI) between expected and actual distributions."""
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Quantile bin edges from reference distribution
    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(expected, percentiles)
    bin_edges = np.unique(bin_edges)

    if len(bin_edges) < 2:
        return 0.0

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    # Convert to proportions with smoothing epsilon
    eps = 1e-4
    expected_pct = (expected_counts / len(expected)) + eps
    actual_pct = (actual_counts / len(actual)) + eps

    # Re-normalize
    expected_pct /= np.sum(expected_pct)
    actual_pct /= np.sum(actual_pct)

    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(max(0.0, psi_val))


def compute_ks(expected: np.ndarray, actual: np.ndarray) -> Tuple[float, float]:
    """Calculate Kolmogorov-Smirnov 2-sample test (statistic, p-value)."""
    if len(expected) == 0 or len(actual) == 0:
        return 0.0, 1.0
    res = stats.ks_2samp(expected, actual)
    return float(res.statistic), float(res.pvalue)


def assess_drift(
    reference_data: Dict[str, List[float]],
    current_data: Dict[str, List[float]],
) -> Dict[str, Any]:
    """Assess overall and per-feature drift across numerical features."""
    feature_reports = {}
    psi_scores = []
    ks_pvalues = []

    for feat_name, ref_vals in reference_data.items():
        if feat_name not in current_data or len(current_data[feat_name]) == 0:
            continue

        ref_arr = np.array(ref_vals, dtype=float)
        cur_arr = np.array(current_data[feat_name], dtype=float)

        if len(ref_arr) < 5 or len(cur_arr) < 5:
            continue

        psi = compute_psi(ref_arr, cur_arr)
        ks_stat, ks_pval = compute_ks(ref_arr, cur_arr)

        if psi < 0.1:
            status = "stable"
        elif psi < 0.25:
            status = "moderate_drift"
        else:
            status = "significant_drift"

        feature_reports[feat_name] = {
            "psi": round(psi, 4),
            "ks_statistic": round(ks_stat, 4),
            "ks_pvalue": round(ks_pval, 4),
            "status": status,
        }
        psi_scores.append(psi)
        ks_pvalues.append(ks_pval)

    avg_psi = float(np.mean(psi_scores)) if psi_scores else 0.0
    min_ks_pval = float(np.min(ks_pvalues)) if ks_pvalues else 1.0

    if avg_psi < 0.1:
        overall_status = "stable"
    elif avg_psi < 0.25:
        overall_status = "moderate_drift"
    else:
        overall_status = "significant_drift"

    return {
        "overall_psi": round(avg_psi, 4),
        "min_ks_pvalue": round(min_ks_pval, 4),
        "status": overall_status,
        "features": feature_reports,
    }
