"""Regression tests for findings F-04 to F-07 and the Default-Deny OpenAPI guard."""

import json
from pathlib import Path

import pytest
from epk.artifacts import default_loader
from fastapi.testclient import TestClient

from backend.app.api_v2 import update_champion_file
from backend.app.config import settings
from backend.app.main import app, create_app
from backend.core.security import create_access_token

client = TestClient(app)


def test_f04_models_endpoint_rbac_regression():
    """F-04 Regression: GET /api/v2/models must deny anonymous requests and require valid auth."""
    # 1. Anonymous request without token must be rejected with 401
    resp_anon = client.get("/api/v2/models")
    assert (
        resp_anon.status_code == 401
    ), f"Expected 401 Unauthorized for anonymous request, got {resp_anon.status_code}"

    # 2. Authenticated request with valid token must succeed
    token = create_access_token({"sub": "viewer@test.com", "role": "viewer"})
    resp_auth = client.get(
        "/api/v2/models", headers={"Authorization": f"Bearer {token}"}
    )
    assert (
        resp_auth.status_code == 200
    ), f"Expected 200 OK for authenticated viewer, got {resp_auth.status_code}"
    models = resp_auth.json()
    assert len(models) == 7
    keys = {m["key"] for m in models}
    assert keys == {"boost", "dt", "knn", "linreg", "logreg", "rf", "svm"}


def test_f05_champion_update_property_regression():
    """F-05 Regression: update_champion_file must not fail with AttributeError on default_loader.manifest."""
    champ_path = default_loader.root_dir / "champion.json"
    manifest_path = default_loader.root_dir / "MANIFEST.json"
    orig_champ = champ_path.read_bytes() if champ_path.exists() else None
    orig_manifest = manifest_path.read_bytes() if manifest_path.exists() else None

    champion_payload = {
        "champion_key": "boost",
        "champion": "boost",
        "rule": "MCDA Balanced Profile score >= 0.60 with paired bootstrap validation",
        "score": 0.6665,
        "selection_timestamp": "2026-10-12T00:00:00Z",
    }
    try:
        # Must succeed without AttributeError: can't set attribute 'manifest'
        update_champion_file(champion_payload)
        assert default_loader._manifest is not None
        assert default_loader.manifest is not None
    finally:
        if orig_champ is not None:
            champ_path.write_bytes(orig_champ)
        if orig_manifest is not None:
            manifest_path.write_bytes(orig_manifest)
        if hasattr(default_loader, "reset_cache"):
            default_loader.reset_cache()


def test_f07_champion_approval_keeps_champion_key_and_provenance():
    """F-07 Regression: approving a champion must keep `champion_key` and provenance.

    `approve_champion` used to overwrite champion.json with a payload that only had
    the `champion` key, so every consumer that reads `champion_key` (model list,
    predict-all, batch defaults, PDF reports) silently fell back to `rf`.
    """
    champ_path = default_loader.root_dir / "champion.json"
    manifest_path = default_loader.root_dir / "MANIFEST.json"
    orig_champ = champ_path.read_bytes()
    orig_manifest = manifest_path.read_bytes()
    token = create_access_token({"sub": "admin@test.com", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.post(
            "/api/v2/models/approve-champion",
            json={"champion_key": "svm", "version": "v2.9"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

        written = json.loads(champ_path.read_text(encoding="utf-8"))
        assert written["champion_key"] == "svm"
        assert written["champion"] == "svm"
        assert written["champion_label"] == "Support vector machine (RBF)"
        # Provenance fields from the artifact bundle survive the promotion.
        assert written["score"] == pytest.approx(0.6665)
        assert written["selection_rule"]
        assert written["approved_by"] == "admin@test.com"

        # Consumers must agree with the freshly approved champion.
        models = client.get("/api/v2/models", headers=headers).json()
        assert [m["key"] for m in models if m["is_champion"]] == ["svm"]
    finally:
        champ_path.write_bytes(orig_champ)
        manifest_path.write_bytes(orig_manifest)
        if hasattr(default_loader, "reset_cache"):
            default_loader.reset_cache()
        else:
            default_loader._manifest = None
            default_loader._loaded_champion = None


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
    resp = client.post(
        "/predict", json=sample_features, headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "prediction" in resp.json()


def test_legacy_v1_disabled_reports_governed_v2_runtime(monkeypatch):
    """The default startup path must skip V1 artifacts and expose the V2 source."""
    monkeypatch.setattr(settings, "enable_legacy_v1", False)
    test_app = create_app()
    test_client = TestClient(test_app)

    version = test_client.get("/version")
    assert version.status_code == 200
    assert version.json()["model_version"].startswith("v2.0")

    ready = test_client.get("/ready")
    assert ready.status_code == 200
    ready_payload = ready.json()
    assert ready_payload["model"] == "available"
    assert ready_payload["model_source"] == "governed-v2"


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

    assert (
        not violations
    ), f"Default-deny violation! The following routes do not require auth and are not in PUBLIC_ALLOWLIST: {violations}"
