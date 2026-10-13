import numpy as np

def compute_conformal_threshold(y_calib, y_prob_calib, classes, alpha=0.1):
    """
    Computes split-conformal threshold using LAC (Least Ambiguous set-valued Classifiers) score.
    """
    n = len(y_calib)
    scores = []
    classes = list(classes)
    for y_true, probs in zip(y_calib, y_prob_calib):
        true_idx = classes.index(y_true)
        # Score is 1 - prob of true class. Lower score is better.
        scores.append(1 - probs[true_idx])
    
    # Sort and take the (n+1)(1-alpha) / n quantile
    scores = np.sort(scores)
    q_level = min((n + 1.0) * (1 - alpha) / n, 1.0)
    
    threshold = np.quantile(scores, q_level, method="higher")
    return threshold

def get_prediction_set(
    probs,
    classes=None,
    threshold=None,
    min_prob_threshold=None,
    tol: float = 1e-9,
):
    """
    Returns the conformal prediction set of classes for a given predicted probability vector.

    Standard split conformal inclusion condition:
        Include class c in C(x) if nonconformity score s_c = 1 - p_c <= qhat.
        Under floating-point arithmetic with tolerance tol:
            (1.0 - p_c) <= threshold + tol

    Equivalence with min_prob_threshold:
        If min_prob_threshold is passed (or derived as 1.0 - threshold):
            p_c >= min_prob_threshold - tol

    Parameters:
    - probs: array-like of predicted class probabilities summing to 1.
    - classes: list/array of class labels (defaults to [0, 1, ..., K-1]).
    - threshold: conformal nonconformity quantile threshold qhat (in [0, 1]).
    - min_prob_threshold: minimum class probability threshold (1.0 - threshold).
      If threshold is provided and min_prob_threshold is None, min_prob_threshold
      defaults to 1.0 - threshold, guaranteeing exact split-conformal inclusion.
    - tol: numerical comparison tolerance for floating-point boundaries (default 1e-9).
    """
    probs = np.asarray(probs, dtype=float)
    if classes is None:
        classes = list(range(len(probs)))
    else:
        classes = list(classes)

    # Standard split conformal: threshold (qhat) provided
    if threshold is not None and min_prob_threshold is None:
        return [classes[i] for i, p in enumerate(probs) if (1.0 - p) <= threshold + tol]

    # Explicit min_prob_threshold provided
    if min_prob_threshold is not None and threshold is None:
        return [classes[i] for i, p in enumerate(probs) if p >= min_prob_threshold - tol]

    # Both provided: evaluate standard split conformal threshold <= qhat + tol
    if threshold is not None and min_prob_threshold is not None:
        return [classes[i] for i, p in enumerate(probs) if (1.0 - p) <= threshold + tol]

    raise ValueError("Must provide either threshold or min_prob_threshold")


def stability_score(probs):
    """
    A simple metric between 0 and 1 indicating how stable the prediction is 
    (1 means 100% confidence in one class, 0 means uniform distribution).
    """
    p = np.asarray(probs)
    # Normalized entropy
    entropy = -np.sum(p * np.log(p + 1e-9))
    max_entropy = np.log(len(p))
    return max(0.0, 1.0 - (entropy / max_entropy))

def performance_index(probs):
    """
    Expected value assuming Low=0, Medium=50, High=100.
    """
    return float(probs[0] * 0 + probs[1] * 50 + probs[2] * 100)
