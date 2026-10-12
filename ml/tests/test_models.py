"""Tests for Model Registry, Specs, and ScoreToBand wrapper."""

import numpy as np
import pytest
from sklearn.pipeline import Pipeline
from epk.models.registry import REGISTRY, MODEL_KEYS, get_model_spec
from epk.models.score_to_band import ScoreToBand
from epk.features import build_preprocessor


def test_registry_contains_seven_models():
    assert len(MODEL_KEYS) == 7
    expected = {"linreg", "logreg", "knn", "svm", "dt", "rf", "boost"}
    assert set(MODEL_KEYS) == expected


def test_score_to_band_synthetic():
    np.random.seed(42)
    X = np.random.randn(100, 4)
    # Continuous score 0 to 100
    y_score = np.random.uniform(20, 80, size=100)

    from sklearn.linear_model import LinearRegression

    wrapper = ScoreToBand(regressor=LinearRegression(), quantiles=(0.30, 0.75), cv=3)
    wrapper.fit(X, y_score)

    assert hasattr(wrapper, "classes_")
    np.testing.assert_array_equal(wrapper.classes_, np.array([0, 1, 2]))

    preds = wrapper.predict(X)
    assert set(preds).issubset({0, 1, 2})
    assert len(preds) == 100

    probas = wrapper.predict_proba(X)
    assert probas.shape == (100, 3)
    assert np.all(probas >= 0)
    np.testing.assert_allclose(probas.sum(axis=1), 1.0, rtol=1e-5)


@pytest.mark.parametrize("key", MODEL_KEYS)
def test_all_models_fit_and_classes(key):
    spec = get_model_spec(key)
    est = spec.make()

    np.random.seed(42)
    X = np.random.randn(60, 4)

    if spec.task == "score_to_band":
        y = np.random.uniform(20, 80, size=60)
    else:
        # Balanced 3 classes 0, 1, 2
        y = np.array([0, 1, 2] * 20)

    est.fit(X, y)
    assert hasattr(est, "classes_")
    np.testing.assert_array_equal(est.classes_, np.array([0, 1, 2]))

    preds = est.predict(X)
    assert set(preds).issubset({0, 1, 2})
