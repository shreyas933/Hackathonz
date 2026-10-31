from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.audit import AuditLogOut
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/logs", response_model=List[AuditLogOut])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()

