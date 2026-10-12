"""Gradient Boosting (Histogram) Model Specification."""

from scipy.stats import loguniform, randint
from sklearn.ensemble import HistGradientBoostingClassifier
from ..spec_base import ModelSpec


def make_estimator():
    return HistGradientBoostingClassifier(random_state=42)


SPEC = ModelSpec(
    key="boost",
    label="Gradient boosting (histogram)",
    family="Ensemble",
    task="classifier",
    needs_scaling=False,
    make=make_estimator,
    search_space={
        "model__learning_rate": loguniform(0.02, 0.3),
        "model__max_iter": randint(50, 300),
        "model__max_leaf_nodes": randint(8, 64),
        "model__l2_regularization": loguniform(1e-4, 10.0),
    },
    n_iter=30,
    explain_tier="partial",
)
