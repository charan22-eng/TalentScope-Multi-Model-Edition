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
    threshold: float = None,
    fallback_to_argmax: bool = False,
    tol: float = 1e-9,
):
    """
    Returns the split-conformal prediction set of classes for a given predicted probability vector.

    Standard Split Conformal Inclusion:
        Include class c in C(x) if nonconformity score s_c = 1 - p_c <= threshold + tol.
        Under floating-point comparison, this includes all classes where p_c >= 1.0 - threshold - tol.

    Fallback ("Never Return an Empty Set"):
        In rare cases where no class satisfies (1 - p_c) <= threshold (e.g. high uncertainty with
        small threshold), standard conformal prediction produces the empty set [].
        When `fallback_to_argmax=True`, the operational fallback includes the class(es) with the
        highest predicted probability. If multiple classes share the maximal probability within `tol`,
        all tied top classes are included.

    Parameters:
    - probs: array-like of predicted class probabilities summing to 1.
    - classes: list/array of class labels (defaults to [0, 1, ..., K-1]).
    - threshold: conformal nonconformity quantile threshold qhat in [0, 1].
    - fallback_to_argmax: whether to enforce non-empty set by falling back to argmax (default False).
    - tol: numerical comparison tolerance for floating-point boundaries (default 1e-9).
    """
    if threshold is None:
        raise ValueError("Must provide threshold (conformal nonconformity quantile qhat)")

    probs = np.asarray(probs, dtype=float)
    if classes is None:
        classes = list(range(len(probs)))
    else:
        classes = list(classes)

    selected = [classes[i] for i, p in enumerate(probs) if (1.0 - p) <= threshold + tol]

    if not selected and fallback_to_argmax:
        max_p = np.max(probs)
        selected = [classes[i] for i, p in enumerate(probs) if np.isclose(p, max_p, atol=tol)]

    return selected


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
