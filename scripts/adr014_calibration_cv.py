"""adr014_calibration_cv.py — Cross-validate candidate calibration methods on cal-A only.

Candidate methods applied identically to all seven models:
1. Sigmoid OvR (Platt scaling) via CalibratedClassifierCV(method="sigmoid", cv="prefit")
2. Isotonic OvR via CalibratedClassifierCV(method="isotonic", cv="prefit")
3. Multinomial Temperature Scaling implemented with scipy.optimize (optimizing NLL/Brier)
4. Raw (Uncalibrated baseline)

Evaluation protocol:
5-fold StratifiedKFold strictly within cal-A (N = 1,190).
Computes out-of-fold Brier score, ECE (10 equal-width bins), and Log Loss.
Selects one common calibration method by lowest mean Brier across all seven models.
"""

import json
import sys
from pathlib import Path

# Ensure ml/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml" / "src"))

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import log_loss
from sklearn.model_selection import StratifiedKFold

from epk.features import ALL_FEATURES
from epk.labels import encode_bands
from epk.split import load_split


def compute_ece(y_true: np.ndarray, probas: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE), 10 equal-width bins, top-label."""
    conf = np.max(probas, axis=1)
    preds = np.argmax(probas, axis=1)
    accs = (preds == y_true).astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for b_lo, b_hi in zip(bins[:-1], bins[1:]):
        in_bin = (conf > b_lo) & (conf <= b_hi)
        if np.any(in_bin):
            b_acc = np.mean(accs[in_bin])
            b_conf = np.mean(conf[in_bin])
            ece += np.sum(in_bin) / len(y_true) * np.abs(b_acc - b_conf)
    return float(ece)


def compute_brier(y_true: np.ndarray, probas: np.ndarray) -> float:
    """Multiclass Brier score: mean squared error between probabilities and one-hot true class."""
    n_classes = probas.shape[1]
    y_bin = np.zeros_like(probas)
    for c in range(n_classes):
        y_bin[:, c] = (y_true == c).astype(float)
    return float(np.mean(np.sum((probas - y_bin) ** 2, axis=1)))


class TemperatureScalingCalibrator(BaseEstimator, ClassifierMixin):
    """Multinomial Temperature Scaling Calibrator.

    Scales logits z by scalar temperature T > 0:
        P(y = c | x) = softmax(z / T)_c
    Where logits z are derived from:
      - decision_function(X) if available (e.g. SVM), or
      - log(clip(predict_proba(X), 1e-12, 1.0)) if probabilities are returned.
    Temperature T is fitted by minimizing cross-entropy (NLL) on calibration data.
    """

    def __init__(self, estimator):
        self.estimator = estimator
        self.temperature_ = 1.0
        self.classes_ = np.array([0, 1, 2])

    def _get_logits(self, X):
        if hasattr(self.estimator, "decision_function"):
            logits = self.estimator.decision_function(X)
            if logits.ndim == 1:
                logits = np.vstack([-logits, logits]).T
            return logits
        elif hasattr(self.estimator, "predict_proba"):
            p = self.estimator.predict_proba(X)
            p = np.clip(p, 1e-12, 1.0 - 1e-12)
            # Center logits: log(p) - mean(log(p))
            logits = np.log(p)
            return logits - np.mean(logits, axis=1, keepdims=True)
        else:
            raise ValueError(f"Estimator {self.estimator} lacks decision_function or predict_proba")

    def fit(self, X, y):
        logits = self._get_logits(X)
        n = len(y)

        def nll_obj(T):
            if T <= 1e-4:
                return 1e6
            scaled = logits / T
            # Numerically stable log-softmax
            max_s = np.max(scaled, axis=1, keepdims=True)
            log_sum_exp = max_s + np.log(np.sum(np.exp(scaled - max_s), axis=1, keepdims=True))
            log_probs = scaled - log_sum_exp
            # NLL for true classes
            return -np.sum(log_probs[np.arange(n), y]) / n

        res = minimize_scalar(nll_obj, bounds=(0.05, 10.0), method="bounded")
        self.temperature_ = float(res.x)
        return self

    def predict_proba(self, X):
        logits = self._get_logits(X)
        return softmax(logits / self.temperature_, axis=1)

    def predict(self, X):
        p = self.predict_proba(X)
        return np.argmax(p, axis=1)


def cross_validate_calibration(
    base_model,
    X_cal: pd.DataFrame,
    y_cal: np.ndarray,
    n_splits: int = 5,
    seed: int = 42,
) -> dict:
    """5-fold CV within cal-A evaluating raw, sigmoid, isotonic, temperature scaling."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)

    methods = ["raw", "sigmoid", "isotonic", "temperature"]
    fold_metrics = {m: {"brier": [], "ece": [], "log_loss": []} for m in methods}

    for train_idx, val_idx in skf.split(X_cal, y_cal):
        X_tr, y_tr = X_cal.iloc[train_idx], y_cal[train_idx]
        X_va, y_va = X_cal.iloc[val_idx], y_cal[val_idx]

        # 1. Raw baseline
        if hasattr(base_model, "predict_proba"):
            p_raw = base_model.predict_proba(X_va)
        else:
            p_raw = softmax(base_model.decision_function(X_va), axis=1)

        fold_metrics["raw"]["brier"].append(compute_brier(y_va, p_raw))
        fold_metrics["raw"]["ece"].append(compute_ece(y_va, p_raw))
        fold_metrics["raw"]["log_loss"].append(log_loss(y_va, p_raw, labels=[0, 1, 2]))

        # 2. Sigmoid OvR
        cal_sig = CalibratedClassifierCV(estimator=base_model, method="sigmoid", cv="prefit")
        cal_sig.fit(X_tr, y_tr)
        p_sig = cal_sig.predict_proba(X_va)
        fold_metrics["sigmoid"]["brier"].append(compute_brier(y_va, p_sig))
        fold_metrics["sigmoid"]["ece"].append(compute_ece(y_va, p_sig))
        fold_metrics["sigmoid"]["log_loss"].append(log_loss(y_va, p_sig, labels=[0, 1, 2]))

        # 3. Isotonic OvR
        cal_iso = CalibratedClassifierCV(estimator=base_model, method="isotonic", cv="prefit")
        cal_iso.fit(X_tr, y_tr)
        p_iso = cal_iso.predict_proba(X_va)
        fold_metrics["isotonic"]["brier"].append(compute_brier(y_va, p_iso))
        fold_metrics["isotonic"]["ece"].append(compute_ece(y_va, p_iso))
        fold_metrics["isotonic"]["log_loss"].append(log_loss(y_va, p_iso, labels=[0, 1, 2]))

        # 4. Temperature scaling
        cal_temp = TemperatureScalingCalibrator(estimator=base_model)
        cal_temp.fit(X_tr, y_tr)
        p_temp = cal_temp.predict_proba(X_va)
        fold_metrics["temperature"]["brier"].append(compute_brier(y_va, p_temp))
        fold_metrics["temperature"]["ece"].append(compute_ece(y_va, p_temp))
        fold_metrics["temperature"]["log_loss"].append(log_loss(y_va, p_temp, labels=[0, 1, 2]))

    # Aggregate means
    summary = {}
    for m in methods:
        summary[m] = {
            "brier_mean": float(np.mean(fold_metrics[m]["brier"])),
            "brier_std": float(np.std(fold_metrics[m]["brier"])),
            "ece_mean": float(np.mean(fold_metrics[m]["ece"])),
            "ece_std": float(np.std(fold_metrics[m]["ece"])),
            "log_loss_mean": float(np.mean(fold_metrics[m]["log_loss"])),
        }
    return summary


