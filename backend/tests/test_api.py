import io

import pandas as pd
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

import importlib

from backend.core.security import (
    get_current_user,
    get_current_user_email,
    oauth2_scheme,
)
from backend.db.models import User

main_module = importlib.import_module("app.main")
admin_user = User(id=1, email="admin@test.com", role="admin")
app.dependency_overrides[oauth2_scheme] = lambda: "mock-token"
app.dependency_overrides[get_current_user_email] = lambda: "admin@test.com"
app.dependency_overrides[get_current_user] = lambda: admin_user


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "api_version" in response.json()


def test_predict_validation():
    # Missing required fields
    response = client.post("/predict", json={"attendance": 100})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

    # Out of range
    response = client.post(
        "/predict",
        json={
            "attendance": 105,  # ge 0, le 100
            "experience_years": 5.0,
            "training_hours": 100,
            "projects_completed": 5,
            "weekly_hours": 40,
            "prev_score": 3,
            "department": "Sales",
            "job_level": "Junior",
        },
    )
    assert response.status_code == 422


from pathlib import Path

GOLDEN_CSV = (
    Path(__file__).resolve().parent.parent.parent
    / "artifacts"
    / "v1"
    / "golden_tests.csv"
)


def test_predict_equals_pipeline():
    import pandas as pd

    if GOLDEN_CSV.exists():
        golden = pd.read_csv(GOLDEN_CSV)
        row = {
            k: (None if pd.isna(v) else v) for k, v in golden.iloc[0].to_dict().items()
        }
        row.pop("expected_label", None)
        row.pop("employee_id", None)
    else:
        row = {
            "attendance": 90.0,
            "experience_years": 5.0,
            "training_hours": 100.0,
            "projects_completed": 5.0,
            "weekly_hours": 40.0,
            "prev_score": 3.0,
            "department": "Sales",
            "job_level": "Junior",
        }
    response = client.post("/predict", json=row)
    assert response.status_code == 200
    assert response.json()["prediction"]


def test_explain_contract():
    row = {
        "attendance": 90,
        "experience_years": 5.0,
        "training_hours": 100,
        "projects_completed": 5,
        "weekly_hours": 40,
        "prev_score": 3,
        "department": "Sales",
        "job_level": "Junior",
    }
    response = client.post("/explain?k=5", json=row)
    assert response.status_code == 200
    data = response.json()
    assert len(data["neighbors"]) <= 5
    assert sum(data["votes"].values()) > 0.99
    assert "summary" in data


def test_batch_upload():
    csv_content = """attendance,experience_years,training_hours,projects_completed,weekly_hours,prev_score,department,job_level
90,5.0,100,5,40,3,Sales,Junior
"""
    response = client.post(
        "/batch",
        files={
            "file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
        },
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1


def test_upload_abuse():
    bad_csv = "=CMD(),1,2,3\n"
    response = client.post(
        "/batch",
        files={"file": ("test.csv", io.BytesIO(bad_csv.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 400


def test_cors():
    response = client.options("/predict", headers={"Origin": "http://evil.com"})
    assert "access-control-allow-origin" not in response.headers

    response = client.options("/predict", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_rate_limit(monkeypatch):
    """Exercise the limiter without spending minutes in explainability code."""

    monkeypatch.setattr(
        main_module,
        "explain",
        lambda *_args: (
            pd.DataFrame([{"performance": "Medium"}]),
            {"Low": 0.2, "Medium": 0.5, "High": 0.3},
        ),
    )
    monkeypatch.setattr(main_module, "local_attribution", lambda *_args: {})
    monkeypatch.setattr(main_module, "counterfactual", lambda *_args: [])
    monkeypatch.setattr(main_module, "summarise", lambda *_args: "ok")

    response = None
    for _ in range(21):
        response = client.post(
            "/explain?k=5",
            json={
                "attendance": 90,
                "experience_years": 5.0,
                "training_hours": 100,
                "projects_completed": 5,
                "weekly_hours": 40,
                "prev_score": 3,
                "department": "Sales",
                "job_level": "Junior",
            },
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
    assert response is not None
    assert response.status_code == 429


def test_viz_surface():
    response = client.get("/viz/surface?size=80")
    assert response.status_code == 200
    grid = response.json()
    # The legacy grid is served from the governed v2 artifact bundle, not stubbed.
    assert grid["grid_size"] == 40
    assert len(grid["grid_predictions"]) == 40
    assert len(grid["prob_high_surface"]) == 40
    response = client.get("/viz/surface?size=81")
    assert response.status_code == 400


def test_legacy_analytics_summary():
    response = client.get("/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"] == "Balanced"
    assert data["champion"] in {row["key"] for row in data["models"]}
    assert len(data["models"]) == 7
    assert all(row["macro_f1"] is not None for row in data["models"])
