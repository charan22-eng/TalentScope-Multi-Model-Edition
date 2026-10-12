"""Model-aware preprocessing pipeline for TalentScope Multi-Model Edition.

One unified factory build_preprocessor(spec) tailored to model scaling needs:
- Trees (dt, rf, boost): No scaling.
- Distance & margin models (linreg, logreg, knn, svm): StandardScaler.
- Imputation: Median imputation for all numeric features.
- Outlier control: Winsorizer fitted strictly on training data (G4 leakage-safe).
- Categoricals: Department (OneHotEncoder), Job Level (OrdinalEncoder).
"""

from typing import Any
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

NUMERIC_FEATURES = [
    "attendance",
    "experience_years",
    "training_hours",
    "projects_completed",
    "weekly_hours",
    "prev_score",
    "peer_feedback",
    "tasks_on_time_pct",
    "certifications",
]

CATEGORICAL_FEATURES = ["department"]
ORDINAL_FEATURES = ["job_level"]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + ORDINAL_FEATURES

JOB_LEVEL_CATEGORIES = [["Junior", "Mid", "Senior", "Lead"]]
DEPTS = ["Engineering", "Sales", "HR", "Finance", "Operations", "Support", "Marketing", "Legal"]


class Winsorizer(BaseEstimator, TransformerMixin):
    """Clip each numeric column to quantile bounds learned on the training data only."""

    def __init__(self, lower: float = 0.01, upper: float = 0.99):
        self.lower = lower
        self.upper = upper

    def fit(self, X, y=None):
        X_arr = np.asarray(X, dtype=float)
        self.lo_ = np.nanquantile(X_arr, self.lower, axis=0)
        self.hi_ = np.nanquantile(X_arr, self.upper, axis=0)
        return self

    def transform(self, X):
        X_arr = np.asarray(X, dtype=float)
        return np.clip(X_arr, self.lo_, self.hi_)


def build_preprocessor(
    spec: Any = None,
    scale_override: bool | None = None,
    winsorize: bool = True,
) -> ColumnTransformer:
    """Build model-aware preprocessing pipeline.

    Args:
        spec: A ModelSpec instance, or None. If spec.needs_scaling is True,
              StandardScaler is applied; otherwise numerics are unscaled.
        scale_override: Explicit boolean to force scaling on or off (e.g. for ablation).
        winsorize: Boolean indicating whether to fit Winsorizer on training numerics.
    """
    if scale_override is not None:
        needs_scaling = scale_override
    elif hasattr(spec, "needs_scaling"):
        needs_scaling = bool(spec.needs_scaling)
    elif spec is None:
        needs_scaling = True
    else:
        # Backward compatibility if an existing transformer was passed
        needs_scaling = True

    num_steps: list[tuple[str, Any]] = [
        ("impute", SimpleImputer(strategy="median")),
    ]

    if winsorize:
        num_steps.append(("winsor", Winsorizer(0.01, 0.99)))
    else:
        num_steps.append(("winsor", "passthrough"))

    if needs_scaling:
        num_steps.append(("scale", StandardScaler()))
    else:
        num_steps.append(("scale", "passthrough"))

    numeric_transformer = Pipeline(num_steps)

    categorical_transformer = ColumnTransformer(
        [
            ("dept_ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["department"]),
            (
                "level_ord",
                OrdinalEncoder(
                    categories=JOB_LEVEL_CATEGORIES,
                    handle_unknown="use_encoded_value",
                    unknown_value=-1,
                ),
                ["job_level"],
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES + ORDINAL_FEATURES),
        ],
        remainder="drop",
    )

    return preprocessor
