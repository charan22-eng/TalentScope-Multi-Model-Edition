"""Comprehensive test suite for Local LLM validator (Guard G9 & G10).

Verifies at least 12 failing cases, 4 passing cases, prompt isolation, and SSRF guard.
"""

import pytest

from epk.llm.client import FakeLLM, assert_local
from epk.llm.fallback import generate_template_verdict
from epk.llm.orchestrator import generate_verdict
from epk.llm.prompts import format_user_prompt, scan_prompt_for_forbidden_keys
from epk.llm.validator import validate_verdict


@pytest.fixture
def sample_packet():
    return {
        "schema_version": "1.0",
        "checksum": "abc123hash",
        "dataset": {"name": "employees_v2", "variant": "nonlinear", "rows": 12000},
        "profile": {"name": "Balanced", "weights": {"macro_f1": 0.30}},
        "deterministic_winner": "rf",
        "decision_strength": "marginal",
        "synthetic_caveat_fact": "F90",
        "models": [
            {"key": "rf", "label": "Random Forest", "rank": 1, "mcda_score": 0.573},
            {"key": "svm", "label": "Support Vector Machine", "rank": 2, "mcda_score": 0.560},
            {"key": "boost", "label": "Histogram Gradient Boosting", "rank": 3, "mcda_score": 0.540},
        ],
        "facts": [
            {"id": "F1", "text": "Random Forest macro-F1 is 0.7804 (accuracy 0.7770, 77.70%) on 2,381 test rows."},
            {"id": "F2", "text": "Support Vector Machine macro-F1 is 0.8164 with inference latency 23.47 ms."},
            {"id": "F3", "text": "Random Forest calibration error ECE is 0.0133 compared to 0.0270 for SVM."},
            {"id": "F4", "text": "Random Forest versus SVM McNemar-Holm p-value is 0.001."},
            {"id": "F90", "text": "The data is synthetic (12,000 rows) and rankings depend on how it was generated."},
        ],
    }


@pytest.fixture
def valid_verdict():
    return {
        "headline": "Random Forest selected as recommended model under Balanced profile",
        "recommendation": {
            "model_key": "rf",
            "confidence": "marginal",
            "agreement": "agree",
        },
        "claims": [
            {
                "text": "Random Forest achieved macro-F1 0.7804 with test accuracy 0.7770.",
                "fact_ids": ["F1"],
            },
            {
                "text": "Random Forest demonstrated low calibration error with ECE 0.0133.",
                "fact_ids": ["F3"],
            },
        ],
        "tradeoffs": [
            {
                "text": "Support Vector Machine achieved higher macro-F1 of 0.8164 but RF has lower ECE.",
                "fact_ids": ["F2", "F3"],
            }
        ],
        "caveats": [
            {
                "text": "The data is synthetic (12,000 rows) and rankings depend on how it was generated.",
                "fact_ids": ["F90"],
            }
        ],
    }


# ==============================================================================
# PASSING CASES (>= 4 cases)
# ==============================================================================

def test_pass_case_1_standard_valid(sample_packet, valid_verdict):
    """Case P1: Fully valid verdict with agreed champion."""
    errs = validate_verdict(valid_verdict, sample_packet)
    assert len(errs) == 0, f"Expected 0 errors, got: {errs}"


def test_pass_case_2_percentage_equivalence(sample_packet, valid_verdict):
    """Case P2: Number written as percentage matches decimal in fact (77.70% matches 0.7770)."""
    valid_verdict["claims"][0]["text"] = "Random Forest achieved test accuracy of 77.70%."
    errs = validate_verdict(valid_verdict, sample_packet)
    assert len(errs) == 0, f"Expected 0 errors, got: {errs}"


def test_pass_case_3_disagreement_with_reason(sample_packet, valid_verdict):
    """Case P3: Valid recommendation disagreeing with winner when marked agreement='disagree'."""
    valid_verdict["recommendation"]["model_key"] = "svm"
    valid_verdict["recommendation"]["agreement"] = "disagree"
    valid_verdict["claims"].append({
        "text": "SVM is selected due to top macro-F1 0.8164.",
        "fact_ids": ["F2"],
    })
    errs = validate_verdict(valid_verdict, sample_packet)
    assert len(errs) == 0, f"Expected 0 errors, got: {errs}"


def test_pass_case_4_clear_confidence_when_strength_clear(sample_packet, valid_verdict):
    """Case P4: Confidence 'clear' is valid when decision_strength is 'clear'."""
    sample_packet["decision_strength"] = "clear"
    valid_verdict["recommendation"]["confidence"] = "clear"
    errs = validate_verdict(valid_verdict, sample_packet)
    assert len(errs) == 0, f"Expected 0 errors, got: {errs}"


# ==============================================================================
# FAILING CASES (>= 12 cases)
# ==============================================================================

def test_fail_case_1_wrong_number(sample_packet, valid_verdict):
    """Fail 1: Number not present in cited facts."""
    valid_verdict["claims"][0]["text"] = "Random Forest achieved macro-F1 0.9999."
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("not supported by cited facts" in e for e in errs)


