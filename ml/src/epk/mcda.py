"""Multi-Criteria Decision Analysis (MCDA) Engine and Champion Selection Rule.

Implements:
- 5 Predefined Priority Profiles + User Custom Weights
- Min-Max Normalization with criteria directionality
- Dirichlet Rank-1 Probability (5,000 draws, concentration=50)
- Decision Strength Rule (clear / marginal / none) per ADR-009
"""

from typing import Any, Dict, List, Literal, Tuple
import numpy as np
import pandas as pd

PROFILES = {
    "Balanced": {
        "macro_f1": 0.30,
        "qwk": 0.10,
        "calibration": 0.10,
        "robustness": 0.10,
        "fairness": 0.10,
        "stability": 0.05,
        "latency": 0.05,
        "train_cost": 0.05,
        "explainability": 0.15,
    },
    "Accuracy-first": {
        "macro_f1": 0.50,
        "qwk": 0.15,
        "calibration": 0.10,
        "robustness": 0.10,
        "fairness": 0.05,
        "stability": 0.05,
        "latency": 0.02,
        "train_cost": 0.01,
        "explainability": 0.02,
    },
    "Explainability-first": {
        "macro_f1": 0.20,
        "qwk": 0.05,
        "calibration": 0.10,
        "robustness": 0.05,
        "fairness": 0.10,
        "stability": 0.05,
        "latency": 0.05,
        "train_cost": 0.05,
        "explainability": 0.35,
    },
    "Speed-first": {
        "macro_f1": 0.20,
        "qwk": 0.05,
        "calibration": 0.05,
        "robustness": 0.05,
        "fairness": 0.05,
        "stability": 0.05,
        "latency": 0.30,
        "train_cost": 0.20,
        "explainability": 0.05,
    },
    "Fairness-first": {
        "macro_f1": 0.20,
        "qwk": 0.05,
        "calibration": 0.10,
        "robustness": 0.10,
        "fairness": 0.35,
        "stability": 0.05,
        "latency": 0.05,
        "train_cost": 0.05,
        "explainability": 0.05,
    },
}

HIGHER_IS_BETTER = {
    "macro_f1": True,
    "qwk": True,
    "calibration": True,
    "robustness": True,
    "fairness": True,
    "stability": True,
    "latency": False,     # Lower latency is better
    "train_cost": False,  # Lower training time is better
    "explainability": True,
}


def minmax_normalise(table: pd.DataFrame, higher_is_better: Dict[str, bool]) -> pd.DataFrame:
    """Normalize criteria into [0, 1] adhering to optimization direction."""
    out = pd.DataFrame(index=table.index)
    for c, hib in higher_is_better.items():
        if c not in table.columns:
            continue
        vals = table[c].to_numpy(dtype=float)
        lo, hi = np.nanmin(vals), np.nanmax(vals)
        if hi > lo:
            norm_col = (vals - lo) / (hi - lo)
        else:
            norm_col = np.ones_like(vals)
        out[c] = norm_col if hib else (1.0 - norm_col)
    return out


def mcda_rank(
    table: pd.DataFrame,
    weights: Dict[str, float],
    higher_is_better: Dict[str, bool] = None,
) -> pd.DataFrame:
    """Compute normalized MCDA weighted score and integer ranks."""
    if higher_is_better is None:
        higher_is_better = HIGHER_IS_BETTER

    crit = [c for c in weights if c in table.columns]
    w = pd.Series({c: float(weights[c]) for c in crit})
    w = w / w.sum()

    norm_t = minmax_normalise(table[crit], {c: higher_is_better[c] for c in crit})
    score = (norm_t[crit] * w).sum(axis=1)

    result = pd.DataFrame({
        "mcda_score": np.round(score, 4),
        "rank": score.rank(ascending=False, method="min").astype(int),
    }, index=table.index).sort_values("rank")

    return result


def rank_probability(
    table: pd.DataFrame,
    base_weights: Dict[str, float],
    higher_is_better: Dict[str, bool] = None,
    n_draws: int = 5000,
    concentration: float = 50.0,
    seed: int = 0,
) -> pd.Series:
    """Share of random Dirichlet weight draws for which each model ranks first."""
    if higher_is_better is None:
        higher_is_better = HIGHER_IS_BETTER

    crit = [c for c in base_weights if c in table.columns]
    base = np.array([base_weights[c] for c in crit], dtype=float)
    base = base / base.sum()

    norm_t = minmax_normalise(table[crit], {c: higher_is_better[c] for c in crit})[crit].to_numpy()

    rng = np.random.default_rng(seed)
    # Dirichlet weight perturbations
    W = rng.dirichlet(concentration * base + 1e-6, size=n_draws)
    scores = norm_t @ W.T
    best_idx = scores.argmax(axis=0)

    counts = np.bincount(best_idx, minlength=len(table))
    p_rank1 = counts / float(n_draws)

    return pd.Series(np.round(p_rank1, 4), index=table.index, name="p_rank1")


def compute_decision_strength(
    diff_excludes_zero: bool,
    mcnemar_holm_p: float,
    p_rank1: float,
) -> Literal["clear", "marginal", "none"]:
    """ADR-009 Decision Strength Determination.

    Conditions:
    (a) Bootstrap difference interval between rank 1 and 2 excludes zero
    (b) McNemar-Holm test between rank 1 and 2 has adjusted p < 0.05
    (c) Rank-1 probability >= 0.80 under Dirichlet weight perturbation
    """
    cond_a = bool(diff_excludes_zero)
    cond_b = bool(mcnemar_holm_p < 0.05)
    cond_c = bool(p_rank1 >= 0.80)

    satisfied = sum([cond_a, cond_b, cond_c])
    if satisfied == 3:
        return "clear"
    elif satisfied > 0:
        return "marginal"
    else:
        return "none"


def run_mcda_pipeline(
    metrics_table: pd.DataFrame,
    profile_name: str = "Balanced",
    custom_weights: Dict[str, float] = None,
    diff_excludes_zero: bool = False,
    mcnemar_holm_p: float = 1.0,
) -> Dict[str, Any]:
    """Execute complete MCDA ranking and decision strength determination."""
    weights = custom_weights if custom_weights else PROFILES.get(profile_name, PROFILES["Balanced"])

    ranks_df = mcda_rank(metrics_table, weights)
    p_rank1 = rank_probability(metrics_table, weights)

    merged = ranks_df.join(p_rank1).sort_values("rank")
    winner_key = merged.index[0]
    rank2_key = merged.index[1] if len(merged) > 1 else None

    winner_p_rank1 = float(merged.loc[winner_key, "p_rank1"])
    strength = compute_decision_strength(diff_excludes_zero, mcnemar_holm_p, winner_p_rank1)

    model_entries = []
    for k in merged.index:
        model_entries.append({
            "key": k,
            "rank": int(merged.loc[k, "rank"]),
            "mcda_score": float(merged.loc[k, "mcda_score"]),
            "p_rank1": float(merged.loc[k, "p_rank1"]),
        })

    return {
        "profile": profile_name,
        "weights": weights,
        "deterministic_winner": winner_key,
        "runner_up": rank2_key,
        "decision_strength": strength,
        "winner_p_rank1": winner_p_rank1,
        "ranking": model_entries,
    }
