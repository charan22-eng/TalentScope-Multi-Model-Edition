"""Unit tests for split-conformal prediction sets, tied probabilities, and fallback handling."""
import numpy as np
import pytest

from epk.uncertainty import get_prediction_set, compute_conformal_threshold


def test_conformal_tied_probabilities():
    """Verify that tied probabilities are handled consistently with threshold."""
    classes = ["Low", "Medium", "High"]

    # Exactly tied probabilities between two classes (0.50, 0.50, 0.0)
    probs_two_way_tie = np.array([0.5, 0.5, 0.0])

    # threshold = 0.50 => 1 - p <= 0.50 => p >= 0.50
    pred_set_50 = get_prediction_set(probs_two_way_tie, classes, threshold=0.50)
    assert pred_set_50 == ["Low", "Medium"], "Both tied classes with p >= 0.50 must be included"

    # threshold = 0.49 => 1 - p <= 0.49 => p >= 0.51
    pred_set_49 = get_prediction_set(probs_two_way_tie, classes, threshold=0.49, fallback_to_argmax=False)
    assert pred_set_49 == [], "Neither tied class should be included if score > threshold"

    # Three-way tie
    probs_three_way_tie = np.array([1 / 3, 1 / 3, 1 / 3])
    # threshold = 0.67 => 1 - p <= 0.67 => p >= 0.33
    pred_set_three = get_prediction_set(probs_three_way_tie, classes, threshold=0.67)
    assert pred_set_three == ["Low", "Medium", "High"], "All three tied classes must be included"

    # Discrete boundary edge case mimicking Decision Tree leaf ties
    probs_dt_tie = np.array([0.1482, 0.1482, 0.7036])
    # threshold = 0.8518 => 1 - p <= 0.8518 => p >= 0.1482
    pred_set_exact = get_prediction_set(probs_dt_tie, classes, threshold=0.8518)
    assert pred_set_exact == ["Low", "Medium", "High"]

    # threshold = 0.8517 => p >= 0.1483
    pred_set_strict = get_prediction_set(probs_dt_tie, classes, threshold=0.8517)
    assert pred_set_strict == ["High"]


def test_conformal_fallback_guarantee():
    """Verify standard split conformal empty set vs fallback_to_argmax operational guarantee."""
    classes = ["Low", "Medium", "High"]
    probs = np.array([0.25, 0.40, 0.35])

    # Very strict threshold: threshold = 0.50 => p >= 0.50. No class satisfies this.
    empty_set = get_prediction_set(probs, classes, threshold=0.50, fallback_to_argmax=False)
    assert empty_set == [], "Standard conformal must allow empty set when no class meets threshold"

    # Fallback to argmax
    fallback_set = get_prediction_set(probs, classes, threshold=0.50, fallback_to_argmax=True)
    assert fallback_set == ["Medium"], "Fallback must return top-1 class when set is otherwise empty"


def test_conformal_fallback_with_tie():
    """Verify fallback when two classes share the maximal probability."""
    classes = ["Low", "Medium", "High"]
    probs = np.array([0.45, 0.45, 0.10])

    # Strict threshold 0.50 => p >= 0.50 => none pass
    empty_set = get_prediction_set(probs, classes, threshold=0.50, fallback_to_argmax=False)
    assert empty_set == []

    # Fallback returns both tied top classes
    fallback_set = get_prediction_set(probs, classes, threshold=0.50, fallback_to_argmax=True)
    assert fallback_set == ["Low", "Medium"], "Fallback on tie must include all tied top classes"


def test_conformal_default_classes_and_validation():
    """Verify default integer class indices and error on missing threshold."""
    probs = np.array([0.2, 0.8])
    assert get_prediction_set(probs, threshold=0.5) == [1]

    with pytest.raises(ValueError, match="Must provide threshold"):
        get_prediction_set(probs)
