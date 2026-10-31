from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class BankFeedItem(Base):
    __tablename__ = "bank_feed_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    bank_account_number = Column(String(50), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    raw_narration = Column(Text, nullable=False)
    parsed_reference = Column(String(100), nullable=True, index=True)
    sender_name = Column(String(255), nullable=True)
    
    # Status: unmatched, suggested_match, reconciled, disputed, ignored
    status = Column(String(50), default="unmatched", index=True, nullable=False)
    confidence_score = Column(Numeric(3, 2), default=Decimal("0.00"), nullable=False)
    
    suggested_invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    suggested_business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="SET NULL"), nullable=True)
    matched_payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    
    reconciliation_notes = Column(Text, nullable=True)
    reconciled_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    suggested_invoice = relationship("Invoice", foreign_keys=[suggested_invoice_id])
    suggested_business = relationship("CustomerBusiness", foreign_keys=[suggested_business_id])
    matched_payment = relationship("Payment", foreign_keys=[matched_payment_id])
    reconciled_by = relationship("User", foreign_keys=[reconciled_by_user_id])


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    source = Column(String(50), default="payment_gateway", nullable=False)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(50), default="processed", nullable=False)  # processed, failed, ignored
    processing_result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ReminderRule(Base):
    __tablename__ = "reminder_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    # trigger_type: before_due, on_due, after_due_overdue, upcoming_renewal
    trigger_type = Column(String(50), nullable=False)
    days_offset = Column(Integer, nullable=False)  # e.g. -3 for 3 days before due, 0 for due date, 7 for 7 days overdue
    channel = Column(String(50), default="email", nullable=False)  # email, in_app
    subject_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    escalation_level = Column(String(50), default="standard", nullable=False)  # standard, urgent, final_notice
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("customer_businesses.id", ondelete="CASCADE"), index=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    reminder_rule_id = Column(Integer, ForeignKey("reminder_rules.id", ondelete="SET NULL"), nullable=True)
    
    recipient_email = Column(String(255), nullable=False)
    channel = Column(String(50), default="email", nullable=False)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="delivered", nullable=False)  # queued, sent, delivered, failed
    failure_reason = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    business = relationship("CustomerBusiness")
    invoice = relationship("Invoice")
    subscription = relationship("Subscription")
    reminder_rule = relationship("ReminderRule")

