import numpy as np


def calculate_psi(expected, actual, bins=10):
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    cuts = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    cuts[0], cuts[-1] = -np.inf, np.inf

    e = np.histogram(expected, cuts)[0] / len(expected)
    a = np.histogram(actual, cuts)[0] / len(actual)

    e = np.clip(e, 1e-6, None)
    a = np.clip(a, 1e-6, None)

    return float(np.sum((a - e) * np.log(a / e)))


def get_current_drift(db_history, train_stats):
    """
    Mock logic: we extract 'experience_years' from the JSON input_data in history
    and compare against a mock training baseline.
    """
    import json

    actual_exp = []
    for h in db_history:
        try:
            data = json.loads(h.input_data)
            actual_exp.append(data.get("experience_years", 0))
        except:
            pass

    # Mock training stats for experience_years (e.g., normally distributed around 5)
    expected_exp = np.random.normal(5, 2, 1000).tolist()

    if len(actual_exp) < 10:
        return {"psi": 0.0, "status": "Insufficient data"}

    psi_score = calculate_psi(expected_exp, actual_exp)

    status = "Stable"
    if psi_score > 0.25:
        status = "Significant shift"
    elif psi_score > 0.1:
        status = "Moderate shift"

    return {"psi": round(psi_score, 4), "status": status}
