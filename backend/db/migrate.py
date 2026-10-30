"""Database Migration and Seed Runner (Stage L1).

Initializes all database tables for SQLite / PostgreSQL and seeds default role accounts
and initial governed model versions.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[2])
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from sqlalchemy import inspect, text

from backend.core.security import get_password_hash
from backend.db.database import SessionLocal, engine, init_db
from backend.db.models import AuditLog, ModelVersion, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("talentscope.migrate")


def upgrade_existing_tables():
    """Ensure existing tables have new columns required by v2."""
    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        if "users" in tables:
            columns = {col["name"] for col in inspector.get_columns("users")}
            if "is_active" not in columns:
                logger.info("Migrating users table: adding is_active column")
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
                )
            if "created_at" not in columns:
                logger.info("Migrating users table: adding created_at column")
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT '2026-01-01 00:00:00'"
                    )
                )
            conn.commit()


def seed_users(db):
    """Seed standard test users for each role if they do not exist."""
    default_users = [
        {"email": "admin@test.com", "role": "admin", "password": "AdminPassword123!"},
        {
            "email": "hrmanager@test.com",
            "role": "hr_manager",
            "password": "HRManagerPassword123!",
        },
        {
            "email": "analyst@test.com",
            "role": "analyst",
            "password": "AnalystPassword123!",
        },
        {
            "email": "viewer@test.com",
            "role": "viewer",
            "password": "ViewerPassword123!",
        },
        {
            "email": "reviewer@test.com",
            "role": "reviewer",
            "password": "ReviewerPassword123!",
        },
    ]

    for u in default_users:
        existing = db.query(User).filter(User.email == u["email"]).first()
        if not existing:
            user = User(
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                is_active=1,
            )
            db.add(user)
            logger.info("Seeded user: %s with role: %s", u["email"], u["role"])
    db.commit()


def seed_model_versions(db):
    """Seed initial model versions into governance store."""
    leaderboard_file = Path(_ROOT) / "artifacts/v2/comparison/leaderboard.json"
    champion_file = Path(_ROOT) / "artifacts/v2/champion.json"

    champion_key = "rf"
    if champion_file.exists():
        try:
            with open(champion_file, "r", encoding="utf-8") as f:
                c_data = json.load(f)
                champion_key = (
                    c_data.get("champion_key") or c_data.get("champion") or "rf"
                )
        except Exception:
            pass

    metrics_map = {}
    if leaderboard_file.exists():
        try:
            with open(leaderboard_file, "r", encoding="utf-8") as f:
                lb_data = json.load(f)
                for row in lb_data.get("metrics", []):
                    model_key = row.get("key")
                    if model_key:
                        metrics_map[model_key] = row
        except Exception:
            pass

    models = ["boost", "dt", "knn", "linreg", "logreg", "rf", "svm"]
    for m in models:
        existing = (
            db.query(ModelVersion)
            .filter(ModelVersion.model_key == m, ModelVersion.version == "v2.0")
            .first()
        )
        m_metrics = metrics_map.get(m, {})
        if not existing:
            version = ModelVersion(
                model_key=m,
                version="v2.0",
                is_champion=1 if m == champion_key else 0,
                status="active",
                metrics_json=json.dumps(m_metrics),
                approved_by="system_seed",
                approved_at=datetime.now(timezone.utc),
            )
            db.add(version)
            logger.info(
                "Seeded ModelVersion: %s v2.0 (champion=%s)", m, m == champion_key
            )
        elif existing.status == "active" and m_metrics:
            # Repair older seeds that used the obsolete `leaderboard` key and
            # therefore stored the synthetic 0.8/0.8 fallback metrics.
            existing.metrics_json = json.dumps(m_metrics)
            existing.is_champion = 1 if m == champion_key else 0
    db.commit()


def run_migrations():
    """Execute migration and seed."""
    logger.info("Initializing database tables...")
    upgrade_existing_tables()
    init_db()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_model_versions(db)
        # Log migration audit event
        audit = AuditLog(
            user_email="system@talentscope.local",
            action="database_migration",
            resource="all_tables",
            details_json=json.dumps({"status": "success", "tables_created": 18}),
        )
        db.add(audit)
        db.commit()
        logger.info("Migrations completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    run_migrations()
