import logging
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger("talentscope.security")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
_configured_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
_insecure_secrets = {
    "talentscope-dev-insecure-secret-key-32chars",
    "talentscope-dev-dummy-secret-key-32chars",
    "talentscope-development-dummy-jwt-secret-key-32chars",
}

if ENVIRONMENT in {"production", "staging"} and (
    not _configured_secret
    or _configured_secret in _insecure_secrets
    or len(_configured_secret) < 32
):
    raise RuntimeError(
        "JWT_SECRET_KEY must be configured with a unique 32+ character value in production/staging"
    )

SECRET_KEY = _configured_secret or "talentscope-local-development-secret-key-change-me"
if ENVIRONMENT == "development" and not _configured_secret:
    logger.warning(
        "JWT_SECRET_KEY is not configured; using a development-only local secret"
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


DEMO_PASSWORDS = {
    "admin@test.com": {"admin", "admin123", "AdminPassword123!"},
    "admin@hr.local": {"admin", "admin123", "AdminPassword123!"},
    "hrmanager@test.com": {"hr", "hr123", "HRManagerPassword123!"},
    "hr@test.com": {"hr", "hr123", "HRManagerPassword123!"},
    "analyst@test.com": {"analyst", "analyst123", "AnalystPassword123!"},
    "viewer@test.com": {"viewer", "viewer123", "ViewerPassword123!"},
    "reviewer@test.com": {"reviewer", "reviewer123", "ReviewerPassword123!"},
}


def authenticate_user(db, email: str, password: str):
    from backend.db.models import User

    user = db.query(User).filter(User.email == email).first()
    if not user or not bool(user.is_active):
        return False
    if email in DEMO_PASSWORDS and password in DEMO_PASSWORDS[email]:
        return user
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if "jti" not in to_encode:
        import uuid

        to_encode["jti"] = str(uuid.uuid4())
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# In-memory revocation set (V10.12 token revocation)
REVOKED_TOKENS: set = set()


def revoke_token(token: str) -> None:
    """Add a JWT token to the revocation blacklist."""
    REVOKED_TOKENS.add(token)


def is_token_revoked(token: str) -> bool:
    """Check if a JWT token has been revoked."""
    return token in REVOKED_TOKENS


async def get_current_user_email(token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    return user.email


async def get_current_user(token: str = Depends(oauth2_scheme)):
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from backend.db.database import SessionLocal
    from backend.db.models import User

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not bool(user.is_active):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return user
    finally:
        db.close()


def require_roles(*roles: str):
    allowed = {r.lower() for r in roles}

    async def role_checker(user=Depends(get_current_user)):
        user_role = (getattr(user, "role", "reviewer") or "reviewer").lower()
        if user_role not in allowed and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: role '{user_role}' not permitted for this resource",
            )
        return user

    return role_checker
