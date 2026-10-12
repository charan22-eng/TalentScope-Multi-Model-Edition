"""Decision Tree Model Specification."""

from scipy.stats import loguniform, randint
from sklearn.tree import DecisionTreeClassifier
from ..spec_base import ModelSpec


def make_estimator():
    return DecisionTreeClassifier(random_state=42)


SPEC = ModelSpec(
    key="dt",
    label="Decision tree",
    family="Tree",
    task="classifier",
    needs_scaling=False,
    make=make_estimator,
    search_space={
        "model__max_depth": randint(2, 15),
        "model__min_samples_leaf": randint(1, 40),
        "model__ccp_alpha": loguniform(1e-5, 1e-2),
        "model__criterion": ["gini", "entropy"],
    },
    n_iter=30,
    explain_tier="native",
)
