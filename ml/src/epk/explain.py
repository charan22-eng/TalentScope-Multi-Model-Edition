"""Multi-Model Explainability & Uncertainty Engine for TalentScope.

Supports all seven models with both native and model-agnostic methods:
- E1: Permutation importance, local attribution, counterfactuals, stability, conformal sets.
- E2: Native explainers (coefficients/odds ratios, tree rules, KNN neighbours).
- E3: Similar-cases view for non-KNN models labeled 'not how this model decided'.
- E4: Scaled-space PCA 2D/3D fitted on train data with anonymized background sample.
- E5: 2D surface grids (40x40 default), Spearman importance agreement, persona summaries.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

# Ensure ml/src is on sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
from sklearn.inspection import permutation_importance
from sklearn.tree import _tree

from epk.features import ALL_FEATURES, NUMERIC_FEATURES, build_preprocessor
from epk.labels import BANDS, INT_TO_BAND, decode_bands, encode_bands
from epk.models.registry import MODEL_KEYS, get_model_spec

ACTIONABLE_LEVERS = {
    "training_hours": {"step": 5.0, "min": 0.0, "max": 120.0, "cost": 1.0},
    "projects_completed": {"step": 1.0, "min": 0.0, "max": 25.0, "cost": 2.0},
    "weekly_hours": {"step": 2.0, "min": 30.0, "max": 55.0, "cost": 1.5},
    "certifications": {"step": 1.0, "min": 0.0, "max": 6.0, "cost": 3.0},
    "attendance": {"step": 2.0, "min": 70.0, "max": 100.0, "cost": 2.5},
    "tasks_on_time_pct": {"step": 3.0, "min": 50.0, "max": 100.0, "cost": 1.5},
}


def get_underlying_model(pipeline_or_calibrator: Any) -> Tuple[Any, Any]:
    """Unwrap preprocessor and core estimator from pipeline or CalibratedClassifierCV."""
    est = pipeline_or_calibrator
    if hasattr(est, "calibrated_classifiers_"):
        # Scikit-learn CalibratedClassifierCV
        est = est.calibrated_classifiers_[0].estimator

    if hasattr(est, "named_steps"):
        prep = est.named_steps.get("prep")
        model = est.named_steps.get("model")
        return prep, model

    return None, est


def explain_model_native(model_obj: Any, key: str, feature_names: List[str] = None) -> Dict[str, Any]:
    """Extract native interpretable parameters according to model family."""
    if feature_names is None:
        feature_names = ALL_FEATURES

    spec = get_model_spec(key)
    prep, core = get_underlying_model(model_obj)
    out: Dict[str, Any] = {
        "key": key,
        "label": spec.label,
        "explanation_type": spec.explain_tier,
    }

    if key == "linreg":
        # Linear regression inside ScoreToBand
        reg = core.regressor_ if hasattr(core, "regressor_") else core
        if hasattr(reg, "coef_"):
            coefs = reg.coef_.flatten().tolist()
            out["coefficients"] = {fn: round(float(c), 4) for fn, c in zip(feature_names[:len(coefs)], coefs)}
            out["intercept"] = round(float(reg.intercept_), 4) if hasattr(reg, "intercept_") else 0.0
            out["thresholds"] = [round(float(t), 2) for t in getattr(core, "thresholds_", [30.0, 75.0])]

    elif key == "logreg":
        # Logistic Regression: coefficients and odds ratios
        if hasattr(core, "coef_"):
            coef_matrix = core.coef_
            classes = getattr(core, "classes_", [0, 1, 2])
            per_class_coefs = {}
            per_class_odds = {}
            for idx, c in enumerate(classes):
                c_name = INT_TO_BAND.get(int(c), str(c))
                c_coefs = coef_matrix[idx].tolist()
                per_class_coefs[c_name] = {fn: round(float(w), 4) for fn, w in zip(feature_names[:len(c_coefs)], c_coefs)}
                per_class_odds[c_name] = {fn: round(float(np.exp(w)), 4) for fn, w in zip(feature_names[:len(c_coefs)], c_coefs)}
            out["coefficients"] = per_class_coefs
            out["odds_ratios"] = per_class_odds
            out["intercept"] = [round(float(b), 4) for b in core.intercept_.tolist()]

    elif key == "dt":
        # Decision Tree: top level split rules
        if hasattr(core, "tree_"):
            tree = core.tree_
            out["max_depth"] = int(core.get_depth())
            out["n_leaves"] = int(core.get_n_leaves())
            rules = []

            def recurse(node, depth=0):
                if depth >= 3 or tree.feature[node] == _tree.TREE_UNDEFINED:
                    val = tree.value[node][0]
                    pred_class = INT_TO_BAND[int(val.argmax())]
                    rules.append(f"{'  ' * depth}-> Predict {pred_class} (samples: {int(tree.n_node_samples[node])})")
                    return
                feat_idx = tree.feature[node]
                feat_name = feature_names[feat_idx] if feat_idx < len(feature_names) else f"feature_{feat_idx}"
                th = tree.threshold[node]
                rules.append(f"{'  ' * depth}IF {feat_name} <= {th:.2f}:")
                recurse(tree.children_left[node], depth + 1)
                rules.append(f"{'  ' * depth}ELSE:")
                recurse(tree.children_right[node], depth + 1)

            recurse(0, 0)
            out["top_rules"] = rules[:15]
            if hasattr(core, "feature_importances_"):
                out["importances"] = {
                    fn: round(float(imp), 4)
                    for fn, imp in zip(feature_names[:len(core.feature_importances_)], core.feature_importances_)
                }

    elif key in ("rf", "boost"):
        # Ensembles: Feature importances
        if hasattr(core, "feature_importances_"):
            imps = core.feature_importances_.tolist()
            out["importances"] = {
                fn: round(float(imp), 4)
                for fn, imp in zip(feature_names[:len(imps)], imps)
            }
        elif hasattr(core, "train_score_"):
            out["iterations"] = len(core.train_score_)

    elif key == "knn":
        out["n_neighbors"] = getattr(core, "n_neighbors", 25)
        out["weights"] = getattr(core, "weights", "distance")
        out["metric"] = getattr(core, "metric", "minkowski")

    elif key == "svm":
        out["kernel"] = getattr(core, "kernel", "rbf")
        out["C"] = round(float(getattr(core, "C", 1.0)), 4)
        out["gamma"] = getattr(core, "gamma", "scale")
        out["n_support"] = getattr(core, "n_support_", []).tolist()

    return out


def local_attribution(
    model: Any,
    x_row: pd.DataFrame,
    background_medians: pd.Series,
) -> Dict[str, float]:
    """Calculate local feature attribution by replacing features with background medians."""
    base_proba = model.predict_proba(x_row)[0]
    pred_idx = int(base_proba.argmax())

    attributions = {}
    for col in x_row.columns:
        if col not in background_medians:
            continue
        perturbed = x_row.copy()
        perturbed[col] = background_medians[col]
        perturbed_proba = model.predict_proba(perturbed)[0][pred_idx]
        delta = float(base_proba[pred_idx] - perturbed_proba)
        attributions[col] = round(delta, 4)

    return dict(sorted(attributions.items(), key=lambda kv: abs(kv[1]), reverse=True))


def find_counterfactuals(
    model: Any,
    x_row: pd.DataFrame,
    target_band: str = "High",
    max_options: int = 3,
    max_steps: int = 25,
) -> List[Dict[str, Any]]:
    """Search for actionable counterfactuals to achieve target band under the explained model."""
    classes = list(model.classes_)
    target_idx = 2 if target_band == "High" else 1

    current_pred = int(model.predict(x_row)[0])
    if current_pred == target_idx:
        return []

    options: List[Dict[str, Any]] = []

    # Strategy 1: Greedy multi-lever gradient
    curr_df = x_row.copy()
    changes_accum = {}
    total_cost = 0.0

    for _ in range(max_steps):
        if int(model.predict(curr_df)[0]) == target_idx:
            break

        best_lever = None
        best_prob_gain = -1.0
        best_trial_df = None

        for lever, cfg in ACTIONABLE_LEVERS.items():
            if lever not in curr_df.columns:
                continue
            cur_val = float(curr_df[lever].iloc[0])
            new_val = min(cfg["max"], cur_val + cfg["step"])
            if new_val == cur_val:
                continue

            trial = curr_df.copy()
            trial[lever] = new_val
            p = float(model.predict_proba(trial)[0][target_idx])
            gain = p - float(model.predict_proba(curr_df)[0][target_idx])
            efficiency = gain / cfg["cost"]

            if efficiency > best_prob_gain:
                best_prob_gain = efficiency
                best_lever = lever
                best_trial_df = trial

        if best_trial_df is not None:
            cfg = ACTIONABLE_LEVERS[best_lever]
            curr_df = best_trial_df
            changes_accum[best_lever] = float(curr_df[best_lever].iloc[0])
            total_cost += cfg["cost"]
        else:
            break

    if int(model.predict(curr_df)[0]) == target_idx:
        options.append({
            "option_id": 1,
            "description": "Multi-lever balanced intervention",
            "changes": changes_accum,
            "cost_score": round(total_cost, 2),
            "achieved_proba": round(float(model.predict_proba(curr_df)[0][target_idx]), 4),
            "validated": True,
        })

    # Strategy 2 & 3: Single-lever aggressive pushes
    for single_lever in ["training_hours", "projects_completed"]:
        if single_lever not in x_row.columns:
            continue
        cfg = ACTIONABLE_LEVERS[single_lever]
        single_df = x_row.copy()
        for mult in [1.5, 2.0, 2.5]:
            val = float(x_row[single_lever].iloc[0])
            new_val = min(cfg["max"], val + cfg["step"] * mult)
            single_df[single_lever] = new_val
            if int(model.predict(single_df)[0]) == target_idx:
                options.append({
                    "option_id": len(options) + 1,
                    "description": f"Focused intervention on {single_lever.replace('_', ' ')}",
                    "changes": {single_lever: new_val},
                    "cost_score": round(cfg["cost"] * mult, 2),
                    "achieved_proba": round(float(model.predict_proba(single_df)[0][target_idx]), 4),
                    "validated": True,
                })
                break
        if len(options) >= max_options:
            break

    return options[:max_options]


def find_similar_cases(
    train_df: pd.DataFrame,
    train_labels: pd.Series,
    x_row: pd.DataFrame,
    model_key: str,
    k: int = 5,
) -> Dict[str, Any]:
    """Find k nearest cases in feature space.

    Labeled 'not how this model decided' for non-KNN models (E3).
    """
    is_knn = (model_key == "knn")
    banner = "Native Decision Reasoning" if is_knn else "Similar Historical Cases (Not how this model decided)"

    numeric_cols = [c for c in NUMERIC_FEATURES if c in train_df.columns and c in x_row.columns]
    X_train_num = train_df[numeric_cols].to_numpy(dtype=float)
    x_num = x_row[numeric_cols].to_numpy(dtype=float)

    # Normalized Euclidean distance
    stds = np.nanstd(X_train_num, axis=0) + 1e-6
    X_scaled = X_train_num / stds
    x_scaled = x_num / stds

    dists = cdist(x_scaled, X_scaled, metric="euclidean")[0]
    nearest_indices = np.argsort(dists)[:k]

    neighbors = []
    for idx in nearest_indices:
        item = train_df.iloc[idx].to_dict()
        item["distance"] = round(float(dists[idx]), 3)
        item["performance"] = str(train_labels.iloc[idx])
        neighbors.append(item)

    label_counts = pd.Series([n["performance"] for n in neighbors]).value_counts().to_dict()

    return {
        "banner": banner,
        "is_native_reasoning": is_knn,
        "model_key": model_key,
        "k": k,
        "neighbors": neighbors,
        "neighborhood_distribution": label_counts,
    }


def compute_stability_score(probas: np.ndarray) -> float:
    """Compute stability score based on margin between top 2 class probabilities."""
    sorted_p = np.sort(probas)[::-1]
    margin = sorted_p[0] - sorted_p[1]
    return round(float(margin), 4)


def compute_performance_index(model: Any, x_row: pd.DataFrame, key: str) -> float:
    """Compute performance index on a 0-100 scale."""
    if key == "linreg":
        prep, core = get_underlying_model(model)
        prep_X = prep.transform(x_row) if prep else x_row
        score = core.predict_score(prep_X)[0]
        return round(float(np.clip(score, 0.0, 100.0)), 2)

    probas = model.predict_proba(x_row)[0]
    # Expectation: Low=15, Med=50, High=85
    exp_score = probas[0] * 15.0 + probas[1] * 50.0 + probas[2] * 85.0
    return round(float(exp_score), 2)


def generate_decision_landscape_grid(
    model: Any,
    x_background: pd.DataFrame,
    feature_x: str = "attendance",
    feature_y: str = "projects_completed",
    grid_size: int = 40,
) -> Dict[str, Any]:
    """Compute 2D decision landscape surface grid (E5)."""
    grid_size = min(80, max(20, grid_size))

    x_min, x_max = float(x_background[feature_x].min()), float(x_background[feature_x].max())
    y_min, y_max = float(x_background[feature_y].min()), float(x_background[feature_y].max())

    xs = np.linspace(x_min, x_max, grid_size)
    ys = np.linspace(y_min, y_max, grid_size)
    grid_xx, grid_yy = np.meshgrid(xs, ys)

    # Base row using median of all features
    base_row = x_background.median(numeric_only=True).to_dict()
    for col in x_background.select_dtypes(include="object").columns:
        base_row[col] = x_background[col].mode()[0]

    mesh_df = pd.DataFrame([base_row] * (grid_size * grid_size))
    mesh_df[feature_x] = grid_xx.flatten()
    mesh_df[feature_y] = grid_yy.flatten()

    preds = model.predict(mesh_df)
    probas = model.predict_proba(mesh_df)

    return {
        "feature_x": feature_x,
        "feature_y": feature_y,
        "grid_size": grid_size,
        "x_range": [round(x_min, 2), round(x_max, 2)],
        "y_range": [round(y_min, 2), round(y_max, 2)],
        "grid_predictions": preds.reshape(grid_size, grid_size).tolist(),
        "prob_high_surface": np.round(probas[:, 2].reshape(grid_size, grid_size), 3).tolist(),
    }


def fit_pca_projection(train_df: pd.DataFrame, max_background_samples: int = 2000) -> Dict[str, Any]:
    """Fit 2D and 3D PCA projection on standardized training data (E4)."""
    num_cols = [c for c in NUMERIC_FEATURES if c in train_df.columns]
    numeric_df = train_df[num_cols].fillna(train_df[num_cols].median())
    stds = numeric_df.std() + 1e-6
    scaled = (numeric_df - numeric_df.mean()) / stds

    pca = PCA(n_components=min(3, len(num_cols)), random_state=42)
    pca.fit(scaled)

    # Sample up to 2,000 points
    n_sample = min(max_background_samples, len(train_df))
    sampled_indices = np.random.default_rng(42).choice(len(train_df), size=n_sample, replace=False)
    projected = pca.transform(scaled.iloc[sampled_indices])

    background_points = []
    for i, idx in enumerate(sampled_indices):
        background_points.append({
            "opaque_id": f"BG{i+1:04d}",
            "pc1": round(float(projected[i, 0]), 3),
            "pc2": round(float(projected[i, 1]), 3),
            "pc3": round(float(projected[i, 2]), 3),
            "performance": str(train_df["performance"].iloc[idx]),
        })

    return {
        "explained_variance_ratio": [round(float(v), 4) for v in pca.explained_variance_ratio_],
        "components": pca.components_.tolist(),
        "feature_names": NUMERIC_FEATURES,
        "means": numeric_df.mean().to_dict(),
        "stds": stds.to_dict(),
        "background_points": background_points,
    }


def generate_persona_summaries(
    key: str,
    label: str,
    pred_band: str,
    proba: List[float],
    attribution: Dict[str, float],
    counterfactuals: List[Dict[str, Any]],
    stability: float,
) -> Dict[str, str]:
    """Produce neutral summaries tailored to HR and Data Science personas."""
    top_pos = [f"{k.replace('_', ' ')} (+{v:.2f})" for k, v in attribution.items() if v > 0.05][:2]
    top_neg = [f"{k.replace('_', ' ')} ({v:.2f})" for k, v in attribution.items() if v < -0.05][:2]

    hr_text = (
        f"Algorithm {label} recommends band '{pred_band}' based primarily on "
        f"{', '.join(top_pos) if top_pos else 'consistent baseline metrics'}. "
    )
    if top_neg:
        hr_text += f"Areas for growth include {', '.join(top_neg)}. "
    if counterfactuals:
        cf = counterfactuals[0]
        cf_changes = [f"raise {k.replace('_', ' ')} to {v:.1f}" for k, v in cf["changes"].items()]
        hr_text += f"To achieve a higher performance band, suggested levers: {', '.join(cf_changes)}."

    ds_text = (
        f"Model '{key}' ({label}) classification: '{pred_band}' with probability distribution "
        f"[Low: {proba[0]:.3f}, Med: {proba[1]:.3f}, High: {proba[2]:.3f}]. "
        f"Decision stability margin is {stability:.3f}. "
        f"Local attribution top drivers: {dict(list(attribution.items())[:3])}."
    )

    return {
        "hr_summary": hr_text,
        "datascience_summary": ds_text,
    }


def explain(pipe: Any, X_train: pd.DataFrame, y_train: pd.Series, x_row: pd.DataFrame, k: int = 2) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Legacy v1 helper for nearest neighbor explanation."""
    res = find_similar_cases(X_train, y_train, x_row, model_key="knn", k=k)
    nb_df = pd.DataFrame(res["neighbors"])
    total = sum(res["neighborhood_distribution"].values()) or 1
    votes = {k_v: float(v / total) for k_v, v in res["neighborhood_distribution"].items()}
    return nb_df, votes


def counterfactual(*args: Any, **kwargs: Any) -> Any:
    """Legacy v1 alias for find_counterfactuals."""
    return find_counterfactuals(*args, **kwargs)


def summarise(pred_data: Dict[str, Any]) -> str:
    """Legacy v1 helper generating a natural language summary."""
    lbl = pred_data.get("label", "Medium")
    conf = pred_data.get("confidence", 0.8)
    return f"Prediction is {lbl} with confidence {conf:.2f}."


