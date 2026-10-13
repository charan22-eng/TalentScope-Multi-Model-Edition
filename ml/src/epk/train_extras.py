import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.inspection import permutation_importance
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from epk.features import build_preprocessor


def load_data(data_path=None):
    if data_path is None:
        data_path = "data/nonlinear/dataset.csv" if Path("data/nonlinear/dataset.csv").exists() else "data/raw/dataset.csv"
    df = pd.read_csv(data_path).drop_duplicates(subset=["employee_id"])
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

    k = best_knn.get("knn__n_neighbors", 17)
    weights = best_knn.get("knn__weights", "distance")
    p = best_knn.get("knn__p", 1)

    # Train final pipeline
    pipe = Pipeline(
        [
            ("prep", build_preprocessor()),
            ("knn", KNeighborsClassifier(n_neighbors=k, weights=weights, p=p)),
        ]
    )
    pipe.fit(X_train, y_train)

    Path("artifacts/v1").mkdir(parents=True, exist_ok=True)

    # Save pipeline
    joblib.dump(pipe, "artifacts/v1/pipeline.joblib")

    # Generate PCA Projection
    X_scaled = pipe.named_steps["prep"].transform(X_train)
    pca = PCA(n_components=2, random_state=42)
    pca.fit(X_scaled)
    joblib.dump(pca, "artifacts/v1/projection.joblib")

    # Save background sample (500 points) for UI scatter plot
    bg_sample = X_train.sample(min(500, len(X_train)), random_state=42).copy()
    bg_sample["class"] = y_train.loc[bg_sample.index].values

    bg_scaled = pipe.named_steps["prep"].transform(bg_sample.drop(columns=["class"]))
    bg_pca = pca.transform(bg_scaled)
    bg_sample["pca_x"] = bg_pca[:, 0]
    bg_sample["pca_y"] = bg_pca[:, 1]
    bg_sample.to_csv("artifacts/v1/background_sample.csv", index=False, lineterminator="\n")

    # Global permutation importance (using train for simplicity as it's just KNN)
    print("Calculating permutation importance...")
    r = permutation_importance(
        pipe,
        X_train.sample(500, random_state=42),
        y_train.sample(500, random_state=42),
        n_repeats=5,
        random_state=42,
        scoring="f1_macro",
        n_jobs=1,
    )
    importance = {
        X_train.columns[i]: float(r.importances_mean[i])
        for i in range(len(X_train.columns))
    }
    importance = dict(sorted(importance.items(), key=lambda item: -item[1]))

    with open("artifacts/v1/importance.json", "w") as f:
        json.dump(importance, f, indent=2)

    # K-Means Personas
    print("Clustering personas...")
    kmeans = KMeans(n_clusters=4, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(X_scaled)

    # We just create a simple cross-tab
    bg_sample_for_personas = X_train.copy()
    bg_sample_for_personas["persona"] = labels
    bg_sample_for_personas["class"] = y_train.values

    crosstab = pd.crosstab(
        bg_sample_for_personas["persona"],
        bg_sample_for_personas["class"],
        normalize="index",
    ).to_dict(orient="index")

    with open("artifacts/v1/personas.json", "w") as f:
        json.dump(crosstab, f, indent=2)

    print("Phase 8 extras completed.")


if __name__ == "__main__":
    main()
