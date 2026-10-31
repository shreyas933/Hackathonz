import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog

class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        actor_email: Optional[str] = None,
        actor_role: Optional[str] = None,
        before_state: Optional[Any] = None,
        after_state: Optional[Any] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        before_str = json.dumps(before_state, default=str) if before_state is not None else None
        after_str = json.dumps(after_state, default=str) if after_state is not None else None

        log_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            actor_role=actor_role,
            before_state=before_str,
            after_state=after_str,
            ip_address=ip_address,
        )
        db.add(log_entry)
        db.flush()
        return log_entry

