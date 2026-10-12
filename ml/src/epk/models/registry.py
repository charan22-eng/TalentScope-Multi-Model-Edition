"""Model Registry for TalentScope Multi-Model Edition.

Defines the ModelSpec dataclass and registry of seven models.
Adding an eighth model requires only adding a new spec.
"""

from dataclasses import dataclass
from typing import Callable, Literal
from sklearn.base import BaseEstimator
from scipy.stats import loguniform, randint, uniform
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

from .score_to_band import ScoreToBand


@dataclass(frozen=True)
class ModelSpec:
    """Specification of an algorithm participating in the comparison arena."""

    key: str
    label: str
    family: str
    task: Literal["classifier", "score_to_band"]
    needs_scaling: bool
    make: Callable[[], BaseEstimator]
    search_space: dict
    n_iter: int = 30
    explain_tier: Literal["native", "partial", "post_hoc"] = "post_hoc"


def _make_linreg():
    return ScoreToBand(regressor=LinearRegression(), quantiles=(0.30, 0.75), cv=5)


def _make_logreg():
    return LogisticRegression(max_iter=5000, random_state=42)


def _make_knn():
    return KNeighborsClassifier(n_neighbors=25, weights="distance")


def _make_svm():
    # Tune with probability=False for training speed; calibrate post-hoc on cal-A
    return SVC(kernel="rbf", probability=False, random_state=42)


def _make_dt():
    return DecisionTreeClassifier(random_state=42)


def _make_rf():
    return RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)


def _make_boost():
    return HistGradientBoostingClassifier(random_state=42)


REGISTRY: dict[str, ModelSpec] = {
    "linreg": ModelSpec(
        key="linreg",
        label="Linear regression (score to band)",
        family="Linear",
        task="score_to_band",
        needs_scaling=True,
        make=_make_linreg,
        search_space={},  # Untuned directly fitted
        n_iter=1,
        explain_tier="native",
    ),
    "logreg": ModelSpec(
        key="logreg",
        label="Logistic regression (multinomial)",
        family="Linear",
        task="classifier",
        needs_scaling=True,
        make=_make_logreg,
        search_space={
            "model__C": loguniform(1e-3, 1e2),
            "model__class_weight": [None, "balanced"],
        },
        n_iter=30,
        explain_tier="native",
    ),
    "knn": ModelSpec(
        key="knn",
        label="K-nearest neighbours",
        family="Instance",
        task="classifier",
        needs_scaling=True,
        make=_make_knn,
        search_space={
            "model__n_neighbors": [3, 5, 9, 15, 21, 25, 31, 41, 51],
            "model__weights": ["uniform", "distance"],
            "model__p": [1, 2],
        },
        n_iter=30,
        explain_tier="partial",
    ),
    "svm": ModelSpec(
        key="svm",
        label="Support vector machine (RBF)",
        family="Kernel",
        task="classifier",
        needs_scaling=True,
        make=_make_svm,
        search_space={
            "model__C": loguniform(0.1, 100.0),
            "model__gamma": loguniform(1e-3, 1.0),
        },
        n_iter=30,
        explain_tier="post_hoc",
    ),
    "dt": ModelSpec(
        key="dt",
        label="Decision tree",
        family="Tree",
        task="classifier",
        needs_scaling=False,
        make=_make_dt,
        search_space={
            "model__max_depth": randint(2, 15),
            "model__min_samples_leaf": randint(1, 40),
            "model__ccp_alpha": loguniform(1e-5, 1e-2),
            "model__criterion": ["gini", "entropy"],
        },
        n_iter=30,
        explain_tier="native",
    ),
    "rf": ModelSpec(
        key="rf",
        label="Random forest",
        family="Ensemble",
        task="classifier",
        needs_scaling=False,
        make=_make_rf,
        search_space={
            "model__n_estimators": randint(50, 300),
            "model__max_depth": [None, 6, 10, 15, 20],
            "model__min_samples_leaf": randint(1, 10),
            "model__max_features": ["sqrt", "log2", None],
        },
        n_iter=30,
        explain_tier="partial",
    ),
    "boost": ModelSpec(
        key="boost",
        label="Gradient boosting (histogram)",
        family="Ensemble",
        task="classifier",
        needs_scaling=False,
        make=_make_boost,
        search_space={
            "model__learning_rate": loguniform(0.02, 0.3),
            "model__max_iter": randint(50, 300),
            "model__max_leaf_nodes": randint(8, 64),
            "model__l2_regularization": loguniform(1e-4, 10.0),
        },
        n_iter=30,
        explain_tier="partial",
    ),
}

MODEL_KEYS = list(REGISTRY.keys())


def get_model_spec(key: str) -> ModelSpec:
    if key not in REGISTRY:
        raise ValueError(f"Unknown model key '{key}'. Supported models: {MODEL_KEYS}")
    return REGISTRY[key]


def list_model_specs() -> list[ModelSpec]:
    return list(REGISTRY.values())
