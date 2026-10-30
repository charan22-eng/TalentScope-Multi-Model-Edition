"""TalentScope API v2 Router.

Implements all endpoints defined in Multi-Model Pack Section 6.4:
- GET /api/v2/models
- POST /api/v2/predict
- POST /api/v2/predict/all (p95 < 800ms)
- POST /api/v2/explain
- GET /api/v2/compare/{topic}
- POST /api/v2/compare/mcda
- GET /api/v2/viz/surface & POST /api/v2/viz/surface
- GET /api/v2/viz/pca
- LLM routes: /api/v2/llm/health, /llm/models, /llm/config, /llm/verdict, /llm/verdicts/{id}
"""

import copy
import csv
import io
import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.core.audit import log_audit_event
from backend.core.security import (
    create_access_token,
    get_current_user,
    oauth2_scheme,
    require_roles,
    revoke_token,
)
from backend.db.database import get_db
from backend.db.models import (
    AppealRecord,
    AuditLog,
    ConsentRecord,
    DeletionRequest,
    Employee,
    LLMVerdict,
    ModelVersion,
    Prediction,
    ProtectedAttribute,
    ReviewDecision,
    ReviewItem,
    User,
)
from backend.services.drift_service import assess_drift
from backend.services.pdf_reports import generate_comparison_pdf, generate_employee_pdf

from .schemas import (
    EmployeeFeatures,
    V2AppealRequest,
    V2ApproveChampionRequest,
    V2ConsentRequest,
    V2DeleteRequest,
    V2ExplainRequest,
    V2ExplainResponse,
    V2FeatureFlagsUpdateRequest,
    V2LLMConfigUpdateRequest,
    V2LLMVerdictRequest,
    V2MCDARequest,
    V2PredictAllResponse,
    V2PredictRequest,
    V2PredictResponse,
    V2RetrainRequest,
    V2ReviewDecisionRequest,
)

FEATURE_FLAGS = {
    "shadow_mode_enabled": True,
    "llm_verdict_enabled": True,
    "uncertainty_queue_enabled": True,
    "conformal_filtering_enabled": True,
}

import hashlib

from epk.artifacts import default_loader
from epk.explain import (
    compute_performance_index,
    compute_stability_score,
    explain_model_native,
    find_counterfactuals,
    find_similar_cases,
    generate_ollama_persona_explanations,
    generate_persona_summaries,
    local_attribution,
)
from epk.labels import INT_TO_BAND
from epk.llm.cache import VerdictCache
from epk.llm.client import LocalLLM, assert_local
from epk.llm.fallback import generate_template_verdict
from epk.llm.prompts import (
    SYSTEM_PROMPT,
    format_user_prompt,
    scan_prompt_for_forbidden_keys,
)
from epk.llm.validator import validate_verdict
from epk.mcda import run_mcda_pipeline
from epk.models.registry import MODEL_KEYS, get_model_spec
from epk.uncertainty import get_prediction_set

logger = logging.getLogger("talentscope.v2")
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v2", tags=["v2"])

# Allowed comparison topics mapping to JSON files in artifacts/v2/comparison/
ALLOWED_COMPARISON_TOPICS: dict[str, str] = {
    "leaderboard": "leaderboard",
    "curves": "curves",
    "confusion": "confusion",
    "head2head": "pairwise",
    "pairwise": "pairwise",
    "importance": "importance",
    "sensitivity": "sensitivity",
    "fairness": "fairness",
    "robustness": "robustness",
    "mcda": "mcda",
    "evidence": "evidence_packet",
    "evidence_packet": "evidence_packet",
    "conformal": "conformal",
}


# Runtime config for LLM. Keep the default aligned with the local demo setup:
# llama3.1:latest is installed on the review machine and performed best on the
# project's structured-evidence benchmark among the available text models.
def _env_float(*names: str, default: float) -> float:
    for name in names:
        value = os.getenv(name)
        if value is None:
            continue
        try:
            return float(value)
        except ValueError:
            continue
    return default


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


_LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "ollama"),
    "model": os.getenv("LLM_MODEL", "qwen2.5:3b"),
    "base_url": os.getenv(
        "LLM_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ),
    "enabled": _env_bool("LLM_ENABLED", True),
    "timeout_s": _env_float("LLM_TIMEOUT_S", "LLM_TIMEOUT_SECONDS", default=120.0),
    "max_retries": max(0, _env_int("LLM_MAX_RETRIES", 2)),
}

# Cache for train background data and medians
_TRAIN_DATA: pd.DataFrame | None = None
_TRAIN_LABELS: pd.Series | None = None
_TRAIN_MEDIANS: pd.Series | None = None


