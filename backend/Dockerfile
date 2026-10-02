FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY backend/requirements.txt .
RUN uv pip install --system -r requirements.txt
RUN uv pip install --system sqlalchemy alembic passlib bcrypt pyjwt python-multipart "python-jose[cryptography]" scikit-learn pandas

COPY backend /app/backend
COPY ml /app/ml

# In real deployment, the ML artifact would be copied here as well.
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
