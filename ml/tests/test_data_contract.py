from epk.data import generate_data, hash_dataframe


def test_data_generation_reproducibility():
    df1, _ = generate_data(size=100, seed=42)
    df2, _ = generate_data(size=100, seed=42)

    assert hash_dataframe(df1) == hash_dataframe(df2)


def test_data_contract_schema():
    df, _ = generate_data(size=1000, seed=42)

    # Check columns
    expected_cols = {
        "employee_id",
        "attendance",
        "experience_years",
        "training_hours",
        "projects_completed",
        "weekly_hours",
        "prev_score",
        "department",
        "job_level",
        "performance",
    }
    assert set(df.columns) == expected_cols

    # Check class balance (~ 30% Low, 45% Medium, 25% High)
    # Because of noise/duplicates, give some margin
    counts = df["performance"].value_counts(normalize=True)
    assert 0.25 <= counts.get("Low", 0) <= 0.35
    assert 0.40 <= counts.get("Medium", 0) <= 0.50
    assert 0.20 <= counts.get("High", 0) <= 0.30

    # Check uniqueness of IDs
    assert df["employee_id"].is_unique


def test_data_contract_ranges():
    df, _ = generate_data(size=1000, seed=42)

    # Ignore NaNs for range checks
    assert df["attendance"].dropna().between(0, 100).all()
    assert df["experience_years"].dropna().between(0, 50).all()
    assert df["prev_score"].dropna().between(1, 5).all()


def test_no_protected_attributes_in_main_data():
    df, protected = generate_data(size=100, seed=42)
    assert "gender" not in df.columns
    assert "age_band" not in df.columns
    assert "gender" in protected.columns