def main():
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "nonlinear" / "dataset.csv"
    split_path = root / "data" / "processed" / "split.json"
    models_dir = root / "artifacts" / "v2" / "models"

    df = pd.read_csv(data_path)
    splits = load_split(str(split_path))

    cal_a_idx = splits["cal_a"]
    X_cal_a = df.loc[cal_a_idx, ALL_FEATURES].reset_index(drop=True)
    y_cal_a = encode_bands(df.loc[cal_a_idx, "performance"])

    models = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]
    all_results = {}

    print("=" * 90)
    print("CALIBRATION CROSS-VALIDATION ON CAL-A ONLY (N = 1,190, 5-Fold Stratified CV)")
    print("Candidates: Raw (baseline), Sigmoid (Platt OvR), Isotonic (OvR), Temperature Scaling")
    print("=" * 90)

    for m in models:
        model_path = models_dir / m / "model.joblib"
        cal_model = joblib.load(model_path)
        base_model = cal_model.estimator
        res = cross_validate_calibration(base_model, X_cal_a, y_cal_a, n_splits=5, seed=42)
        all_results[m] = res
        print(f"\nModel: {m}")
        for meth in ["raw", "sigmoid", "isotonic", "temperature"]:
            r = res[meth]
            print(f"  {meth:12s} Brier: {r['brier_mean']:.4f} +- {r['brier_std']:.4f} | ECE: {r['ece_mean']:.4f} | NLL: {r['log_loss_mean']:.4f}")

    # Compute overall mean Brier across all seven models
    print("\n" + "=" * 90)
    print("OVERALL SUMMARY ACROSS ALL 7 MODELS (Mean across models of 5-Fold CV metrics on cal-A):")
    print("=" * 90)
    print(f"{'Method':15s} | {'Mean Brier':12s} | {'Mean ECE':10s} | {'Mean Log Loss':14s}")
    print("-" * 60)
    method_scores = {}
    for meth in ["raw", "sigmoid", "isotonic", "temperature"]:
        mean_brier = float(np.mean([all_results[m][meth]["brier_mean"] for m in models]))
        mean_ece = float(np.mean([all_results[m][meth]["ece_mean"] for m in models]))
        mean_nll = float(np.mean([all_results[m][meth]["log_loss_mean"] for m in models]))
        method_scores[meth] = {"brier": mean_brier, "ece": mean_ece, "nll": mean_nll}
        print(f"{meth:15s} | {mean_brier:12.4f} | {mean_ece:10.4f} | {mean_nll:14.4f}")

    best_method = min(method_scores, key=lambda k: method_scores[k]["brier"])
    print(f"\n===> SELECTED COMMON CALIBRATION METHOD BY MEAN BRIER: {best_method.upper()} <===")

    # Save to reports/calibration_cv_cal_a.json
    out_file = root / "reports" / "calibration_cv_cal_a.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump({"per_model": all_results, "overall": method_scores, "selected": best_method}, f, indent=2)
    print(f"Saved full CV report to {out_file}")


if __name__ == "__main__":
    main()
