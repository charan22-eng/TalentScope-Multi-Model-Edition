"""Multinomial Temperature Scaling Calibrator per ADR-014.

Implements probability calibration via a single learnable temperature scalar T > 0:
    P(y = c | x) = softmax(z / T)_c
Where logits z are derived from:
  - decision_function(X) if available (e.g. SVM), or
  - log(clip(predict_proba(X), 1e-12, 1.0)) if probabilities are returned.

Temperature T is fitted by minimizing Negative Log-Likelihood (cross-entropy)
on held-out calibration split cal-A using scipy.optimize.minimize_scalar.
"""

from typing import Any, Optional
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.base import BaseEstimator, ClassifierMixin


class TemperatureScalingCalibrator(BaseEstimator, ClassifierMixin):
    """Multinomial Temperature Scaling Calibrator.

    Wraps a pre-fitted estimator (pipeline or model) and scales its output
    probabilities or decision values by a scalar temperature T > 0.
    """

    def __init__(self, estimator: Any = None, temperature: float = 1.0):
        self.estimator = estimator
        self.temperature = temperature
        self.temperature_ = temperature
        self.classes_ = np.array([0, 1, 2])

    def _get_logits(self, X) -> np.ndarray:
        if hasattr(self.estimator, "decision_function"):
            logits = self.estimator.decision_function(X)
            if logits.ndim == 1:
                logits = np.vstack([-logits, logits]).T
            return logits
        elif hasattr(self.estimator, "predict_proba"):
            p = self.estimator.predict_proba(X)
            p = np.clip(p, 1e-12, 1.0 - 1e-12)
            logits = np.log(p)
            # Center logits: log(p) - mean(log(p))
            return logits - np.mean(logits, axis=1, keepdims=True)
        else:
            raise ValueError(f"Estimator {self.estimator} lacks decision_function or predict_proba")

    def fit(self, X, y) -> "TemperatureScalingCalibrator":
        """Fit temperature parameter T on calibration data (cal-A)."""
        logits = self._get_logits(X)
        y = np.asarray(y, dtype=int)
        n = len(y)

        def nll_objective(T: float) -> float:
            if T <= 1e-4:
                return 1e6
            scaled = logits / T
            max_s = np.max(scaled, axis=1, keepdims=True)
            log_sum_exp = max_s + np.log(np.sum(np.exp(scaled - max_s), axis=1, keepdims=True))
            log_probs = scaled - log_sum_exp
            return float(-np.sum(log_probs[np.arange(n), y]) / n)

        res = minimize_scalar(nll_objective, bounds=(0.05, 10.0), method="bounded")
        self.temperature_ = float(res.x)
        self.temperature = self.temperature_
        return self

    def predict_proba(self, X) -> np.ndarray:
        """Compute calibrated class probabilities."""
        logits = self._get_logits(X)
        return softmax(logits / self.temperature_, axis=1)

    def predict(self, X) -> np.ndarray:
        """Predict class labels with highest calibrated probability."""
        p = self.predict_proba(X)
        return np.argmax(p, axis=1)
