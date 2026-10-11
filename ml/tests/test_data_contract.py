import pytest
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))
from epk.data import make_employee_data

@pytest.fixture(scope="module")
def default_data():
    df, protected = make_employee_data(variant="nonlinear")
    return df, protected

def test_row_count(default_data):
    df, _ = default_data
    assert len(df) >= 10000

def test_determinism():
    df1, _ = make_employee_data(variant="linear", seed=42)
    df2, _ = make_employee_data(variant="linear", seed=42)
    pd.testing.assert_frame_equal(df1, df2)

def test_class_balance(default_data):
    df, _ = default_data
    dist = df["performance"].value_counts(normalize=True)
    assert 0.28 <= dist.get("Low", 0) <= 0.32
    assert 0.43 <= dist.get("Medium", 0) <= 0.47
    assert 0.23 <= dist.get("High", 0) <= 0.27

def test_score_band_consistency(default_data):
    df, _ = default_data
    low_max = df[df["performance"] == "Low"]["performance_score"].max()
    med_min = df[df["performance"] == "Medium"]["performance_score"].min()
    med_max = df[df["performance"] == "Medium"]["performance_score"].max()
    high_min = df[df["performance"] == "High"]["performance_score"].min()
    
    assert low_max <= med_min
    assert med_max <= high_min

def test_no_targets_in_features():
    schema_path = Path(__file__).resolve().parent.parent / "configs" / "schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    features = [f["name"] for f in schema["features"]]
    
    forbidden = ["performance_score", "performance", "employee_id", "gender", "age_band"]
    for fb in forbidden:
        assert fb not in features, f"{fb} is illegally listed as a feature"

def test_schema_ranges(default_data):
    df, _ = default_data
    assert df["attendance"].dropna().between(0, 100).all()
    assert df["weekly_hours"].dropna().between(0, 100).all()
    assert df["training_hours"].dropna().between(0, 300).all()
    
def test_variant_properties():
    # Sanity checks on the generated files
    df_l, _ = make_employee_data(variant="linear")
    df_n, _ = make_employee_data(variant="nonlinear")
    df_no, _ = make_employee_data(variant="noisy_overlap")
    
    assert len(df_l) >= 10000
    assert len(df_n) >= 10000
    assert len(df_no) >= 10000
