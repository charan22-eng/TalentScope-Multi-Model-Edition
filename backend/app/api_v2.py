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

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.core.security import get_current_user, require_roles
from backend.db.database import get_db
from backend.db.models import LLMVerdict, User
from .schemas import (
    EmployeeFeatures,
    ProblemDetails,
    V2ExplainRequest,
    V2ExplainResponse,
    V2LLMConfigUpdateRequest,
    V2LLMVerdictRequest,
    V2MCDARequest,
    V2PredictAllResponse,
    V2PredictRequest,
    V2PredictResponse,
)

from epk.artifacts import default_loader, ModelKeyError
from epk.explain import (
    compute_performance_index,
    compute_stability_score,
    explain_model_native,
    find_counterfactuals,
    find_similar_cases,
    generate_persona_summaries,
    local_attribution,
)
import hashlib
from epk.labels import BANDS, INT_TO_BAND
from epk.llm.cache import VerdictCache
from epk.llm.client import LocalLLM, assert_local
from epk.llm.fallback import generate_template_verdict
from epk.llm.prompts import (
    format_user_prompt,
    scan_prompt_for_forbidden_keys,
    SYSTEM_PROMPT,
)
from epk.llm.validator import validate_verdict
from epk.mcda import PROFILES, run_mcda_pipeline
from epk.models.registry import MODEL_KEYS, get_model_spec
from epk.uncertainty import get_prediction_set

logger = logging.getLogger("talentscope.v2")
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v2", tags=["v2"])

