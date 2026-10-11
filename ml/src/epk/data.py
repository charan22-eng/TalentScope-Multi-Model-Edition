import argparse
import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEPTS = ["Engineering", "Sales", "HR", "Finance", "Operations", "Support", "Marketing", "Legal"]
DEPT_P = [0.30, 0.18, 0.06, 0.08, 0.14, 0.12, 0.08, 0.04]
DEPT_EFFECT = dict(zip(DEPTS, [0.10, 0.05, -0.05, 0.00, -0.05, -0.10, 0.05, 0.00]))
LEVELS = ["Junior", "Mid", "Senior", "Lead"]

def make_employee_data(n=12000, seed=42, variant="nonlinear", inject_bias=False):
    rng = np.random.default_rng(seed)
    
    dept = rng.choice(DEPTS, n, p=DEPT_P)
    level = rng.choice(LEVELS, n, p=[.35, .35, .20, .10])
    exp = rng.gamma(3, 2.5, n).clip(0, 35)
    att = rng.normal(90, 6, n).clip(60, 100)
    trn = rng.normal(40 + 0.8 * exp, 15, n).clip(0, 120)
    prj = rng.poisson(4 + 0.25 * exp, n).clip(0, 20)
    hrs = rng.normal(44, 5, n).clip(30, 60)
    prev = rng.normal(3.1 + 0.03 * exp, 0.7, n).clip(1, 5)
    peer = rng.normal(3.4 + 0.25 * (prev - 3), 0.6, n).clip(1, 5)
    ontime = rng.normal(82 + 2 * (prev - 3), 8, n).clip(30, 100)
    certs = rng.poisson(1 + 0.1 * exp, n).clip(0, 10)
    
    d = np.array([DEPT_EFFECT[x] for x in dept])
    zs = lambda x, m, s: (x - m) / s
    
    if variant == "linear":
        z = (0.35 * zs(att, 90, 6) + 0.25 * zs(trn, 50, 20) + 
             0.45 * zs(prj, 6, 3) + 0.60 * zs(prev, 3, 0.7) + 
             0.15 * zs(peer, 3.4, 0.6) + 0.20 * zs(ontime, 82, 8) + 
             0.10 * zs(certs, 2, 1.5) + 0.10 * zs(hrs, 44, 5) + d)
        noise = 0.45
    else:
        sat = 1 - np.exp(-trn / 35)
        z = (0.55 * np.minimum(att - 86, 0) / 4 + 0.15 * zs(att, 90, 6) + 
             1.6 * (sat - 0.7) / 0.25 * 0.5 + 0.35 * zs(prj, 6, 3) + 
             0.9 * zs(prj, 6, 3) * zs(prev, 3, 0.7) * 0.6 + 
             0.50 * zs(prev, 3, 0.7) - 0.9 * (np.abs(hrs - 42) / 5) ** 1.5 * 0.5 + 
             0.15 * zs(peer, 3.4, 0.6) + 0.20 * zs(ontime, 82, 8) + 
             0.10 * zs(certs, 2, 1.5) + d)
        noise = 0.35 if variant == "nonlinear" else 0.8
        
    z = z + rng.normal(0, noise, n) * (1 + 0.15 * (level == "Junior"))
    
    score = 100 / (1 + np.exp(-z / 1.6))
    t1, t2 = np.quantile(score, [0.30, 0.75])
    band = np.where(score < t1, "Low", np.where(score < t2, "Medium", "High"))
    
    if variant == "noisy_overlap":
        flip = rng.random(n) < 0.03
        order = {"Low": 0, "Medium": 1, "High": 2}
        inv = ["Low", "Medium", "High"]
        shift = rng.choice([-1, 1], n)
        idx = np.clip(np.vectorize(order.get)(band) + shift, 0, 2)
        band = np.where(flip, np.array(inv)[idx], band)
        
    employee_ids = [f"EMP{i:05d}" for i in range(1, n + 1)]
    
    df = pd.DataFrame(dict(
        employee_id=employee_ids,
        department=dept, job_level=level, attendance=np.round(att, 1), 
        experience_years=np.round(exp, 1), training_hours=np.round(trn, 0), 
        projects_completed=prj, weekly_hours=np.round(hrs, 1), 
        prev_score=np.round(prev, 2), peer_feedback=np.round(peer, 2), 
        tasks_on_time_pct=np.round(ontime, 1), certifications=certs, 
        performance_score=np.round(score, 2), performance=band
    ))
    
    # Protected features
    genders = rng.choice(["Male", "Female", "Non-binary"], n, p=[0.48, 0.48, 0.04])
    age_bands = rng.choice(["20-30", "31-40", "41-50", "51+"], n)
    
    if inject_bias:
        # Bias injection on gender
        df["performance_score"] = np.where(genders == "Male", df["performance_score"] + 5, df["performance_score"])
        t1, t2 = np.quantile(df["performance_score"], [0.30, 0.75])
        df["performance"] = np.where(df["performance_score"] < t1, "Low", 
                                     np.where(df["performance_score"] < t2, "Medium", "High"))

    protected_df = pd.DataFrame(dict(employee_id=employee_ids, gender=genders, age_band=age_bands))

    # Realism layer
    # Missing values (3-5%)
    for col in ["attendance", "experience_years", "training_hours", "projects_completed", "weekly_hours", "prev_score"]:
        mask = rng.random(n) < 0.04
        df.loc[mask, col] = np.nan
        
    # Outliers (impossible values) = 0.8% (limit <= 1%)
    impossible_idx = rng.choice(df.index, int(n * 0.008), replace=False)
    k1, k2 = len(impossible_idx) // 3, 2 * (len(impossible_idx) // 3)
    df.loc[impossible_idx[:k1], "training_hours"] = 500
    df.loc[impossible_idx[k1:k2], "weekly_hours"] = 150
    df.loc[impossible_idx[k2:], "attendance"] = -10
    
    # Duplicates <= 1%
    dupes = df.sample(int(n * 0.008), random_state=seed)
    df = pd.concat([df, dupes], ignore_index=True)
    protected_df = pd.concat([protected_df, protected_df.loc[dupes.index]], ignore_index=True)

    # Cleaning
    initial_rows = len(df)
    
    # Drop duplicates completely based on employee_id
    df = df.drop_duplicates(subset=["employee_id"], keep="first")
    protected_df = protected_df.drop_duplicates(subset=["employee_id"], keep="first")
    
    # Drop impossible values
    impossible_mask = (
        (df["training_hours"] > 300) | 
        (df["weekly_hours"] > 100) | 
        (df["attendance"] < 0) | 
        (df["attendance"] > 100)
    )
    df = df[~impossible_mask]
    protected_df = protected_df[~impossible_mask]
    
    final_rows = len(df)
    
    logger.info(f"Variant: {variant} | Raw rows: {initial_rows} | Cleaned rows: {final_rows}")
    
    if variant == "nonlinear":
        assert final_rows >= 10000, f"Expected at least 10,000 rows after cleaning, got {final_rows}"

    return df.reset_index(drop=True), protected_df.reset_index(drop=True)

def hash_dataframe(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--size", type=int, default=12000)
    parser.add_argument("--inject-bias", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {"seed": args.seed, "size": args.size, "injected_bias": args.inject_bias, "variants": {}}

    for variant in ["linear", "nonlinear", "noisy_overlap"]:
        df, protected_df = make_employee_data(
            n=args.size, seed=args.seed, variant=variant, inject_bias=args.inject_bias
        )
        
        v_dir = out_dir / variant
        v_dir.mkdir(exist_ok=True)
        
        train_path = v_dir / "dataset.csv"
        protected_path = v_dir / "protected.csv"
        
        df.to_csv(train_path, index=False)
        protected_df.to_csv(protected_path, index=False)
        
        manifest["variants"][variant] = {
            "dataset.csv": {"sha256": hash_dataframe(df), "rows": len(df)},
            "protected.csv": {"sha256": hash_dataframe(protected_df), "rows": len(protected_df)}
        }
        
    manifest_path = out_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Data generated at {out_dir}")

if __name__ == "__main__":
    main()
