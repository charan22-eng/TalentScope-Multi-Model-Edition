"""Comprehensive tests for TalentScope API v2 and Guards G11/G12."""

import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.core.security import get_current_user, get_current_user_email
from backend.db.models import User

client = TestClient(app)

# Test users fixture
ADMIN_USER = User(id=1, email="admin@test.com", role="admin")
ANALYST_USER = User(id=2, email="analyst@test.com", role="analyst")
HR_USER = User(id=3, email="hr@test.com", role="hr")
REVIEWER_USER = User(id=4, email="reviewer@test.com", role="reviewer")

SAMPLE_FEATURES = {
    "attendance": 92.5,
    "experience_years": 4.5,
    "training_hours": 35.0,
    "projects_completed": 6.0,
    "weekly_hours": 41.0,
    "prev_score": 3.8,
    "department": "Engineering",
    "job_level": "Mid",
    "peer_feedback": 3.9,
    "tasks_on_time_pct": 85.0,
    "certifications": 2.0,
}


@pytest.fixture(autouse=True)
def setup_auth():
    """Default auth override to Admin for general tests."""
    app.dependency_overrides[get_current_user_email] = lambda: "admin@test.com"
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    yield
    app.dependency_overrides.clear()


# ==============================================================================
# 1. Models & Registry
# ==============================================================================

def test_v2_models_list():
    resp = client.get("/api/v2/models")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 7
    keys = {m["key"] for m in data}
    assert keys == {"linreg", "logreg", "knn", "svm", "dt", "rf", "boost"}

    rf_model = next(m for m in data if m["key"] == "rf")
    assert rf_model["is_champion"] is True
    assert rf_model["sha256"] != "unknown"


# ==============================================================================
# 2. Prediction Endpoints & G11 Whitelist Guard
# ==============================================================================

def test_v2_predict_single_model():
    resp = client.post("/api/v2/predict", json={"model_key": "rf", "features": SAMPLE_FEATURES})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_key"] == "rf"
    assert data["predicted_band"] in ["Low", "Medium", "High"]
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["prediction_set"], list)
    assert sum(data["probabilities"].values()) == pytest.approx(1.0, abs=0.01)


def test_v2_predict_whitelist_guard_g11():
    """Guard G11: Unrecognized model key must be rejected with 400 Problem Details."""
    resp = client.post("/api/v2/predict", json={"model_key": "catboost_unknown", "features": SAMPLE_FEATURES})
    assert resp.status_code == 400
    err = resp.json()
    assert "detail" in err
    assert "Unknown model key" in err["detail"]


def test_v2_predict_path_traversal_refused_g11():
    """Guard G11: Path traversal attempts must be rejected with 400 Problem Details."""
    resp = client.post("/api/v2/predict", json={"model_key": "../../etc/passwd", "features": SAMPLE_FEATURES})
    assert resp.status_code == 400
    err = resp.json()
    assert "Path traversal" in err["detail"]


def test_v2_predict_all_performance_and_consensus():
    """Verify predict/all runs all 7 models under 800ms with consensus & split-decision flag."""
    resp = client.post("/api/v2/predict/all", json=SAMPLE_FEATURES)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["predictions"]) == 7
    assert data["champion_key"] == "rf"
    assert data["consensus_band"] in ["Low", "Medium", "High"]
    assert 0.0 < data["agreement_rate"] <= 1.0
    assert isinstance(data["split_decision"], bool)
    assert "latency_ms" in data
    # Latency budget: p95 < 800 ms
    assert data["latency_ms"] < 800.0


# ==============================================================================
# 3. Explainability
# ==============================================================================

def test_v2_explain_endpoint():
    resp = client.post("/api/v2/explain", json={"model_key": "rf", "features": SAMPLE_FEATURES, "k": 3})
    assert resp.status_code == 200
    data = resp.json()

    assert data["explanation_type"] in ["native", "partial", "model_agnostic"]
    assert "native_explanation" in data
    assert "local_attribution" in data
    assert "counterfactuals" in data
    assert "similar_cases" in data
    assert data["similar_cases"]["banner"] == "Similar Historical Cases (Not how this model decided)"
    assert "persona_summaries" in data
    assert "hr_summary" in data["persona_summaries"]


