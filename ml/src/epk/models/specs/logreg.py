"""Logistic Regression Model Specification."""

from scipy.stats import loguniform
from sklearn.linear_model import LogisticRegression
from ..spec_base import ModelSpec


def make_estimator():
    return LogisticRegression(max_iter=5000, random_state=42)


SPEC = ModelSpec(
    key="logreg",
    label="Logistic regression (multinomial)",
    family="Linear",
    task="classifier",
    needs_scaling=True,
    make=make_estimator,
    search_space={
        "model__C": loguniform(1e-3, 1e2),
        "model__class_weight": [None, "balanced"],
    },
    n_iter=30,
    explain_tier="native",
)
