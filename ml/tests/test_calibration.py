"""Unit tests for TemperatureScalingCalibrator per ADR-014."""

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

from epk.calibration import TemperatureScalingCalibrator


def test_temperature_scaling_logistic_regression():
    """Verify temperature scaling wraps LogisticRegression predict_proba."""
    X = np.array([
        [1.0, 2.0], [1.5, 1.8], [0.8, 2.2],
        [5.0, 6.0], [5.2, 5.8], [4.9, 6.1],
        [9.0, 1.0], [9.2, 1.2], [8.8, 0.9],
    ])
    y = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])

    base = LogisticRegression(random_state=42).fit(X, y)
    cal = TemperatureScalingCalibrator(estimator=base)
    cal.fit(X, y)

    assert hasattr(cal, "temperature_")
    assert cal.temperature_ > 0.05
    assert cal.classes_.tolist() == [0, 1, 2]

    # Predict proba
    probas = cal.predict_proba(X)
    assert probas.shape == (9, 3)
    np.testing.assert_allclose(probas.sum(axis=1), np.ones(9), atol=1e-5)

    preds = cal.predict(X)
    assert len(preds) == 9
    assert set(preds).issubset({0, 1, 2})


def test_temperature_scaling_svm_decision_function():
    """Verify temperature scaling operates on SVC decision_function."""
    X = np.array([
        [1.0, 2.0], [1.5, 1.8], [0.8, 2.2],
        [5.0, 6.0], [5.2, 5.8], [4.9, 6.1],
        [9.0, 1.0], [9.2, 1.2], [8.8, 0.9],
    ])
    y = np.array([0, 0, 0, 1, 1, 1, 2, 2, 2])

    base = SVC(probability=False, random_state=42).fit(X, y)
    cal = TemperatureScalingCalibrator(estimator=base)
    cal.fit(X, y)

    probas = cal.predict_proba(X)
    assert probas.shape == (9, 3)
    np.testing.assert_allclose(probas.sum(axis=1), np.ones(9), atol=1e-5)

    preds = cal.predict(X)
    assert len(preds) == 9


def test_temperature_scaling_invalid_estimator():
    """Verify error on estimator lacking decision_function and predict_proba."""
    class DummyEstimator:
        pass

    cal = TemperatureScalingCalibrator(estimator=DummyEstimator())
    with pytest.raises(ValueError, match="lacks decision_function or predict_proba"):
        cal.fit([[1, 2]], [0])