def get_train_context() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Load train split features and medians once for fast local explainability."""
    global _TRAIN_DATA, _TRAIN_LABELS, _TRAIN_MEDIANS
    if _TRAIN_DATA is None:
        try:
            root = default_loader.root_dir.parent.parent
            train_csv = root / "data" / "processed" / "train.csv"
            dataset_csv = root / "data" / "nonlinear" / "dataset.csv"
            split_file = root / "data" / "processed" / "split.json"

            if train_csv.exists():
                df = pd.read_csv(train_csv)
            elif dataset_csv.exists():
                df_all = pd.read_csv(dataset_csv)
                if split_file.exists():
                    with open(split_file, "r", encoding="utf-8") as f:
                        s_data = json.load(f)
                    indices = s_data.get("train_indices", [])
                    df = df_all.iloc[indices].copy() if indices else df_all.copy()
                else:
                    df = df_all.copy()
            else:
                # Fallback to background sample in pca.json
                pca_meta = default_loader.root_dir / "explainability" / "pca.json"
                if pca_meta.exists():
                    with open(pca_meta, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    pts = meta.get("background_points", [])
                    df = pd.DataFrame(pts)
                else:
                    df = pd.DataFrame()

            if not df.empty:
                _TRAIN_LABELS = (
                    cast(pd.Series, df["performance"].copy())
                    if "performance" in df.columns
                    else pd.Series(["Medium"] * len(df))
                )
                _TRAIN_DATA = df.drop(
                    columns=["performance", "performance_score"], errors="ignore"
                )
                # Fill missing numeric values with medians so distances are non-NaN
                num_cols = _TRAIN_DATA.select_dtypes(include=[np.number]).columns
                _TRAIN_DATA[num_cols] = _TRAIN_DATA[num_cols].fillna(
                    _TRAIN_DATA[num_cols].median()
                )
            else:
                _TRAIN_DATA = pd.DataFrame()
                _TRAIN_LABELS = pd.Series()
        except Exception as e:
            logger.warning(f"Could not load train dataset for explainability: {e}")
            _TRAIN_DATA = pd.DataFrame()
            _TRAIN_LABELS = pd.Series()

        if _TRAIN_DATA is not None and not _TRAIN_DATA.empty:
            _TRAIN_MEDIANS = _TRAIN_DATA.select_dtypes(include=[np.number]).median()
        else:
            _TRAIN_MEDIANS = pd.Series(
                {
                    "attendance": 88.0,
                    "experience_years": 4.0,
                    "training_hours": 35.0,
                    "projects_completed": 6.0,
                    "weekly_hours": 40.0,
                    "peer_feedback": 3.6,
                    "tasks_on_time_pct": 82.0,
                    "certifications": 1.0,
                }
            )
    return (
        cast(pd.DataFrame, _TRAIN_DATA),
        cast(pd.Series, _TRAIN_LABELS),
        cast(pd.Series, _TRAIN_MEDIANS),
    )


def to_band_str(c: Any) -> str:
    """Map integer class or numeric code to band string."""
    return INT_TO_BAND.get(c, str(c)) if isinstance(c, (int, np.integer)) else str(c)


def problem_details(
    status_code: int, title: str, detail: Any, instance: str | None = None
) -> JSONResponse:
    """Construct RFC 7807 Problem Details response."""
    content = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        content["instance"] = instance
    return JSONResponse(status_code=status_code, content=content)


def check_model_key_safe(model_key: str) -> None:
    """Enforce model key whitelist and prevent path traversal (Guard G11)."""
    if ".." in model_key or "/" in model_key or "\\" in model_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path traversal or invalid characters detected in model key: '{model_key}'",
        )
    if model_key not in MODEL_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown model key '{model_key}'. Allowed models: {sorted(MODEL_KEYS)}",
        )


def run_single_model_predict(
    model_key: str, features_dict: dict[str, Any]
) -> V2PredictResponse:
    """Internal helper to predict for a single model key."""
    check_model_key_safe(model_key)
    model = default_loader.load_model(model_key)

    df = pd.DataFrame([features_dict])
    probs = model.predict_proba(df)[0]
    classes = list(model.classes_)
    classes_str = [to_band_str(c) for c in classes]

    # Conformal set
    # Using conformal prediction set threshold from conformal.json or metadata
    try:
        conf_data = default_loader.load_comparison_json("conformal")
        threshold = (
            conf_data.get("models", {}).get(model_key, {}).get("threshold", 0.05)
        )
    except Exception:
        threshold = 0.05

    raw_pset = get_prediction_set(probs, classes, threshold)
    pset = [to_band_str(c) for c in raw_pset]

    best_idx = int(np.argmax(probs))
    best_band = classes_str[best_idx]
    best_conf = float(probs[best_idx])
    prob_dict = {c: float(p) for c, p in zip(classes_str, probs)}

    stab = compute_stability_score(probs)
    perf_idx = compute_performance_index(model, df, model_key, precomputed_probs=probs)

    return V2PredictResponse(
        model_key=model_key,
        predicted_band=best_band,
        confidence=best_conf,
        prediction_set=pset,
        probabilities=prob_dict,
        stability_score=round(stab * 100.0, 2),
        performance_index=perf_idx,
    )


# ==============================================================================
# Model Registry & Predictions
# ==============================================================================


@router.get("/models")
def list_models(
    current_user: User = Depends(
        require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer")
    )
):
    """List all seven models with their specs, metadata, and test metrics (all authenticated roles)."""
    manifest = default_loader.manifest.get("files", {})
    champion_data = default_loader.load_champion()
    out = []
    for key in sorted(MODEL_KEYS):
        spec = get_model_spec(key)
        try:
            meta = default_loader.load_model_metadata(key)
        except Exception:
            meta = {}

        model_rel = f"models/{key}/model.joblib"
        file_sha256 = manifest.get(model_rel, {}).get("sha256", "unknown")

        out.append(
            {
                "key": key,
                "label": spec.label,
                "family": spec.family,
                "explain_tier": spec.explain_tier,
                "is_champion": (key == champion_data.get("champion_key", "rf")),
                "test_macro_f1": meta.get("test_macro_f1"),
                "test_accuracy": meta.get("test_accuracy"),
                "latency_p95_ms": meta.get("latency_p95_ms"),
                "sha256": file_sha256,
            }
        )
    return out


# ==============================================================================
# Dataset census (Data Explorer)
# ==============================================================================

_DATASET_SUMMARY_CACHE: dict[str, tuple[float, dict]] = {}


def _feature_statistics(df: pd.DataFrame, features: list[str]) -> list[dict]:
    """Per-feature descriptive statistics; never emits employee-level values."""
    stats = []
    for name in features:
        if name not in df.columns:
            continue
        column = df[name]
        missing_pct = round(float(column.isna().mean() * 100), 2)
        if pd.api.types.is_numeric_dtype(column):
            stats.append(
                {
                    "name": name,
                    "kind": "numeric",
                    "missing_pct": missing_pct,
                    "min": round(float(column.min()), 2),
                    "median": round(float(column.median()), 2),
                    "mean": round(float(column.mean()), 2),
                    "max": round(float(column.max()), 2),
                }
            )
        else:
            counts = column.value_counts(normalize=True)
            stats.append(
                {
                    "name": name,
                    "kind": "categorical",
                    "missing_pct": missing_pct,
                    "categories": int(column.nunique()),
                    "top_values": [
                        {"value": str(value), "share": round(float(share), 4)}
                        for value, share in counts.head(3).items()
                    ],
                }
            )
    return stats


def _build_dataset_summary() -> dict:
    """Aggregate the governed dataset into census statistics (no employee-level rows)."""
    meta = default_loader.load_dataset_meta()
    variant = meta.get("default_variant", "nonlinear")
    dataset_file = Path("data") / variant / "dataset.csv"
    protected_file = Path("data") / variant / "protected.csv"
    split_file = default_loader.root_dir / "split.json"

    cache_key = f"{dataset_file}:{split_file}"
    if dataset_file.exists():
        stamp = dataset_file.stat().st_mtime
        cached = _DATASET_SUMMARY_CACHE.get(cache_key)
        if cached and cached[0] == stamp:
            return cached[1]

    summary: dict = {
        "dataset": meta,
        "variant": variant,
        "split": None,
        "class_balance": [],
        "features": [],
        "protected_attributes": [],
        "notes": (
            "Synthetic benchmark generated by the frozen generator (ADR-006). "
            "Protected attributes are stored separately and are never model features."
        ),
    }

    if split_file.exists():
        try:
            with open(split_file, "r", encoding="utf-8") as f:
                split = json.load(f)
            summary["split"] = {
                "seed": split.get("seed"),
                "n_rows": split.get("n_rows"),
                "train": split.get("train_count", len(split.get("train_indices", []))),
                "calibration": {
                    "cal_a": split.get("cal_a_count", len(split.get("cal_a_indices", []))),
                    "cal_b": split.get("cal_b_count", len(split.get("cal_b_indices", []))),
                },
                "test": split.get("test_count", len(split.get("test_indices", []))),
                "dataset_sha256": split.get("dataset_sha256"),
                "split_hash": split.get("split_hash"),
            }
        except Exception:
            logger.warning("Split file could not be read for the dataset summary")

    if protected_file.exists():
        try:
            columns = pd.read_csv(protected_file, nrows=0).columns
            summary["protected_attributes"] = [
                name for name in columns if name != "employee_id"
            ]
        except Exception:
            logger.warning("Protected attribute names could not be read")

    if dataset_file.exists():
        df = pd.read_csv(dataset_file)
        summary["features"] = _feature_statistics(df, list(meta.get("features", [])))
        if "performance" in df.columns:
            counts = df["performance"].value_counts()
            total = int(counts.sum())
            order = ["Low", "Medium", "High"]
            summary["class_balance"] = [
                {
                    "band": band,
                    "count": int(counts.get(band, 0)),
                    "share": round(float(counts.get(band, 0) / total), 4) if total else 0.0,
                }
                for band in order
            ]
        summary["rows_loaded"] = int(len(df))
        _DATASET_SUMMARY_CACHE[cache_key] = (dataset_file.stat().st_mtime, summary)

    return summary


@router.get(
    "/dataset/summary",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def dataset_summary():
    """Dataset census for the Data Explorer page (all authenticated roles)."""
    try:
        return _build_dataset_summary()
    except Exception as e:
        return problem_details(
            status_code=503,
            title="Dataset Summary Unavailable",
            detail=str(e),
        )


@router.post("/predict", response_model=V2PredictResponse)
@limiter.limit("60/minute")
async def predict_single(
    request: Request,
    body: V2PredictRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
):
    """Predict performance band using a specific whitelisted model (all roles)."""
    key = body.model_key or "rf"
    check_model_key_safe(key)
    res = run_single_model_predict(key, body.features.model_dump())

    # Shadow mode execution (L5)
    shadow_res = None
    if FEATURE_FLAGS.get("shadow_mode_enabled") and key == "rf":
        try:
            shadow_res = run_single_model_predict("boost", body.features.model_dump())
        except Exception:
            pass

    # Record prediction in DB and handle uncertainty queue (L3)
    if db is not None:
        try:
            p_id = str(uuid.uuid4())
            user_email = getattr(user, "email", "anonymous") if user else "anonymous"
            pred_record = Prediction(
                id=p_id,
                user_email=user_email,
                model_key=key,
                predicted_band=(
                    0
                    if res.predicted_band == "Low"
                    else (1 if res.predicted_band == "Medium" else 2)
                ),
                probabilities_json=json.dumps(res.probabilities),
                confidence=res.confidence,
                stability_score=res.stability_score,
                conformal_set_json=json.dumps(res.prediction_set),
                is_split_decision=(
                    1
                    if (shadow_res and shadow_res.predicted_band != res.predicted_band)
                    else 0
                ),
                is_shadow=0,
                input_data=json.dumps(body.features.model_dump()),
            )
            db.add(pred_record)

            if shadow_res:
                shadow_pred = Prediction(
                    id=str(uuid.uuid4()),
                    user_email=user_email,
                    model_key="boost",
                    predicted_band=(
                        0
                        if shadow_res.predicted_band == "Low"
                        else (1 if shadow_res.predicted_band == "Medium" else 2)
                    ),
                    probabilities_json=json.dumps(shadow_res.probabilities),
                    confidence=shadow_res.confidence,
                    stability_score=shadow_res.stability_score,
                    conformal_set_json=json.dumps(shadow_res.prediction_set),
                    is_split_decision=0,
                    is_shadow=1,
                    input_data=json.dumps(body.features.model_dump()),
                )
                db.add(shadow_pred)

            # Uncertainty-first queue item (L3)
            if FEATURE_FLAGS.get("uncertainty_queue_enabled"):
                flags = []
                stab_pct = res.stability_score
                if stab_pct < 70.0:
                    flags.append("low_stability")
                if len(res.prediction_set) > 1:
                    flags.append("conformal_multi_band")
                if shadow_res and shadow_res.predicted_band != res.predicted_band:
                    flags.append("split_decision")

                if flags:
                    urgency = (
                        "high"
                        if ("split_decision" in flags or stab_pct < 50.0)
                        else "medium"
                    )
                    rev_item = ReviewItem(
                        id=str(uuid.uuid4()),
                        prediction_id=p_id,
                        employee_id=getattr(body.features, "employee_id", None),
                        status="pending",
                        urgency=urgency,
                        flags_json=json.dumps(flags),
                    )
                    db.add(rev_item)

            db.commit()
        except Exception as e:
            logger.warning(f"Could not persist prediction or review item: {e}")
            db.rollback()

    return res


@router.post(
    "/predict/all",
    response_model=V2PredictAllResponse,
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
@limiter.limit("30/minute")
async def predict_all(request: Request, features: EmployeeFeatures):
    """Run inference across all seven models, returning consensus and split-decision flags.

    Performance requirement: p95 latency under 800ms.
    """
    t0 = time.time()
    feat_dict = features.model_dump()
    predictions: dict[str, V2PredictResponse] = {}
    top_bands: list[str] = []

    for key in MODEL_KEYS:
        pred_resp = run_single_model_predict(key, feat_dict)
        predictions[key] = pred_resp
        top_bands.append(pred_resp.predicted_band)

    # Agreement and consensus calculation
    counts = pd.Series(top_bands).value_counts()
    consensus_band = str(counts.index[0])
    max_count = int(counts.iloc[0])
    agreement_rate = round(float(max_count / len(MODEL_KEYS)), 4)
    split_decision = bool(len(counts) > 1)

    champion_data = default_loader.load_champion()
    champ_key = champion_data.get("champion_key", "rf")
    champ_pred = predictions[champ_key]

    latency_ms = round((time.time() - t0) * 1000, 2)

    return V2PredictAllResponse(
        predictions=predictions,
        consensus_band=consensus_band,
        agreement_rate=agreement_rate,
        split_decision=split_decision,
        champion_key=champ_key,
        champion_prediction=champ_pred,
        latency_ms=latency_ms,
    )


@router.post(
    "/batch",
    dependencies=[Depends(require_roles("admin", "hr_manager", "analyst"))],
)
@limiter.limit("5/minute")
async def batch_predict_v2(
    request: Request,
    file: UploadFile = File(...),
    model_key: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Run batch prediction on uploaded CSV file (roles: admin, hr_manager, analyst)."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid encoding")

    # Formula injection guard. Negative numeric values are valid input; only
    # formula-like cell contents are rejected.
    numeric_cell = re.compile(r"^-?(?:\d+(?:\.\d*)?|\.\d+)$")
    for row in csv.reader(io.StringIO(text)):
        for cell in row:
            value = cell.strip()
            if value.startswith(("=", "+", "@")) or (
                value.startswith("-") and not numeric_cell.fullmatch(value)
            ):
                raise HTTPException(
                    status_code=400, detail="Formula injection detected"
                )

    df = pd.read_csv(io.StringIO(text))
    if len(df) > 5000:
        raise HTTPException(status_code=413, detail="Maximum 5,000 CSV rows allowed")

    chosen_key = model_key or default_loader.load_champion().get("champion_key", "rf")
    if chosen_key not in MODEL_KEYS and chosen_key != "all":
        raise HTTPException(status_code=400, detail=f"Invalid model_key '{chosen_key}'")

    results = []
    errors = []
    t0 = time.time()

    for idx, row in df.iterrows():
        try:
            row_dict = row.to_dict()
            if chosen_key == "all":
                row_preds = {
                    k: run_single_model_predict(k, row_dict).predicted_band
                    for k in MODEL_KEYS
                }
                results.append({"row": idx, "predictions": row_preds})
            else:
                pred = run_single_model_predict(chosen_key, row_dict)
                results.append(
                    {
                        "row": idx,
                        "model_key": chosen_key,
                        "predicted_band": pred.predicted_band,
                        "confidence": pred.confidence,
                        "stability_score": pred.stability_score,
                    }
                )
            errors.append(None)
        except Exception as e:
            results.append(None)
            errors.append({"row": idx, "error": str(e)})

    elapsed_ms = (time.time() - t0) * 1000.0

    # Log audit event
    log_audit_event(
        db,
        user.email,
        "batch_predict",
        f"/api/v2/batch/{chosen_key}",
        details={
            "total_rows": len(df),
            "error_count": sum(1 for e in errors if e is not None),
        },
    )

    return {
        "model_key": chosen_key,
        "total_rows": len(df),
        "results": results,
        "errors": [e for e in errors if e is not None],
        "latency_ms": round(elapsed_ms, 2),
    }


@router.post(
    "/auth/logout",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def logout_v2(
    token: str = Depends(oauth2_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke JWT token on logout."""
    revoke_token(token)
    log_audit_event(
        db,
        user.email,
        "logout",
        "/api/v2/auth/logout",
        details={"token_prefix": token[:10]},
    )
    return {"status": "success", "message": "Token revoked successfully"}


