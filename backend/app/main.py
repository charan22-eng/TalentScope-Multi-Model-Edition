import json
import logging
import time
import uuid
from typing import List

import pandas as pd
import numpy as np
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import joblib

from .schemas import EmployeeFeatures, PredictResponse, ExplainResponse, BatchPredictResponse
from .config import settings
from backend.db.database import get_db, engine, Base
from backend.db.models import User, PredictionHistory
from backend.core.security import authenticate_user, create_access_token, get_current_user_email, get_password_hash
from backend.services.drift import get_current_drift
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import Response
import io
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

Base.metadata.create_all(bind=engine)

# Wait, we need the epk package for predictions. 
# We'll import dynamically or just rely on standard joblib and the pre-loaded python path.
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../ml/src'))
from epk.loader import load_artifact
from epk.uncertainty import get_prediction_set, stability_score
from epk.explain import explain, local_attribution, counterfactual, summarise
from epk.labels import INT_TO_BAND

def to_band_str(c):
    return INT_TO_BAND.get(c, str(c)) if isinstance(c, (int, np.integer)) else str(c)

logger = logging.getLogger("talentscope")
logger.setLevel(logging.INFO)

limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = FastAPI(title=settings.api_name, version=settings.api_version)
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    origins = settings.cors_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def struct_logger_and_size_limit(request: Request, call_next):
        req_id = str(uuid.uuid4())
        request.state.req_id = req_id
        
        # Check size limit
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > settings.request_size_limit:
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
            
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(json.dumps({
            "req_id": req_id,
            "method": request.method,
            "url": str(request.url),
            "status": response.status_code,
            "process_time_ms": round(process_time * 1000, 2)
        }))
        return response

    # Exception handler for Problem Details format
    from fastapi.exceptions import RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"type": "about:blank", "title": "Validation Error", "status": 422, "detail": details},
        )

    # Load Model State
    try:
        with open(f"{settings.artifact_path}/metadata.json", "r") as f:
            metadata = json.load(f)
        
        calibrated_knn = load_artifact("calibrated_knn.pkl", settings.artifact_path, expected_hash=metadata["hashes"]["calibrated_knn.pkl"])
        pipe = load_artifact("pipeline.pkl", settings.artifact_path, expected_hash=metadata["hashes"]["pipeline.pkl"])
        
        with open(f"{settings.artifact_path}/conformal.json", "r") as f:
            conformal = json.load(f)
        
        train_df = pd.read_csv("data/raw/dataset.csv").drop_duplicates(subset=["employee_id"])
        X_train = train_df.drop(columns=["performance"])
        y_train = train_df["performance"]
        
        pca2 = joblib.load(f"{settings.artifact_path}/assets/pca2d.joblib")
        pca3 = joblib.load(f"{settings.artifact_path}/assets/pca3d.joblib")
        
    except Exception as e:
        logger.warning(f"v1 artifacts loading error ({e}), falling back to v2 KNN model")
        try:
            from epk.artifacts import default_loader
            calibrated_knn = default_loader.load_model("knn")
            pipe = calibrated_knn
            conformal = {"threshold": 0.85}
            train_df = pd.read_csv("data/raw/dataset.csv")
            if "employee_id" in train_df.columns:
                train_df = train_df.drop_duplicates(subset=["employee_id"])
            X_train = train_df.drop(columns=["performance", "performance_score"], errors="ignore")
            y_train = train_df["performance"] if "performance" in train_df.columns else pd.Series(["Medium"] * len(train_df))
            metadata = {"version": "v2.0 (KNN Fallback)"}
            pca2, pca3 = None, None
        except Exception as e2:
            logger.error(f"Failed to load fallback v2 model: {e2}")
            metadata, calibrated_knn, pipe, conformal, X_train, y_train, pca2, pca3 = {}, None, None, {}, None, None, None, None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def readiness(db: Session = Depends(get_db)):
        from sqlalchemy import text
        from epk.artifacts import default_loader
        db_status = "connected"
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unavailable"

        champ_status = "available" if (default_loader.root_dir / "champion.json").exists() else "missing"
        is_ready = (db_status == "connected" and champ_status == "available")
        return {
            "status": "ready" if is_ready else "not_ready",
            "database": db_status,
            "artifacts": champ_status,
        }

    @app.get("/version")
    def version():
        return {"api_version": settings.api_version, "model_version": metadata.get("version", "unknown")}

    @app.post("/login")
    def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        access_token = create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}

    @app.post("/predict", response_model=PredictResponse)
    @limiter.limit("50/minute")
    async def predict(request: Request, features: EmployeeFeatures, db: Session = Depends(get_db), current_user: str = Depends(get_current_user_email)):
        df = pd.DataFrame([features.model_dump()])
        probs = calibrated_knn.predict_proba(df)[0]
        classes = list(calibrated_knn.classes_)
        classes_str = [to_band_str(c) for c in classes]
        
        raw_pset = get_prediction_set(probs, classes, conformal.get("threshold", 0.8))
        pset = [to_band_str(c) for c in raw_pset]
        conf_dict = {c: float(p) for c, p in zip(classes_str, probs)}
        
        
        # Save to history
        hist = PredictionHistory(
            user_email=current_user,
            input_data=features.model_dump_json(),
            prediction=pset[0] if pset else "Unknown",
            confidence=float(max(probs)),
            needs_review=1 if (stability_score(probs) * 100.0 < 70) else 0
        )
        db.add(hist)
        db.commit()

        return PredictResponse(
            prediction=pset,
            confidence=float(max(probs)),
            probabilities=conf_dict,
            stability_index=stability_score(probs) * 100.0
        )

    @app.get("/analytics/drift")
    def drift_report(db: Session = Depends(get_db)):
        history = db.query(PredictionHistory).order_by(PredictionHistory.timestamp.desc()).limit(1000).all()
        drift_result = get_current_drift(history, {})
        return drift_result

    @app.post("/explain", response_model=ExplainResponse)
    @limiter.limit("20/minute")
    async def explain_pred(request: Request, features: EmployeeFeatures, k: int = 5):
        df = pd.DataFrame([features.model_dump()])
        probs = calibrated_knn.predict_proba(df)[0]
        classes = list(calibrated_knn.classes_)
        classes_str = [to_band_str(c) for c in classes]
        raw_pset = get_prediction_set(probs, classes, conformal.get("threshold", 0.8))
        pset = [to_band_str(c) for c in raw_pset]
        
        nb_df, votes = explain(pipe, X_train, y_train, df)
        nb_df = nb_df.head(k)
        
        # Calculate local attribution using training medians
        train_medians = X_train.select_dtypes(include=[np.number]).median()
        attrib = local_attribution(pipe, df, train_medians)
        pred_class = classes_str[int(np.argmax(probs))]
        
        cfs = counterfactual(pipe, df)
        path = [str(opt.get("description", "Intervention")) for opt in cfs] if isinstance(cfs, list) else []
        
        prediction_data = {
            "label": pred_class,
            "confidence": float(max(probs)),
            "votes": votes,
            "attribution": attrib,
            "neighbours": nb_df
        }
        
        return ExplainResponse(
            prediction=pset,
            confidence=float(max(probs)),
            neighbors=nb_df.to_dict(orient="records"),
            votes=votes,
            summary=summarise(prediction_data),
            attribution=attrib,
            counterfactual_path=path
        )

    @app.post("/batch")
    @limiter.limit("5/minute")
    async def batch(request: Request, file: UploadFile = File(...)):
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files allowed")
        
        # Abuse checks
        content = await file.read()
        if len(content) > settings.request_size_limit:
            raise HTTPException(status_code=413, detail="File too large")
            
        import io
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid encoding")
            
        # check formula injection
        for line in text.splitlines():
            if line.strip().startswith(("=", "+", "-", "@")):
                raise HTTPException(status_code=400, detail="Formula injection detected")
                
        df = pd.read_csv(io.StringIO(text))
        
        t0 = time.time()
        results = []
        errors = []
        for i, row in df.iterrows():
            try:
                feat = EmployeeFeatures(**row.to_dict())
                r_df = pd.DataFrame([feat.model_dump()])
                probs = calibrated_knn.predict_proba(r_df)[0]
                classes = list(calibrated_knn.classes_)
                classes_str = [to_band_str(c) for c in classes]
                raw_pset = get_prediction_set(probs, classes, conformal.get("threshold", 0.8))
                pset = [to_band_str(c) for c in raw_pset]
                conf_dict = {c: float(p) for c, p in zip(classes_str, probs)}
                
                results.append(PredictResponse(
                    prediction=pset,
                    confidence=float(max(probs)),
                    probabilities=conf_dict,
                    stability_index=stability_score(probs) * 100.0
                ))
                errors.append(None)
            except Exception as e:
                results.append(None)
                errors.append({"row": i, "error": str(e)})
                
        t1 = time.time()
        
        return {"results": results, "errors": errors, "latency_ms": (t1-t0)*1000}

    @app.get("/batch/report/pdf")
    def export_pdf_report(db: Session = Depends(get_db)):
        if not HAS_REPORTLAB:
            return Response(content="ReportLab not installed", media_type="text/plain")
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "TalentScope Batch Prediction Report")
        c.drawString(100, 730, "=================================")
        
        history = db.query(PredictionHistory).order_by(PredictionHistory.timestamp.desc()).limit(10).all()
        y = 700
        for h in history:
            c.drawString(100, y, f"[{h.timestamp.strftime('%Y-%m-%d %H:%M')}] {h.user_email}: {h.prediction} ({h.confidence:.2f})")
            y -= 20
            if y < 100:
                c.showPage()
                y = 750
        
        c.save()
        pdf = buffer.getvalue()
        buffer.close()
        
        return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=report.pdf"})

    @app.get("/viz/galaxy")
    def galaxy():
        bkg = pd.read_csv(f"{settings.artifact_path}/assets/background_sample.csv")
        return bkg.to_dict(orient="records")

    @app.get("/viz/surface")
    def surface(size: int = 40):
        if size > 80:
            raise HTTPException(status_code=400, detail="Grid size too large")
        return {"status": "stubbed"}

    @app.get("/analytics")
    def analytics():
        return {"status": "stubbed"}
        
    @app.get("/analytics/constellation")
    def constellation():
        return {"status": "stubbed"}
        
    @app.get("/drift/projection")
    def drift():
        return {"status": "stubbed"}

    from backend.app.api_v2 import router as v2_router
    app.include_router(v2_router)

    return app

app = create_app()
