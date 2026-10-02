from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class EmployeeFeatures(BaseModel):
    attendance: int = Field(..., ge=0, le=100)
    experience_years: float = Field(..., ge=0.0, le=50.0)
    training_hours: int = Field(..., ge=0, le=1000)
    projects_completed: int = Field(..., ge=0, le=100)
    weekly_hours: int = Field(..., ge=0, le=168)
    prev_score: int = Field(..., ge=1, le=5)
    department: str
    job_level: str
    
    model_config = ConfigDict(extra='forbid')

class PredictResponse(BaseModel):
    prediction: List[str]
    confidence: float
    probabilities: Dict[str, float]
    stability_index: float

class ExplainResponse(BaseModel):
    prediction: List[str]
    confidence: float
    neighbors: List[Dict[str, Any]]
    votes: Dict[str, float]
    summary: str
    attribution: Dict[str, float]
    counterfactual_path: List[str]

class BatchPredictResponse(BaseModel):
    results: List[Optional[PredictResponse]]
    errors: List[Optional[Dict[str, Any]]]
    latency_ms: float
