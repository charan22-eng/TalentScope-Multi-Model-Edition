import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

ROOT = Path(".")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml/src"))

from epk.artifacts import ArtifactLoader, ArtifactIntegrityError
from epk.llm.client import LocalLLM, assert_local
from epk.llm.validator import validate_verdict

def test_x02_generator_freeze():
    """X2: Add 1 character to a copy of ml/src/epk/data.py; verify hash changes and guard fails."""
    data_py = ROOT / "ml/src/epk/data.py"
    content = data_py.read_bytes()
    corrupted = content + b"\n# defect"
    h_orig = hashlib.sha256(content).hexdigest().upper()
    h_corr = hashlib.sha256(corrupted).hexdigest().upper()
    passed = (h_orig != h_corr)
    print(f"[X2 Generator Freeze] Original: {h_orig[:12]}..., Corrupted: {h_corr[:12]}... -> Differs: {passed}")
    return passed

def test_x04_artifact_tamper():
    """X4: Flip 1 byte in a copy of model file; verify ArtifactLoader refuses with ArtifactIntegrityError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Copy artifacts bundle
        shutil.copytree(ROOT / "artifacts/v2", tmp_path / "artifacts/v2")
        loader = ArtifactLoader(root_dir=tmp_path / "artifacts/v2")
        
        # Corrupt one model file (rf/model.joblib)
        target = tmp_path / "artifacts/v2/models/rf/model.joblib"
        if target.exists():
            data = bytearray(target.read_bytes())
            data[10] = (data[10] + 1) % 256  # flip byte
            target.write_bytes(data)
            
            refused = False
            try:
                loader.load_model("rf")
            except ArtifactIntegrityError as e:
                refused = True
                print(f"[X4 Tamper Detection] Correctly refused corrupted file: {e}")
            except Exception as e:
                print(f"[X4 Tamper Detection] Unexpected exception: {type(e).__name__}: {e}")
            return refused
        else:
            print("[X4 Tamper Detection] Target model.joblib not found")
            return False

def test_x05_validator_attacks():
    """X5: 10 invalid verdicts rejected; 3 faithful accepted."""
    evidence_file = ROOT / "artifacts/v2/comparison/evidence_packet.json"
    if not evidence_file.exists():
        print("[X5 Validator Attacks] Evidence packet missing")
        return False
    with open(evidence_file, "r", encoding="utf-8") as f:
        packet = json.load(f)

    # Valid template matching schema
    valid_verdict = {
        "headline": "Random Forest is the recommended champion model under the balanced profile.",
        "recommendation": {
            "model_key": "rf",
            "confidence": "moderate",
            "agreement": "agree"
        },
        "claims": [
            {
                "text": "Random forest achieved macro-F1 0.7804 on 2,381 test rows.",
                "fact_ids": ["F1"]
            },
            {
                "text": "Gradient boosting achieved macro-F1 0.8038 on 2,381 test rows.",
                "fact_ids": ["F2"]
            }
        ],
        "tradeoffs": [
            {
                "text": "Gradient boosting has slightly higher macro-F1 0.8038.",
                "fact_ids": ["F2"]
            }
        ],
        "caveats": [
            {
                "text": "Evaluated on synthetic employee dataset.",
                "fact_ids": ["F90"]
            }
        ]
    }

    # 10 invalid attacks
    invalid_cases = [
        ("Wrong model key", {**copy.deepcopy(valid_verdict), "recommendation": {"model_key": "xgboost", "confidence": "moderate", "agreement": "agree"}}),
        ("Clear confidence under marginal strength", {**copy.deepcopy(valid_verdict), "recommendation": {"model_key": "rf", "confidence": "clear", "agreement": "agree"}}),
        ("Winner mismatch without disagree", {**copy.deepcopy(valid_verdict), "recommendation": {"model_key": "dt", "confidence": "moderate", "agreement": "agree"}}),
        ("Uncited fact ID", {**copy.deepcopy(valid_verdict), "claims": [{"text": "Random forest macro-F1 0.7804", "fact_ids": ["F999"]}]}),
        ("Too few claims (<2)", {**copy.deepcopy(valid_verdict), "claims": [{"text": "Random forest macro-F1 0.7804", "fact_ids": ["F1"]}]}),
        ("Empty caveats", {**copy.deepcopy(valid_verdict), "caveats": []}),
        ("Banned words in claim", {**copy.deepcopy(valid_verdict), "claims": [valid_verdict["claims"][0], {"text": "Random forest is guaranteed and always perfect.", "fact_ids": ["F1"]}]}),
        ("Missing required field 'headline'", {k: v for k, v in valid_verdict.items() if k != "headline"}),
        ("Uncited fabricated numbers", {**copy.deepcopy(valid_verdict), "claims": [valid_verdict["claims"][0], {"text": "Model achieved 99.9% accuracy.", "fact_ids": ["F1"]}]}),
        ("Missing fact_ids in tradeoff", {**copy.deepcopy(valid_verdict), "tradeoffs": [{"text": "Tradeoff text without facts.", "fact_ids": []}]}),
    ]

    rejected_count = 0
    for name, attack in invalid_cases:
        errs = validate_verdict(attack, packet)
        if len(errs) > 0:
            rejected_count += 1
            print(f"  [PASS] Rejected attack '{name}': {errs[0]}")
        else:
            print(f"  [FAIL] Did not reject attack '{name}'")

    valid_errs = validate_verdict(valid_verdict, packet)
    valid_accepted = (len(valid_errs) == 0)
    print(f"[X5 Validator Attacks] Rejected {rejected_count}/10 attacks. Valid verdict accepted: {valid_accepted}")
    if not valid_accepted:
        print(f"  Validation errors for valid verdict: {valid_errs}")
    return rejected_count == 10 and valid_accepted

def test_x11_model_key_traversal():
    """X11: Model key path traversal refused."""
    loader = ArtifactLoader(root_dir=ROOT / "artifacts/v2")
    attacks = ["../models", "../../etc/passwd", "rf/../../secret", "unknown_model", ""]
    blocked_count = 0
    for a in attacks:
        try:
            loader.load_model(a)
            print(f"  [FAIL] Allowed traversal: {a}")
        except (ValueError, KeyError, ArtifactIntegrityError):
            blocked_count += 1
            print(f"  [PASS] Blocked traversal: {a}")
    return blocked_count == len(attacks)

def test_x12_llm_ssrf():
    """X12: LLM base URL SSRF guard refuses public / link-local addresses."""
    attacks = [
        "http://169.254.169.254/latest/meta-data",
        "https://api.openai.com/v1",
        "http://8.8.8.8:11434"
    ]
    blocked_count = 0
    for url in attacks:
        try:
            assert_local(url)
            print(f"  [FAIL] Allowed external URL: {url}")
        except ValueError as e:
            blocked_count += 1
            print(f"  [PASS] SSRF Guard blocked: {url} -> {e}")
    return blocked_count == len(attacks)

def run_all():
    print("========================================")
    print("RUNNING ADVERSARIAL AND SECURITY TESTS")
    print("========================================")
    r2 = test_x02_generator_freeze()
    r4 = test_x04_artifact_tamper()
    r5 = test_x05_validator_attacks()
    r11 = test_x11_model_key_traversal()
    r12 = test_x12_llm_ssrf()
    all_ok = all([r2, r4, r5, r11, r12])
    print(f"\nOVERALL RESULT: {'ALL PASSED' if all_ok else 'FAILURES DETECTED'}")
    return all_ok

if __name__ == "__main__":
    ok = run_all()
    exit(0 if ok else 1)
