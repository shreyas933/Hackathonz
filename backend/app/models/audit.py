from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_email = Column(String(255), nullable=True)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=True, index=True)
    before_state = Column(Text, nullable=True)
    after_state = Column(Text, nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

