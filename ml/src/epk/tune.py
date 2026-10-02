import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from epk.features import build_preprocessor


def load_data():
    df = pd.read_csv("data/raw/dataset.csv").drop_duplicates(subset=["employee_id"])
    X = df.drop(columns=["performance"])
    y = df["performance"]

    with open("data/processed/split.json") as f:
        json.load(f)
        # We need to recreate the exact split from seed 42. Since we saved indices length,
        # let's just use StratifiedShuffleSplit like before.
    from sklearn.model_selection import StratifiedShuffleSplit

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y))

    return X.iloc[train_idx], y.iloc[train_idx], X.iloc[test_idx], y.iloc[test_idx]


def main():
    X_train, y_train, X_test, y_test = load_data()

    # 6.2 Grid search over n_neighbors, weights, p
    print("Starting Grid Search...")
    pipe = Pipeline(
        [
            ("prep", build_preprocessor()),
            ("knn", KNeighborsClassifier(algorithm="auto")),
        ]
    )

    grid = {
        "knn__n_neighbors": list(range(5, 32, 4)),
        "knn__weights": ["uniform", "distance"],
        "knn__p": [1, 2],  # Manhattan vs Euclidean
    }

    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=42)
    search = GridSearchCV(pipe, grid, cv=cv, scoring="f1_macro", n_jobs=1, refit=True)
    search.fit(X_train, y_train)

    best_params = search.best_params_
    best_cv_score = search.best_score_

    print(f"Best Params: {best_params}")
    print(f"Best CV Macro-F1: {best_cv_score:.3f}")

    # 6.7 Single final test evaluation
    best_model = search.best_estimator_
    y_pred = best_model.predict(X_test)
    test_f1 = f1_score(y_test, y_pred, average="macro")

    print("--- Final Tuned KNN ---")
    print(classification_report(y_test, y_pred))

    # Log experiments
    with open("reports/experiments.csv", "a") as f:
        f.write(
            f'knn_tuned,6.7,Tuned KNN,{best_cv_score:.3f},{test_f1:.3f},"Params: {best_params}"\n'
        )

    with open("reports/v0.3_final.md", "w") as f:
        f.write("# v0.3 Tuned KNN Report\n\n")
        f.write(f"**Best Parameters:** `{best_params}`\n")
        f.write(f"**CV Macro F1:** {best_cv_score:.3f}\n")
        f.write(f"**Test Macro F1:** {test_f1:.3f}\n\n")
        f.write("```\n")
        f.write(classification_report(y_test, y_pred))
        f.write("\n```\n")

    # Save best parameters for artifacts
    Path("ml/configs").mkdir(exist_ok=True)
    with open("ml/configs/best_knn.json", "w") as f:
        json.dump(best_params, f, indent=2)


if __name__ == "__main__":
    main()
