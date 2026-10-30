import csv
import importlib.util
import io
import json
import logging
import time
import uuid
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from backend.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
    oauth2_scheme,
    require_roles,
    revoke_token,
)
from backend.db.database import Base, engine, get_db
from backend.db.models import PredictionHistory, User
from backend.services.drift import get_current_drift

from .config import settings
from .schemas import (
    EmployeeFeatures,
    ExplainResponse,
    PredictResponse,
)

HAS_REPORTLAB = importlib.util.find_spec("reportlab") is not None

Base.metadata.create_all(bind=engine)

# Import the ML package from the workspace source tree for the legacy routes.
import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../ml/src"))
from epk.artifacts import default_loader
from epk.explain import counterfactual, explain, local_attribution, summarise
from epk.labels import INT_TO_BAND
from epk.loader import load_artifact
from epk.uncertainty import get_prediction_set, stability_score


def to_band_str(c):
    return INT_TO_BAND.get(c, str(c)) if isinstance(c, (int, np.integer)) else str(c)


logger = logging.getLogger("talentscope")
logger.setLevel(logging.INFO)

limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Adapt slowapi's narrow handler type to FastAPI's generic handler contract."""
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))


def create_app():
    app = FastAPI(title=settings.api_name, version=settings.api_version)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    origins = [orig.strip() for orig in settings.cors_origins.split(",") if orig.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def struct_logger_and_size_limit(request: Request, call_next):
        req_id = str(uuid.uuid4())
        request.state.req_id = req_id

        # Check size limit
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.request_size_limit:
            return JSONResponse(
                status_code=413, content={"detail": "Request too large"}
            )

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            json.dumps(
                {
                    "req_id": req_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                }
            )
        )

        # V13.6 Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    # Exception handler for Problem Details format
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        details = [
            {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "type": "about:blank",
                "title": "Validation Error",
                "status": 422,
                "detail": details,
            },
        )

    # Load Model State
    model_source = "unavailable"
    try:
        if not settings.enable_legacy_v1:
            raise RuntimeError(
                "legacy v1 artifact loading is disabled; using governed v2 artifacts"
            )
        with open(f"{settings.artifact_path}/metadata.json", "r") as f:
            metadata = json.load(f)

        calibrated_knn = load_artifact(
            "calibrated_knn.pkl",
            settings.artifact_path,
            expected_hash=metadata["hashes"]["calibrated_knn.pkl"],
        )
        pipe = load_artifact(
            "pipeline.pkl",
            settings.artifact_path,
            expected_hash=metadata["hashes"]["pipeline.pkl"],
        )

        with open(f"{settings.artifact_path}/conformal.json", "r") as f:
            conformal = json.load(f)

        train_df = pd.read_csv("data/raw/dataset.csv").drop_duplicates(
            subset=["employee_id"]
        )
        X_train = train_df.drop(columns=["performance"])
        y_train = train_df["performance"]
        model_source = "legacy-v1"

    except Exception as e:
        logger.info("Using governed v2 model artifacts: %s", e)
        try:
            from epk.artifacts import default_loader

            calibrated_knn = default_loader.load_model("knn")
            pipe = calibrated_knn
            conformal = {"threshold": 0.85}
            data_path = (
                Path("data/raw/dataset.csv")
                if Path("data/raw/dataset.csv").exists()
                else Path("data/nonlinear/dataset.csv")
            )
            train_df = (
                pd.read_csv(data_path)
                if data_path.exists()
                else pd.DataFrame({"employee_id": [1], "performance": ["Medium"]})
            )
            if "employee_id" in train_df.columns:
                train_df = train_df.drop_duplicates(subset=["employee_id"])
            X_train = train_df.drop(
                columns=["performance", "performance_score"], errors="ignore"
            )
            y_train = (
                train_df["performance"]
                if "performance" in train_df.columns
                else pd.Series(["Medium"] * len(train_df))
            )
            metadata = {"version": "v2.0 (governed KNN)"}
            model_source = "governed-v2"
        except Exception as e2:
            logger.error(f"Failed to load fallback v2 model: {e2}")
            metadata, calibrated_knn, pipe, conformal, X_train, y_train = (
                {},
                None,
                None,
                {},
                None,
                None,
            )
            model_source = "unavailable"

    @app.get("/health")
    def health():
        # Keep the lightweight liveness contract stable. Detailed dependency
        # status belongs to /ready, which is used by orchestration.
        return {"status": "ok"}

    @app.get("/ready")
    def readiness(db: Session = Depends(get_db)):
        from epk.artifacts import default_loader
        from sqlalchemy import text

        db_status = "connected"
        try:
            db.execute(text("SELECT 1"))
        except Exception:
            db_status = "unavailable"

        champ_status = (
            "available"
            if (default_loader.root_dir / "champion.json").exists()
            else "missing"
        )
        model_status = "available" if calibrated_knn is not None else "missing"
        is_ready = (
            db_status == "connected"
            and champ_status == "available"
            and model_status == "available"
        )
        return {
            "status": "ready" if is_ready else "not_ready",
            "database": db_status,
            "artifacts": champ_status,
            "model": model_status,
            "model_source": model_source,
        }

    @app.get("/version")
    def version():
        return {
            "api_version": settings.api_version,
            "model_version": metadata.get("version", "unknown"),
        }

    @app.post("/login")
    @limiter.limit("10/minute")
    def login(
        request: Request,
        response: Response,
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db),
    ):
        user = authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        access_token = create_access_token(data={"sub": user.email, "role": user.role})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        # V10.7 Audit log entry for login
        try:
            from backend.db.models import AuditLog

            db.add(
                AuditLog(
                    user_email=user.email,
                    action="login",
                    resource="/login",
                    details_json=json.dumps({"role": user.role}),
                )
            )
            db.commit()
        except Exception:
            pass
        return {"access_token": access_token, "token_type": "bearer", "role": user.role}

    @app.post("/refresh")
    def refresh(
        token: str = Depends(oauth2_scheme),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        revoke_token(token)
        new_token = create_access_token(data={"sub": user.email, "role": user.role})
        try:
            from backend.db.models import AuditLog

            db.add(
                AuditLog(
                    user_email=user.email,
                    action="token_refresh",
                    resource="/refresh",
                    details_json=json.dumps({"role": user.role}),
                )
            )
            db.commit()
        except Exception:
            pass
        return {"access_token": new_token, "token_type": "bearer", "role": user.role}

    @app.post("/logout")
    def logout(
        token: str = Depends(oauth2_scheme),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        revoke_token(token)
        try:
            from backend.db.models import AuditLog

            db.add(
                AuditLog(
                    user_email=user.email,
                    action="logout",
                    resource="/logout",
                    details_json=json.dumps({"token_prefix": token[:10]}),
                )
            )
            db.commit()
        except Exception:
            pass
        return {"status": "success", "message": "Logged out and token revoked"}

    @app.post("/predict", response_model=PredictResponse)
    @limiter.limit("50/minute")
    async def predict(
        request: Request,
        features: EmployeeFeatures,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst")),
    ):
        if calibrated_knn is None:
            raise HTTPException(status_code=503, detail="Prediction model unavailable")
        model = calibrated_knn
        df = pd.DataFrame([features.model_dump()])
        probs = model.predict_proba(df)[0]
        classes = list(model.classes_)
        classes_str = [to_band_str(c) for c in classes]

        raw_pset = get_prediction_set(
            probs, classes, threshold=conformal.get("threshold", 0.8)
        )
        pset = [to_band_str(c) for c in raw_pset]
        conf_dict = {c: float(p) for c, p in zip(classes_str, probs)}

        # Save to history
        hist = PredictionHistory(
            user_email=current_user.email,
            input_data=features.model_dump_json(),
            prediction=pset[0] if pset else "Unknown",
            confidence=float(max(probs)),
            needs_review=1 if (stability_score(probs) * 100.0 < 70) else 0,
        )
        db.add(hist)
        db.commit()

        return PredictResponse(
            prediction=pset,
            confidence=float(max(probs)),
            probabilities=conf_dict,
            stability_index=stability_score(probs) * 100.0,
        )

    @app.get("/analytics/drift")
    def drift_report(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst")),
    ):
        history = (
            db.query(PredictionHistory)
            .order_by(PredictionHistory.timestamp.desc())
            .limit(1000)
            .all()
        )
        drift_result = get_current_drift(history, {})
        return drift_result

    @app.post("/explain", response_model=ExplainResponse)
    @limiter.limit("20/minute")
    async def explain_pred(
        request: Request,
        features: EmployeeFeatures,
        k: int = 5,
        current_user: User = Depends(
            require_roles("admin", "hr_manager", "analyst", "reviewer")
        ),
    ):
        if calibrated_knn is None or pipe is None or X_train is None or y_train is None:
            raise HTTPException(
                status_code=503, detail="Explainability model unavailable"
            )
        model = calibrated_knn
        explain_pipe = pipe
        train_features = X_train
        train_labels = y_train
        df = pd.DataFrame([features.model_dump()])
        probs = model.predict_proba(df)[0]
        classes = list(model.classes_)
        classes_str = [to_band_str(c) for c in classes]
        raw_pset = get_prediction_set(
            probs, classes, threshold=conformal.get("threshold", 0.8)
        )
        pset = [to_band_str(c) for c in raw_pset]

        nb_df, votes = explain(explain_pipe, train_features, train_labels, df)
        nb_df = nb_df.head(k)

        # Calculate local attribution using training medians
        train_medians = train_features.select_dtypes(include=[np.number]).median()
        attrib = local_attribution(explain_pipe, df, train_medians)
        pred_class = classes_str[int(np.argmax(probs))]

        cfs = counterfactual(explain_pipe, df)
        path = (
            [str(opt.get("description", "Intervention")) for opt in cfs]
            if isinstance(cfs, list)
            else []
        )

        prediction_data = {
            "label": pred_class,
            "confidence": float(max(probs)),
            "votes": votes,
            "attribution": attrib,
            "neighbours": nb_df,
        }

        return ExplainResponse(
            prediction=pset,
            confidence=float(max(probs)),
            neighbors=nb_df.to_dict(orient="records"),
            votes=votes,
            summary=summarise(prediction_data),
            attribution=attrib,
            counterfactual_path=path,
        )

    @app.post("/batch")
    @limiter.limit("5/minute")
    async def batch(
        request: Request,
        file: UploadFile = File(...),
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst")),
    ):
        if calibrated_knn is None:
            raise HTTPException(status_code=503, detail="Prediction model unavailable")
        model = calibrated_knn
        if not file.filename or not file.filename.lower().endswith(".csv"):
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

        # Reject formula-like cells while allowing legitimate negative numbers.
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
            raise HTTPException(
                status_code=413, detail="Maximum 5,000 CSV rows allowed"
            )

        t0 = time.time()
        results = []
        errors = []
        for i, row in df.iterrows():
            try:
                feat = EmployeeFeatures(**row.to_dict())
                r_df = pd.DataFrame([feat.model_dump()])
                probs = model.predict_proba(r_df)[0]
                classes = list(model.classes_)
                classes_str = [to_band_str(c) for c in classes]
                raw_pset = get_prediction_set(
                    probs, classes, threshold=conformal.get("threshold", 0.8)
                )
                pset = [to_band_str(c) for c in raw_pset]
                conf_dict = {c: float(p) for c, p in zip(classes_str, probs)}

                results.append(
                    PredictResponse(
                        prediction=pset,
                        confidence=float(max(probs)),
                        probabilities=conf_dict,
                        stability_index=stability_score(probs) * 100.0,
                    )
                )
                errors.append(None)
            except Exception as e:
                results.append(None)
                errors.append({"row": i, "error": str(e)})

        t1 = time.time()

        return {"results": results, "errors": errors, "latency_ms": (t1 - t0) * 1000}

    @app.get("/batch/report/pdf")
    def export_pdf_report(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst")),
    ):
        if not HAS_REPORTLAB:
            return Response(content="ReportLab not installed", media_type="text/plain")
        from reportlab.lib.pagesizes import letter as pdf_letter
        from reportlab.pdfgen import canvas as pdf_canvas

        buffer = io.BytesIO()
        c = pdf_canvas.Canvas(buffer, pagesize=pdf_letter)
        c.drawString(100, 750, "TalentScope Batch Prediction Report")
        c.drawString(100, 730, "=================================")

        history = (
            db.query(PredictionHistory)
            .order_by(PredictionHistory.timestamp.desc())
            .limit(10)
            .all()
        )
        y = 700
        for h in history:
            c.drawString(
                100,
                y,
                f"[{h.timestamp.strftime('%Y-%m-%d %H:%M')}] {h.user_email}: {h.prediction} ({h.confidence:.2f})",
            )
            y -= 20
            if y < 100:
                c.showPage()
                y = 750

        c.save()
        pdf = buffer.getvalue()
        buffer.close()

        # V10.7 Audit log entry for export
        try:
            from backend.db.models import AuditLog

            db.add(
                AuditLog(
                    user_email=current_user.email,
                    action="export",
                    resource="/batch/report/pdf",
                    details_json=json.dumps({"format": "pdf"}),
                )
            )
            db.commit()
        except Exception:
            pass

        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=report.pdf"},
        )

    @app.get("/viz/galaxy")
    def galaxy(
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst"))
    ):
        for candidate in [
            f"{settings.artifact_path}/assets/background_sample.csv",
            "data/processed/assets/background_sample.csv",
            "artifacts/v1/background_sample.csv",
            "data/nonlinear/dataset.csv",
        ]:
            if Path(candidate).exists():
                bkg = pd.read_csv(candidate)
                return bkg.iloc[:2000].replace({np.nan: None}).to_dict(orient="records")
        return []

    @app.get("/viz/surface")
    def surface(
        size: int = 40,
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst")),
    ):
        """Legacy 2D decision-surface grid for the calibrated KNN model.

        The grid is served from the governed v2 explainability bundle so the legacy
        route returns the same precomputed surface as ``/api/v2/viz/surface``.
        """
        if size > 80:
            raise HTTPException(status_code=400, detail="Grid size too large")

        surfaces_path = default_loader.root_dir / "explainability" / "surfaces.json"
        if not surfaces_path.exists():
            raise HTTPException(status_code=503, detail="Surface artifact unavailable")
        with open(surfaces_path, "r", encoding="utf-8") as f:
            surfaces = json.load(f)
        grid = surfaces.get("knn")
        if grid is None:
            raise HTTPException(status_code=503, detail="KNN surface not present")
        return grid

    @app.get("/analytics")
    def analytics(
        current_user: User = Depends(require_roles("admin", "hr_manager", "analyst"))
    ):
        """Legacy analytics summary backed by the v2 comparison artifacts (Arena metrics)."""
        try:
            leaderboard = default_loader.load_comparison_json("leaderboard")
            mcda = default_loader.load_comparison_json("mcda")
            champion = default_loader.load_champion()
        except Exception as e:
            raise HTTPException(
                status_code=503, detail=f"Comparison artifacts unavailable: {e}"
            )

        return {
            "champion": champion.get("champion_key", "rf"),
            "profile": mcda.get("profile", "Balanced"),
            "decision_strength": mcda.get("decision_strength", "none"),
            "runner_up": mcda.get("runner_up"),
            "ranking": mcda.get("ranking", []),
            "models": [
                {
                    "key": row.get("key"),
                    "label": row.get("label"),
                    "accuracy": row.get("accuracy"),
                    "macro_f1": row.get("macro_f1"),
                    "qwk": row.get("qwk"),
                    "latency_single_p95_ms": row.get("latency_single_p95_ms"),
                }
                for row in leaderboard.get("metrics", [])
            ],
        }

    from backend.app.api_v2 import router as v2_router

    app.include_router(v2_router)

    return app


app = create_app()
