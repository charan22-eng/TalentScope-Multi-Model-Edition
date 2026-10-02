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

def get_prediction_set(probs, classes, threshold):
    """
    Returns the set of classes for a given prediction based on conformal threshold.
    """
    scores = 1 - probs
    # Include classes where score <= threshold (i.e. prob >= 1 - threshold)
    return [classes[i] for i, score in enumerate(scores) if score <= threshold]

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
