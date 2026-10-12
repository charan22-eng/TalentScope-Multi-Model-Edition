"""Precompute global explainability artifacts for all 7 models (Stage E).

Generates:
- artifacts/v2/explainability/pca.json (E4)
- artifacts/v2/explainability/importance_matrix.json (E5)
- artifacts/v2/explainability/surfaces.json (E5)
"""

import json
import sys
from pathlib import Path

# Ensure ml/src is on sys.path
_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.inspection import permutation_importance

from epk.explain import (
    explain_model_native,
    fit_pca_projection,
    generate_decision_landscape_grid,
)
from epk.features import ALL_FEATURES, NUMERIC_FEATURES
from epk.labels import encode_bands
from epk.models.registry import MODEL_KEYS, get_model_spec
from epk.split import load_split


def main():
    print("Precomputing Stage E Explainability Artifacts...")
    out_dir = Path("artifacts/v2/explainability")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    df = pd.read_csv("data/nonlinear/dataset.csv")
    split = load_split("data/processed/split.json")
    train_idx = split["train"]
    train_df = df.iloc[train_idx].reset_index(drop=True)

    # 2. PCA 2D/3D projection (E4)
    print("Fitting PCA projection...")
    pca_data = fit_pca_projection(train_df, max_background_samples=2000)
    with open(out_dir / "pca.json", "w", encoding="utf-8") as f:
        json.dump(pca_data, f, indent=2)

    # 3. Load all 7 models
    models = {}
    for k in MODEL_KEYS:
        m_path = Path("artifacts/v2/models") / k / "model.joblib"
        models[k] = joblib.load(m_path)

    # 4. Decision landscape surface grids (E5)
    print("Generating decision landscapes (40x40 grids)...")
    surfaces = {}
    for k in MODEL_KEYS:
        grid = generate_decision_landscape_grid(
            models[k],
            train_df[ALL_FEATURES],
            feature_x="attendance",
            feature_y="projects_completed",
            grid_size=40,
        )
        surfaces[k] = grid

    with open(out_dir / "surfaces.json", "w", encoding="utf-8") as f:
        json.dump(surfaces, f, indent=2)

    # 5. Permutation importance & Spearman agreement matrix (E5)
    print("Computing feature importance vectors & Spearman agreement...")
    X_sample = train_df[ALL_FEATURES].iloc[:500]
    y_sample = encode_bands(train_df["performance"].iloc[:500])

    model_importances = {}
    for k in MODEL_KEYS:
        res = permutation_importance(models[k], X_sample, y_sample, n_repeats=3, random_state=42)
        model_importances[k] = res.importances_mean.tolist()

    agreement_matrix = {}
    for k1 in MODEL_KEYS:
        agreement_matrix[k1] = {}
        for k2 in MODEL_KEYS:
            rho, _ = spearmanr(model_importances[k1], model_importances[k2])
            agreement_matrix[k1][k2] = round(float(rho), 4) if not np.isnan(rho) else 1.0

    imp_data = {
        "features": ALL_FEATURES,
        "importances": {
            k: {fn: round(float(val), 4) for fn, val in zip(ALL_FEATURES, model_importances[k])}
            for k in MODEL_KEYS
        },
        "spearman_agreement_matrix": agreement_matrix,
    }

    with open(out_dir / "importance_matrix.json", "w", encoding="utf-8") as f:
        json.dump(imp_data, f, indent=2)

    print("Stage E explainability precomputation complete.")


if __name__ == "__main__":
    main()
