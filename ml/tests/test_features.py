import numpy as np
import pandas as pd

from epk.features import Winsorizer, build_preprocessor


def test_winsorizer():
    # Setup data with extreme outliers
    X = np.array([[1, 10], [2, 20], [3, 30], [4, 40], [1000, -1000]])  # Outliers

    w = Winsorizer(lower=0.1, upper=0.9)
    w.fit(X)

    X_trans = w.transform(X)

    # 90th percentile of [1, 2, 3, 4, 1000] is around 600, but actually it's calculated precisely
    assert np.max(X_trans[:, 0]) < 1000
    assert np.min(X_trans[:, 1]) > -1000


def test_build_preprocessor_no_leakage():
    df = pd.DataFrame(
        {
            "attendance": [100, 90, 80, None],
            "experience_years": [5, 10, None, 2],
            "training_hours": [50, 100, 150, 200],
            "projects_completed": [5, 10, 15, 20],
            "weekly_hours": [40, 40, 40, 40],
            "prev_score": [3, 4, 5, 2],
            "department": ["Sales", "HR", "Sales", "Engineering"],
            "job_level": ["Junior", "Senior", "Mid", "Lead"],
            "employee_id": ["E1", "E2", "E3", "E4"],
        }
    )

    preprocessor = build_preprocessor()
    preprocessor.fit(df)

    # Test data shouldn't affect medians or bounds
    test_df = pd.DataFrame(
        {
            "attendance": [None],
            "experience_years": [100],  # Outlier
            "training_hours": [0],
            "projects_completed": [0],
            "weekly_hours": [40],
            "prev_score": [1],
            "department": ["Unknown"],
            "job_level": ["Unknown"],
            "employee_id": ["T1"],
        }
    )

    X_trans = preprocessor.transform(test_df)
    assert not np.isnan(X_trans).any()

    # Check that 'employee_id' is dropped and features are generated correctly
    # num (6) + onehot dept (3 in train) + ord level (1) = 10 features expected
    assert X_trans.shape[1] == 10
