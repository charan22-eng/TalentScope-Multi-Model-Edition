"""Comprehensive unit and leakage tests for model-aware preprocessing."""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from epk.features import (
    ALL_FEATURES,
    NUMERIC_FEATURES,
    Winsorizer,
    build_preprocessor,
)
from epk.labels import BANDS, decode_bands, encode_bands
from epk.models.registry import REGISTRY, ModelSpec


@pytest.fixture
def sample_df():
    """Create a synthetic dataframe with 11 features matching Dataset v2 schema."""
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame({
        "attendance": rng.uniform(60, 100, n),
        "experience_years": rng.uniform(0, 30, n),
        "training_hours": rng.uniform(0, 120, n),
        "projects_completed": rng.integers(0, 15, n),
        "weekly_hours": rng.uniform(30, 60, n),
        "prev_score": rng.uniform(1.0, 5.0, n),
        "peer_feedback": rng.uniform(1.0, 5.0, n),
        "tasks_on_time_pct": rng.uniform(40, 100, n),
        "certifications": rng.integers(0, 8, n),
        "department": rng.choice(["Engineering", "Sales", "HR", "Finance", "Operations", "Support", "Marketing", "Legal"], n),
        "job_level": rng.choice(["Junior", "Mid", "Senior", "Lead"], n),
        "employee_id": [f"EMP{i:05d}" for i in range(n)],
        "performance_score": rng.uniform(10, 95, n),
        "performance": rng.choice(["Low", "Medium", "High"], n),
    })


def test_winsorizer():
    X = np.array([[1, 10], [2, 20], [3, 30], [4, 40], [1000, -1000]])
    w = Winsorizer(lower=0.1, upper=0.9).fit(X)
    X_trans = w.transform(X)
    assert np.max(X_trans[:, 0]) < 1000
    assert np.min(X_trans[:, 1]) > -1000


def test_preprocessor_shapes(sample_df):
    spec = REGISTRY["knn"]
    pre = build_preprocessor(spec).fit(sample_df)
    Xt = pre.transform(sample_df)
    
    # 9 numeric + 8 department OHE (8 depts in train) + 1 ordinal job_level = 18 features
    assert Xt.ndim == 2
    assert Xt.shape[0] == len(sample_df)
    assert Xt.shape[1] == 18


def test_preprocessor_no_nan_or_inf(sample_df):
    # Inject NaNs and extreme values into test set
    df_noisy = sample_df.copy()
    df_noisy.loc[0, "attendance"] = np.nan
    df_noisy.loc[1, "training_hours"] = np.nan
    df_noisy.loc[2, "prev_score"] = 999.0
    df_noisy.loc[3, "weekly_hours"] = -50.0

    pre = build_preprocessor(REGISTRY["logreg"]).fit(sample_df)
    Xt = pre.transform(df_noisy)

    assert not np.isnan(Xt).any(), "NaN found in transformed output"
    assert not np.isinf(Xt).any(), "Inf found in transformed output"


def test_preprocessor_idempotence(sample_df):
    pre = build_preprocessor(REGISTRY["dt"]).fit(sample_df)
    out1 = pre.transform(sample_df)
    out2 = pre.transform(sample_df)
    np.testing.assert_array_equal(out1, out2)


def test_preprocessor_unseen_categories(sample_df):
    pre = build_preprocessor(REGISTRY["rf"]).fit(sample_df)
    unseen_df = sample_df.iloc[:2].copy()
    unseen_df["department"] = ["SpaceExploration", "Robotics"]
    unseen_df["job_level"] = ["Executive", "Intern"]

    Xt = pre.transform(unseen_df)
    assert not np.isnan(Xt).any()
    assert Xt.shape[0] == 2


def test_model_aware_scaling(sample_df):
    # Trees get no scaler
    for tree_key in ["dt", "rf", "boost"]:
        tree_spec = REGISTRY[tree_key]
        pre_tree = build_preprocessor(tree_spec).fit(sample_df)
        scaler_step = pre_tree.named_transformers_["num"].named_steps["scale"]
        assert scaler_step == "passthrough", f"Tree model {tree_key} should not scale"

    # Scaled models get StandardScaler
    for scaled_key in ["linreg", "logreg", "knn", "svm"]:
        scaled_spec = REGISTRY[scaled_key]
        pre_scaled = build_preprocessor(scaled_spec).fit(sample_df)
        scaler_step = pre_scaled.named_transformers_["num"].named_steps["scale"]
        assert hasattr(scaler_step, "mean_"), f"Model {scaled_key} must have fitted StandardScaler"


@pytest.mark.parametrize("spec", list(REGISTRY.values()), ids=lambda s: s.key)
def test_leakage_parametrised_over_specs(sample_df, spec: ModelSpec):
    """G4: Assert no data leakage for every model spec."""
    train_df, test_df = train_test_split(sample_df, test_size=0.25, random_state=42)

    preprocessor = build_preprocessor(spec)
    preprocessor.fit(train_df)

    # Store train-fitted winsorizer thresholds and imputer statistics
    num_pipeline = preprocessor.named_transformers_["num"]
    winsorizer = num_pipeline.named_steps["winsor"]
    imputer = num_pipeline.named_steps["impute"]

    lo_train = winsorizer.lo_.copy()
    hi_train = winsorizer.hi_.copy()
    stats_train = imputer.statistics_.copy()

    # Transform test set (with potentially extreme values)
    extreme_test = test_df.copy()
    extreme_test.loc[:, "attendance"] = 1000.0  # Massive outlier in test only
    preprocessor.transform(extreme_test)

    # Assert that test transform did NOT alter training-derived state
    np.testing.assert_array_equal(winsorizer.lo_, lo_train)
    np.testing.assert_array_equal(winsorizer.hi_, hi_train)
    np.testing.assert_array_equal(imputer.statistics_, stats_train)


def test_ordered_labels():
    """G3/Task B4: Labels mapped to ordered integers 0, 1, 2."""
    raw = ["Low", "Medium", "High", "Low", "High"]
    encoded = encode_bands(raw)
    np.testing.assert_array_equal(encoded, np.array([0, 1, 2, 0, 2]))

    decoded = decode_bands(encoded)
    np.testing.assert_array_equal(decoded, np.array(raw, dtype=object))
