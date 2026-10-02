import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, OrdinalEncoder

NUMERIC_FEATURES = [
    "attendance",
    "experience_years",
    "training_hours",
    "projects_completed",
    "weekly_hours",
    "prev_score",
]
CATEGORICAL_FEATURES = ["department", "job_level"]


class Winsorizer(BaseEstimator, TransformerMixin):
    """Clip each numeric column to quantile bounds learned on the training data only."""

    def __init__(self, lower=0.01, upper=0.99):
        self.lower = lower
        self.upper = upper

    def fit(self, X, y=None):
        X_arr = np.asarray(X, dtype=float)
        # Using nanquantile to ignore NaNs during fit
        self.lo_ = np.nanquantile(X_arr, self.lower, axis=0)
        self.hi_ = np.nanquantile(X_arr, self.upper, axis=0)
        return self

    def transform(self, X):
        X_arr = np.asarray(X, dtype=float)
        return np.clip(X_arr, self.lo_, self.hi_)


class EngineeredFeatures(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        self.is_fitted_ = True
        return self

    def transform(self, X):
        X_arr = np.asarray(X, dtype=float).copy()
        # Assume columns match NUMERIC_FEATURES order
        # ['attendance', 'experience_years', 'training_hours', 'projects_completed', 'weekly_hours', 'prev_score']
        exp_idx = NUMERIC_FEATURES.index("experience_years")
        proj_idx = NUMERIC_FEATURES.index("projects_completed")
        
        # Safe division: projects / (experience + 1) to avoid divide by zero
        projects_per_year = X_arr[:, proj_idx] / (X_arr[:, exp_idx] + 1.0)
        
        # Append new features
        return np.column_stack([X_arr, projects_per_year])

def build_preprocessor(scaler=None):
    """Builds the scikit-learn preprocessing pipeline."""
    scaler = scaler or MinMaxScaler()

    numeric_transformer = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median")),
            ("winsor", Winsorizer(0.01, 0.99)),
            ("engineer", EngineeredFeatures()),
            ("scale", scaler),
        ]
    )

    # department -> OneHot, job_level -> Ordinal
    # job_level has a natural order, we can map it explicitly or just use OrdinalEncoder
    job_level_categories = [["Junior", "Mid", "Senior", "Lead"]]

    categorical_transformer = ColumnTransformer(
        [
            ("dept_ohe", OneHotEncoder(handle_unknown="ignore"), ["department"]),
            (
                "level_ord",
                OrdinalEncoder(
                    categories=job_level_categories,
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
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ],
        remainder="drop",  # Drop employee_id and performance
    )

    return preprocessor
