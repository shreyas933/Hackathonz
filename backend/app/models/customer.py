from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class CustomerBusiness(Base):
    __tablename__ = "customer_businesses"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    tax_id = Column(String(100), nullable=True)  # GSTIN or corporate tax ID
    billing_address = Column(Text, nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(50), nullable=True)
    billing_country = Column(String(100), default="India", nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    status = Column(String(50), default="active", nullable=False)  # active, suspended, inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    memberships = relationship("CustomerMembership", back_populates="business", cascade="all, delete-orphan")


class CustomerMembership(Base):
    __tablename__ = "customer_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="owner", nullable=False)  # owner, finance_contact, subscription_manager
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_user_business"),
    )

    user = relationship("User", back_populates="customer_memberships")
    business = relationship("CustomerBusiness", back_populates="memberships")

