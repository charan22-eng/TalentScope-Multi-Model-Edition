"""Unit tests for split-conformal prediction sets and tied probabilities handling."""
import numpy as np
import pytest

from epk.uncertainty import get_prediction_set, compute_conformal_threshold


def test_conformal_tied_probabilities():
    """Verify that tied probabilities are handled consistently and included/excluded uniformly."""
    classes = ["Low", "Medium", "High"]

    # Exactly tied probabilities between two classes
    probs_two_way_tie = np.array([0.5, 0.5, 0.0])
    pred_set_50 = get_prediction_set(probs_two_way_tie, classes, min_prob_threshold=0.50)
    assert pred_set_50 == ["Low", "Medium"], "Both tied classes with p >= 0.50 must be included"

    pred_set_51 = get_prediction_set(probs_two_way_tie, classes, min_prob_threshold=0.51)
    assert pred_set_51 == [], "Neither tied class should be included if threshold > probability"

    # Three-way tie
    probs_three_way_tie = np.array([1 / 3, 1 / 3, 1 / 3])
    pred_set_three = get_prediction_set(probs_three_way_tie, classes, min_prob_threshold=0.33)
    assert pred_set_three == ["Low", "Medium", "High"], "All three tied classes must be included"

    # Discrete boundary edge case mimicking Decision Tree leaf ties
    probs_dt_tie = np.array([0.1482, 0.1482, 0.7036])
    pred_set_exact = get_prediction_set(probs_dt_tie, classes, min_prob_threshold=0.1482)
    assert pred_set_exact == ["Low", "Medium", "High"]

    pred_set_strict = get_prediction_set(probs_dt_tie, classes, min_prob_threshold=0.1483)
    assert pred_set_strict == ["High"]


def test_conformal_threshold_and_min_prob_equivalence():
    """Verify equivalence between threshold (score <= threshold) and min_prob_threshold (prob >= 1 - threshold)."""
    probs = np.array([0.10, 0.30, 0.60])
    threshold = 0.70  # score = 1 - p <= 0.70 <=> p >= 0.30
    min_prob = 0.30

    set_via_thresh = get_prediction_set(probs, classes=[0, 1, 2], threshold=threshold)
    set_via_min_p = get_prediction_set(probs, classes=[0, 1, 2], min_prob_threshold=min_prob)

    assert set_via_thresh == [1, 2]
    assert set_via_min_p == [1, 2]
    assert set_via_thresh == set_via_min_p


def test_conformal_default_classes_and_validation():
    """Verify default integer class indices and error on missing threshold."""
    probs = np.array([0.2, 0.8])
    assert get_prediction_set(probs, min_prob_threshold=0.5) == [1]

    with pytest.raises(ValueError, match="Must provide either threshold or min_prob_threshold"):
        get_prediction_set(probs)
