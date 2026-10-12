"""K-Nearest Neighbours Model Specification."""

from sklearn.neighbors import KNeighborsClassifier
from ..spec_base import ModelSpec


def make_estimator():
    return KNeighborsClassifier(n_neighbors=25, weights="distance")


SPEC = ModelSpec(
    key="knn",
    label="K-nearest neighbours",
    family="Instance",
    task="classifier",
    needs_scaling=True,
    make=make_estimator,
    search_space={
        "model__n_neighbors": [3, 5, 9, 15, 21, 25, 31, 41, 51],
        "model__weights": ["uniform", "distance"],
        "model__p": [1, 2],
    },
    n_iter=30,
    explain_tier="partial",
)
