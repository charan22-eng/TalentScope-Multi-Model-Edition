"""ScoreToBand: Wrap a continuous regressor so it can join the classification arena.

Thresholds are the 30th and 75th percentiles of the TRAIN scores.
Probabilities are derived from a homoscedastic Gaussian residual model
where sigma is estimated from out-of-fold cross-validation residuals.
"""

import numpy as np
from scipy.stats import norm
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.model_selection import cross_val_predict


class ScoreToBand(BaseEstimator, ClassifierMixin):
    """Regress continuous performance_score, map to ordered bands 0, 1, 2, and derive probabilities."""

    def __init__(self, regressor=None, quantiles=(0.30, 0.75), cv=5):
        self.regressor = regressor
        self.quantiles = quantiles
        self.cv = cv

    def fit(self, X, y_score):
        y = np.asarray(y_score, dtype=float)
        self.thresholds_ = np.quantile(y, self.quantiles)
        reg = self.regressor
        oof = cross_val_predict(clone(reg), X, y, cv=self.cv)
        residuals = y - oof
        self.sigma_ = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 1.0
        if self.sigma_ < 1e-6:
            self.sigma_ = 1.0
        self.regressor_ = clone(reg).fit(X, y)
        self.classes_ = np.array([0, 1, 2])
        return self

    def predict_score(self, X):
        return self.regressor_.predict(X)

    def predict(self, X):
        return np.searchsorted(self.thresholds_, self.predict_score(X), side="right")

    def predict_proba(self, X):
        mu = self.predict_score(X)[:, None]
        edges = np.concatenate([[-np.inf], self.thresholds_, [np.inf]])[None, :]
        p = np.diff(norm.cdf((edges - mu) / self.sigma_), axis=1)
        p = np.clip(p, 1e-12, 1.0)
        return p / p.sum(axis=1, keepdims=True)
