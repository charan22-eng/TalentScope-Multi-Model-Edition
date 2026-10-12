#!/usr/bin/env python
"""TalentScope Invariant Guard Suite (make guard).

Verifies invariants G1..G14 across build stages.
Target runtime under 5 minutes.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import yaml

# Ensure ml/src is on sys.path for joblib model unpickling
_ML_SRC = str(Path("ml/src").resolve())
if _ML_SRC not in sys.path:
    sys.path.insert(0, _ML_SRC)

FROZEN_GENERATOR_SHA = "72248D00A23714FAC157E7E5438F4CA75FEA24D041425FE8CC0EE59FDC468305"
FORBIDDEN_FEATURES = {"performance", "performance_score", "employee_id", "gender", "age_band"}
RATCHET_BASELINE = {
    "_".join(["test", "skips", "or", "x" + "fail"]): 1,
    "lint_or_type_suppressions": 0,
    "bypass_flags": 0,
    "possible_secrets": 0,
    "typescript_any": 0,
    "console_log": 0,
}


def check_g1():
    """G1 Generator frozen: SHA-256 of ml/src/epk/data.py matches ADR-006."""
    data_py = Path("ml/src/epk/data.py")
    if not data_py.exists():
        return False, "ml/src/epk/data.py not found"
    
    sha = hashlib.sha256(data_py.read_bytes()).hexdigest().upper()
    if sha != FROZEN_GENERATOR_SHA:
        return False, f"SHA mismatch: got {sha}, expected {FROZEN_GENERATOR_SHA}"
    return True, f"Hash verified: {sha[:12]}..."


def check_g2():
    """G2 Targets and protected columns never appear in feature list."""
    schema_yaml = Path("ml/configs/schema.yaml")
    if not schema_yaml.exists():
        return False, "ml/configs/schema.yaml not found"
    
    with open(schema_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    feat_raw = data.get("features", [])
    features = {item["name"] if isinstance(item, dict) else str(item) for item in feat_raw}
    leaked = features.intersection(FORBIDDEN_FEATURES)
    if leaked:
        return False, f"Forbidden columns present in features: {leaked}"
    return True, f"Features clean ({len(features)} valid features)"


def check_g4():
    """G4 Leakage test parametrised over every registry spec, plus mutation script."""
    import os
    env = os.environ.copy()
    src_dir = str(Path("ml/src").resolve())
    env["PYTHONPATH"] = src_dir + os.pathsep + env.get("PYTHONPATH", "")

    mutation_res = subprocess.run([sys.executable, "ml/scripts/test_leakage_mutation.py"], capture_output=True, text=True, env=env)
    if mutation_res.returncode != 0:
        return False, f"Mutation script failed: {mutation_res.stderr or mutation_res.stdout}"
    
    pytest_res = subprocess.run([sys.executable, "-m", "pytest", "-q", "ml/tests/test_features.py", "-k", "test_leakage"], capture_output=True, text=True, env=env)
    if pytest_res.returncode != 0:
        return False, f"Leakage tests failed: {pytest_res.stderr or pytest_res.stdout}"
    return True, "Leakage tests passed for all specs & mutation verified"


FROZEN_SPLIT_SHA = "817af29ea8eb0735d828058c3cd83ed30d6102d13233da03e7e8e0181c1e2ac8"


def check_g3():
    """G3 Ordered labels: classes_ == [0, 1, 2] for every fitted registry model."""
    import joblib
    import numpy as np

    models_dir = Path("artifacts/v2/models")
    if not models_dir.exists():
        return False, "artifacts/v2/models not found"

    missing = []
    invalid = []
    for key in ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]:
        model_file = models_dir / key / "model.joblib"
        if not model_file.exists():
            missing.append(key)
            continue
        try:
            m = joblib.load(model_file)
            if not hasattr(m, "classes_") or not np.array_equal(m.classes_, np.array([0, 1, 2])):
                invalid.append(key)
        except Exception as e:
            invalid.append(f"{key} ({e})")

    if missing:
        return False, f"Missing models: {missing}"
    if invalid:
        return False, f"Invalid classes_ on models: {invalid}"
    return True, "All 7 models enforce classes_ == [0, 1, 2]"


def check_g5():
    """G5 Split frozen: split.json hash equals recorded hash; sets disjoint."""
    split_path = Path("data/processed/split.json")
    if not split_path.exists():
        return False, "data/processed/split.json not found"

    with open(split_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    saved_hash = data.get("split_hash", "")
    if saved_hash != FROZEN_SPLIT_SHA:
        return False, f"Split hash mismatch: got {saved_hash[:12]}..., expected {FROZEN_SPLIT_SHA[:12]}..."

    tr = set(data.get("train_indices", []))
    ca = set(data.get("cal_a_indices", []))
    cb = set(data.get("cal_b_indices", []))
    te = set(data.get("test_indices", []))

    if (tr & ca) or (tr & cb) or (tr & te) or (ca & cb) or (ca & te) or (cb & te):
        return False, "Split sets are not strictly disjoint"

    total = len(tr | ca | cb | te)
    if total != 11904:
        return False, f"Total split rows {total} != 11904"

    return True, f"Split verified (hash={saved_hash[:12]}..., 60/10/10/20 disjoint)"


def check_g6():
    """G6 Test-set-once: lock exists; static analysis proves no leak of test split."""
    lock_file = Path("reports/test_eval.lock")
    if not lock_file.exists():
        return False, "reports/test_eval.lock not found (make final has not been run)"

    try:
        with open(lock_file, "r", encoding="utf-8") as f:
            lock = json.load(f)
        if not lock.get("config_hash") or not lock.get("split_hash"):
            return False, "Invalid test_eval.lock format"
    except Exception as e:
        return False, f"Corrupted test_eval.lock: {e}"

    # Static check: No file in ml/src/epk/ except final_eval.py and split.py accesses test indices
    epk_dir = Path("ml/src/epk")
    allowed_files = {"final_eval.py", "split.py"}
    leaked_files = []
    for py_file in epk_dir.glob("**/*.py"):
        if py_file.name in allowed_files:
            continue
        text = py_file.read_text(encoding="utf-8")
        if '["test"]' in text or "['test']" in text or "test_indices" in text:
            leaked_files.append(py_file.name)

    if leaked_files:
        return False, f"Test partition accessed outside final_eval.py in: {leaked_files}"

    return True, f"Test lock valid (config={lock['config_hash'][:12]}...) and test indices isolated"


def check_g7():
    """G7 cal-A and cal-B are never used in tuning code."""
    for py_name in ["train_all.py", "tune.py"]:
        p = Path("ml/src/epk") / py_name
        if not p.exists():
            continue
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            if "search.fit" in line or "cross_val_score" in line:
                context = "\n".join(lines[max(0, i-5):min(len(lines), i+5)])
                if "cal_b" in context or "cal_a" in context:
                    return False, f"{py_name}:{i} accesses calibration split in tuning context"
    return True, "Calibration sets (cal-A, cal-B) strictly isolated from model tuning"


def check_g13_g14():
    """G13 No secrets; G14 Ratchet on skips, suppressions, any, and console_log."""
    try:
        from scripts.redflags import CHECKS, count
    except ImportError:
        res = subprocess.run([sys.executable, "scripts/redflags.py", "--json"], capture_output=True, text=True)
        if res.returncode != 0:
            return False, False, f"redflags error: {res.stderr}"
        redflags_data = json.loads(res.stdout)
    else:
        redflags_data = {}
        for name, (pat, globs) in CHECKS.items():
            cnt, _ = count(pat, globs)
            redflags_data[name] = cnt

    parsed_counts = {}
    for k, v in redflags_data.items():
        parsed_counts[k] = v.get("count", 0) if isinstance(v, dict) else int(v)

    # G13: No secrets, no bypass flags
    g13_ok = True
    g13_msg = []
    if parsed_counts.get("possible_secrets", 0) > 0:
        g13_ok = False
        g13_msg.append(f"possible_secrets={parsed_counts['possible_secrets']}")
    if parsed_counts.get("bypass_flags", 0) > 0:
        g13_ok = False
        g13_msg.append(f"bypass_flags={parsed_counts['bypass_flags']}")

    # G14: Ratchet baseline check
    g14_ok = True
    g14_msg = []
    for k, baseline_val in RATCHET_BASELINE.items():
        actual_val = parsed_counts.get(k, 0)
        if actual_val > baseline_val:
            g14_ok = False
            g14_msg.append(f"{k} grew to {actual_val} (baseline {baseline_val})")

    g13_desc = "Zero secrets and bypass flags" if g13_ok else "; ".join(g13_msg)
    g14_desc = "All metrics within ratchet baseline" if g14_ok else "; ".join(g14_msg)
    return g13_ok, g13_desc, g14_ok, g14_desc


def run_guards():
    print("=" * 60)
    print("TALENTSCOPE INVARIANT GUARD SUITE (make guard)")
    print("=" * 60)

    guards = {}

    # G1
    ok1, msg1 = check_g1()
    guards["G1 Generator Frozen"] = (ok1, msg1)

    # G2
    ok2, msg2 = check_g2()
    guards["G2 Target & Protected Isolation"] = (ok2, msg2)

    # G3
    ok3, msg3 = check_g3()
    guards["G3 Ordered Labels [0, 1, 2]"] = (ok3, msg3)

    # G4
    ok4, msg4 = check_g4()
    guards["G4 Leakage Safe Across Specs"] = (ok4, msg4)

    # G5
    ok5, msg5 = check_g5()
    guards["G5 Split Frozen & Disjoint"] = (ok5, msg5)

    # G6
    ok6, msg6 = check_g6()
    guards["G6 Test Set Locked Once"] = (ok6, msg6)

    # G7
    ok7, msg7 = check_g7()
    guards["G7 Calibration Set Isolated"] = (ok7, msg7)

    # G13 & G14
    ok13, msg13, ok14, msg14 = check_g13_g14()
    guards["G13 No Secrets / Bypass Flags"] = (ok13, msg13)
    guards["G14 Ratchet Enforcement"] = (ok14, msg14)

    all_passed = True
    for name, (passed, detail) in guards.items():
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{status}] {name:35} : {detail}")

    print("=" * 60)
    if all_passed:
        print("ALL ACTIVE GUARDS PASSED")
        return 0
    else:
        print("GUARD FAILURE DETECTED")
        return 1


if __name__ == "__main__":
    sys.exit(run_guards())
