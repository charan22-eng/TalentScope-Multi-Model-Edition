"""Regression tests for findings F-04, F-05, F-06 and the Default-Deny OpenAPI guard."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, create_app
from backend.core.security import create_access_token
from backend.app.api_v2 import update_champion_file
from epk.artifacts import default_loader


client = TestClient(app)


def test_f04_models_endpoint_rbac_regression():
    """F-04 Regression: GET /api/v2/models must deny anonymous requests and require valid auth."""
    # 1. Anonymous request without token must be rejected with 401
    resp_anon = client.get("/api/v2/models")
    assert resp_anon.status_code == 401, f"Expected 401 Unauthorized for anonymous request, got {resp_anon.status_code}"

    # 2. Authenticated request with valid token must succeed
    token = create_access_token({"sub": "viewer@test.com", "role": "viewer"})
    resp_auth = client.get("/api/v2/models", headers={"Authorization": f"Bearer {token}"})
    assert resp_auth.status_code == 200, f"Expected 200 OK for authenticated viewer, got {resp_auth.status_code}"
    models = resp_auth.json()
    assert len(models) == 7
    keys = {m["key"] for m in models}
    assert keys == {"boost", "dt", "knn", "linreg", "logreg", "rf", "svm"}


def test_f05_champion_update_property_regression():
    """F-05 Regression: update_champion_file must not fail with AttributeError on default_loader.manifest."""
    champion_payload = {
        "champion_key": "rf",
        "rule": "MCDA Balanced Profile score >= 0.60 with paired bootstrap validation",
        "score": 0.6387,
        "selection_timestamp": "2026-10-12T00:00:00Z",
    }
    # Must succeed without AttributeError: can't set attribute 'manifest'
    update_champion_file(champion_payload)
    assert default_loader._manifest is not None
    assert default_loader.manifest is not None


def test_f06_main_fallback_and_path_import_regression():
    """F-06 Regression: create_app() and test_api fallback must not fail on missing Path or golden_tests.csv."""
    # Instantiating the app must succeed cleanly even if v1 artifacts are absent
    test_app = create_app()
    assert test_app is not None

    # Verify predict fallback works
    sample_features = {
        "attendance": 90.0,
        "experience_years": 5.0,
        "training_hours": 100.0,
        "projects_completed": 5.0,
        "weekly_hours": 40.0,
        "prev_score": 3.0,
        "department": "Sales",
        "job_level": "Junior",
    }
    token = create_access_token({"sub": "admin@test.com", "role": "admin"})
    resp = client.post("/predict", json=sample_features, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "prediction" in resp.json()


def test_default_deny_openapi_guard():
    """Default-Deny Guard: every route in openapi.json must either require authentication or be on PUBLIC_ALLOWLIST."""
    openapi_file = Path("backend/openapi.json")
    assert openapi_file.exists(), "backend/openapi.json must exist"

    spec = json.loads(openapi_file.read_text(encoding="utf-8"))
    public_allowlist = {
        ("GET", "/health"),
        ("GET", "/ready"),
        ("GET", "/version"),
        ("POST", "/login"),
        ("GET", "/analytics/drift"),
        ("POST", "/explain"),
        ("POST", "/batch"),
        ("GET", "/batch/report/pdf"),
        ("GET", "/viz/galaxy"),
        ("GET", "/viz/surface"),
        ("GET", "/analytics"),
        ("GET", "/analytics/constellation"),
        ("GET", "/drift/projection"),
        ("POST", "/api/v2/predict/all"),
        ("POST", "/api/v2/explain"),
        ("GET", "/api/v2/compare/{topic}"),
        ("POST", "/api/v2/compare/mcda"),
        ("POST", "/api/v2/viz/surface"),
        ("GET", "/api/v2/viz/surface"),
        ("GET", "/api/v2/viz/pca"),
    }

    violations = []
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method.lower() in ("parameters", "$ref"):
                continue
            has_auth = len(details.get("security", [])) > 0
            is_allowlisted = (method.upper(), path) in public_allowlist
            if not has_auth and not is_allowlisted:
                violations.append(f"{method.upper()} {path}")

    assert not violations, f"Default-deny violation! The following routes do not require auth and are not in PUBLIC_ALLOWLIST: {violations}"
