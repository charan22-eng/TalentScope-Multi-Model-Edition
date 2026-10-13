"""Independent calibration audit script for all seven models."""
import json
from pathlib import Path
import numpy as np
import pandas as pd


def compute_ece(y_true: np.ndarray, probas: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) with 10 equal-width bins, top-label."""
    confidences = np.max(probas, axis=1)
    predictions = np.argmax(probas, axis=1)
    accuracies = (predictions == y_true).astype(float)
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for bin_lower, bin_upper in zip(bin_boundaries[:-1], bin_boundaries[1:]):
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = float(np.mean(in_bin))
        if prop_in_bin > 0:
            acc_in_bin = float(np.mean(accuracies[in_bin]))
            conf_in_bin = float(np.mean(confidences[in_bin]))
            ece += np.abs(conf_in_bin - acc_in_bin) * prop_in_bin
    return float(ece)


def compute_brier(y_true: np.ndarray, probas: np.ndarray) -> float:
    """Compute multi-class Brier score."""
    n_classes = probas.shape[1]
    y_one_hot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((probas - y_one_hot) ** 2, axis=1)))


def main():
    models = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]
    print(f"{'Model':<8} | {'Method':<10} | {'ECE':<8} | {'Brier':<8}")
    print("-" * 42)
    methods = []
    for m in models:
        meta_path = Path(f"artifacts/v2/models/{m}/metadata.json")
        pred_path = Path(f"artifacts/v2/models/{m}/test_predictions.csv")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        cal_method = meta.get("tuning_parameters", {}).get("calibration_method", "unknown")
        methods.append(cal_method)
        df = pd.read_csv(pred_path)
        y_true = df["y_true"].values
        probas = df[["prob_low", "prob_med", "prob_high"]].values
        ece = compute_ece(y_true, probas)
        brier = compute_brier(y_true, probas)
        print(f"{m:<8} | {cal_method:<10} | {ece:<8.4f} | {brier:<8.4f}")

    unique_methods = set(methods)
    print("-" * 42)
    print(f"Calibration identical across all models: {len(unique_methods) == 1} (Method: {list(unique_methods)[0]})")


if __name__ == "__main__":
    main()
