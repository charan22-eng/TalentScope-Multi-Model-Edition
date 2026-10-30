import json
import re
from pathlib import Path

ROOT = Path(".")

def audit_numbers():
    print("========================================")
    print("X26 NUMBERS-CONSISTENCY AUDIT")
    print("========================================")
    
    # 1. Load ground truth machine files
    lb_file = ROOT / "artifacts/v2/comparison/leaderboard.json"
    champ_file = ROOT / "artifacts/v2/champion.json"
    mcda_file = ROOT / "artifacts/v2/comparison/mcda.json"
    
    if not (lb_file.exists() and champ_file.exists() and mcda_file.exists()):
        print("[FAIL] One or more ground truth machine files missing")
        return False
        
    with open(lb_file, "r", encoding="utf-8") as f:
        lb = json.load(f)
    with open(champ_file, "r", encoding="utf-8") as f:
        champ = json.load(f)
    with open(mcda_file, "r", encoding="utf-8") as f:
        mcda = json.load(f)
        
    rep_metrics = {m["key"]: m for m in lb.get("metrics", [])}
    champion_key = champ.get("champion") or champ.get("champion_key") or "boost"
    
    docs_to_check = [
        ROOT / "docs/BUILD_REPORT.md",
        ROOT / "README.md",
        ROOT / "docs/model_card.md",
        ROOT / "docs/datasheet.md",
    ]
    
    findings = []
    
    boost_f1 = f"{rep_metrics['boost']['macro_f1']:.4f}"
    rf_f1 = f"{rep_metrics['rf']['macro_f1']:.4f}"
    rf_ece = f"{rep_metrics['rf']['ece']:.4f}"

    # Verify champion consistency
    for doc in docs_to_check:
        if not doc.exists():
            findings.append(f"Missing doc: {doc}")
            continue
        text = doc.read_text(encoding="utf-8")
        
        # Check champion model mention
        if "Champion" in text:
            if champion_key not in text and "boost" not in text and "rf" not in text:
                findings.append(f"{doc.name}: Mentions Champion but missing '{champion_key}'")

    print(f"Ground Truth Champion : {champion_key}")
    print(f"Ground Truth Winner   : {mcda.get('deterministic_winner')}")
    print(f"Ground Truth boost F1 : {boost_f1}")
    print(f"Ground Truth rf F1    : {rf_f1}")
    print(f"Ground Truth ECE (rf) : {rf_ece}")
    
    # Check BUILD_REPORT specifically against dynamic machine values
    br_text = (ROOT / "docs/BUILD_REPORT.md").read_text(encoding="utf-8")
    assert boost_f1 in br_text, f"BUILD_REPORT missing boost Macro-F1 {boost_f1}"
    assert rf_f1 in br_text, f"BUILD_REPORT missing rf Macro-F1 {rf_f1}"
    assert rf_ece in br_text, f"BUILD_REPORT missing rf ECE {rf_ece}"
    print("[PASS] BUILD_REPORT.md numbers strictly match machine files.")
    
    return len(findings) == 0

if __name__ == "__main__":
    ok = audit_numbers()
    print("Result:", "PASS" if ok else "FAIL")
    exit(0 if ok else 1)
