from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class SubscriptionRequest(Base):
    __tablename__ = "subscription_requests"

    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String(50), unique=True, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    request_type = Column(String(50), nullable=False)  # new_subscription, additional_seats, upgrade, downgrade, renewal, cancellation
    related_subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    requested_quantity = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), default="new", nullable=False)  # new, under_review, clarification_required, quoted, approved_accepted, processing, completed, rejected, cancelled
    assigned_sales_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business = relationship("CustomerBusiness")
    product = relationship("Product")
    plan = relationship("Plan")
    variant = relationship("ProductVariant")
    assigned_sales = relationship("User", foreign_keys=[assigned_sales_user_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    activities = relationship("RequestActivity", back_populates="request", cascade="all, delete-orphan")


class RequestActivity(Base):
    __tablename__ = "request_activities"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("subscription_requests.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    activity_type = Column(String(50), nullable=False)  # status_change, sales_note, clarification_request, customer_response, quotation_linked
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request = relationship("SubscriptionRequest", back_populates="activities")
    actor = relationship("User")


class QuotationTemplate(Base):
    __tablename__ = "quotation_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    lines_json = Column(Text, nullable=False)
    payment_terms = Column(String(100), default="net_30", nullable=False)
    validity_days = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(50), unique=True, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    request_id = Column(Integer, ForeignKey("subscription_requests.id", ondelete="SET NULL"), nullable=True)
    current_version_number = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, submitted_for_approval, changes_requested, approved, rejected_by_admin, sent_to_customer, accepted, rejected_by_customer, expired, superseded
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business = relationship("CustomerBusiness")
    request = relationship("SubscriptionRequest")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    versions = relationship("QuotationVersion", back_populates="quotation", cascade="all, delete-orphan", order_by="QuotationVersion.version_number.desc()")


class QuotationVersion(Base):
    __tablename__ = "quotation_versions"

    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), index=True, nullable=False)
    version_number = Column(Integer, nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft, submitted_for_approval, changes_requested, approved, rejected_by_admin, sent_to_customer, accepted, rejected_by_customer, superseded
    revision_reason = Column(Text, nullable=True)
    subtotal = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    final_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    payment_terms = Column(String(100), default="net_30", nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    is_latest = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("quotation_id", "version_number", name="uq_quotation_version"),
    )

    quotation = relationship("Quotation", back_populates="versions")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    lines = relationship("QuotationVersionLine", back_populates="quotation_version", cascade="all, delete-orphan")
    decisions = relationship("QuotationDecision", back_populates="quotation_version", cascade="all, delete-orphan", order_by="QuotationDecision.created_at.desc()")


class QuotationVersionLine(Base):
    __tablename__ = "quotation_version_lines"

    id = Column(Integer, primary_key=True, index=True)
    quotation_version_id = Column(Integer, ForeignKey("quotation_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    description = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)  # Single-field bulk quantity entry
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    quotation_version = relationship("QuotationVersion", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    plan = relationship("Plan")


class QuotationDecision(Base):
    __tablename__ = "quotation_decisions"

    id = Column(Integer, primary_key=True, index=True)
    quotation_version_id = Column(Integer, ForeignKey("quotation_versions.id", ondelete="CASCADE"), index=True, nullable=False)
    decision_maker_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision_type = Column(String(50), nullable=False)  # admin_approved, admin_rejected, admin_changes_requested, customer_accepted, customer_rejected
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quotation_version = relationship("QuotationVersion", back_populates="decisions")
    decision_maker = relationship("User")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscription_number = Column(String(50), unique=True, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    accepted_quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="RESTRICT"), nullable=True)
    accepted_quotation_version_id = Column(Integer, ForeignKey("quotation_versions.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(50), default="confirmed", nullable=False)  # draft, quotation, confirmed, active, paused, closed
    activation_policy = Column(String(50), default="prepaid", nullable=False)  # prepaid, credit_terms, scheduled_start
    start_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    billing_frequency = Column(String(50), default="monthly", nullable=False)
    payment_terms = Column(String(100), default="net_30", nullable=False)
    total_recurring_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business = relationship("CustomerBusiness")
    accepted_quotation = relationship("Quotation", foreign_keys=[accepted_quotation_id])
    accepted_version = relationship("QuotationVersion", foreign_keys=[accepted_quotation_version_id])
    lines = relationship("SubscriptionLine", back_populates="subscription", cascade="all, delete-orphan")


class SubscriptionLine(Base):
    __tablename__ = "subscription_lines"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    subscription = relationship("Subscription", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    plan = relationship("Plan")

