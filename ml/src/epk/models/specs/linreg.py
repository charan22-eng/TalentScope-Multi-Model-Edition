"""Linear Regression (Score to Band) Model Specification."""

from sklearn.linear_model import LinearRegression
from ..score_to_band import ScoreToBand
from ..spec_base import ModelSpec


def make_estimator():
    return ScoreToBand(regressor=LinearRegression(), quantiles=(0.30, 0.75), cv=5)


SPEC = ModelSpec(
    key="linreg",
    label="Linear regression (score to band)",
    family="Linear",
    task="score_to_band",
    needs_scaling=True,
    make=make_estimator,
    search_space={},  # Untuned directly fitted
    n_iter=1,
    explain_tier="native",
)
