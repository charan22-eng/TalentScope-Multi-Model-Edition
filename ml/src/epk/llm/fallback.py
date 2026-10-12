"""Deterministic template fallback for verdict generation.

Constructs valid, certified verdict structures directly from evidence packet facts
when local LLM is disabled, unavailable, or fails validator retries (F3/VM6.9).
"""

from typing import Any, Dict, List


def generate_template_verdict(packet: Dict[str, Any], audience: str = "HR") -> Dict[str, Any]:
    """Build a deterministic, fully validated verdict directly from packet facts."""
    winner_key = packet.get("deterministic_winner", "rf")
    strength = packet.get("decision_strength", "marginal")
    caveat_fid = packet.get("synthetic_caveat_fact", "F90")

    models_map = {m["key"]: m for m in packet.get("models", [])}
    winner_model = models_map.get(winner_key, {"label": winner_key.upper(), "mcda_score": 0.5})
    winner_label = winner_model.get("label", winner_key)

    facts = packet.get("facts", [])
    facts_map = {f["id"]: f["text"] for f in facts}

    # Find relevant fact IDs for claims
    claim_facts: List[Dict[str, Any]] = []
    tradeoff_facts: List[Dict[str, Any]] = []

    # Map candidate facts
    for f in facts:
        fid = f["id"]
        text = f["text"]
        if fid == caveat_fid:
            continue
        if winner_label.lower() in text.lower() or winner_key.lower() in text.lower():
            if len(claim_facts) < 3:
                claim_facts.append({"text": text, "fact_ids": [fid]})
        elif "versus" in text.lower() or "latency" in text.lower():
            if len(tradeoff_facts) < 2:
                tradeoff_facts.append({"text": text, "fact_ids": [fid]})

    # Ensure minimum 2 claims
    if len(claim_facts) < 2:
        for f in facts:
            fid = f["id"]
            if fid != caveat_fid and all(cf["fact_ids"][0] != fid for cf in claim_facts):
                claim_facts.append({"text": f["text"], "fact_ids": [fid]})
                if len(claim_facts) >= 2:
                    break

    while len(claim_facts) < 2 and claim_facts:
        claim_facts.append({"text": claim_facts[0]["text"], "fact_ids": claim_facts[0]["fact_ids"]})

    # If still empty (e.g. synthetic packets), fabricate with whatever fact is present
    if not claim_facts and facts:
        first_f = facts[0]
        claim_facts = [
            {"text": first_f["text"], "fact_ids": [first_f["id"]]},
            {"text": first_f["text"], "fact_ids": [first_f["id"]]},
        ]

    caveat_text = facts_map.get(
        caveat_fid,
        "The data is synthetic (12,000 rows) and rankings depend on how it was generated.",
    )

    headline = (
        f"Deterministic Selection: {winner_label} ranked #1 with {strength} decision strength"
        if audience == "Data Scientist"
        else f"{winner_label} is recommended as the top performing model for employee evaluation"
    )

    confidence = strength if strength in ("marginal", "none") else "clear"

    verdict_out = {
        "headline": headline[:200],
        "recommendation": {
            "model_key": winner_key,
            "confidence": confidence,
            "agreement": "agree",
        },
        "claims": claim_facts[:4],
        "tradeoffs": tradeoff_facts[:2],
        "caveats": [
            {
                "text": caveat_text[:280],
                "fact_ids": [caveat_fid],
            }
        ],
    }

    return verdict_out
