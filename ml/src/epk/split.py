"""Dataset split generator and manager for TalentScope Multi-Model Edition.

Generates and validates the frozen 60/20/20 split:
- 60% Train (inner CV tuning)
- 20% Calibration: halved into disjoint cal-A (10%, probability calibration) and cal-B (10%, conformal prediction)
- 20% Test (strictly locked for final single evaluation via make final)
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit


def create_frozen_split(
    data_path: str = "data/nonlinear/dataset.csv",
    out_path: str = "data/processed/split.json",
    seed: int = 42,
) -> Dict:
    """Create a stratified 60/20/20 split and persist to JSON."""
    df = pd.read_csv(data_path)
    y = df["performance"]
    n_rows = len(df)
    indices = np.arange(n_rows)

    # 1. Split 60% train, 40% temp
    sss_train = StratifiedShuffleSplit(n_splits=1, test_size=0.40, random_state=seed)
    train_rel, temp_rel = next(sss_train.split(indices, y))
    train_idx = indices[train_rel]
    temp_idx = indices[temp_rel]

    # 2. Split 40% temp into 20% test and 20% calibration
    sss_test = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=seed)
    calib_rel, test_rel = next(sss_test.split(temp_idx, y.iloc[temp_idx]))
    calib_idx = temp_idx[calib_rel]
    test_idx = temp_idx[test_rel]

    # 3. Split 20% calibration into 10% cal-A and 10% cal-B
    sss_cal = StratifiedShuffleSplit(n_splits=1, test_size=0.50, random_state=seed)
    cal_a_rel, cal_b_rel = next(sss_cal.split(calib_idx, y.iloc[calib_idx]))
    cal_a_idx = calib_idx[cal_a_rel]
    cal_b_idx = calib_idx[cal_b_rel]

    # Assert mutual disjointness
    s_train, s_ca, s_cb, s_test = set(train_idx), set(cal_a_idx), set(cal_b_idx), set(test_idx)
    assert len(s_train & s_ca) == 0, "Train and cal-A overlap"
    assert len(s_train & s_cb) == 0, "Train and cal-B overlap"
    assert len(s_train & s_test) == 0, "Train and test overlap"
    assert len(s_ca & s_cb) == 0, "cal-A and cal-B overlap"
    assert len(s_ca & s_test) == 0, "cal-A and test overlap"
    assert len(s_cb & s_test) == 0, "cal-B and test overlap"
    assert len(s_train | s_ca | s_cb | s_test) == n_rows, "Splits do not cover all rows"

    # Compute dataset hash
    with open(data_path, "rb") as f:
        dataset_sha256 = hashlib.sha256(f.read()).hexdigest()

    data = {
        "seed": seed,
        "n_rows": n_rows,
        "dataset_sha256": dataset_sha256,
        "train_indices": [int(i) for i in sorted(train_idx)],
        "cal_a_indices": [int(i) for i in sorted(cal_a_idx)],
        "cal_b_indices": [int(i) for i in sorted(cal_b_idx)],
        "test_indices": [int(i) for i in sorted(test_idx)],
        # legacy count fields for backward compatibility
        "train_count": len(train_idx),
        "calibration_count": len(calib_idx),
        "test_count": len(test_idx),
    }

    # Canonical split hash computed without the split_hash key
    payload_bytes = json.dumps(data, sort_keys=True).encode("utf-8")
    split_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    data["split_hash"] = split_sha256

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)

    return data


def load_split(split_path: str = "data/processed/split.json") -> Dict[str, np.ndarray]:
    """Load and validate the frozen split."""
    with open(split_path, "r") as f:
        data = json.load(f)

    train_idx = np.array(data["train_indices"], dtype=int)
    cal_a_idx = np.array(data["cal_a_indices"], dtype=int)
    cal_b_idx = np.array(data["cal_b_indices"], dtype=int)
    test_idx = np.array(data["test_indices"], dtype=int)

    # Disjointness check
    s_train, s_ca, s_cb, s_test = set(train_idx), set(cal_a_idx), set(cal_b_idx), set(test_idx)
    assert len(s_train & s_ca) == 0, "Train and cal-A overlap"
    assert len(s_train & s_cb) == 0, "Train and cal-B overlap"
    assert len(s_train & s_test) == 0, "Train and test overlap"
    assert len(s_ca & s_cb) == 0, "cal-A and cal-B overlap"
    assert len(s_ca & s_test) == 0, "cal-A and test overlap"
    assert len(s_cb & s_test) == 0, "cal-B and test overlap"

    return {
        "train": train_idx,
        "cal_a": cal_a_idx,
        "cal_b": cal_b_idx,
        "test": test_idx,
        "split_hash": data.get("split_hash", ""),
        "meta": data,
    }


if __name__ == "__main__":
    split_data = create_frozen_split()
    print(
        f"Created frozen split: Train={len(split_data['train_indices'])}, "
        f"Cal-A={len(split_data['cal_a_indices'])}, Cal-B={len(split_data['cal_b_indices'])}, "
        f"Test={len(split_data['test_indices'])}, Split Hash={split_data['split_hash'][:12]}..."
    )
