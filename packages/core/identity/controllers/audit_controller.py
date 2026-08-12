"""
Audit logging controller
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from packages.core.database import get_db
from packages.core.identity.models import AuditLog
from packages.core.identity.schemas import AuditLogResponse
from packages.core.security import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    user_id: Optional[str] = Query(None, description="Filter logs by user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs up to this date"),
    limit: int = Query(100, ge=1, le=1000),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to view audit logs"
        )

    query = db.query(AuditLog).filter(AuditLog.organization_id == current_user["organization_id"])

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)

    audit_logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [AuditLogResponse.from_orm(log) for log in audit_logs]
