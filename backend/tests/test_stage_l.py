"""Verification and Negative Access Tests for Stage L (Secure App and MLOps).

Tests:
- L1: 17 Table Database Migrations & Initial Seed
- L2: Comprehensive RBAC Matrix & Negative Access Checks
- L3: Uncertainty Review Queue, Mandatory Override Reasons & Transparency Appeals
- L4: Governed Retrain Pipeline, Champion Approval & One-Click Rollback
- L5: Per-Model PSI/KS Drift Monitoring & Feature Flag Administration
- L6: PDF Report Streaming for Employees and Multi-Model Arena Comparison
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from backend.app.main import app
from backend.core.security import get_current_user, get_current_user_email
from backend.db.database import SessionLocal, engine
from backend.db.migrate import run_migrations
from backend.db.models import AuditLog, Employee, ModelVersion, Prediction, ReviewItem, User

client = TestClient(app)

@pytest.fixture(autouse=True, scope="session")
def setup_database_session():
    """Ensure database schema and standard roles are seeded."""
    run_migrations()

ADMIN_USER = User(id=1, email="admin@test.com", role="admin")
HR_USER = User(id=2, email="hrmanager@test.com", role="hr_manager")
ANALYST_USER = User(id=3, email="analyst@test.com", role="analyst")
VIEWER_USER = User(id=4, email="viewer@test.com", role="viewer")

SAMPLE_FEATURES = {
    "attendance": 92.0,
    "experience_years": 4.0,
    "training_hours": 35.0,
    "projects_completed": 6.0,
    "weekly_hours": 40.0,
    "prev_score": 3.8,
    "department": "Engineering",
    "job_level": "Mid",
    "peer_feedback": 3.9,
    "tasks_on_time_pct": 85.0,
    "certifications": 2.0,
}


@pytest.fixture(autouse=True)
def default_auth():
    """Default to Admin for general tests unless explicitly overridden."""
    app.dependency_overrides[get_current_user_email] = lambda: "admin@test.com"
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    yield
    app.dependency_overrides.clear()


# ==============================================================================
# L1: Database Migrations & Models
# ==============================================================================

def test_l1_all_tables_exist():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected_tables = {
        "users",
        "employees",
        "protected_attributes",
        "snapshots",
        "predictions",
        "review_items",
        "review_decisions",
        "batch_jobs",
        "model_versions",
        "comparison_runs",
        "llm_verdicts",
        "drift_reports",
        "fairness_reports",
        "api_keys",
        "audit_logs",
        "consent_records",
        "deletion_requests",
    }
    for t in expected_tables:
        assert t in tables, f"Expected table '{t}' missing from database"


def test_l1_seed_data_present():
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        assert user_count >= 4, "Expected seeded users (admin, hr_manager, analyst, viewer)"
        version_count = db.query(ModelVersion).count()
        assert version_count >= 7, "Expected at least 7 seeded model versions"
    finally:
        db.close()


# ==============================================================================
# L2: RBAC Matrix & Negative Access Checks
# ==============================================================================

def test_l2_rbac_viewer_denied_admin_audit():
    app.dependency_overrides[get_current_user] = lambda: VIEWER_USER
    resp = client.get("/api/v2/audit/logs")
    assert resp.status_code == 403, f"Expected 403 for Viewer on audit logs, got {resp.status_code}"


def test_l2_rbac_analyst_denied_transparency():
    app.dependency_overrides[get_current_user] = lambda: ANALYST_USER
    resp = client.get("/api/v2/transparency/employee/EMP-001")
    assert resp.status_code == 403, f"Expected 403 for Analyst on employee transparency, got {resp.status_code}"


def test_l2_rbac_analyst_denied_retrain():
    app.dependency_overrides[get_current_user] = lambda: ANALYST_USER
    resp = client.post("/api/v2/retrain", json={"profile": "fast"})
    assert resp.status_code == 403, f"Expected 403 for Analyst on retrain, got {resp.status_code}"


def test_l2_rbac_hr_denied_approve_champion():
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    resp = client.post("/api/v2/models/approve-champion", json={"champion_key": "boost", "version": "v2.0"})
    assert resp.status_code == 403, f"Expected 403 for HR on approve-champion, got {resp.status_code}"


def test_l2_rbac_admin_allowed_audit():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    resp = client.get("/api/v2/audit/logs")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ==============================================================================
# L3: Review Workflow, Transparency & Appeals
# ==============================================================================

def test_l3_review_queue_and_mandatory_override_reason():
    import uuid
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    pred_id = f"test-pred-{uuid.uuid4()}"
    item_id = f"test-rev-{uuid.uuid4()}"
    db = SessionLocal()
    try:
        # Create an artificial low-stability prediction
        pred = Prediction(
            id=pred_id,
            user_email="hr@test.com",
            model_key="rf",
            predicted_band=1,  # Medium
            probabilities_json=json.dumps({"Low": 0.1, "Medium": 0.5, "High": 0.4}),
            confidence=0.50,
            stability_score=45.0,  # Below 70 threshold!
            conformal_set_json=json.dumps(["Medium", "High"]),
            is_split_decision=1,
            is_shadow=0,
            input_data=json.dumps(SAMPLE_FEATURES),
        )
        db.add(pred)
        item = ReviewItem(
            id=item_id,
            prediction_id=pred.id,
            employee_id="EMP-999",
            status="pending",
            urgency="high",
            flags_json=json.dumps(["low_stability", "split_decision"]),
        )
        db.add(item)
        db.commit()
    finally:
        db.close()

    # 1. Fetch queue as HR Manager
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    queue_resp = client.get("/api/v2/review/queue?status_filter=pending")
    assert queue_resp.status_code == 200
    items = queue_resp.json()
    assert any(i["id"] == item_id for i in items)

    # 2. Overturn model band (predicted 1, decide 2) WITHOUT override_reason -> 422
    fail_resp = client.post(
        f"/api/v2/review/{item_id}/decision",
        json={"decision_band": 2, "override_reason": ""},
    )
    assert fail_resp.status_code == 422
    assert "Override Reason Mandatory" in fail_resp.json().get("title", "")

    # 3. Overturn WITH mandatory override_reason -> 200 Success
    success_resp = client.post(
        f"/api/v2/review/{item_id}/decision",
        json={
            "decision_band": 2,
            "override_reason": "High business impact projects completed outside measurement cycle",
            "comments": "Reviewed with engineering department lead",
        },
    )
    assert success_resp.status_code == 200
    assert success_resp.json()["status"] == "success"

    # 4. Check review analytics
    analytics_resp = client.get("/api/v2/review/analytics")
    assert analytics_resp.status_code == 200
    data = analytics_resp.json()
    assert data["total_reviewed"] >= 1
    assert data["overturn_count"] >= 1


def test_l3_employee_transparency_and_appeal():
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    # Transparency endpoint
    t_resp = client.get("/api/v2/transparency/employee/EMP-999")
    assert t_resp.status_code == 200
    data = t_resp.json()
    assert data["employee_id"] == "EMP-999"
    assert "TalentScope Ethics Charter" in data["notice"]

    # Submit employee appeal
    appeal_resp = client.post(
        "/api/v2/transparency/appeal",
        json={
            "employee_id": "EMP-999",
            "reason": "Recent performance review misaligned with external patent delivery",
            "supporting_info": "Patent filed US-2026-0988",
        },
    )
    assert appeal_resp.status_code == 200
    assert appeal_resp.json()["status"] == "success"


def test_l3_privacy_deletion_request():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    del_resp = client.post(
        "/api/v2/privacy/delete-request",
        json={"employee_id": "EMP-999", "reason": "GDPR right to erasure statutory request"},
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "success"


# ==============================================================================
# L4: Governed Retrain Pipeline & Champion Lifecycle
# ==============================================================================

def test_l4_retrain_and_champion_lifecycle():
    champ_path = Path("artifacts/v2/champion.json")
    manifest_path = Path("artifacts/v2/MANIFEST.json")
    orig_champ = champ_path.read_bytes() if champ_path.exists() else None
    orig_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
    try:
        app.dependency_overrides[get_current_user] = lambda: ADMIN_USER

        # 1. Trigger retrain candidate evaluation
        retrain_resp = client.post("/api/v2/retrain", json={"profile": "fast"})
        assert retrain_resp.status_code == 200
        r_data = retrain_resp.json()
        assert r_data["status"] == "candidate_ready"
        assert r_data["requires_admin_approval"] is True

        # 2. Approve champion
        approve_resp = client.post(
            "/api/v2/models/approve-champion",
            json={"champion_key": "svm", "version": "v2.1"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["champion"] == "svm"

        # 3. Rollback champion to baseline
        rollback_resp = client.post("/api/v2/models/rollback")
        assert rollback_resp.status_code == 200
        assert rollback_resp.json()["active_champion"] == "boost"

        # 4. List model versions
        versions_resp = client.get("/api/v2/models/versions")
        assert versions_resp.status_code == 200
        v_list = versions_resp.json()
        assert len(v_list) >= 7
    finally:
        if orig_champ is not None:
            champ_path.write_bytes(orig_champ)
        if orig_manifest is not None:
            manifest_path.write_bytes(orig_manifest)
        from backend.app.api_v2 import default_loader
        if hasattr(default_loader, "reset_cache"):
            default_loader.reset_cache()
        else:
            default_loader._manifest = None


# ==============================================================================
# L5: Drift Monitoring & Feature Flags
# ==============================================================================

def test_l5_drift_monitoring_status():
    app.dependency_overrides[get_current_user] = lambda: ANALYST_USER
    resp = client.get("/api/v2/drift/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_psi" in data
    assert "status" in data
    assert "features" in data
    assert "attendance" in data["features"]


def test_l5_feature_flags_get_and_update():
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    get_resp = client.get("/api/v2/admin/feature-flags")
    assert get_resp.status_code == 200
    flags = get_resp.json()
    assert "shadow_mode_enabled" in flags

    # Admin update
    update_resp = client.post(
        "/api/v2/admin/feature-flags",
        json={"flags": {"shadow_mode_enabled": True, "uncertainty_queue_enabled": True}},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["shadow_mode_enabled"] is True


# ==============================================================================
# L6: PDF Reports Streaming
# ==============================================================================

def test_l6_employee_report_pdf():
    app.dependency_overrides[get_current_user] = lambda: HR_USER
    resp = client.get("/api/v2/reports/employee/EMP-1001/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert len(resp.content) > 1000


def test_l6_comparison_report_pdf():
    app.dependency_overrides[get_current_user] = lambda: VIEWER_USER
    resp = client.get("/api/v2/reports/comparison/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
    assert len(resp.content) > 1000
