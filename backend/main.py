import logging
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user_email,
    get_password_hash,
    verify_password,
)
from backend.db import models
from backend.db.database import engine, get_db
from backend.schemas import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

# Create tables
models.Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Employee Performance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:80",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DummyModelBundle:
    def __init__(self):
        self.meta = {"version": "v1.0 (KNN Tuned)", "review_threshold": 0.6}
        # In a real app we load pipeline.joblib here


bundle = DummyModelBundle()


@app.on_event("startup")
def create_default_user():
    db = next(get_db())
    admin = db.query(models.User).filter(models.User.email == "admin@hr.local").first()
    if not admin:
        new_user = models.User(
            email="admin@hr.local",
            hashed_password=get_password_hash("admin123"),
            role="admin",
        )
        db.add(new_user)
        db.commit()


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}


@app.post("/api/v1/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/analytics/drift")
def get_drift(
    db: Session = Depends(get_db), current_user: str = Depends(get_current_user_email)
):
    from backend.services.drift import get_current_drift

    history = (
        db.query(models.PredictionHistory)
        .order_by(models.PredictionHistory.id.desc())
        .limit(100)
        .all()
    )
    # Mocking train_stats
    return get_current_drift(history, train_stats={})


@app.post("/api/v1/predict")
def predict(
    emp: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user_email),
):
    # Dummy logic to mimic the ML model
    pred_class = "High"
    if emp.prev_score < 3:
        pred_class = "Low"
    elif emp.attendance < 80:
        pred_class = "Medium"

    out = PredictionResponse(
        prediction=pred_class,
        confidence=0.85,
        summary=f"Prediction is {pred_class} based on input factors.",
        votes={pred_class: 4, "Other": 1},
        attribution={"experience_years": 0.2},
        neighbours=[
            {
                "employee_id": 123,
                "department": emp.department,
                "job_level": emp.job_level,
                "class": pred_class,
            }
        ],
        counterfactual_path=[],
        is_flagged=False,
    )

    # Save to history
    history = models.PredictionHistory(
        user_email=current_user,
        input_data=emp.model_dump_json(),
        prediction=out.prediction,
        confidence=out.confidence,
        needs_review=1 if out.is_flagged else 0,
    )
    db.add(history)
    db.commit()

    return out.model_dump()
