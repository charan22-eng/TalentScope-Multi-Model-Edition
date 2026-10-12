"""Base dataclass for model specifications."""

from dataclasses import dataclass
from typing import Callable, Literal
from sklearn.base import BaseEstimator


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
