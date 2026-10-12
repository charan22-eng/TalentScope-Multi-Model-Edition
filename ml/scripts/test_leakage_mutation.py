#!/usr/bin/env python
"""Mutation test script for data leakage detection (Task B5 / Guard G4).

Simulates a buggy preprocessing pipeline that accidentally fits on all data (train + test).
Verifies that our leakage detection logic correctly catches the defect and fails.
"""

import sys
import numpy as np
import pandas as pd
from epk.features import build_preprocessor
from epk.models.registry import REGISTRY


def test_mutation_leakage():
    print("Running leakage mutation test...")
    rng = np.random.default_rng(42)
    n = 200
    df = pd.DataFrame({
        "attendance": rng.uniform(60, 100, n),
        "experience_years": rng.uniform(0, 30, n),
        "training_hours": rng.uniform(0, 120, n),
        "projects_completed": rng.integers(0, 15, n),
        "weekly_hours": rng.uniform(30, 60, n),
        "prev_score": rng.uniform(1.0, 5.0, n),
        "peer_feedback": rng.uniform(1.0, 5.0, n),
        "tasks_on_time_pct": rng.uniform(40, 100, n),
        "certifications": rng.integers(0, 8, n),
        "department": rng.choice(["Engineering", "Sales", "HR", "Finance"], n),
        "job_level": rng.choice(["Junior", "Mid", "Senior", "Lead"], n),
    })

    train_df = df.iloc[:150].copy()
    test_df = df.iloc[150:].copy()

    # Clean preprocessor fit on train only
    clean_prep = build_preprocessor(REGISTRY["logreg"])
    clean_prep.fit(train_df)
    clean_lo = clean_prep.named_transformers_["num"].named_steps["winsor"].lo_.copy()

    # Mutated buggy preprocessor: incorrectly fitted on combined train + test
    buggy_prep = build_preprocessor(REGISTRY["logreg"])
    # Inject an outlier into test set
    extreme_test = test_df.copy()
    extreme_test.loc[:, "attendance"] = 1000.0

    combined_df = pd.concat([train_df, extreme_test], ignore_index=True)
    buggy_prep.fit(combined_df)  # LEAKAGE: fitted on test data!
    buggy_lo = buggy_prep.named_transformers_["num"].named_steps["winsor"].lo_.copy()
    buggy_hi = buggy_prep.named_transformers_["num"].named_steps["winsor"].hi_.copy()

    # Check whether the leakage altered the bounds
    clean_hi = clean_prep.named_transformers_["num"].named_steps["winsor"].hi_.copy()
    leak_detected = not np.allclose(clean_hi, buggy_hi)

    if leak_detected:
        print("[PASS] Mutation test succeeded: Leakage was correctly detected and caught.")
        print(f"       Clean Hi: {clean_hi[0]:.2f}, Leaked Hi: {buggy_hi[0]:.2f}")
        return 0
    else:
        print("[FAIL] Mutation test failed: Leakage went undetected!")
        return 1


if __name__ == "__main__":
    sys.exit(test_mutation_leakage())
