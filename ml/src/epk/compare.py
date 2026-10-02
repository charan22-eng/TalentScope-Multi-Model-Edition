import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from epk.features import build_preprocessor


def load_data():
    df = pd.read_csv("data/raw/dataset.csv").drop_duplicates(subset=["employee_id"])
    X = df.drop(columns=["performance"])
    y = df["performance"]

    with open("data/processed/split.json") as f:
        json.load(f)
    from sklearn.model_selection import StratifiedShuffleSplit

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y))

    return X.iloc[train_idx], y.iloc[train_idx]


def main():
    X_train, y_train = load_data()

    with open("ml/configs/best_knn.json") as f:
        best_knn = json.load(f)

    k = best_knn.get("knn__n_neighbors", 5)
    weights = best_knn.get("knn__weights", "uniform")
    p = best_knn.get("knn__p", 2)

    models = {
        "KNN (Tuned)": KNeighborsClassifier(n_neighbors=k, weights=weights, p=p),
        "Logistic Regression": LogisticRegression(
            max_iter=1000, class_weight="balanced"
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=50, max_depth=10, random_state=42
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=50, random_state=42
        ),
    }

    cv = RepeatedStratifiedKFold(n_splits=3, n_repeats=2, random_state=42)

    results = []

    for name, clf in models.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("clf", clf)])
        print(f"Evaluating {name}...")
        scores = cross_validate(
            pipe,
            X_train,
            y_train,
            cv=cv,
            scoring="f1_macro",
            n_jobs=1,
            return_train_score=False,
        )

        mean_f1 = np.mean(scores["test_score"])
        std_f1 = np.std(scores["test_score"])

        results.append(
            {
                "model": name,
                "macro_f1_mean": float(mean_f1),
                "macro_f1_std": float(std_f1),
            }
        )

    # Export for UI
    Path("artifacts/v1").mkdir(parents=True, exist_ok=True)
    with open("artifacts/v1/comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    print("Comparison results saved.")


if __name__ == "__main__":
    main()
