from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="reviewer")  # admin, reviewer


class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_email = Column(String, index=True)
    input_data = Column(Text)  # JSON string of inputs
    prediction = Column(String)
    confidence = Column(Float)
    needs_review = Column(Integer, default=0)  # SQLite lacks bool by default, using 1/0


class LLMVerdict(Base):
    __tablename__ = "llm_verdicts"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_email = Column(String, index=True)
    mode = Column(String, default="verdict")
    audience = Column(String, default="HR")
    prompt_hash = Column(String, index=True)
    verdict_json = Column(Text)
    is_valid = Column(Integer, default=1)
    is_fallback = Column(Integer, default=0)
    validation_json = Column(Text)

