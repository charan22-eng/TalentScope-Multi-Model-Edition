"""Strict validator for Local LLM verdict outputs (Guard G9).

Verifies:
1. Valid JSON and schema structure
2. Every cited fact_id exists in packet["facts"]
3. Every claim, tradeoff, caveat cites >= 1 fact
4. Numbers in text match numbers in cited facts (numeric faithfulness)
5. Recommendation model_key exists in packet["models"]
6. Recommendation equals deterministic_winner unless agreement="disagree"
7. Confidence "clear" is rejected when decision_strength is "marginal" or "none"
8. Synthetic caveat fact is cited in caveats
9. Unsupported absolute words (always, never, guaranteed, perfect, etc.) are rejected
"""

import re
from typing import Any, Dict, List, Set

NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")
BANNED_WORDS_RE = re.compile(r"\b(guarantee[sd]?|always|never fails|perfect|certainly|proves?)\b", re.IGNORECASE)


def _canonicalize_numbers(tok: str) -> Set[float]:
    """Parse number or percentage into set of equivalent floats."""
    t = tok.replace(",", "")
    pct = t.endswith("%")
    try:
        v = float(t.rstrip("%"))
    except ValueError:
        return set()

    vals = {round(v, 4)}
    if pct:
        vals.add(round(v / 100.0, 4))
    else:
        if 0.0 <= v <= 1.0:
            vals.add(round(v * 100.0, 4))
    return vals


def validate_verdict(out: Dict[str, Any], packet: Dict[str, Any]) -> List[str]:
    """Return a list of violations (empty list = accepted)."""
    errs: List[str] = []

    if not isinstance(out, dict):
        return ["output is not a JSON object"]

    # Basic top-level schema check
    for req_field in ["headline", "recommendation", "claims", "tradeoffs", "caveats"]:
        if req_field not in out:
            errs.append(f"missing required field '{req_field}'")

    if errs:
        return errs

    facts_map = {f["id"]: f["text"] for f in packet.get("facts", [])}
    models = packet.get("models", [])
    model_keys = {m["key"] for m in models}

    headline = out.get("headline", "")
    if not isinstance(headline, str) or len(headline) > 200:
        errs.append("headline: must be a string under 200 characters")

    # Recommendation checks
    rec = out.get("recommendation", {})
    if not isinstance(rec, dict):
        errs.append("recommendation: must be an object")
    else:
        m_key = rec.get("model_key")
        conf = rec.get("confidence")
        agree = rec.get("agreement")

        if m_key not in model_keys:
            errs.append(f"recommendation: unknown model_key '{m_key}'")
        elif m_key != packet.get("deterministic_winner") and agree != "disagree":
            errs.append(
                f"recommendation differs from deterministic winner '{packet.get('deterministic_winner')}' "
                f"without agreement='disagree'"
            )

        dec_strength = packet.get("decision_strength", "none")
        if dec_strength in ("marginal", "none") and conf == "clear":
            errs.append(f"confidence 'clear' not allowed when decision_strength is '{dec_strength}'")

    # Collect cited blocks
    blocks = [("headline", headline, [])]
    for section in ("claims", "tradeoffs", "caveats"):
        items = out.get(section, [])
        if not isinstance(items, list):
            errs.append(f"{section}: must be an array")
            continue

        if section == "claims" and (len(items) < 2 or len(items) > 6):
            errs.append(f"claims: array length must be between 2 and 6 (got {len(items)})")
        elif section == "tradeoffs" and len(items) > 4:
            errs.append(f"tradeoffs: array length must be at most 4 (got {len(items)})")
        elif section == "caveats" and (len(items) < 1 or len(items) > 4):
            errs.append(f"caveats: array length must be between 1 and 4 (got {len(items)})")

        for i, item in enumerate(items):
            prefix = f"{section}[{i}]"
            if not isinstance(item, dict):
                errs.append(f"{prefix}: must be an object")
                continue
            text = item.get("text", "")
            if not isinstance(text, str) or len(text) > 280:
                errs.append(f"{prefix}: text must be a string under 280 characters")
            fact_ids = item.get("fact_ids", [])
            if not isinstance(fact_ids, list) or len(fact_ids) == 0:
                errs.append(f"{prefix}: no fact_ids provided")
            blocks.append((prefix, text, fact_ids))

    # Citation & numeric faithfulness verification
    for name, text, ids in blocks:
        # Check fact IDs exist
        bad_ids = [fid for fid in ids if fid not in facts_map]
        if bad_ids:
            errs.append(f"{name}: unknown fact ids {bad_ids}")

        # Number extraction
        allowed_nums: Set[float] = set()
        for fid in ids:
            if fid in facts_map:
                for tok in NUM_RE.findall(facts_map[fid]):
                    allowed_nums |= _canonicalize_numbers(tok)

        text_nums = NUM_RE.findall(text)
        for tok in text_nums:
            canon = _canonicalize_numbers(tok)
            if not (canon & allowed_nums):
                errs.append(f"{name}: number {tok} not supported by cited facts")

        # Absolute wording check
        if BANNED_WORDS_RE.search(text):
            errs.append(f"{name}: unsupported absolute wording")

    # Synthetic-data caveat fact check
    caveat_fact = packet.get("synthetic_caveat_fact", "F90")
    cited_caveats = {
        fid
        for c in out.get("caveats", [])
        if isinstance(c, dict)
        for fid in c.get("fact_ids", [])
    }
    if caveat_fact not in cited_caveats:
        errs.append(f"synthetic-data caveat fact '{caveat_fact}' missing from caveats")

    return errs