# Allowed comparison topics mapping to JSON files in artifacts/v2/comparison/
ALLOWED_COMPARISON_TOPICS: Dict[str, str] = {
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

# Runtime config for LLM
_LLM_CONFIG = {
    "provider": "ollama",
    "model": "qwen2.5:7b-instruct",
    "base_url": "http://localhost:11434",
}

# Cache for train background data and medians
_TRAIN_DATA: Optional[pd.DataFrame] = None
_TRAIN_LABELS: Optional[pd.Series] = None
_TRAIN_MEDIANS: Optional[pd.Series] = None


def get_train_context():
    """Load train split features and medians once for fast local explainability."""
    global _TRAIN_DATA, _TRAIN_LABELS, _TRAIN_MEDIANS
    if _TRAIN_DATA is None:
        try:
            data_file = default_loader.root_dir.parent.parent / "data" / "processed" / "train.csv"
            if data_file.exists():
                df = pd.read_csv(data_file)
                _TRAIN_DATA = df.drop(columns=["performance"], errors="ignore")
                _TRAIN_LABELS = df["performance"] if "performance" in df.columns else pd.Series(["Medium"] * len(df))
            else:
                # Fallback to background sample in pca.json
                pca_meta = default_loader.root_dir / "explainability" / "pca.json"
                if pca_meta.exists():
                    with open(pca_meta, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    pts = meta.get("background_points", [])
                    _TRAIN_DATA = pd.DataFrame(pts)
                    _TRAIN_LABELS = pd.Series([p.get("band", "Medium") for p in pts])
        except Exception as e:
            logger.warning(f"Could not load train dataset for explainability: {e}")
            _TRAIN_DATA = pd.DataFrame()
            _TRAIN_LABELS = pd.Series()

        if _TRAIN_DATA is not None and not _TRAIN_DATA.empty:
            _TRAIN_MEDIANS = _TRAIN_DATA.select_dtypes(include=[np.number]).median()
        else:
            _TRAIN_MEDIANS = pd.Series({
                "attendance": 88.0,
                "experience_years": 4.0,
                "training_hours": 35.0,
                "projects_completed": 6.0,
                "weekly_hours": 40.0,
                "peer_feedback": 3.6,
                "tasks_on_time_pct": 82.0,
                "certifications": 1.0,
            })
    return _TRAIN_DATA, _TRAIN_LABELS, _TRAIN_MEDIANS


def to_band_str(c: Any) -> str:
    """Map integer class or numeric code to band string."""
    return INT_TO_BAND.get(c, str(c)) if isinstance(c, (int, np.integer)) else str(c)


def problem_details(status_code: int, title: str, detail: Any, instance: Optional[str] = None) -> JSONResponse:
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
            detail=f"Unknown model key '{model_key}'. Allowed models: {sorted(list(MODEL_KEYS))}",
        )


def run_single_model_predict(model_key: str, features_dict: Dict[str, Any]) -> V2PredictResponse:
    """Internal helper to predict for a single model key."""
    check_model_key_safe(model_key)
    model = default_loader.load_model(model_key)
    meta = default_loader.load_model_metadata(model_key)

    df = pd.DataFrame([features_dict])
    probs = model.predict_proba(df)[0]
    classes = list(model.classes_)
    classes_str = [to_band_str(c) for c in classes]

    # Conformal set
    alpha_threshold = meta.get("conformal_threshold", 0.10)
    # Using conformal prediction set threshold from conformal.json or metadata
    try:
        conf_data = default_loader.load_comparison_json("conformal")
        threshold = conf_data.get("models", {}).get(model_key, {}).get("threshold", 0.05)
    except Exception:
        threshold = 0.05

    raw_pset = get_prediction_set(probs, classes, threshold)
    pset = [to_band_str(c) for c in raw_pset]

    best_idx = int(np.argmax(probs))
    best_band = classes_str[best_idx]
    best_conf = float(probs[best_idx])
    prob_dict = {c: float(p) for c, p in zip(classes_str, probs)}

    stab = compute_stability_score(probs)
    perf_idx = compute_performance_index(model, df, model_key)

    return V2PredictResponse(
        model_key=model_key,
        predicted_band=best_band,
        confidence=best_conf,
        prediction_set=pset,
        probabilities=prob_dict,
        stability_score=stab,
        performance_index=perf_idx,
    )


# ==============================================================================
# Model Registry & Predictions
# ==============================================================================

@router.get("/models")
def list_models():
    """List all seven models with their specs, metadata, and test metrics (all roles)."""
    manifest = default_loader.manifest.get("files", {})
    champion_data = default_loader.load_champion()
    out = []
    for key in sorted(list(MODEL_KEYS)):
        spec = get_model_spec(key)
        try:
            meta = default_loader.load_model_metadata(key)
        except Exception:
            meta = {}

        model_rel = f"models/{key}/model.joblib"
        file_sha256 = manifest.get(model_rel, {}).get("sha256", "unknown")

        out.append({
            "key": key,
            "label": spec.label,
            "family": spec.family,
            "explain_tier": spec.explain_tier,
            "is_champion": (key == champion_data.get("champion_key", "rf")),
            "test_macro_f1": meta.get("test_macro_f1"),
            "test_accuracy": meta.get("test_accuracy"),
            "latency_p95_ms": meta.get("latency_p95_ms"),
            "sha256": file_sha256,
        })
    return out


@router.post("/predict", response_model=V2PredictResponse)
@limiter.limit("60/minute")
async def predict_single(request: Request, body: V2PredictRequest):
    """Predict performance band using a specific whitelisted model (all roles)."""
    key = body.model_key or "rf"
    check_model_key_safe(key)
    return run_single_model_predict(key, body.features.model_dump())


@router.post("/predict/all", response_model=V2PredictAllResponse)
@limiter.limit("30/minute")
async def predict_all(request: Request, features: EmployeeFeatures):
    """Run inference across all seven models, returning consensus and split-decision flags.
    
    Performance requirement: p95 latency under 800ms.
    """
    t0 = time.time()
    feat_dict = features.model_dump()
    predictions: Dict[str, V2PredictResponse] = {}
    top_bands: List[str] = []

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


# ==============================================================================
# Explainability
# ==============================================================================

@router.post("/explain", response_model=V2ExplainResponse)
@limiter.limit("30/minute")
async def explain_model(request: Request, body: V2ExplainRequest):
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

    # 5. Persona summaries
    stab = compute_stability_score(probs)
    summaries = generate_persona_summaries(
        key=key,
        label=spec.label,
        pred_band=best_band,
        proba=probs.tolist(),
        attribution=attrib,
        counterfactuals=cfs,
        stability=stab,
    )

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
    )


