import json
from pathlib import Path

import joblib
import pandas as pd


def load_data():
    df = pd.read_csv("data/raw/dataset.csv").drop_duplicates(subset=["employee_id"])
    prot = pd.read_csv("data/raw/protected.csv")

    # Merge on employee_id
    df = df.merge(prot, on="employee_id", how="left")

    X = df.drop(columns=["performance"])
    y = df["performance"]

    with open("data/processed/split.json") as f:
        json.load(f)
    from sklearn.model_selection import StratifiedShuffleSplit

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y))

    return X.iloc[test_idx], y.iloc[test_idx]


def main():
    X_test, y_test = load_data()

    pipe = joblib.load("artifacts/v1/pipeline.joblib")

    y_pred = pipe.predict(X_test.drop(columns=["gender", "age_band"]))

    results = pd.DataFrame(
        {
            "gender": X_test["gender"],
            "age_band": X_test["age_band"],
            "actual": y_test,
            "pred": y_pred,
        }
    )

    audit = {}

    # Disparate Impact (Ratio of High performance predictions across genders relative to majority)
    # Using 'Male' as baseline
    prob_high_male = (results[results["gender"] == "Male"]["pred"] == "High").mean()
    prob_high_female = (results[results["gender"] == "Female"]["pred"] == "High").mean()

    if prob_high_male > 0:
        di_gender = prob_high_female / prob_high_male
    else:
        di_gender = 1.0

    audit["disparate_impact_gender_female_vs_male"] = float(di_gender)

    # 9.2 Robustness Noise Check
    # Add 10% noise to attendance and see how many predictions change
    X_noisy = X_test.copy().drop(columns=["gender", "age_band"])
    X_noisy["attendance"] = X_noisy["attendance"] * 1.10

    y_pred_noisy = pipe.predict(X_noisy)
    stability = (y_pred == y_pred_noisy).mean()
    audit["robustness_stability_10pct_attendance_noise"] = float(stability)

    Path("artifacts/v1").mkdir(parents=True, exist_ok=True)
    with open("artifacts/v1/audit_report.json", "w") as f:
        json.dump(audit, f, indent=2)

    print(f"Audit completed: {audit}")


if __name__ == "__main__":
    main()