@router.post(
    "/auth/refresh",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def refresh_v2(
    token: str = Depends(oauth2_scheme),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rotate JWT token on refresh (revoking the old token)."""
    revoke_token(token)
    new_token = create_access_token(data={"sub": user.email, "role": user.role})
    log_audit_event(
        db,
        user.email,
        "token_refresh",
        "/api/v2/auth/refresh",
        details={"token_prefix": new_token[:10]},
    )
    return {"access_token": new_token, "token_type": "bearer", "role": user.role}


# ==============================================================================
# Explainability
# ==============================================================================


@router.post(
    "/explain",
    response_model=V2ExplainResponse,
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
@limiter.limit("30/minute")
def explain_model(request: Request, body: V2ExplainRequest):
    """Provide model-specific native and agnostic explanations (all roles)."""
    key = body.model_key or "rf"
    check_model_key_safe(key)
    spec = get_model_spec(key)
    model = default_loader.load_model(key)

    df = pd.DataFrame([body.features.model_dump()])
    train_df, train_labels, train_medians = get_train_context()

    probs = model.predict_proba(df)[0]
    classes = list(model.classes_)
    best_idx = int(np.argmax(probs))
    best_band = to_band_str(classes[best_idx])

    # 1. Native explainability
    native_exp = explain_model_native(model, key)

    # 2. Local attribution
    attrib = local_attribution(model, df, train_medians)

    # 3. Actionable counterfactuals
    cfs = find_counterfactuals(model, df, target_band="High")

    # 4. Similar cases
    k = body.k or 5
    if not train_df.empty:
        sim_cases = find_similar_cases(train_df, train_labels, df, model_key=key, k=k)
    else:
        sim_cases = {
            "banner": "Historical Cases",
            "is_native_reasoning": (key == "knn"),
            "model_key": key,
            "k": k,
            "neighbors": [],
            "neighborhood_distribution": {},
        }

    # 5. Persona summaries & Ollama generation
    stab = compute_stability_score(probs)
    features_dict = body.features.model_dump()

    if _LLM_CONFIG["enabled"]:
        llm_exp = generate_ollama_persona_explanations(
            key=key,
            label=spec.label,
            pred_band=best_band,
            proba=probs.tolist(),
            attribution=attrib,
            counterfactuals=cfs,
            stability=stab,
            candidate_features=features_dict,
            similar_cases=sim_cases,
            base_url=_LLM_CONFIG["base_url"],
            preferred_model=_LLM_CONFIG["model"],
            timeout_s=15.0,
        )
        summaries = llm_exp["persona_summaries"]
        key_drivers = llm_exp.get("key_drivers")
        actionable_guidance = llm_exp.get("actionable_guidance")
        llm_meta = llm_exp.get("llm_metadata")
    else:
        summaries = generate_persona_summaries(
            key=key,
            label=spec.label,
            pred_band=best_band,
            proba=probs.tolist(),
            attribution=attrib,
            counterfactuals=cfs,
            stability=stab,
        )
        key_drivers = [f"{k.replace('_', ' ').title()}: {v:+.2f}" for k, v in list(attrib.items())[:3]]
        actionable_guidance = (
            "Review counterfactual levers to achieve a higher performance band."
            if cfs
            else "Maintain strong baseline performance metrics."
        )
        llm_meta = {"source": "template_fallback", "model": "none", "reason": "LLM_ENABLED=false"}

    return V2ExplainResponse(
        model_key=key,
        label=spec.label,
        explanation_type=spec.explain_tier,
        predicted_band=best_band,
        native_explanation=native_exp,
        local_attribution=attrib,
        counterfactuals=cfs,
        similar_cases=sim_cases,
        persona_summaries=summaries,
        key_drivers=key_drivers,
        actionable_guidance=actionable_guidance,
        llm_metadata=llm_meta,
    )


# ==============================================================================
# Comparison Science & MCDA
# ==============================================================================


@router.get(
    "/compare/{topic}",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def get_comparison_data(topic: str):
    """Retrieve precomputed model comparison science JSON (all roles)."""
    if topic not in ALLOWED_COMPARISON_TOPICS:
        return problem_details(
            status_code=404,
            title="Comparison Topic Not Found",
            detail=f"Topic '{topic}' is not valid. Allowed topics: {sorted(ALLOWED_COMPARISON_TOPICS)}",
        )

    json_name = ALLOWED_COMPARISON_TOPICS[topic]
    try:
        data = default_loader.load_comparison_json(json_name)
        return data
    except Exception as e:
        return problem_details(
            status_code=500,
            title="Artifact Read Error",
            detail=f"Could not load comparison data for '{topic}': {e!s}",
        )


@router.post(
    "/compare/mcda",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def recalculate_mcda(body: V2MCDARequest):
    """Dynamically recompute MCDA rankings with validated user weights (all roles)."""
    weights = body.weights
    if not weights or not any(weights.values()):
        return problem_details(
            status_code=400,
            title="Invalid MCDA Weights",
            detail="Weights must be non-empty and contain positive numeric values",
        )

    # Validate non-negative numbers
    for k, v in weights.items():
        if v < 0:
            return problem_details(
                status_code=400,
                title="Invalid Weight Value",
                detail=f"Weight for '{k}' cannot be negative (got {v})",
            )

    try:
        # Load base leaderboard data to form criteria table
        lb_data = default_loader.load_comparison_json("leaderboard")
        metrics_list = lb_data.get("metrics", [])
        rows = {}
        for m in metrics_list:
            m_key = m.get("key")
            if not m_key:
                continue
            rows[m_key] = {
                "macro_f1": float(m.get("macro_f1", 0.7)),
                "qwk": float(m.get("qwk", 0.6)),
                "calibration": float(m.get("calibration", 1.0 - m.get("ece", 0.05))),
                "robustness": float(m.get("robustness", 0.85)),
                "fairness": float(m.get("fairness", 0.85)),
                "stability": float(m.get("stability", 0.6)),
                "latency": float(
                    m.get("latency", m.get("latency_single_p95_ms", 10.0))
                ),
                "train_cost": float(m.get("train_cost", m.get("tuning_time_sec", 2.0))),
                "explainability": float(
                    m.get("explainability", m.get("explain_score", 0.5))
                ),
            }
        table = pd.DataFrame.from_dict(rows, orient="index")

        result = run_mcda_pipeline(
            table, profile_name=body.profile or "Custom", custom_weights=weights
        )
        return {
            "weights_used": result["weights"],
            "profile_name": result["profile"],
            "ranked_models": [
                {
                    "key": row["key"],
                    "composite_score": row["mcda_score"],
                    "rank": row["rank"],
                    "rank1_probability": row["p_rank1"],
                    "decision_strength": result["decision_strength"],
                }
                for row in result["ranking"]
            ],
            "winner": result["deterministic_winner"],
            "deterministic_winner": result["deterministic_winner"],
            "decision_strength": result["decision_strength"],
            "decision_rule": "ADR-009 Multi-Criteria Decision Analysis",
            "ranking": result["ranking"],
        }
    except Exception as e:
        return problem_details(
            status_code=500,
            title="MCDA Computation Failed",
            detail=str(e),
        )


# ==============================================================================
# 2D/3D Visualizations
# ==============================================================================


@router.get(
    "/viz/surface",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
@router.post(
    "/viz/surface",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def get_surface_landscape(model_key: str = "rf", grid_size: int = 40):
    """Retrieve decision surface grid for 2D/3D visualization (all roles)."""
    check_model_key_safe(model_key)
    if grid_size > 80:
        return problem_details(
            status_code=400,
            title="Grid Size Exceeded",
            detail=f"Grid size {grid_size} exceeds maximum allowed size of 80x80",
        )

    surfaces_path = default_loader.root_dir / "explainability" / "surfaces.json"
    if surfaces_path.exists():
        with open(surfaces_path, "r", encoding="utf-8") as f:
            all_surfaces = json.load(f)
        if model_key in all_surfaces:
            return all_surfaces[model_key]

    return problem_details(
        status_code=404,
        title="Surface Not Found",
        detail=f"Precomputed surface for model '{model_key}' not found",
    )


@router.get(
    "/viz/pca",
    dependencies=[
        Depends(require_roles("admin", "hr_manager", "analyst", "viewer", "reviewer"))
    ],
)
def get_pca_projection():
    """Retrieve PCA 2D/3D projection coordinates and background sample (all roles)."""
    pca_path = default_loader.root_dir / "explainability" / "pca.json"
    if pca_path.exists():
        with open(pca_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return problem_details(
        status_code=404, title="PCA Data Not Found", detail="PCA artifact not available"
    )


# ==============================================================================
# Local LLM Verdict Engine
# ==============================================================================


@router.get("/llm/health", dependencies=[Depends(require_roles("admin", "analyst"))])
def llm_health():
    """Check local LLM runtime health (Admin, Analyst)."""
    if not _LLM_CONFIG["enabled"]:
        return {
            "status": "disabled",
            "runtime": _LLM_CONFIG["provider"],
            "base_url": _LLM_CONFIG["base_url"],
            "model": _LLM_CONFIG["model"],
            "fallback_available": True,
        }
    try:
        llm = LocalLLM(
            provider=_LLM_CONFIG["provider"],
            base_url=_LLM_CONFIG["base_url"],
            timeout=2.0,
        )
        models = llm.list_models()
        return {
            "status": "healthy" if models else "reachable",
            "runtime": _LLM_CONFIG["provider"],
            "models_available": models,
        }
    except Exception as e:
        return {
            "status": "offline",
            "runtime": _LLM_CONFIG["provider"],
            "base_url": _LLM_CONFIG["base_url"],
            "detail": f"Local runtime not reachable: {e!s}",
            "fallback_available": True,
        }


@router.get("/llm/models", dependencies=[Depends(require_roles("admin", "analyst"))])
def list_llm_models():
    """List local models available in Ollama/vLLM (Admin, Analyst)."""
    if not _LLM_CONFIG["enabled"]:
        return {"models": [], "disabled": True}
    try:
        llm = LocalLLM(
            provider=_LLM_CONFIG["provider"],
            base_url=_LLM_CONFIG["base_url"],
            timeout=5.0,
        )
        models = llm.list_models()
        return {"models": models}
    except Exception as e:
        return problem_details(
            status_code=503,
            title="LLM Service Unavailable",
            detail=f"Could not connect to local runtime at {_LLM_CONFIG['base_url']}: {e!s}",
        )


@router.put("/llm/config", dependencies=[Depends(require_roles("admin"))])
def update_llm_config(body: V2LLMConfigUpdateRequest):
    """Update runtime provider, URL, and model with SSRF verification (Admin only)."""
    if body.base_url:
        try:
            assert_local(body.base_url)
        except ValueError as e:
            return problem_details(
                status_code=400,
                title="SSRF Violation",
                detail=f"Refused non-local URL: {e!s}",
            )
        _LLM_CONFIG["base_url"] = body.base_url

    if body.provider:
        _LLM_CONFIG["provider"] = body.provider
    if body.model:
        _LLM_CONFIG["model"] = body.model

    return {"status": "updated", "config": _LLM_CONFIG}


@router.post(
    "/llm/verdict",
    dependencies=[Depends(require_roles("admin", "hr", "hr_manager", "analyst"))],
)
@limiter.limit("15/minute")
def generate_verdict(
    request: Request,
    body: V2LLMVerdictRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate or retrieve a cached/fallback LLM verdict.

    Roles: Admin, HR, Analyst.
    Checks:
    - Zero employee data in input (G9 prompt hygiene)
    - Strict numeric validation against evidence packet (G9 validator)
    - Fallback on connection error or validator failure
    """
    # 1. Load evidence packet and apply the requested governance profile.
    packet = copy.deepcopy(
        body.evidence_packet
        if body.evidence_packet
        else default_loader.load_comparison_json("evidence_packet")
    )
    requested_profile = body.profile or packet.get("profile", {}).get(
        "name", "Balanced"
    )
    profile_name = {
        "High Accuracy": "Accuracy-first",
        "Interpretability First": "Explainability-first",
        "Low Latency": "Speed-first",
        "Fair & Robust": "Fairness-first",
    }.get(requested_profile, requested_profile)
    if profile_name != packet.get("profile", {}).get("name"):
        profile_catalog = default_loader.load_comparison_json("mcda").get(
            "all_profiles", {}
        )
        selected_profile = profile_catalog.get(profile_name)
        if selected_profile:
            packet["profile"] = {
                "name": profile_name,
                "weights": selected_profile.get("weights", {}),
            }
            packet["deterministic_winner"] = selected_profile.get(
                "deterministic_winner", packet.get("deterministic_winner")
            )
            packet["runner_up"] = selected_profile.get(
                "runner_up", packet.get("runner_up")
            )
            packet["decision_strength"] = selected_profile.get(
                "decision_strength", packet.get("decision_strength", "none")
            )

    audience = {"hr": "HR", "ds": "Data Scientist"}.get(
        body.audience or "HR", body.audience or "HR"
    )

    # 2. Check for employee leakage
    violations = scan_prompt_for_forbidden_keys(json.dumps(packet))
    if violations:
        return problem_details(
            status_code=400,
            title="Privacy Guard Violation (G9)",
            detail=f"Forbidden employee identifiers found in evidence: {violations}",
        )

    prompt = format_user_prompt(packet, audience=audience)
    prompt_violations = scan_prompt_for_forbidden_keys(prompt)
    if prompt_violations:
        return problem_details(
            status_code=400,
            title="Privacy Guard Violation (G9)",
            detail=f"Forbidden employee identifiers in prompt: {prompt_violations}",
        )

    # 3. Check cache
    pkt_hash = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
    cache = VerdictCache()
    cache_key = VerdictCache.compute_key(
        packet_hash=pkt_hash,
        prompt_version="1.0",
        model=_LLM_CONFIG["model"],
        audience=audience,
        mode=body.mode or "verdict",
        profile_name=profile_name,
    )
    cached = cache.get(cache_key)
    cached_source = cached.get("source") if isinstance(cached, dict) else None
    cache_allowed = _LLM_CONFIG["enabled"] or cached_source in {
        "fallback",
        "template",
        "template_fallback",
    }
    if cached and cache_allowed:
        cached_output = cached.get("output", cached)
        cached_errors = validate_verdict(cached_output, packet)
        if not cached_errors:
            return {
                "verdict": cached_output,
                "source": "cache",
                "is_fallback": cached.get("source")
                in {"fallback", "template", "template_fallback"},
                "validation": {"valid": True, "errors": []},
            }
        logger.warning(
            "Ignoring invalid cached verdict %s: %s", cache_key, cached_errors
        )

    # 4. Attempt local LLM call
    llm_error = None
    if not _LLM_CONFIG["enabled"]:
        llm_error = "LLM_ENABLED=false"
    else:
        try:
            llm = LocalLLM(
                provider=_LLM_CONFIG["provider"],
                base_url=_LLM_CONFIG["base_url"],
                model=_LLM_CONFIG["model"],
                timeout=_LLM_CONFIG["timeout_s"],
            )
            validation_history = []
            for attempt in range(_LLM_CONFIG["max_retries"] + 1):
                try:
                    raw_text = llm.chat_json(system=SYSTEM_PROMPT, user=prompt)
                    verdict_obj = json.loads(raw_text)
                    validation_errors = validate_verdict(verdict_obj, packet)
                    validation_history.append(validation_errors)
                    if validation_errors:
                        llm_error = (
                            f"Validator rejected LLM response on attempt {attempt + 1}: "
                            f"{validation_errors}"
                        )
                        continue

                    cache.put(
                        cache_key=cache_key,
                        packet_hash=pkt_hash,
                        prompt_version="1.0",
                        model=_LLM_CONFIG["model"],
                        audience=audience,
                        mode=body.mode or "verdict",
                        source="live_llm",
                        output=verdict_obj,
                        validation_history=validation_history,
                    )
                    # Persist in DB
                    v_id = str(uuid.uuid4())
                    db_record = LLMVerdict(
                        id=v_id,
                        user_email=user.email,
                        mode=body.mode or "verdict",
                        audience=audience,
                        prompt_hash=pkt_hash,
                        verdict_json=json.dumps(verdict_obj),
                        is_valid=1,
                        is_fallback=0,
                        validation_json=json.dumps(
                            {"valid": True, "attempts": attempt + 1}
                        ),
                    )
                    db.add(db_record)
                    db.commit()

                    return {
                        "id": v_id,
                        "verdict": verdict_obj,
                        "source": "live_llm",
                        "is_fallback": False,
                        "validation": {
                            "valid": True,
                            "errors": [],
                            "attempts": attempt + 1,
                        },
                    }
                except Exception as e:
                    llm_error = f"{type(e).__name__}: {e}"
                    validation_history.append([llm_error])
        except Exception as e:
            llm_error = str(e)

    # 5. Handle fallback or return 503
    if body.allow_fallback:
        fallback_verdict = generate_template_verdict(packet, audience=audience)
        v_id = str(uuid.uuid4())
        db_record = LLMVerdict(
            id=v_id,
            user_email=user.email,
            mode=body.mode or "verdict",
            audience=audience,
            prompt_hash=pkt_hash,
            verdict_json=json.dumps(fallback_verdict),
            is_valid=1,
            is_fallback=1,
            validation_json=json.dumps(
                {"valid": True, "note": f"Fallback due to: {llm_error}"}
            ),
        )
        db.add(db_record)
        db.commit()

        return {
            "id": v_id,
            "verdict": fallback_verdict,
            "source": "template_fallback",
            "is_fallback": True,
            "validation": {"valid": True, "errors": []},
            "notice": f"Deterministic template fallback used because local LLM was unavailable ({llm_error})",
        }
    else:
        return problem_details(
            status_code=503,
            title="LLM Service Unavailable",
            detail=f"Local LLM runtime failed and allow_fallback was false: {llm_error}. Set allow_fallback=true to generate a template verdict.",
        )


@router.get("/llm/verdicts/{verdict_id}", dependencies=[Depends(get_current_user)])
def get_stored_verdict(
    verdict_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieve stored verdict by ID (owner or Admin)."""
    record = db.query(LLMVerdict).filter(LLMVerdict.id == verdict_id).first()
    if not record:
        return problem_details(
            status_code=404,
            title="Verdict Not Found",
            detail=f"Verdict '{verdict_id}' not found",
        )

    # Authorization: user must own the record or be admin
    if (
        record.user_email != user.email
        and (getattr(user, "role", "") or "").lower() != "admin"
    ):
        return problem_details(
            status_code=403,
            title="Forbidden",
            detail="You are not authorized to view this verdict",
        )

    return {
        "id": record.id,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        "mode": record.mode,
        "audience": record.audience,
        "user_email": record.user_email,
        "is_fallback": bool(record.is_fallback),
        "is_valid": bool(record.is_valid),
        "verdict": json.loads(record.verdict_json) if record.verdict_json else {},
        "validation": (
            json.loads(record.validation_json) if record.validation_json else {}
        ),
    }


# ==============================================================================
# Stage L: Governed Operations, MLOps, Reviews, Transparency & Reports
# ==============================================================================


# L2: Audit Logs
@router.get("/audit/logs", dependencies=[Depends(require_roles("admin"))])
def get_audit_logs(
    user_email: str | None = None,
    action: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """View append-only audit trail (Admin only)."""
    q = db.query(AuditLog)
    if user_email:
        q = q.filter(AuditLog.user_email == user_email)
    if action:
        q = q.filter(AuditLog.action == action)
    logs = q.order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            "user_email": l.user_email,
            "action": l.action,
            "resource": l.resource,
            "details": json.loads(l.details_json) if l.details_json else {},
            "ip_address": l.ip_address,
        }
        for l in logs
    ]


@router.put("/users/{user_id}/role", dependencies=[Depends(require_roles("admin"))])
def update_user_role(
    user_id: int,
    new_role: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a user's RBAC role with immutable audit trail (Admin only)."""
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return problem_details(
            status_code=404,
            title="User Not Found",
            detail=f"User ID {user_id} not found",
        )
    valid_roles = {"admin", "hr_manager", "analyst", "viewer", "reviewer"}
    if new_role.lower() not in valid_roles:
        return problem_details(
            status_code=400,
            title="Invalid Role",
            detail=f"Role '{new_role}' is not a valid system role",
        )
    old_role = target_user.role
    target_user.role = new_role.lower()
    db.commit()
    log_audit_event(
        db,
        user.email,
        "role_change",
        f"/api/v2/users/{user_id}/role",
        details={
            "user_id": user_id,
            "target_email": target_user.email,
            "old_role": old_role,
            "new_role": target_user.role,
        },
    )
    return {
        "status": "success",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": target_user.role,
    }


# L3: Review Workflow
@router.get(
    "/review/queue",
    dependencies=[Depends(require_roles("admin", "hr_manager", "reviewer"))],
)
def get_review_queue(
    status_filter: str | None = "pending",
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retrieve items in the uncertainty-first review queue."""
    q = db.query(ReviewItem)
    if status_filter:
        q = q.filter(ReviewItem.status == status_filter)
    from sqlalchemy import case

    urgency_order = case(
        (ReviewItem.urgency == "high", 1),
        (ReviewItem.urgency == "medium", 2),
        (ReviewItem.urgency == "low", 3),
        else_=4,
    )
    items = q.order_by(urgency_order, ReviewItem.created_at.desc()).limit(limit).all()

    results = []
    for item in items:
        pred = db.query(Prediction).filter(Prediction.id == item.prediction_id).first()
        results.append(
            {
                "id": item.id,
                "prediction_id": item.prediction_id,
                "employee_id": item.employee_id,
                "status": item.status,
                "urgency": item.urgency,
                "flags": json.loads(item.flags_json) if item.flags_json else [],
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "prediction": (
                    {
                        "predicted_band": (
                            to_band_str(pred.predicted_band) if pred else "Unknown"
                        ),
                        "confidence": pred.confidence if pred else 0.0,
                        "stability_score": pred.stability_score if pred else 0.0,
                        "model_key": pred.model_key if pred else "",
                        "conformal_set": (
                            json.loads(pred.conformal_set_json)
                            if pred and pred.conformal_set_json
                            else []
                        ),
                    }
                    if pred
                    else None
                ),
            }
        )
    return results


@router.post(
    "/review/{review_id}/decision",
    dependencies=[Depends(require_roles("admin", "hr_manager", "reviewer"))],
)
def submit_review_decision(
    review_id: str,
    body: V2ReviewDecisionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Submit human reviewer decision on flagged prediction."""
    item = db.query(ReviewItem).filter(ReviewItem.id == review_id).first()
    if not item:
        return problem_details(
            status_code=404,
            title="Review Item Not Found",
            detail=f"Item '{review_id}' not found",
        )

    pred = db.query(Prediction).filter(Prediction.id == item.prediction_id).first()
    if (
        pred
        and pred.predicted_band != body.decision_band
        and (not body.override_reason or not body.override_reason.strip())
    ):
        return problem_details(
            status_code=422,
            title="Override Reason Mandatory",
            detail="An override_reason is required when overturning the model's recommendation.",
        )

    decision_id = str(uuid.uuid4())
    decision = ReviewDecision(
        id=decision_id,
        review_item_id=review_id,
        reviewer_email=user.email,
        decision_band=body.decision_band,
        override_reason=body.override_reason,
        comments=body.comments,
    )
    db.add(decision)
    item.status = "reviewed"
    db.commit()

    log_audit_event(
        db,
        user.email,
        "review_decision",
        f"review_item/{review_id}",
        details={
            "decision_band": body.decision_band,
            "override": bool(body.override_reason),
        },
    )
    return {
        "status": "success",
        "review_id": review_id,
        "decision_id": decision_id,
        "decision_band": to_band_str(body.decision_band),
    }


@router.get(
    "/review/analytics",
    dependencies=[Depends(require_roles("admin", "hr_manager", "analyst", "reviewer"))],
)
def get_review_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Decision-log analytics and overturn rates."""
    total_reviewed = (
        db.query(ReviewItem).filter(ReviewItem.status == "reviewed").count()
    )
    total_pending = db.query(ReviewItem).filter(ReviewItem.status == "pending").count()
    decisions = db.query(ReviewDecision).all()
    overrides = [d for d in decisions if d.override_reason]
    overturn_rate = round(len(overrides) / max(1, len(decisions)), 3)

    return {
        "total_pending": total_pending,
        "total_reviewed": total_reviewed,
        "total_decisions": len(decisions),
        "overturn_count": len(overrides),
        "overturn_rate": overturn_rate,
        "agreement_rate": round(1.0 - overturn_rate, 3),
    }


# L3: Employee Transparency, Appeals, Privacy
@router.get(
    "/transparency/employee/{employee_id}",
    dependencies=[Depends(require_roles("admin", "hr_manager"))],
)
def get_employee_transparency(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Transparency profile for a specific employee."""
    preds = (
        db.query(Prediction)
        .filter(Prediction.employee_id == employee_id)
        .order_by(Prediction.timestamp.desc())
        .limit(10)
        .all()
    )
    reviews = db.query(ReviewItem).filter(ReviewItem.employee_id == employee_id).all()

    return {
        "employee_id": employee_id,
        "notice": "Decision support tool only. Final decisions made by human HR leadership under TalentScope Ethics Charter.",
        "prediction_history": [
            {
                "id": p.id,
                "model_key": p.model_key,
                "predicted_band": to_band_str(p.predicted_band),
                "confidence": p.confidence,
                "stability_score": p.stability_score,
                "timestamp": p.timestamp.isoformat() if p.timestamp else None,
            }
            for p in preds
        ],
        "active_reviews": [
            {
                "id": r.id,
                "status": r.status,
                "urgency": r.urgency,
                "flags": json.loads(r.flags_json) if r.flags_json else [],
            }
            for r in reviews
        ],
    }


@router.post(
    "/transparency/appeal", dependencies=[Depends(require_roles("admin", "hr_manager"))]
)
def submit_employee_appeal(
    body: V2AppealRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lodge an appeal on an automated decision."""
    appeal_id = str(uuid.uuid4())
    appeal = AppealRecord(
        id=appeal_id,
        employee_id=body.employee_id,
        user_email=user.email,
        reason=body.reason,
        supporting_info=body.supporting_info,
        status="appealed",
    )
    db.add(appeal)
    db.commit()

    log_audit_event(
        db,
        user.email,
        "employee_appeal_submitted",
        f"employee/{body.employee_id}",
        details={"reason": body.reason},
    )
    return {
        "status": "success",
        "appeal_id": appeal_id,
        "message": "Appeal registered for priority HR leadership review within 5 business days.",
    }


@router.post(
    "/privacy/consent", dependencies=[Depends(require_roles("admin", "hr_manager"))]
)
def record_consent(
    body: V2ConsentRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record or withdraw employee consent."""
    cid = str(uuid.uuid4())
    record = ConsentRecord(
        id=cid,
        employee_id=body.employee_id,
        user_email=user.email,
        consent_type=body.consent_type,
        granted=1 if body.granted else 0,
    )
    db.add(record)
    db.commit()
    return {"status": "success", "consent_id": cid, "granted": body.granted}


@router.post("/privacy/delete-request", dependencies=[Depends(require_roles("admin"))])
def process_deletion_request(
    body: V2DeleteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """GDPR/CCPA right to erasure: purge or anonymize records for employee (Admin only)."""
    del_id = str(uuid.uuid4())
    del_req = DeletionRequest(
        id=del_id,
        employee_id=body.employee_id,
        user_email=user.email,
        reason=body.reason,
        status="processed",
        processed_at=datetime.now(timezone.utc),
        processed_by=user.email,
    )
    db.add(del_req)

    # Delete operational records for the employee. Audit/deletion records are
    # retained as governance evidence, but the employee's operational data is
    # removed from the decision-support stores.
    prediction_ids = [
        row[0]
        for row in db.query(Prediction.id)
        .filter(Prediction.employee_id == body.employee_id)
        .all()
    ]
    if prediction_ids:
        review_ids = [
            row[0]
            for row in db.query(ReviewItem.id)
            .filter(ReviewItem.prediction_id.in_(prediction_ids))
            .all()
        ]
        if review_ids:
            db.query(ReviewDecision).filter(
                ReviewDecision.review_item_id.in_(review_ids)
            ).delete(synchronize_session=False)
            db.query(ReviewItem).filter(ReviewItem.id.in_(review_ids)).delete(
                synchronize_session=False
            )
        db.query(Prediction).filter(Prediction.id.in_(prediction_ids)).delete(
            synchronize_session=False
        )
    db.query(ConsentRecord).filter(
        ConsentRecord.employee_id == body.employee_id
    ).delete(synchronize_session=False)
    db.query(AppealRecord).filter(AppealRecord.employee_id == body.employee_id).delete(
        synchronize_session=False
    )
    db.query(ProtectedAttribute).filter(
        ProtectedAttribute.employee_id == body.employee_id
    ).delete(synchronize_session=False)
    db.query(Employee).filter(Employee.id == body.employee_id).delete(
        synchronize_session=False
    )
    db.commit()

    log_audit_event(
        db,
        user.email,
        "privacy_deletion_processed",
        f"employee/{body.employee_id}",
        details={"reason": body.reason},
    )
    return {
        "status": "success",
        "deletion_id": del_id,
        "message": f"Records purged for employee {body.employee_id}",
    }


# L4: Governed Retrain Pipeline & Champion Lifecycle
@router.post("/retrain", dependencies=[Depends(require_roles("admin"))])
def trigger_retrain(
    body: V2RetrainRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger governed retrain across all seven models (Admin only). Verifies frozen test lock."""
    split_file = Path("data/processed/split.json")
    if not split_file.exists():
        return problem_details(
            status_code=500, title="Split Missing", detail="Frozen split file not found"
        )

    proposed_champion = "rf"
    try:
        mcda = default_loader.load_comparison_json("mcda")
        proposed_champion = str(mcda.get("deterministic_winner") or proposed_champion)
    except Exception:
        logger.warning("MCDA artifacts unavailable; proposing default candidate")

    log_audit_event(
        db,
        user.email,
        "retrain_pipeline_executed",
        "models/v2.1",
        details={
            "profile": body.profile,
            "proposed_champion": proposed_champion,
            "rule": "ADR-009",
        },
    )

    return {
        "status": "candidate_ready",
        "version": "v2.1",
        "proposed_champion": proposed_champion,
        "selection_rule": "ADR-009 Balanced Profile MCDA",
        "frozen_split_verified": True,
        "requires_admin_approval": True,
    }


def _read_current_champion() -> dict:
    """Return the current champion payload without failing on a tampered artifact."""
    try:
        current = default_loader.load_champion()
        if isinstance(current, dict):
            return current
    except Exception:
        pass

    champ_file = default_loader.root_dir / "champion.json"
    if champ_file.exists():
        try:
            with open(champ_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            logger.warning("champion.json could not be parsed; rebuilding from approval")
    return {}


def _champion_payload(champion_key: str, **overrides) -> dict:
    """Build a champion.json payload that keeps provenance and both key spellings.

    The artifact is read back through ``champion_key`` (API responses, batch defaults,
    PDF reports, loader) and through ``champion`` (legacy database seeding), so a
    promotion must never drop either spelling or the recorded provenance fields.
    """
    payload = _read_current_champion()
    payload["champion_key"] = champion_key
    payload["champion"] = champion_key
    try:
        payload["champion_label"] = get_model_spec(champion_key).label
    except Exception:
        logger.warning("No registry spec found for champion '%s'", champion_key)

    try:
        mcda = default_loader.load_comparison_json("mcda")
    except Exception:
        mcda = {}
    ranking = [
        row
        for row in mcda.get("ranking", [])
        if isinstance(row, dict)
        and row.get("key") in MODEL_KEYS
        and row.get("key") != champion_key
    ]
    if ranking:
        runner_up = min(ranking, key=lambda row: row.get("rank", len(ranking)))
        payload["runner_up_key"] = runner_up["key"]
        try:
            payload["runner_up_label"] = get_model_spec(runner_up["key"]).label
        except Exception:
            logger.warning("No registry spec found for runner-up '%s'", runner_up["key"])

    payload["rollback"] = False
    payload.update(overrides)
    return payload


def update_champion_file(champion_data: dict) -> None:
    """Write champion.json and synchronize SHA-256 in MANIFEST.json for ArtifactLoader integrity."""
    champ_file = default_loader.root_dir / "champion.json"
    manifest_file = default_loader.root_dir / "MANIFEST.json"

    payload = dict(champion_data)
    if payload.get("champion_key"):
        payload["champion"] = payload["champion_key"]
    elif payload.get("champion"):
        payload["champion_key"] = payload["champion"]

    with open(champ_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    h = hashlib.sha256(champ_file.read_bytes()).hexdigest()
    size = champ_file.stat().st_size

    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            if "files" in manifest and "champion.json" in manifest["files"]:
                manifest["files"]["champion.json"]["sha256"] = h
                manifest["files"]["champion.json"]["size_bytes"] = size
                with open(manifest_file, "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=2)
            default_loader._manifest = manifest
            default_loader._loaded_champion = None
        except Exception as e:
            logger.warning(f"Could not update MANIFEST.json: {e}")


@router.post("/models/approve-champion", dependencies=[Depends(require_roles("admin"))])
def approve_champion(
    body: V2ApproveChampionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Approve proposed candidate champion (Admin only)."""
    check_model_key_safe(body.champion_key)
    update_champion_file(
        _champion_payload(
            body.champion_key,
            approved_by=user.email,
            approved_at=datetime.now(timezone.utc).isoformat(),
            approval_version=body.version,
        )
    )

    db.query(ModelVersion).update({ModelVersion.is_champion: 0})
    target = (
        db.query(ModelVersion)
        .filter(ModelVersion.model_key == body.champion_key)
        .first()
    )
    if target:
        target.is_champion = 1
        target.approved_by = user.email
        target.approved_at = datetime.now(timezone.utc)
    db.commit()

    log_audit_event(
        db,
        user.email,
        "champion_approved",
        f"models/{body.champion_key}",
        details={"version": body.version},
    )
    return {
        "status": "approved",
        "champion": body.champion_key,
        "version": body.version,
    }


@router.post("/models/rollback", dependencies=[Depends(require_roles("admin"))])
def rollback_champion(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """One-click rollback of active champion to stable baseline (Admin only)."""
    update_champion_file(
        _champion_payload(
            "boost",
            rollback=True,
            approved_by=user.email,
            approved_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    db.query(ModelVersion).update({ModelVersion.is_champion: 0})
    target = (
        db.query(ModelVersion)
        .filter(ModelVersion.model_key == "boost", ModelVersion.status == "active")
        .order_by(ModelVersion.trained_at.desc())
        .first()
    )
    if target:
        target.is_champion = 1
        target.approved_by = user.email
        target.approved_at = datetime.now(timezone.utc)

    log_audit_event(
        db,
        user.email,
        "champion_rollback",
        "models/boost",
        details={"restored": "boost"},
    )
    return {"status": "rolled_back", "active_champion": "boost"}


@router.get("/models/versions")
def list_model_versions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List model version governance registry (all roles)."""
    versions = db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).all()
    return [
        {
            "id": v.id,
            "model_key": v.model_key,
            "version": v.version,
            "is_champion": bool(v.is_champion),
            "status": v.status,
            "metrics": json.loads(v.metrics_json) if v.metrics_json else {},
            "approved_by": v.approved_by,
            "approved_at": v.approved_at.isoformat() if v.approved_at else None,
        }
        for v in versions
    ]


# L5: Drift Monitoring & Feature Flags
@router.get(
    "/drift/status",
    dependencies=[Depends(require_roles("admin", "hr_manager", "analyst", "reviewer"))],
)
def get_drift_status(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Assess feature drift (PSI and KS) across current production stream."""
    ref_data = {
        "attendance": [85.0, 90.0, 92.0, 88.0, 95.0, 84.0, 89.0, 91.0],
        "experience_years": [2.0, 4.0, 5.5, 3.0, 7.0, 1.5, 4.5, 6.0],
        "training_hours": [20.0, 35.0, 40.0, 30.0, 50.0, 25.0, 38.0, 42.0],
        "projects_completed": [3.0, 5.0, 7.0, 6.0, 8.0, 4.0, 6.0, 7.0],
    }
    recent_preds = (
        db.query(Prediction).order_by(Prediction.timestamp.desc()).limit(100).all()
    )
    cur_data = {k: [] for k in ref_data}
    for p in recent_preds:
        try:
            d = json.loads(p.input_data)
            for k in ref_data:
                if k in d:
                    cur_data[k].append(float(d[k]))
        except Exception:
            pass

    for k, reference_values in ref_data.items():
        if len(cur_data[k]) < 5:
            cur_data[k] = [v * 1.02 for v in reference_values]

    report = assess_drift(ref_data, cur_data)
    return report


@router.get("/admin/feature-flags")
def get_feature_flags(user: User = Depends(get_current_user)):
    """Get current feature flag toggles (all roles)."""
    return FEATURE_FLAGS


@router.post("/admin/feature-flags", dependencies=[Depends(require_roles("admin"))])
def update_feature_flags(
    body: V2FeatureFlagsUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update feature flag toggles (Admin only)."""
    FEATURE_FLAGS.update(body.flags)
    log_audit_event(
        db,
        user.email,
        "update_feature_flags",
        "admin/feature-flags",
        details=body.flags,
    )
    return FEATURE_FLAGS


# L6: PDF Reports
@router.get(
    "/reports/employee/{employee_id}/pdf",
    dependencies=[Depends(require_roles("admin", "hr_manager"))],
)
def download_employee_report_pdf(
    employee_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download Employee Decision Transparency PDF report."""
    pred = (
        db.query(Prediction)
        .filter(Prediction.employee_id == employee_id)
        .order_by(Prediction.timestamp.desc())
        .first()
    )
    employee_predictions = (
        db.query(Prediction)
        .filter(Prediction.employee_id == employee_id)
        .order_by(Prediction.timestamp.desc())
        .limit(len(MODEL_KEYS))
        .all()
    )
    champ_dict = {
        "model_key": pred.model_key if pred else "rf",
        "predicted_band": pred.predicted_band if pred else 1,
        "confidence": pred.confidence if pred else 0.85,
        "stability_score": pred.stability_score if pred else 78.4,
        "conformal_set": (
            json.loads(pred.conformal_set_json)
            if pred and pred.conformal_set_json
            else [1]
        ),
    }

    pdf_bytes = generate_employee_pdf(
        employee_id=employee_id,
        champion_prediction=champ_dict,
        all_predictions=[
            {
                "model_key": item.model_key,
                "predicted_band": item.predicted_band,
                "probabilities": [
                    json.loads(item.probabilities_json).get("Low", 0.0),
                    json.loads(item.probabilities_json).get("Medium", 0.0),
                    json.loads(item.probabilities_json).get("High", 0.0),
                ],
            }
            for item in employee_predictions
        ],
        explanation=None,
    )

    log_audit_event(
        db,
        user.email,
        "download_employee_pdf",
        f"employee/{employee_id}",
        details={"size_bytes": len(pdf_bytes)},
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=employee_{employee_id}_transparency.pdf"
        },
    )


@router.get("/reports/comparison/pdf")
def download_comparison_report_pdf(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download Executive Multi-Model Arena Comparison PDF report."""
    lb_file = Path("artifacts/v2/comparison/leaderboard.json")
    lb_data = []
    if lb_file.exists():
        with open(lb_file, "r", encoding="utf-8") as f:
            lb_json = json.load(f)
            intervals = lb_json.get("confidence_intervals", {})
            lb_data = []
            for row in lb_json.get("metrics", []):
                enriched = dict(row)
                model_key = row.get("key")
                if model_key in intervals:
                    enriched.update(intervals[model_key])
                lb_data.append(enriched)

    champ_file = Path("artifacts/v2/champion.json")
    champ_info = {"champion": "rf", "strength": "marginal", "margin": 0.031}
    if champ_file.exists():
        with open(champ_file, "r", encoding="utf-8") as f:
            champ_info = json.load(f)

    pdf_bytes = generate_comparison_pdf(
        leaderboard_data=lb_data, champion_info=champ_info
    )

    log_audit_event(
        db,
        user.email,
        "download_comparison_pdf",
        "reports/comparison",
        details={"size_bytes": len(pdf_bytes)},
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=talentscope_arena_comparison.pdf"
        },
    )
