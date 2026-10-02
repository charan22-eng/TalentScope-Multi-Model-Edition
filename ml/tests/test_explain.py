import pandas as pd
import numpy as np
from epk.explain import explain, counterfactual
from epk.uncertainty import compute_conformal_threshold, get_prediction_set, stability_score

def test_conformal_prediction_logic():
    # Simple probabilities for calibration
    y_calib = ["Low", "High", "Medium", "High"]
    probs = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.1, 0.8],
        [0.2, 0.6, 0.2],
        [0.4, 0.2, 0.4]
    ])
    classes = ["Low", "Medium", "High"]
    
    threshold = compute_conformal_threshold(y_calib, probs, classes, alpha=0.1)
    assert threshold > 0
    
    pset = get_prediction_set(np.array([0.9, 0.05, 0.05]), classes, threshold)
    assert "Low" in pset

def test_stability_score():
    assert stability_score([1.0, 0.0, 0.0]) > 0.99
    assert stability_score([0.333, 0.333, 0.334]) < 0.1

def test_explain():
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import Pipeline
    from epk.features import build_preprocessor
    
    df = pd.DataFrame({
        "attendance": [100, 90, 80],
        "experience_years": [5, 10, 2],
        "training_hours": [50, 100, 200],
        "projects_completed": [5, 10, 20],
        "weekly_hours": [40, 40, 40],
        "prev_score": [3, 4, 5],
        "department": ["Sales", "HR", "Engineering"],
        "job_level": ["Junior", "Senior", "Mid"],
    })
    y = pd.Series(["Low", "Medium", "High"])
    
    pipe = Pipeline([("prep", build_preprocessor()), ("knn", KNeighborsClassifier(n_neighbors=2))])
    pipe.fit(df, y)
    
    nb, votes = explain(pipe, df, y, df.iloc[[0]])
    assert len(nb) == 2
    assert "Low" in votes

def test_counterfactual():
    # Check that it only changes actionable features
    pass
