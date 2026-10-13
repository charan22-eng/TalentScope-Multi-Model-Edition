"""Unit tests for live legacy modules: validate.py and train_extras.py."""

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from epk.validate import validate_data
from epk.train_extras import load_data, main as train_extras_main


def test_validate_data_clean_and_anomalous():
    """Verify validate_data flags missing values, negative experience, and negative attendance."""
    clean_df = pd.DataFrame({
        "employee_id": ["E1", "E2"],
        "attendance": [95.0, 98.0],
        "experience_years": [3.0, 5.0],
        "department": ["Engineering", "Sales"],
        "job_level": ["Mid", "Senior"],
    })
    res_clean = validate_data(clean_df)
    assert res_clean["total_issues"] == 0
    assert len(res_clean["details"]) == 0

    # Anomalous dataframe
    bad_df = pd.DataFrame({
        "employee_id": ["E1", "E2", "E3"],
        "attendance": [-5.0, 90.0, 80.0],          # E1 has negative attendance
        "experience_years": [2.0, -1.0, 4.0],       # E2 has negative experience
        "col_a": [None, None, None],
        "col_b": [None, 1, 2],
        "col_c": [None, 1, 2],                     # E1 has 3 missing values (> 2)
    })
    res_bad = validate_data(bad_df)
    assert res_bad["total_issues"] >= 3
    reasons = [d["reason"] for d in res_bad["details"]]
    assert "Negative attendance" in reasons
    assert "Negative experience years" in reasons
    assert "Too many missing values" in reasons


def test_train_extras_pipeline(monkeypatch, tmp_path):
    """Verify train_extras executes correctly and outputs v1 artifacts."""
    # Run train_extras_main
    try:
        train_extras_main()
        assert Path("artifacts/v1/pipeline.joblib").exists()
        assert Path("artifacts/v1/projection.joblib").exists()
        assert Path("artifacts/v1/background_sample.csv").exists()
        assert Path("artifacts/v1/importance.json").exists()
        assert Path("artifacts/v1/personas.json").exists()
    except Exception as e:
        pytest.fail(f"train_extras_main raised an exception: {e}")
