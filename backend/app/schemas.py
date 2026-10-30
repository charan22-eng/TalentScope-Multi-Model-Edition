from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EmployeeFeatures(BaseModel):
    attendance: float = Field(..., ge=0.0, le=100.0)
    experience_years: float = Field(..., ge=0.0, le=50.0)
    training_hours: float = Field(..., ge=0.0, le=1000.0)
    projects_completed: float = Field(..., ge=0.0, le=100.0)
    weekly_hours: float = Field(..., ge=0.0, le=168.0)
    prev_score: float | None = Field(None, ge=1.0, le=5.0)
    department: str
    job_level: str
    peer_feedback: float | None = Field(3.5, ge=1.0, le=5.0)
    tasks_on_time_pct: float | None = Field(80.0, ge=0.0, le=100.0)
    certifications: float | None = Field(1.0, ge=0.0, le=20.0)

    model_config = ConfigDict(extra="forbid")


class PredictResponse(BaseModel):
    prediction: list[str]
    confidence: float
    probabilities: dict[str, float]
    stability_index: float


class ExplainResponse(BaseModel):
    prediction: list[str]
    confidence: float
    neighbors: list[dict[str, Any]]
    votes: dict[str, float]
    summary: str
    attribution: dict[str, float]
    counterfactual_path: list[str]


class BatchPredictResponse(BaseModel):
    results: list[PredictResponse | None]
    errors: list[dict[str, Any] | None]
    latency_ms: float


# --- v2 Schemas ---


class V2PredictRequest(BaseModel):
    model_key: str | None = "rf"
    features: EmployeeFeatures


class V2PredictResponse(BaseModel):
    model_key: str
    predicted_band: str
    confidence: float
    prediction_set: list[str]
    probabilities: dict[str, float]
    stability_score: float
    performance_index: float


class V2PredictAllResponse(BaseModel):
    predictions: dict[str, V2PredictResponse]
    consensus_band: str
    agreement_rate: float
    split_decision: bool
    champion_key: str
    champion_prediction: V2PredictResponse
    latency_ms: float


class V2ExplainRequest(BaseModel):
    model_key: str | None = "rf"
    features: EmployeeFeatures
    k: int | None = 5


class V2ExplainResponse(BaseModel):
    model_key: str
    label: str
    explanation_type: str
    predicted_band: str
    native_explanation: dict[str, Any]
    local_attribution: dict[str, float]
    counterfactuals: list[dict[str, Any]]
    similar_cases: dict[str, Any]
    persona_summaries: dict[str, str]
    key_drivers: list[str] | None = None
    actionable_guidance: str | None = None
    llm_metadata: dict[str, Any] | None = None


class V2MCDARequest(BaseModel):
    weights: dict[str, float]
    profile: str | None = "Custom"


class V2LLMVerdictRequest(BaseModel):
    mode: str | None = "verdict"
    profile: str | None = "Balanced"
    audience: str | None = "HR"
    allow_fallback: bool | None = True
    evidence_packet: dict[str, Any] | None = None


class V2LLMConfigUpdateRequest(BaseModel):
    provider: str | None = None
    model: str | None = None
    base_url: str | None = None


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: Any
    instance: str | None = None


class V2ReviewDecisionRequest(BaseModel):
    decision_band: int = Field(..., ge=0, le=2)
    override_reason: str | None = None
    comments: str | None = None


class V2AppealRequest(BaseModel):
    employee_id: str
    reason: str
    supporting_info: str | None = None


class V2ConsentRequest(BaseModel):
    employee_id: str
    consent_type: str = "automated_decision_support"
    granted: bool = True


class V2DeleteRequest(BaseModel):
    employee_id: str
    reason: str | None = None


class V2RetrainRequest(BaseModel):
    profile: str | None = "fast"


class V2ApproveChampionRequest(BaseModel):
    champion_key: str
    version: str | None = "v2.0"


class V2FeatureFlagsUpdateRequest(BaseModel):
    flags: dict[str, bool]
