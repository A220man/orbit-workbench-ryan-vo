"""Audit trail query and filtering endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import AuthenticatedUser, require_role
from app.models.entities import AuditEntity
from app.models.schemas import AuditLogEntry, AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=AuditLogResponse)
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: AuthenticatedUser = Depends(require_role("analyst")),
):
    """Returns persistent audit log entries with action filtering and UTC timestamps."""
    query = db.query(AuditEntity)
    if action:
        query = query.filter(AuditEntity.action == action)
    if resource_type:
        query = query.filter(AuditEntity.resource_type == resource_type)

    total = query.count()
    records = query.order_by(AuditEntity.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        AuditLogEntry(
            id=r.id,
            timestamp=r.timestamp,
            user_id=r.user_id,
            action=r.action,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            details=r.details,
        )
        for r in records
    ]

    return AuditLogResponse(items=items, total=total, page=page, page_size=page_size)
