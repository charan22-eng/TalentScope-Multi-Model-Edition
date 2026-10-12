from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class EmployeeFeatures(BaseModel):
    attendance: float = Field(..., ge=0.0, le=100.0)
    experience_years: float = Field(..., ge=0.0, le=50.0)
    training_hours: float = Field(..., ge=0.0, le=1000.0)
    projects_completed: float = Field(..., ge=0.0, le=100.0)
    weekly_hours: float = Field(..., ge=0.0, le=168.0)
    prev_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    department: str
    job_level: str
    peer_feedback: Optional[float] = Field(3.5, ge=1.0, le=5.0)
    tasks_on_time_pct: Optional[float] = Field(80.0, ge=0.0, le=100.0)
    certifications: Optional[float] = Field(1.0, ge=0.0, le=20.0)
    
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


# --- v2 Schemas ---

class V2PredictRequest(BaseModel):
    model_key: Optional[str] = "rf"
    features: EmployeeFeatures


class V2PredictResponse(BaseModel):
    model_key: str
    predicted_band: str
    confidence: float
    prediction_set: List[str]
    probabilities: Dict[str, float]
    stability_score: float
    performance_index: float


class V2PredictAllResponse(BaseModel):
    predictions: Dict[str, V2PredictResponse]
    consensus_band: str
    agreement_rate: float
    split_decision: bool
    champion_key: str
    champion_prediction: V2PredictResponse
    latency_ms: float


class V2ExplainRequest(BaseModel):
    model_key: Optional[str] = "rf"
    features: EmployeeFeatures
    k: Optional[int] = 5


class V2ExplainResponse(BaseModel):
    model_key: str
    label: str
    explanation_type: str
    predicted_band: str
    native_explanation: Dict[str, Any]
    local_attribution: Dict[str, float]
    counterfactuals: List[Dict[str, Any]]
    similar_cases: Dict[str, Any]
    persona_summaries: Dict[str, str]


class V2MCDARequest(BaseModel):
    weights: Dict[str, float]


class V2LLMVerdictRequest(BaseModel):
    mode: Optional[str] = "verdict"
    audience: Optional[str] = "HR"
    allow_fallback: Optional[bool] = True
    evidence_packet: Optional[Dict[str, Any]] = None


class V2LLMConfigUpdateRequest(BaseModel):
    provider: Optional[str] = "ollama"
    model: Optional[str] = "qwen2.5:7b-instruct"
    base_url: Optional[str] = "http://localhost:11434"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Any
    instance: Optional[str] = None


class V2ReviewDecisionRequest(BaseModel):
    decision_band: int = Field(..., ge=0, le=2)
    override_reason: Optional[str] = None
    comments: Optional[str] = None


class V2AppealRequest(BaseModel):
    employee_id: str
    reason: str
    supporting_info: Optional[str] = None


class V2ConsentRequest(BaseModel):
    employee_id: str
    consent_type: str = "automated_decision_support"
    granted: bool = True


class V2DeleteRequest(BaseModel):
    employee_id: str
    reason: Optional[str] = None


class V2RetrainRequest(BaseModel):
    profile: Optional[str] = "fast"


class V2ApproveChampionRequest(BaseModel):
    champion_key: str
    version: Optional[str] = "v2.0"


class V2FeatureFlagsUpdateRequest(BaseModel):
    flags: Dict[str, bool]

