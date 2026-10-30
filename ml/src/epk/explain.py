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
    """Unwrap preprocessor and core estimator from pipeline, CalibratedClassifierCV, or TemperatureScalingCalibrator."""
    est = pipeline_or_calibrator
    if hasattr(est, "calibrated_classifiers_"):
        # Scikit-learn CalibratedClassifierCV
        est = est.calibrated_classifiers_[0].estimator
    elif hasattr(est, "estimator") and not hasattr(est, "named_steps"):
        # TemperatureScalingCalibrator or custom wrapper
        est = est.estimator

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
        primary_lever = next(iter(changes_accum.keys())) if changes_accum else "training_hours"
        orig_v = float(x_row[primary_lever].iloc[0]) if primary_lever in x_row.columns else 0.0
        prop_v = float(changes_accum.get(primary_lever, orig_v))
        options.append({
            "option_id": 1,
            "description": "Multi-lever balanced intervention",
            "changes": changes_accum,
            "feature": primary_lever,
            "original_value": round(orig_v, 1),
            "proposed_value": round(prop_v, 1),
            "delta": round(prop_v - orig_v, 1),
            "target_class": target_band,
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
                    "feature": single_lever,
                    "original_value": round(val, 1),
                    "proposed_value": round(new_val, 1),
                    "delta": round(new_val - val, 1),
                    "target_class": target_band,
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
    if not numeric_cols or train_df.empty:
        return {
            "banner": banner,
            "is_native_reasoning": is_knn,
            "model_key": model_key,
            "k": k,
            "neighbors": [],
            "neighborhood_distribution": {},
        }

    meds = train_df[numeric_cols].median(numeric_only=True)
    X_train_num = train_df[numeric_cols].fillna(meds).to_numpy(dtype=float)
    x_num = x_row[numeric_cols].fillna(meds).to_numpy(dtype=float)

    # Normalized Euclidean distance
    stds = np.nanstd(X_train_num, axis=0) + 1e-6
    X_scaled = X_train_num / stds
    x_scaled = x_num / stds

    dists = cdist(x_scaled, X_scaled, metric="euclidean")[0]
    nearest_indices = np.argsort(dists)[:k]

    neighbors = []
    for idx in nearest_indices:
        raw_item = train_df.iloc[idx].to_dict()
        item = {
            k_col: (None if pd.isna(v_val) else v_val)
            for k_col, v_val in raw_item.items()
        }
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


def compute_performance_index(model: Any, x_row: pd.DataFrame, key: str, precomputed_probs: Optional[np.ndarray] = None) -> float:
    """Compute performance index on a 0-100 scale."""
    if key == "linreg":
        prep, core = get_underlying_model(model)
        prep_X = prep.transform(x_row) if prep else x_row
        score = core.predict_score(prep_X)[0]
        return round(float(np.clip(score, 0.0, 100.0)), 2)

    probas = precomputed_probs if precomputed_probs is not None else model.predict_proba(x_row)[0]
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


def generate_ollama_persona_explanations(
    key: str,
    label: str,
    pred_band: str,
    proba: List[float],
    attribution: Dict[str, float],
    counterfactuals: List[Dict[str, Any]],
    stability: float,
    candidate_features: Optional[Dict[str, Any]] = None,
    similar_cases: Optional[Dict[str, Any]] = None,
    base_url: str = "http://localhost:11434",
    preferred_model: str = "qwen2.5:3b",
    timeout_s: float = 15.0,
) -> Dict[str, Any]:
    """Synthesize deep, faithful model explanations using local Ollama model.

    Strictly adheres to Guard G9 (zero employee identifiers) and Guard G10 (loopback only).
    Gracefully falls back to deterministic template summaries if Ollama is unavailable.
    """
    import logging
    import time
    import httpx
    from epk.llm.client import assert_local
    from epk.llm.prompts import FORBIDDEN_EMPLOYEE_PROMPT_KEYS, scan_prompt_for_forbidden_keys

    logger = logging.getLogger("talentscope.explain.ollama")

    fallback_summaries = generate_persona_summaries(
        key=key,
        label=label,
        pred_band=pred_band,
        proba=proba,
        attribution=attribution,
        counterfactuals=counterfactuals,
        stability=stability,
    )

    top_pos_list = [f"{k.replace('_', ' ').title()}: +{v:.2f} positive impact" for k, v in attribution.items() if v > 0.02][:3]
    top_neg_list = [f"{k.replace('_', ' ').title()}: {v:.2f} limiting impact" for k, v in attribution.items() if v < -0.02][:2]
    default_key_drivers = top_pos_list + top_neg_list
    if not default_key_drivers:
        default_key_drivers = ["Consistent baseline metrics across performance dimensions"]

    default_guidance = (
        f"Maintain high standards in primary driver metrics ({', '.join([k.replace('_', ' ') for k, v in list(attribution.items())[:2]])}). "
        f"Examine targeted counterfactual recommendations to elevate to a higher tier."
    )

    t0 = time.time()
    try:
        assert_local(base_url)

        # Discover installed models
        tags_resp = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=3.0)
        tags_resp.raise_for_status()
        installed_models = [m.get("name", "") for m in tags_resp.json().get("models", [])]

        if not installed_models:
            raise RuntimeError("No models installed in local Ollama runtime")

        # Pick best responsive model from installed
        chosen_model = None
        if preferred_model in installed_models:
            chosen_model = preferred_model
        else:
            candidates = ["qwen2.5:3b", "qwen2.5:7b", "qwen-judge:latest", "llama-judge:latest", "llama3.1:latest", installed_models[0]]
            for c in candidates:
                if c in installed_models:
                    chosen_model = c
                    break

        if not chosen_model:
            chosen_model = installed_models[0]

        # Sanitize candidate features for G9 compliance
        clean_features = {}
        if candidate_features:
            for k_feat, v_feat in candidate_features.items():
                if k_feat.lower() not in FORBIDDEN_EMPLOYEE_PROMPT_KEYS:
                    clean_features[k_feat] = v_feat

        p_low = round(proba[0] * 100, 1) if len(proba) > 0 else 0
        p_med = round(proba[1] * 100, 1) if len(proba) > 1 else 0
        p_high = round(proba[2] * 100, 1) if len(proba) > 2 else 0

        sim_dist = {}
        if similar_cases and isinstance(similar_cases, dict):
            sim_dist = similar_cases.get("neighborhood_distribution", {})

        top_attribs_str = ", ".join([f"{k} ({'+' if v > 0 else ''}{v:.3f})" for k, v in list(attribution.items())[:4]])
        cf_str = "None required (already High band)"
        if counterfactuals:
            cf0 = counterfactuals[0]
            cf_str = f"Increase {cf0.get('feature', 'key metrics')} from {cf0.get('original_value', '')} to {cf0.get('proposed_value', '')} to reach {cf0.get('target_class', 'High')}"

        prompt = (
            f"You are an expert HR and Machine Learning explainability advisor for TalentScope.\n"
            f"Synthesize an accurate, contextual, and insightful explanation for the following candidate prediction:\n"
            f"- Model Architecture: {label} (Key: {key})\n"
            f"- Predicted Performance Band: {pred_band} (Class probabilities: Low={p_low}%, Medium={p_med}%, High={p_high}%)\n"
            f"- Prediction Stability Margin: {stability:.3f} (confidence gap between top two classes)\n"
            f"- Evaluated Features: {json.dumps(clean_features)}\n"
            f"- Top Local Attribution Drivers: {top_attribs_str}\n"
            f"- Counterfactual Pathway: {cf_str}\n"
            f"- Similar Historical Cases: {json.dumps(sim_dist)}\n\n"
            f"Provide a structured response adhering strictly to the JSON schema:\n"
            f"1. 'hr_summary': 2-3 clear, professional, empathetic paragraphs for HR leaders and managers explaining why the model predicted '{pred_band}', recognizing specific high achievements, addressing bottlenecks, and recommending next management actions.\n"
            f"2. 'datascience_summary': A rigorous technical review for Data Scientists and ML Auditors covering model mechanism ({label}), probability margin ({stability:.3f}), top feature attributions, and local sensitivity.\n"
            f"3. 'key_drivers': An array of 3-4 concise bullet points summarizing primary drivers with exact metrics.\n"
            f"4. 'actionable_guidance': Specific, realistic steps the employee or manager can take to elevate performance."
        )

        violations = scan_prompt_for_forbidden_keys(prompt)
        if violations:
            logger.warning("Guard G9 violation in prompt; falling back to template: %s", violations)
            raise ValueError(f"Privacy guard violation: {violations}")

        schema = {
            "type": "object",
            "properties": {
                "hr_summary": {"type": "string"},
                "datascience_summary": {"type": "string"},
                "key_drivers": {"type": "array", "items": {"type": "string"}},
                "actionable_guidance": {"type": "string"},
            },
            "required": ["hr_summary", "datascience_summary", "key_drivers", "actionable_guidance"],
        }

        call_resp = httpx.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={
                "model": chosen_model,
                "messages": [
                    {"role": "system", "content": "You are a talent analytics and ML explainability expert. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "format": schema,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "seed": 42,
                    "num_predict": 750,
                },
            },
            timeout=timeout_s,
        )
        call_resp.raise_for_status()

        raw_content = call_resp.json().get("message", {}).get("content", "{}")
        parsed = json.loads(raw_content)

        elapsed_ms = round((time.time() - t0) * 1000.0, 1)

        hr_sum = parsed.get("hr_summary", "").strip() or fallback_summaries["hr_summary"]
        ds_sum = parsed.get("datascience_summary", "").strip() or fallback_summaries["datascience_summary"]
        drivers = parsed.get("key_drivers") if isinstance(parsed.get("key_drivers"), list) and parsed.get("key_drivers") else default_key_drivers
        guidance = parsed.get("actionable_guidance", "").strip() or default_guidance

        return {
            "persona_summaries": {
                "hr_summary": hr_sum,
                "datascience_summary": ds_sum,
            },
            "key_drivers": drivers,
            "actionable_guidance": guidance,
            "llm_metadata": {
                "source": "ollama",
                "model": chosen_model,
                "latency_ms": elapsed_ms,
            },
        }

    except Exception as exc:
        elapsed_ms = round((time.time() - t0) * 1000.0, 1)
        logger.warning("Ollama explainability fallback triggered: %s", exc)
        return {
            "persona_summaries": fallback_summaries,
            "key_drivers": default_key_drivers,
            "actionable_guidance": default_guidance,
            "llm_metadata": {
                "source": "template_fallback",
                "model": "none",
                "latency_ms": elapsed_ms,
                "error": str(exc),
            },
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


