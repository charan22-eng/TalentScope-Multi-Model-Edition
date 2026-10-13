"""Regenerate conformal.json by code and verify artifact integrity."""

import hashlib
import json
from pathlib import Path
import sys

# Ensure ml/src is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml" / "src"))

import joblib
import pandas as pd

from epk.artifacts import ArtifactLoader
from epk.features import ALL_FEATURES
from epk.split import load_split
from epk.stats import compute_conformal_sets_cal_b


def main():
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "nonlinear" / "dataset.csv"
    split_path = root / "data" / "processed" / "split.json"
    conformal_path = root / "artifacts" / "v2" / "comparison" / "conformal.json"
    manifest_path = root / "artifacts" / "v2" / "MANIFEST.json"

    df = pd.read_csv(data_path)
    splits = load_split(str(split_path))

    cal_b_df = df.loc[splits["cal_b"]].copy()
    test_df = df.loc[splits["test"]].copy()

    models = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]
    models_dict = {
        m: joblib.load(root / "artifacts" / "v2" / "models" / m / "model.joblib")
        for m in models
    }

    # Load before
    with open(conformal_path, "r", encoding="utf-8") as f:
        before_data = json.load(f)

    # Compute after
    after_data = compute_conformal_sets_cal_b(cal_b_df, test_df, models_dict, alpha=0.10)

    # Save conformal.json
    with open(conformal_path, "w", encoding="utf-8") as f:
        json.dump(after_data, f, indent=2)

    # Compute SHA-256 and size
    with open(conformal_path, "rb") as f:
        content = f.read()
    new_sha = hashlib.sha256(content).hexdigest()
    new_size = len(content)

    # Update MANIFEST.json
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest["files"]["comparison/conformal.json"] = {
        "sha256": new_sha,
        "size_bytes": new_size,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Run Artifact Integrity Check
    loader = ArtifactLoader(root / "artifacts" / "v2")
    loader.verify_file("comparison/conformal.json")
    print("[PASS] Artifact integrity check verified for comparison/conformal.json")
    print(f"  New SHA-256: {new_sha}")
    print(f"  Size bytes: {new_size}")

    # Output Before / After Table
    print("\n### Conformal Prediction Sets (alpha = 0.10, locked test N = 2,381)")
    print("| Model | Coverage (Before) | Coverage (After) | Set Size (Before) | Set Size (After) | Threshold (qhat) | Min Prob Threshold |")
    print("|---|---|---|---|---|---|---|")
    for m in models:
        b = before_data.get(m, {})
        a = after_data[m]
        print(
            f"| `{m}` | {b.get('empirical_coverage', 0.0):.4f} | {a['empirical_coverage']:.4f} | "
            f"{b.get('avg_set_size', 0.0):.3f} | {a['avg_set_size']:.3f} | {a['threshold']:.4f} | {a['min_prob_threshold']:.4f} |"
        )


if __name__ == "__main__":
    main()