# ==============================================================================
# Comparison Science & MCDA
# ==============================================================================

@router.get("/compare/{topic}")
def get_comparison_data(topic: str):
    """Retrieve precomputed model comparison science JSON (all roles)."""
    if topic not in ALLOWED_COMPARISON_TOPICS:
        return problem_details(
            status_code=404,
            title="Comparison Topic Not Found",
            detail=f"Topic '{topic}' is not valid. Allowed topics: {sorted(list(ALLOWED_COMPARISON_TOPICS.keys()))}",
        )

    json_name = ALLOWED_COMPARISON_TOPICS[topic]
    try:
        data = default_loader.load_comparison_json(json_name)
        return data
    except Exception as e:
        return problem_details(
            status_code=500,
            title="Artifact Read Error",
            detail=f"Could not load comparison data for '{topic}': {str(e)}",
        )


@router.post("/compare/mcda")
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
                "calibration": float(1.0 - m.get("ece", 0.05)),
                "robustness": 0.85,
                "fairness": 0.85,
                "stability": float(m.get("stability_score", 0.6)),
                "latency": float(m.get("latency_p95_ms", 10.0)),
                "train_cost": 2.0,
                "explainability": 0.9 if m_key in ("dt", "linreg", "logreg") else (0.8 if m_key == "knn" else 0.5),
            }
        table = pd.DataFrame.from_dict(rows, orient="index")

        result = run_mcda_pipeline(table, profile_name="Custom", custom_weights=weights)
        return result
    except Exception as e:
        return problem_details(
            status_code=500,
            title="MCDA Computation Failed",
            detail=str(e),
        )


# ==============================================================================
# 2D/3D Visualizations
# ==============================================================================

@router.get("/viz/surface")
@router.post("/viz/surface")
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