def test_fail_case_2_unknown_fact_id(sample_packet, valid_verdict):
    """Fail 2: Cited fact_id does not exist in packet."""
    valid_verdict["claims"][0]["fact_ids"] = ["F999"]
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("unknown fact ids" in e for e in errs)


def test_fail_case_3_missing_fact_ids(sample_packet, valid_verdict):
    """Fail 3: Empty fact_ids array."""
    valid_verdict["claims"][0]["fact_ids"] = []
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("no fact_ids" in e for e in errs)


def test_fail_case_4_missing_synthetic_caveat(sample_packet, valid_verdict):
    """Fail 4: synthetic_caveat_fact (F90) not cited in caveats."""
    valid_verdict["caveats"] = [
        {"text": "Random Forest calibration was good.", "fact_ids": ["F3"]}
    ]
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("synthetic-data caveat fact 'F90' missing" in e for e in errs)


def test_fail_case_5_clear_confidence_under_marginal(sample_packet, valid_verdict):
    """Fail 5: Confidence 'clear' when decision_strength is marginal."""
    sample_packet["decision_strength"] = "marginal"
    valid_verdict["recommendation"]["confidence"] = "clear"
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("confidence 'clear' not allowed" in e for e in errs)


def test_fail_case_6_clear_confidence_under_none(sample_packet, valid_verdict):
    """Fail 6: Confidence 'clear' when decision_strength is none."""
    sample_packet["decision_strength"] = "none"
    valid_verdict["recommendation"]["confidence"] = "clear"
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("confidence 'clear' not allowed" in e for e in errs)


def test_fail_case_7_banned_word_guaranteed(sample_packet, valid_verdict):
    """Fail 7: Absolute wording 'guaranteed' in claim."""
    valid_verdict["claims"][0]["text"] = "Random Forest provides guaranteed performance."
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("unsupported absolute wording" in e for e in errs)


def test_fail_case_8_banned_word_always(sample_packet, valid_verdict):
    """Fail 8: Absolute wording 'always' in tradeoffs."""
    valid_verdict["tradeoffs"][0]["text"] = "Random Forest always beats SVM on calibration."
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("unsupported absolute wording" in e for e in errs)


def test_fail_case_9_wrong_winner_without_disagree(sample_packet, valid_verdict):
    """Fail 9: Winner differs without agreement='disagree'."""
    valid_verdict["recommendation"]["model_key"] = "svm"
    valid_verdict["recommendation"]["agreement"] = "agree"
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("differs from deterministic winner" in e for e in errs)


def test_fail_case_10_unknown_model_key(sample_packet, valid_verdict):
    """Fail 10: Unknown model_key in recommendation."""
    valid_verdict["recommendation"]["model_key"] = "deep_neural_net"
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("unknown model_key" in e for e in errs)


def test_fail_case_11_headline_too_long(sample_packet, valid_verdict):
    """Fail 11: Headline exceeding 200 characters."""
    valid_verdict["headline"] = "X" * 250
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("headline: must be a string under 200 characters" in e for e in errs)


def test_fail_case_12_missing_required_section(sample_packet, valid_verdict):
    """Fail 12: Missing 'tradeoffs' section."""
    del valid_verdict["tradeoffs"]
    errs = validate_verdict(valid_verdict, sample_packet)
    assert any("missing required field 'tradeoffs'" in e for e in errs)


# ==============================================================================
# PROMPT SECURITY & SSRF (Guard G10 & VM6.3)
# ==============================================================================

def test_prompt_no_employee_level_keys(sample_packet):
    """Guard G9 / VM6.3: ensure formatted prompts never leak employee identifiers."""
    prompt = format_user_prompt(sample_packet, audience="HR")
    violations = scan_prompt_for_forbidden_keys(prompt)
    assert violations == []


def test_prompt_scanner_detects_leakage():
    """Verify scanner catches injected employee identifiers."""
    bad_prompt = "Here is employee_id 12345 with salary 85000 and gender Male."
    violations = scan_prompt_for_forbidden_keys(bad_prompt)
    assert len(violations) >= 3


def test_assert_local_ssrf_guard():
    """Guard G10: assert_local allows localhost and refuses public IPs."""
    # Loopback addresses must pass
    assert_local("http://localhost:11434")
    assert_local("http://127.0.0.1:8000")

    # Public hosts must be refused
    with pytest.raises(ValueError, match="refusing"):
        assert_local("http://8.8.8.8:11434")

    # Public hostnames must be refused
    with pytest.raises(ValueError, match="refusing"):
        assert_local("http://api.openai.com")


# ==============================================================================
# ORCHESTRATOR & FALLBACK
# ==============================================================================

def test_template_fallback_validity(sample_packet):
    """Verify deterministic template fallback produces 100% valid verdict."""
    tpl = generate_template_verdict(sample_packet, audience="HR")
    errs = validate_verdict(tpl, sample_packet)
    assert errs == []


def test_orchestrator_fallback_on_failure(sample_packet):
    """Orchestrator retries up to 2 times and falls back to template."""
    bad_llm = FakeLLM(canned_response_or_func={"bad": "response"})
    res = generate_verdict(bad_llm, sample_packet, audience="HR", use_cache=False, max_retries=2)
    assert res["source"] == "template"
    assert res["attempts"] == 3
    assert validate_verdict(res["output"], sample_packet) == []
