import json
from pathlib import Path

import pandas as pd
from sklearn.decomposition import PCA
import joblib

from epk.features import build_preprocessor

def main():
    Path("data/processed/assets").mkdir(parents=True, exist_ok=True)
    
    # 1. Background sample
    df = pd.read_csv("data/raw/dataset.csv").drop_duplicates(subset=["employee_id"])
    
    with open("data/processed/split.json") as f:
        meta = json.load(f)
        
    X = df.drop(columns=["performance"])
    y = df["performance"]
    
    # Just take 2000 points from train
    from sklearn.model_selection import StratifiedShuffleSplit
    split = StratifiedShuffleSplit(n_splits=1, test_size=0.4, random_state=42)
    train_idx, temp_idx = next(split.split(X, y))
    
    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    
    # Subsample 2000 points (anonymized)
    sample = X_train.copy()
    if len(sample) > 2000:
        sample = sample.sample(n=2000, random_state=42)
        
    # Anonymize
    sample["employee_id"] = [f"BKG{i:04d}" for i in range(len(sample))]
    sample.to_csv("data/processed/assets/background_sample.csv", index=False, lineterminator="\n")
    
    # 2. Fit PCA 2D and 3D
    prep = build_preprocessor()
    X_scaled = prep.fit_transform(X_train)
    
    pca2 = PCA(n_components=2, random_state=42)
    pca2.fit(X_scaled)
    joblib.dump(pca2, "data/processed/assets/pca2d.joblib")
    
    pca3 = PCA(n_components=3, random_state=42)
    pca3.fit(X_scaled)
    joblib.dump(pca3, "data/processed/assets/pca3d.joblib")
    
    print(f"PCA2 Explained Variance: {pca2.explained_variance_ratio_.sum():.3f}")
    print(f"PCA3 Explained Variance: {pca3.explained_variance_ratio_.sum():.3f}")
    
    # 3. Personas
    personas = {
        "HR Manager": {"goal": "Fairness and high-level distribution", "tone": "Professional"},
        "Team Lead": {"goal": "Development areas", "tone": "Actionable"},
        "Reviewer": {"goal": "Audit decision basis", "tone": "Analytical"}
    }
    with open("personas.json", "w") as f:
        json.dump(personas, f, indent=2)
        
if __name__ == "__main__":
    main()
