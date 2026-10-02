import json
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

from epk.features import build_preprocessor


def save_split_hash(idx, out_path, seed):
    # Sort index to ensure stable hashing if needed
    idx_sorted = sorted(idx)
    meta = {"train_indices": len(idx_sorted), "seed": seed}
    with open(out_path, "w") as f:
        json.dump(meta, f, indent=2)


def main():
    # 5.1 Freeze the split
    data_path = Path("data/raw/dataset.csv")
    df = pd.read_csv(data_path)

    # Drop duplicates for training (they were injected for realism, but we don't want identical rows in train/test)
    df = df.drop_duplicates(subset=["employee_id"])

    X = df.drop(columns=["performance"])
    y = df["performance"]

    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y))

    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    save_split_hash(train_idx, "data/processed/split.json", 42)

    # Preprocessor
    build_preprocessor()

    # 5.2 Baselines
    print("--- Majority Class Baseline ---")
    dummy = DummyClassifier(strategy="prior")
    dummy.fit(X_train, y_train)
    y_pred_dummy = dummy.predict(X_test)
    print(classification_report(y_test, y_pred_dummy, zero_division=0))
    dummy_f1 = f1_score(y_test, y_pred_dummy, average="macro")

    print("--- Logistic Regression Baseline ---")
    lr = Pipeline(
        [
            ("prep", build_preprocessor()),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    lr.fit(X_train, y_train)
    y_pred_lr = lr.predict(X_test)
    print(classification_report(y_test, y_pred_lr, zero_division=0))
    lr_f1 = f1_score(y_test, y_pred_lr, average="macro")

    # 5.3 Vanilla KNN (Scaled)
    print("--- Vanilla KNN (k=5, Scaled) ---")
    knn = Pipeline(
        [("prep", build_preprocessor()), ("knn", KNeighborsClassifier(n_neighbors=5))]
    )
    knn.fit(X_train, y_train)
    y_pred_knn = knn.predict(X_test)
    classification_report(y_test, y_pred_knn, output_dict=True)
    print(classification_report(y_test, y_pred_knn))
    knn_f1 = f1_score(y_test, y_pred_knn, average="macro")

    # Log experiments
    Path("reports").mkdir(exist_ok=True)
    with open("reports/experiments.csv", "a") as f:
        # Create header if empty
        if not Path("reports/experiments.csv").stat().st_size:
            f.write("run_id,phase,model,cv_macro_f1,test_macro_f1,notes\n")
        f.write(f"baseline_1,5.2,Dummy Prior,N/A,{dummy_f1:.3f},Majority class\n")
        f.write(f"baseline_2,5.2,LogReg,N/A,{lr_f1:.3f},Balanced weights\n")
        f.write(f"knn_v1,5.3,KNN(k=5 scaled),N/A,{knn_f1:.3f},First vertical slice\n")

    # Write metrics report
    with open("reports/v0.2_metrics.md", "w") as f:
        f.write("# v0.2 Metrics Report\n\n")
        f.write(f"- **Dummy Classifier (Majority):** Macro F1 = {dummy_f1:.3f}\n")
        f.write(f"- **Logistic Regression:** Macro F1 = {lr_f1:.3f}\n")
        f.write(f"- **Vanilla KNN (k=5, scaled):** Macro F1 = {knn_f1:.3f}\n\n")
        f.write("## KNN Confusion Matrix\n")
        f.write("```\n")
        f.write(
            str(confusion_matrix(y_test, y_pred_knn, labels=["Low", "Medium", "High"]))
        )
        f.write("\n```\n")


if __name__ == "__main__":
    main()
