import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, brier_score_loss
from sklearn.model_selection import StratifiedShuffleSplit, StratifiedKFold, RepeatedStratifiedKFold, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import label_binarize

from epk.features import build_preprocessor


def save_split_hash(train_idx, calib_idx, test_idx, out_path, seed):
    meta = {
        "train_indices": len(train_idx),
        "calibration_indices": len(calib_idx),
        "test_indices": len(test_idx),
        "seed": seed,
    }
    with open(out_path, "w") as f:
        json.dump(meta, f, indent=2)


def get_ordinal_errors(y_true, y_pred):
    mapping = {"Low": 0, "Medium": 1, "High": 2}
    yt = np.array([mapping[y] for y in y_true])
    yp = np.array([mapping[y] for y in y_pred])
    diff = np.abs(yt - yp)
    exact = np.mean(diff == 0)
    adjacent = np.mean(diff == 1)
    extreme = np.mean(diff == 2)
    return exact, adjacent, extreme


def main():
    data_path = Path("data/raw/dataset.csv")
    df = pd.read_csv(data_path).drop_duplicates(subset=["employee_id"]).reset_index(drop=True)

    X = df.drop(columns=["performance"])
    y = df["performance"]

    # 60/20/20 split
    split1 = StratifiedShuffleSplit(n_splits=1, test_size=0.4, random_state=42)
    train_idx, temp_idx = next(split1.split(X, y))
    
    split2 = StratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=42)
    calib_idx_rel, test_idx_rel = next(split2.split(X.iloc[temp_idx], y.iloc[temp_idx]))
    calib_idx = temp_idx[calib_idx_rel]
    test_idx = temp_idx[test_idx_rel]

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    save_split_hash(train_idx, calib_idx, test_idx, "data/processed/split.json", 42)

    X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
    X_calib, y_calib = X.iloc[calib_idx], y.iloc[calib_idx]
    X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

    # Preprocessor
    preprocessor = build_preprocessor()

    # Baselines
    dummy = DummyClassifier(strategy="prior")
    dummy.fit(X_train, y_train)
    dummy_f1 = f1_score(y_test, dummy.predict(X_test), average="macro")

    lr = Pipeline([("prep", build_preprocessor()), ("lr", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    lr.fit(X_train, y_train)
    lr_f1 = f1_score(y_test, lr.predict(X_test), average="macro")

    # KNN Scaled
    knn_scaled = Pipeline([("prep", build_preprocessor()), ("knn", KNeighborsClassifier(n_neighbors=5))])
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=42)
    cv_scores_scaled = cross_validate(knn_scaled, X_train, y_train, cv=cv, scoring="f1_macro")
    cv_mean = cv_scores_scaled["test_score"].mean()
    cv_std = cv_scores_scaled["test_score"].std()

    # KNN Unscaled for ablation
    knn_unscaled = Pipeline([("prep", build_preprocessor(scaler="passthrough")), ("knn", KNeighborsClassifier(n_neighbors=5))])
    cv_scores_unscaled = cross_validate(knn_unscaled, X_train, y_train, cv=cv, scoring="f1_macro")
    cv_mean_unscaled = cv_scores_unscaled["test_score"].mean()

    # Fit final KNN on Train and evaluate on Test
    knn_scaled.fit(X_train, y_train)
    y_pred_knn = knn_scaled.predict(X_test)
    y_prob_knn = knn_scaled.predict_proba(X_test)
    test_f1 = f1_score(y_test, y_pred_knn, average="macro")
    exact, adjacent, extreme = get_ordinal_errors(y_test, y_pred_knn)
    
    # Brier Score (Uncalibrated vs Calibrated)
    y_calib_bin = label_binarize(y_calib, classes=knn_scaled.classes_)
    y_prob_calib = knn_scaled.predict_proba(X_calib)
    brier_uncalib = brier_score_loss(y_calib_bin.ravel(), y_prob_calib.ravel())

    calibrated_knn = CalibratedClassifierCV(estimator=knn_scaled, method="sigmoid", cv=3)
    calibrated_knn.fit(X_calib, y_calib)
    y_prob_calib_fitted = calibrated_knn.predict_proba(X_calib)
    brier_calib = brier_score_loss(y_calib_bin.ravel(), y_prob_calib_fitted.ravel())

    # Latency Benchmark
    t0 = time.time()
    knn_scaled.predict(X_test.iloc[[0]])
    t1 = time.time()
    single_latency = (t1 - t0) * 1000

    t0 = time.time()
    batch_size = min(len(X_test), 5000)
    knn_scaled.predict(X_test.iloc[:batch_size])
    t1 = time.time()
    batch_latency = (t1 - t0) * 1000

    # Write experiments
    Path("reports").mkdir(exist_ok=True)
    with open("reports/experiments.csv", "w") as f:
        f.write("run_id,phase,model,cv_macro_f1,test_macro_f1,notes\n")
        f.write(f"baseline_majority,3.2,Dummy Prior,N/A,{dummy_f1:.3f},Majority class\n")
        f.write(f"baseline_lr,3.2,LogReg,N/A,{lr_f1:.3f},Balanced weights\n")
        f.write(f"knn_unscaled,3.5,KNN(k=5 unscaled),{cv_mean_unscaled:.3f},N/A,Ablation\n")
        f.write(f"knn_scaled,3.5,KNN(k=5 scaled),{cv_mean:.3f},{test_f1:.3f},Primary model\n")

    # Write metrics report
    with open("reports/v0.3_final.md", "w") as f:
        f.write("# v0.3 Final Model Report\n\n")
        f.write(f"## Metrics\n")
        f.write(f"- **CV Macro F1 (5x3):** {cv_mean:.3f} +/- {cv_std:.3f}\n")
        f.write(f"- **Test Macro F1:** {test_f1:.3f}\n")
        f.write(f"## Ordinal Errors\n")
        f.write(f"- **Exact:** {exact*100:.1f}%\n")
        f.write(f"- **Adjacent:** {adjacent*100:.1f}%\n")
        f.write(f"- **Extreme:** {extreme*100:.1f}%\n")
        f.write(f"## Calibration\n")
        f.write(f"- **Uncalibrated Brier:** {brier_uncalib:.3f}\n")
        f.write(f"- **Calibrated Brier:** {brier_calib:.3f}\n")
        f.write(f"## Latency\n")
        f.write(f"- **Single Row:** {single_latency:.1f} ms\n")
        f.write(f"- **Batch ({batch_size}):** {batch_latency:.1f} ms\n")

if __name__ == "__main__":
    main()