@router.get("/viz/pca")
def get_pca_projection():
    """Retrieve PCA 2D/3D projection coordinates and background sample (all roles)."""
    pca_path = default_loader.root_dir / "explainability" / "pca.json"
    if pca_path.exists():
        with open(pca_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return problem_details(status_code=404, title="PCA Data Not Found", detail="PCA artifact not available")


# ==============================================================================
# Local LLM Verdict Engine
# ==============================================================================

@router.get("/llm/health", dependencies=[Depends(require_roles("admin", "analyst"))])
def llm_health():
    """Check local LLM runtime health (Admin, Analyst)."""
    try:
        llm = LocalLLM(provider=_LLM_CONFIG["provider"], base_url=_LLM_CONFIG["base_url"], timeout=2.0)
        models = llm.list_models()
        return {"status": "healthy" if models else "reachable", "runtime": _LLM_CONFIG["provider"], "models_available": models}
    except Exception as e:
        return {
            "status": "offline",
            "runtime": _LLM_CONFIG["provider"],
            "base_url": _LLM_CONFIG["base_url"],
            "detail": f"Local runtime not reachable: {str(e)}",
            "fallback_available": True,
        }


@router.get("/llm/models", dependencies=[Depends(require_roles("admin", "analyst"))])
def list_llm_models():
    """List local models available in Ollama/vLLM (Admin, Analyst)."""
    try:
        llm = LocalLLM(provider=_LLM_CONFIG["provider"], base_url=_LLM_CONFIG["base_url"], timeout=5.0)
        models = llm.list_models()
        return {"models": models}
    except Exception as e:
        return problem_details(
            status_code=503,
            title="LLM Service Unavailable",
            detail=f"Could not connect to local runtime at {_LLM_CONFIG['base_url']}: {str(e)}",
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
                detail=f"Refused non-local URL: {str(e)}",
            )
        _LLM_CONFIG["base_url"] = body.base_url

    if body.provider:
        _LLM_CONFIG["provider"] = body.provider
    if body.model:
        _LLM_CONFIG["model"] = body.model

    return {"status": "updated", "config": _LLM_CONFIG}


@router.post("/llm/verdict", dependencies=[Depends(require_roles("admin", "hr", "analyst"))])
@limiter.limit("15/minute")
async def generate_verdict(
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
    # 1. Load evidence packet
    if body.evidence_packet:
        packet = body.evidence_packet
    else:
        packet = default_loader.load_comparison_json("evidence_packet")

    # 2. Check for employee leakage
    violations = scan_prompt_for_forbidden_keys(json.dumps(packet))
    if violations:
        return problem_details(
            status_code=400,
            title="Privacy Guard Violation (G9)",
            detail=f"Forbidden employee identifiers found in evidence: {violations}",
        )

    prompt = format_user_prompt(packet, audience=body.audience or "HR")
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
        audience=body.audience or "HR",
        mode=body.mode or "verdict",
        profile_name="Balanced",
    )
    cached = cache.get(cache_key)
    if cached:
        return {
            "verdict": cached.get("output", cached),
            "source": "cache",
            "is_fallback": bool(cached.get("source") == "fallback"),
            "validation": {"valid": True, "errors": []},
        }

    # 4. Attempt local LLM call
    llm_error = None
    try:
        llm = LocalLLM(
            provider=_LLM_CONFIG["provider"],
            base_url=_LLM_CONFIG["base_url"],
            model=_LLM_CONFIG["model"],
            timeout=10.0,
        )
        raw_text = llm.chat_json(system=SYSTEM_PROMPT, user=prompt)
        verdict_obj = json.loads(raw_text)
        val_res = validate_verdict(verdict_obj, packet)
        if val_res.is_valid:
            cache.put(
                cache_key=cache_key,
                packet_hash=pkt_hash,
                prompt_version="1.0",
                model=_LLM_CONFIG["model"],
                audience=body.audience or "HR",
                mode=body.mode or "verdict",
                source="live_llm",
                output=verdict_obj,
                validation_history=val_res.errors,
            )
            # Persist in DB
            v_id = str(uuid.uuid4())
            db_record = LLMVerdict(
                id=v_id,
                user_email=user.email,
                mode=body.mode or "verdict",
                audience=body.audience or "HR",
                verdict_json=json.dumps(verdict_obj),
                is_valid=1,
                is_fallback=0,
                validation_json=json.dumps({"valid": True, "errors": []}),
            )
            db.add(db_record)
            db.commit()

            return {
                "id": v_id,
                "verdict": verdict_obj,
                "source": "live_llm",
                "is_fallback": False,
                "validation": {"valid": True, "errors": []},
            }
        else:
            llm_error = f"Validator rejected LLM response: {val_res.errors}"
    except Exception as e:
        llm_error = str(e)

    # 5. Handle fallback or return 503
    if body.allow_fallback:
        fallback_verdict = generate_template_verdict(packet, audience=body.audience or "HR")
        v_id = str(uuid.uuid4())
        db_record = LLMVerdict(
            id=v_id,
            user_email=user.email,
            mode=body.mode or "verdict",
            audience=body.audience or "HR",
            verdict_json=json.dumps(fallback_verdict),
            is_valid=1,
            is_fallback=1,
            validation_json=json.dumps({"valid": True, "note": f"Fallback due to: {llm_error}"}),
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
def get_stored_verdict(verdict_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Retrieve stored verdict by ID (owner or Admin)."""
    record = db.query(LLMVerdict).filter(LLMVerdict.id == verdict_id).first()
    if not record:
        return problem_details(status_code=404, title="Verdict Not Found", detail=f"Verdict '{verdict_id}' not found")

    # Authorization: user must own the record or be admin
    if record.user_email != user.email and (getattr(user, "role", "") or "").lower() != "admin":
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
        "validation": json.loads(record.validation_json) if record.validation_json else {},
    }
