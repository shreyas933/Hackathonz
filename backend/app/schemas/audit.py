from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class AuditLogOut(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    actor_email: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    before_state: Optional[str] = None
    after_state: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

