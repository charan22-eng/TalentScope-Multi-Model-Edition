import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def generate_data(size=5000, seed=42, inject_bias=False):
    np.random.seed(seed)

    # 1. Base latent factors (to create correlations)
    # Experience drives training (more exp -> slightly less training) and projects (more exp -> more projects)
    experience_years = np.clip(np.random.gamma(2, 3, size), 0, 50)

    attendance = np.clip(np.random.normal(90, 5, size), 0, 100)
    training_hours = np.clip(
        np.random.normal(50, 20, size) - experience_years * 2, 0, 300
    )
    projects_completed = np.clip(
        np.random.poisson(3 + experience_years * 0.5, size), 0, 100
    )
    weekly_hours = np.clip(np.random.normal(40, 5, size), 0, 100)

    # prev_score correlates with projects and attendance
    prev_score_base = (
        3.0
        + (projects_completed * 0.1)
        + ((attendance - 90) * 0.05)
        + np.random.normal(0, 0.5, size)
    )
    prev_score = np.clip(prev_score_base, 1, 5).round(1)

    # 2. Latent performance score
    latent_score = (
        projects_completed * 2.0
        + prev_score * 10.0
        + training_hours * 0.1
        + attendance * 0.2
        + np.random.normal(0, 5, size)
    )

    employee_ids = [f"EMP{i:05d}" for i in range(1, size + 1)]

    # Departments & Job Levels
    depts = np.random.choice(["Sales", "Engineering", "HR", "Marketing"], size)
    levels = np.random.choice(
        ["Junior", "Mid", "Senior", "Lead"], size, p=[0.4, 0.4, 0.15, 0.05]
    )

    # Protected attributes
    genders = np.random.choice(
        ["Male", "Female", "Non-binary"], size, p=[0.48, 0.48, 0.04]
    )
    age_bands = np.random.choice(["20-30", "31-40", "41-50", "51+"], size)

    if inject_bias:
        # Bias injection for Phase 9 demos
        # E.g., Males get a synthetic boost to latent score
        latent_score = np.where(genders == "Male", latent_score + 10, latent_score)

    # 3. Label creation by quantiles (30% Low / 45% Medium / 25% High)
    q_low = np.quantile(latent_score, 0.30)
    q_high = np.quantile(latent_score, 0.75)

    performance = np.where(
        latent_score < q_low, "Low", np.where(latent_score >= q_high, "High", "Medium")
    )

    df = pd.DataFrame(
        {
            "employee_id": employee_ids,
            "attendance": attendance,
            "experience_years": experience_years,
            "training_hours": training_hours,
            "projects_completed": projects_completed,
            "weekly_hours": weekly_hours,
            "prev_score": prev_score,
            "department": depts,
            "job_level": levels,
            "performance": performance,
        }
    )

    protected_df = pd.DataFrame(
        {"employee_id": employee_ids, "gender": genders, "age_band": age_bands}
    )

    # 4. Realism layer (missing values, outliers, duplicates)
    # Inject missing values (3-5%)
    for col in [
        "attendance",
        "experience_years",
        "training_hours",
        "projects_completed",
        "weekly_hours",
        "prev_score",
    ]:
        mask = np.random.rand(size) < 0.04
        df.loc[mask, col] = np.nan

    # Inject outliers
    df.loc[np.random.choice(df.index, int(size * 0.01)), "training_hours"] = 500
    df.loc[np.random.choice(df.index, int(size * 0.01)), "weekly_hours"] = 120

    # Inject duplicates
    dupes = df.sample(int(size * 0.005))
    df = pd.concat([df, dupes], ignore_index=True)
    # Because employee_id must be unique in DB, we append _dup
    df.loc[df.duplicated("employee_id"), "employee_id"] = (
        df.loc[df.duplicated("employee_id"), "employee_id"] + "_dup"
    )

    # Ensure protected_df matches index
    # We will just ignore the duplicated ones for protected_df, or duplicate them too
    protected_df = pd.concat(
        [protected_df, protected_df.loc[dupes.index]], ignore_index=True
    )
    protected_df.loc[protected_df.duplicated("employee_id"), "employee_id"] = (
        protected_df.loc[protected_df.duplicated("employee_id"), "employee_id"] + "_dup"
    )

    return df, protected_df


def hash_dataframe(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--size", type=int, default=5000)
    parser.add_argument("--inject-bias", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df, protected_df = generate_data(
        size=args.size, seed=args.seed, inject_bias=args.inject_bias
    )

    train_path = out_dir / "dataset.csv"
    protected_path = out_dir / "protected.csv"
    manifest_path = out_dir / "manifest.json"

    df.to_csv(train_path, index=False)
    protected_df.to_csv(protected_path, index=False)

    manifest = {
        "dataset.csv": {"sha256": hash_dataframe(df), "rows": len(df)},
        "protected.csv": {
            "sha256": hash_dataframe(protected_df),
            "rows": len(protected_df),
        },
        "seed": args.seed,
        "size": args.size,
        "injected_bias": args.inject_bias,
    }

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Data generated at {out_dir}")
    print(f"Manifest: {json.dumps(manifest, indent=2)}")


if __name__ == "__main__":
    main()
