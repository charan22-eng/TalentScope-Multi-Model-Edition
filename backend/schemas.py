from typing import Any

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    attendance: float = Field(..., ge=0, le=100)
    experience_years: float = Field(..., ge=0, le=50)
    training_hours: float = Field(..., ge=0, le=1000)
    projects_completed: int = Field(..., ge=0, le=500)
    weekly_hours: float = Field(..., ge=0, le=168)
    prev_score: float = Field(..., ge=1, le=5)
    department: str = Field(...)
    job_level: str = Field(...)

    # Audit only, handled optionally by front end
    gender: str | None = None
    age_band: str | None = None


class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    summary: str
    votes: dict[str, float]
    attribution: dict[str, float]
    neighbours: list[dict[str, Any]]
    counterfactual_path: list[str]
    is_flagged: bool
