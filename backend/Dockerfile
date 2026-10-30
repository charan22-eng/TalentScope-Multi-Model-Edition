FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY backend/requirements.txt .
RUN uv pip install --system -r requirements.txt
RUN uv pip install --system sqlalchemy alembic passlib bcrypt pyjwt python-multipart "python-jose[cryptography]" scikit-learn pandas scipy reportlab slowapi

# Non-root user for security hardening
RUN useradd -u 1000 -m -s /bin/bash appuser

COPY --chown=appuser:appuser backend /app/backend
COPY --chown=appuser:appuser ml /app/ml
COPY --chown=appuser:appuser artifacts /app/artifacts
COPY --chown=appuser:appuser data/processed /app/data/processed
COPY --chown=appuser:appuser data/nonlinear /app/data/nonlinear

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
