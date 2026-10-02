import pytest
from fastapi.testclient import TestClient

from backend.core.security import get_password_hash
from backend.db.database import Base, SessionLocal, engine
from backend.db.models import User
from backend.main import app

# Setup test DB
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    db = SessionLocal()
    if not db.query(User).filter(User.email == "admin@hr.local").first():
        new_user = User(
            email="admin@hr.local",
            hashed_password=get_password_hash("admin123"),
            role="admin",
        )
        db.add(new_user)
        db.commit()
    db.close()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_success():
    # 1. Login
    login_res = client.post(
        "/api/v1/login", data={"username": "admin@hr.local", "password": "admin123"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # 2. Predict
    payload = {
        "attendance": 95,
        "experience_years": 5,
        "training_hours": 100,
        "projects_completed": 10,
        "weekly_hours": 40,
        "prev_score": 4,
        "department": "Engineering",
        "job_level": "Mid",
    }

    response = client.post(
        "/api/v1/predict", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "prediction" in data


def test_predict_unauthorized():
    payload = {
        "attendance": 95,
        "experience_years": 5,
        "training_hours": 100,
        "projects_completed": 10,
        "weekly_hours": 40,
        "prev_score": 4,
        "department": "Engineering",
        "job_level": "Mid",
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 401