def test_v2_explain_knn_native_reasoning():
    resp = client.post("/api/v2/explain", json={"model_key": "knn", "features": SAMPLE_FEATURES, "k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_key"] == "knn"
    assert data["similar_cases"]["is_native_reasoning"] is True
    assert "Native Decision Reasoning" in data["similar_cases"]["banner"]


# ==============================================================================
# 4. Comparison Topics & MCDA
# ==============================================================================

@pytest.mark.parametrize("topic", [
    "leaderboard", "curves", "confusion", "head2head", "pairwise",
    "importance", "sensitivity", "fairness", "robustness", "mcda", "evidence"
])
def test_v2_compare_valid_topics(topic):
    resp = client.get(f"/api/v2/compare/{topic}")
    assert resp.status_code == 200


def test_v2_compare_unknown_topic_404():
    resp = client.get("/api/v2/compare/invalid_topic_xyz")
    assert resp.status_code == 404
    err = resp.json()
    assert err["title"] == "Comparison Topic Not Found"


def test_v2_compare_mcda_custom_weights():
    custom_weights = {
        "macro_f1": 0.40,
        "qwk": 0.10,
        "calibration": 0.10,
        "robustness": 0.10,
        "fairness": 0.10,
        "stability": 0.05,
        "latency": 0.05,
        "train_cost": 0.05,
        "explainability": 0.05,
    }
    resp = client.post("/api/v2/compare/mcda", json={"weights": custom_weights})
    assert resp.status_code == 200
    data = resp.json()
    assert "deterministic_winner" in data
    assert "ranking" in data
    assert len(data["ranking"]) == 7


def test_v2_compare_mcda_invalid_weights_400():
    resp = client.post("/api/v2/compare/mcda", json={"weights": {"macro_f1": -0.5}})
    assert resp.status_code == 400


# ==============================================================================
# 5. Visualizations (Surface & PCA)
# ==============================================================================

def test_v2_viz_surface():
    resp = client.get("/api/v2/viz/surface?model_key=rf&grid_size=40")
    assert resp.status_code == 200
    data = resp.json()
    assert "feature_x" in data and "grid_predictions" in data


def test_v2_viz_surface_max_grid_limit():
    resp = client.get("/api/v2/viz/surface?model_key=rf&grid_size=90")
    assert resp.status_code == 400


def test_v2_viz_pca():
    resp = client.get("/api/v2/viz/pca")
    assert resp.status_code == 200
    data = resp.json()
    assert "explained_variance_ratio" in data
    assert "background_points" in data


# ==============================================================================
# 6. LLM Verdicts & RBAC (Guard G12)
# ==============================================================================

def test_v2_llm_rbac_matrix_g12():
    """Guard G12: Role matrix validation on protected endpoints."""
    # Reviewer trying to access /llm/health -> 403 Forbidden
    app.dependency_overrides[get_current_user] = lambda: REVIEWER_USER
    resp = client.get("/api/v2/llm/health")
    assert resp.status_code == 403

    # Analyst accessing /llm/health -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: ANALYST_USER
    resp = client.get("/api/v2/llm/health")
    assert resp.status_code == 200

    # Analyst trying to update /llm/config -> 403 Forbidden (Admin only)
    resp = client.put("/api/v2/llm/config", json={"provider": "ollama"})
    assert resp.status_code == 403

    # Admin updating /llm/config -> 200 OK
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    resp = client.put("/api/v2/llm/config", json={"provider": "ollama"})
    assert resp.status_code == 200


def test_v2_llm_config_ssrf_rejection():
    """Guard G10 integration: Public IP in LLM URL must be rejected."""
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    resp = client.put("/api/v2/llm/config", json={"base_url": "http://169.254.169.254/metadata"})
    assert resp.status_code == 400
    assert "SSRF" in resp.json()["title"]


def test_v2_llm_verdict_template_fallback():
    """Verifies template fallback activates cleanly when offline with allow_fallback=True."""
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    resp = client.post("/api/v2/llm/verdict", json={"mode": "verdict", "audience": "HR", "allow_fallback": True})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_fallback"] is True
    assert "Random forest" in data["verdict"]["headline"]
    assert data["verdict"]["recommendation"]["model_key"] == "rf"


def test_v2_llm_verdict_503_when_no_fallback():
    """Verifies 503 Problem Details when offline and allow_fallback=False."""
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    resp = client.post("/api/v2/llm/verdict", json={"mode": "verdict", "audience": "HR", "allow_fallback": False})
    assert resp.status_code == 503
    err = resp.json()
    assert err["title"] == "LLM Service Unavailable"
    assert "allow_fallback=true" in err["detail"]


def test_v2_llm_privacy_leakage_rejection_g9():
    """Guard G9: Evidence with employee identifiers must be rejected with 400."""
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    bad_evidence = {
        "facts": ["Employee EMP001 had salary 95000"],
        "employee_id": "EMP001",
    }
    resp = client.post("/api/v2/llm/verdict", json={"evidence_packet": bad_evidence})
    assert resp.status_code == 400
    assert "Privacy Guard Violation" in resp.json()["title"]
