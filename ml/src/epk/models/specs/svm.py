"""Support Vector Machine (RBF) Model Specification."""

from scipy.stats import loguniform
from sklearn.svm import SVC
from ..spec_base import ModelSpec


def make_estimator():
    return SVC(kernel="rbf", probability=False, random_state=42)


SPEC = ModelSpec(
    key="svm",
    label="Support vector machine (RBF)",
    family="Kernel",
    task="classifier",
    needs_scaling=True,
    make=make_estimator,
    search_space={
        "model__C": loguniform(0.1, 100.0),
        "model__gamma": loguniform(1e-3, 1.0),
    },
    n_iter=30,
    explain_tier="post_hoc",
)
