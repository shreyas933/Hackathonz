from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), index=True, nullable=True)
    quotation_version_id = Column(Integer, ForeignKey("quotation_versions.id", ondelete="SET NULL"), nullable=True)
    
    # Billing period: e.g. "2026-10" or "2026-10-01_2026-10-31"
    billing_period = Column(String(100), nullable=False)
    issue_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    subtotal = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    discount_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    final_total = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    amount_paid = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    remaining_balance = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    
    currency = Column(String(10), default="INR", nullable=False)
    payment_terms = Column(String(100), default="net_30", nullable=False)
    status = Column(String(50), default="confirmed", nullable=False)  # draft, confirmed, paid, partially_paid, cancelled, overdue
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        # Mandatory idempotency constraint: no duplicate invoice for the same subscription and billing period
        UniqueConstraint("subscription_id", "billing_period", name="uq_subscription_billing_period"),
    )

    business = relationship("CustomerBusiness")
    subscription = relationship("Subscription")
    quotation_version = relationship("QuotationVersion")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("PaymentAllocation", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True)
    plan_id = Column(Integer, ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    description = Column(String(255), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    line_total = Column(Numeric(12, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="lines")
    product = relationship("Product")
    variant = relationship("ProductVariant")
    plan = relationship("Plan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, index=True, nullable=False)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    payment_method = Column(String(50), default="bank_transfer", nullable=False)  # cash, bank_transfer, upi, card, other
    payment_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)  # Bank UTR / Transaction ID
    source = Column(String(50), default="manual", nullable=False)  # manual, gateway, bank_feed
    reconciliation_status = Column(String(50), default="reconciled", nullable=False)  # unmatched, suggested_match, under_review, reconciled, partially_allocated, rejected
    notes = Column(Text, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    business = relationship("CustomerBusiness")
    created_by = relationship("User")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), index=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), index=True, nullable=False)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payment = relationship("Payment", back_populates="allocations")
    invoice = relationship("Invoice", back_populates="allocations")

