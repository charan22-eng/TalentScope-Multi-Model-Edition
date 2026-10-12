"""Random Forest Model Specification."""

from scipy.stats import randint
from sklearn.ensemble import RandomForestClassifier
from ..spec_base import ModelSpec


def make_estimator():
    return RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)


SPEC = ModelSpec(
    key="rf",
    label="Random forest",
    family="Ensemble",
    task="classifier",
    needs_scaling=False,
    make=make_estimator,
    search_space={
        "model__n_estimators": randint(50, 300),
        "model__max_depth": [None, 6, 10, 15, 20],
        "model__min_samples_leaf": randint(1, 10),
        "model__max_features": ["sqrt", "log2", None],
    },
    n_iter=30,
    explain_tier="partial",
)
