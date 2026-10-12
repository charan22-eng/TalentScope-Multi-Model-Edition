"""Append-Only Audit Logging Service (Stage L2).

Records all governed actions to the immutable audit_logs table.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from backend.db.models import AuditLog


def log_audit_event(
    db: Session,
    user_email: str,
    action: str,
    resource: str,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Record an immutable audit event to audit_logs."""
    details_str = json.dumps(details) if details is not None else None
    audit = AuditLog(
        timestamp=datetime.now(timezone.utc),
        user_email=user_email,
        action=action,
        resource=resource,
        details_json=details_str,
        ip_address=ip_address,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
