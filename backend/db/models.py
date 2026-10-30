"""TalentScope Unified Database Models (Stage L1).

Supports SQLite (dev) and PostgreSQL (production/compose).
Covers all governed entities:
1. users
2. employees
3. protected_attributes
4. snapshots
5. predictions
6. review_items
7. review_decisions
8. batch_jobs
9. model_versions
10. comparison_runs
11. llm_verdicts
12. drift_reports
13. fairness_reports
14. api_keys
15. audit_logs
16. consent_records
17. deletion_requests
18. appeals
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from backend.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# 1. Users & Authentication
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    # Roles: admin, hr_manager, analyst, viewer, reviewer
    role = Column(String(50), default="viewer", nullable=False)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


# 2. Employees (Business operational store)
class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(64), primary_key=True, index=True)
    experience_years = Column(Float, nullable=False)
    engagement_score = Column(Float, nullable=False)
    peer_rating = Column(Float, nullable=False)
    projects_completed = Column(Integer, nullable=False)
    tenure_months = Column(Float, nullable=False)
    salary_band = Column(String(32), nullable=False)
    department = Column(String(64), nullable=False)
    education_level = Column(String(32), nullable=False)
    remote_ratio = Column(Float, nullable=False)
    promotion_history = Column(Integer, nullable=False)
    overtime_hours = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


# 3. Protected Attributes (Strictly isolated from feature store)
class ProtectedAttribute(Base):
    __tablename__ = "protected_attributes"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        String(64),
        ForeignKey("employees.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    gender = Column(String(32), nullable=False)
    age_band = Column(String(32), nullable=False)
    ethnicity = Column(String(64), nullable=True)
    disability_status = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


# 4. Dataset Snapshots
class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    dataset_version = Column(String(32), default="v2.0", nullable=False)
    row_count = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


# 5. Model Predictions & Shadow Mode
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(64), primary_key=True, index=True)  # UUID
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    employee_id = Column(String(64), index=True, nullable=True)
    user_email = Column(String(255), index=True, nullable=False)
    model_key = Column(String(32), index=True, nullable=False)
    predicted_band = Column(Integer, nullable=False)  # 0: Low, 1: Medium, 2: High
    predicted_score = Column(Float, nullable=True)
    probabilities_json = Column(Text, nullable=False)  # JSON [p0, p1, p2]
    confidence = Column(Float, nullable=False)
    stability_score = Column(Float, nullable=False)
    conformal_set_json = Column(Text, nullable=False)  # JSON list of bands
    is_split_decision = Column(Integer, default=0, nullable=False)
    is_shadow = Column(
        Integer, default=0, nullable=False
    )  # 1 if runner-up shadow inference
    input_data = Column(Text, nullable=False)  # JSON serialized features


# Legacy compatibility table alias
class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow)
    user_email = Column(String(255), index=True)
    input_data = Column(Text)
    prediction = Column(String(64))
    confidence = Column(Float)
    needs_review = Column(Integer, default=0)


# 6. Review Queue Items (Uncertainty-first workflow)
class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(String(64), primary_key=True, index=True)
    prediction_id = Column(
        String(64),
        ForeignKey("predictions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    employee_id = Column(String(64), index=True, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    # Status: pending, reviewed, appealed, closed
    status = Column(String(32), default="pending", index=True, nullable=False)
    urgency = Column(String(16), default="medium", nullable=False)  # high, medium, low
    flags_json = Column(
        Text, nullable=False
    )  # JSON: ["low_stability", "conformal_multi_band", "split_decision"]


# 7. Review Decisions
class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(64), primary_key=True, index=True)
    review_item_id = Column(
        String(64),
        ForeignKey("review_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reviewer_email = Column(String(255), index=True, nullable=False)
    decision_band = Column(Integer, nullable=False)
    override_reason = Column(
        Text, nullable=True
    )  # Mandatory if decision_band != predicted_band
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


# 8. Batch Jobs
class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(String(64), primary_key=True, index=True)
    user_email = Column(String(255), index=True, nullable=False)
    status = Column(
        String(32), default="queued", index=True, nullable=False
    )  # queued, running, completed, failed
    row_count = Column(Integer, default=0, nullable=False)
    disagreement_count = Column(Integer, default=0, nullable=False)
    result_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


# 9. Governed Model Versions
class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_key = Column(String(32), index=True, nullable=False)
    version = Column(String(32), nullable=False)
    is_champion = Column(Integer, default=0, nullable=False)
    status = Column(
        String(32), default="active", nullable=False
    )  # active, candidate, deprecated, rolled_back
    metrics_json = Column(Text, nullable=False)
    trained_at = Column(DateTime, default=utcnow, nullable=False)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)


# 10. Multi-Model Comparison Runs
class ComparisonRun(Base):
    __tablename__ = "comparison_runs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    created_by = Column(String(255), index=True, nullable=False)
    champion_key = Column(String(32), nullable=False)
    mcda_profile = Column(String(64), default="Balanced", nullable=False)
    decision_strength = Column(String(32), default="marginal", nullable=False)
    evidence_json = Column(Text, nullable=False)


# 11. LLM Verdicts & Explanations Cache
class LLMVerdict(Base):
    __tablename__ = "llm_verdicts"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    mode = Column(String(32), default="verdict", nullable=False)
    audience = Column(String(32), default="HR", nullable=False)
    prompt_hash = Column(String(64), index=True, nullable=True)
    verdict_json = Column(Text, nullable=False)
    is_valid = Column(Integer, default=1, nullable=False)
    is_fallback = Column(Integer, default=0, nullable=False)
    validation_json = Column(Text, nullable=False)


# 12. Drift Monitoring Reports
class DriftReport(Base):
    __tablename__ = "drift_reports"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    model_key = Column(String(32), index=True, nullable=False)
    dataset_name = Column(String(64), default="production_stream", nullable=False)
    sample_size = Column(Integer, nullable=False)
    psi_score = Column(Float, nullable=False)
    ks_pvalue = Column(Float, nullable=False)
    status = Column(
        String(32), nullable=False
    )  # stable, moderate_drift, significant_drift
    feature_drifts_json = Column(Text, nullable=False)


# 13. Fairness & Bias Reports
class FairnessReport(Base):
    __tablename__ = "fairness_reports"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow, nullable=False)
    model_key = Column(String(32), index=True, nullable=False)
    attribute_name = Column(String(64), nullable=False)  # gender, age_band
    disparate_impact_ratio = Column(Float, nullable=False)
    passes_four_fifths_rule = Column(Integer, nullable=False)
    demographic_parity_diff = Column(Float, nullable=False)
    details_json = Column(Text, nullable=False)


# 14. API Keys
class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String(64), primary_key=True, index=True)
    user_email = Column(String(255), index=True, nullable=False)
    key_hash = Column(String(128), index=True, nullable=False)
    name = Column(String(128), nullable=False)
    scopes_json = Column(Text, nullable=False)  # JSON ["predict", "arena:read"]
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


# 15. Append-only Audit Logs
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=utcnow, index=True, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    action = Column(
        String(64), index=True, nullable=False
    )  # predict, review_decision, model_approve, etc.
    resource = Column(String(128), nullable=False)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)


# 16. Employee Consent Records
class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(String(64), primary_key=True, index=True)
    employee_id = Column(String(64), index=True, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    consent_type = Column(
        String(64), nullable=False
    )  # automated_decision_support, data_processing
    granted = Column(Integer, default=1, nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False)


# 17. GDPR/CCPA Deletion & Anonymization Requests
class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    id = Column(String(64), primary_key=True, index=True)
    employee_id = Column(String(64), index=True, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(
        String(32), default="submitted", index=True, nullable=False
    )  # submitted, approved, processed, rejected
    requested_at = Column(DateTime, default=utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(String(255), nullable=True)


# 18. Employee Appeals
class AppealRecord(Base):
    """Human-review appeal record independent of model review items."""

    __tablename__ = "appeals"

    id = Column(String(64), primary_key=True, index=True)
    employee_id = Column(String(64), index=True, nullable=False)
    user_email = Column(String(255), index=True, nullable=False)
    reason = Column(Text, nullable=False)
    supporting_info = Column(Text, nullable=True)
    status = Column(String(32), default="submitted", index=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
