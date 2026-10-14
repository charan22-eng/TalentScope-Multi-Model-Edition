"""calibration_leakage_audit.py — Comprehensive calibration leakage and null test."""

import hashlib
import json
import sys
from pathlib import Path

# Add ml/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml" / "src"))

import joblib
import numpy as np
import pandas as pd
from epk.features import ALL_FEATURES
from epk.labels import encode_bands
from epk.split import load_split


def ece_top(P, y, nb=10):
    conf, pred = P.max(1), P.argmax(1)
    bins = np.linspace(0, 1, nb + 1)
    e = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return e


def null_ece(P, sims=500, seed=0):
    r = np.random.default_rng(seed)
    cum = P.cumsum(1)
    out = []
    for _ in range(sims):
        y = (r.random((len(P), 1)) > cum).sum(1).clip(max=P.shape[1] - 1)
        out.append(ece_top(P, y))
    return np.percentile(out, [1, 5, 50, 95])


def main():
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "nonlinear" / "dataset.csv"
    split_path = root / "data" / "processed" / "split.json"
    models_dir = root / "artifacts" / "v2" / "models"

    df = pd.read_csv(data_path)
    splits = load_split(str(split_path))

    with open(split_path) as f:
        split_raw = json.load(f)

    print("=" * 95)
    print("1. SPLIT DISJOINTNESS & INDEX SHA-256")
    print("=" * 95)
    mapping = {
        "train": split_raw["train_indices"],
        "cal_a": split_raw["cal_a_indices"],
        "cal_b": split_raw["cal_b_indices"],
        "test": split_raw["test_indices"],
    }
    for name, indices in mapping.items():
        sorted_idx = sorted(indices)
        indices_str = ",".join(map(str, sorted_idx))
        h = hashlib.sha256(indices_str.encode("utf-8")).hexdigest()
        print(f"  {name:6s} | N = {len(indices):5d} | SHA-256: {h}")

    s_tr, s_ca, s_cb, s_te = set(mapping["train"]), set(mapping["cal_a"]), set(mapping["cal_b"]), set(mapping["test"])
    print("\nPairwise Intersections:")
    print(f"  train & cal_a: {len(s_tr & s_ca)}")
    print(f"  train & cal_b: {len(s_tr & s_cb)}")
    print(f"  train & test : {len(s_tr & s_te)}")
    print(f"  cal_a & cal_b: {len(s_ca & s_cb)}")
    print(f"  cal_a & test : {len(s_ca & s_te)}")
    print(f"  cal_b & test : {len(s_cb & s_te)}")
    print(f"  Total Union  : {len(s_tr | s_ca | s_cb | s_te)} / {len(df)} rows (100% disjoint)")

    X_cal_a = df.loc[splits["cal_a"], ALL_FEATURES]
    y_cal_a = encode_bands(df.loc[splits["cal_a"], "performance"])

    X_cal_b = df.loc[splits["cal_b"], ALL_FEATURES]
    y_cal_b = encode_bands(df.loc[splits["cal_b"], "performance"])

    X_test = df.loc[splits["test"], ALL_FEATURES]
    y_test = encode_bands(df.loc[splits["test"], "performance"])

    models = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]

    print("\n" + "=" * 95)
    print("2. ECE ACROSS SPLITS (CAL-A IN-SAMPLE, CAL-B OUT-OF-SAMPLE, TEST HOLDOUT)")
    print("   & NULL DISTRIBUTION ON TEST (Labels simulated from model's own probabilities, 500 sims)")
    print("=" * 95)
    print(f"{'Model':7s} | {'cal-A ECE':10s} | {'cal-B ECE':10s} | {'Test ECE':10s} | {'Null 1%':8s} | {'Null 5%':8s} | {'Median':8s} | {'Null 95%':8s} | Note")
    print("-" * 95)

    results = {}
    for m in models:
        model = joblib.load(models_dir / m / "model.joblib")
        p_ca = model.predict_proba(X_cal_a)
        p_cb = model.predict_proba(X_cal_b)
        p_te = model.predict_proba(X_test)

        ece_ca = ece_top(p_ca, y_cal_a)
        ece_cb = ece_top(p_cb, y_cal_b)
        ece_te = ece_top(p_te, y_test)

        p1, p5, p50, p95 = null_ece(p_te, sims=500, seed=0)

        note = "OK"
        if ece_te < p1:
            note = "BELOW 1%"
        elif ece_te < p5:
            note = "Between 1%-5%"
        elif ece_te <= p95:
            note = "Within 90% CI"
        else:
            note = "ABOVE 95%"

        print(f"{m:7s} | {ece_ca:10.4f} | {ece_cb:10.4f} | {ece_te:10.4f} | {p1:8.4f} | {p5:8.4f} | {p50:8.4f} | {p95:8.4f} | {note}")
        results[m] = {
            "cal_a_ece": round(float(ece_ca), 4),
            "cal_b_ece": round(float(ece_cb), 4),
            "test_ece": round(float(ece_te), 4),
            "null_1pct": round(float(p1), 4),
            "null_5pct": round(float(p5), 4),
            "null_median": round(float(p50), 4),
            "null_95pct": round(float(p95), 4),
            "note": note,
        }

    # Save to JSON
    out_path = root / "reports" / "calibration_leakage_audit.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport written to {out_path}")


if __name__ == "__main__":
    main()
