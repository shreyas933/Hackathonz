from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    user_type = Column(String(50), nullable=False, default="customer")  # admin, staff, customer
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    staff_profile = relationship("StaffProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", foreign_keys="StaffProfile.user_id")
    customer_memberships = relationship("CustomerMembership", back_populates="user", cascade="all, delete-orphan")


class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    staff_role = Column(String(50), nullable=False)  # sales, finance
    department = Column(String(100), nullable=True)
    permissions_override = Column(Text, nullable=True)  # JSON-encoded custom overrides
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="staff_profile", foreign_keys=[user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])

