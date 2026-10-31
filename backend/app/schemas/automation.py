from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict

# --- Bank Feed & Reconciliation Schemas ---
class BankFeedItemInput(BaseModel):
    transaction_id: str
    transaction_date: Optional[datetime] = None
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    currency: str = "INR"
    raw_narration: str
    bank_account_number: Optional[str] = None
    sender_name: Optional[str] = None

class IngestBankFeedRequest(BaseModel):
    items: List[BankFeedItemInput]

class BankFeedItemOut(BaseModel):
    id: int
    transaction_id: str
    bank_account_number: Optional[str] = None
    transaction_date: datetime
    amount: Decimal
    currency: str
    raw_narration: str
    parsed_reference: Optional[str] = None
    sender_name: Optional[str] = None
    status: str
    confidence_score: Decimal
    suggested_invoice_id: Optional[int] = None
    suggested_business_id: Optional[int] = None
    matched_payment_id: Optional[int] = None
    reconciliation_notes: Optional[str] = None
    reconciled_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReconciliationMatchRequest(BaseModel):
    invoice_id: int
    allocated_amount: Optional[Decimal] = None
    notes: Optional[str] = None

class ReconciliationDisputeRequest(BaseModel):
    reason: str

# --- Webhook Schemas ---
class WebhookPaymentData(BaseModel):
    transaction_id: str
    amount: Decimal
    currency: str = "INR"
    invoice_number: Optional[str] = None
    business_id: Optional[int] = None
    payment_method: str = "card"
    reference_number: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class WebhookPaymentPayload(BaseModel):
    event_id: str
    event_type: str = Field(..., pattern="^(payment\\.captured|payment\\.failed)$")
    data: WebhookPaymentData

class WebhookResponse(BaseModel):
    status: str
    message: str
    event_id: str

# --- Reminder Schemas ---
class ReminderRuleCreate(BaseModel):
    name: str
    trigger_type: str = Field(..., pattern="^(before_due|on_due|after_due_overdue|upcoming_renewal)$")
    days_offset: int
    channel: str = Field("email", pattern="^(email|in_app)$")
    subject_template: str
    body_template: str
    escalation_level: str = Field("standard", pattern="^(standard|urgent|final_notice)$")
    is_active: bool = True

class ReminderRuleOut(BaseModel):
    id: int
    name: str
    trigger_type: str
    days_offset: int
    channel: str
    subject_template: str
    body_template: str
    escalation_level: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationLogOut(BaseModel):
    id: int
    business_id: int
    invoice_id: Optional[int] = None
    subscription_id: Optional[int] = None
    recipient_email: str
    channel: str
    subject: str
    content: str
    status: str
    failure_reason: Optional[str] = None
    sent_at: datetime
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RunRemindersRequest(BaseModel):
    target_date: Optional[datetime] = None

class RunRemindersResult(BaseModel):
    processed_invoices: int
    reminders_sent: int
    skipped_count: int
    errors: List[str] = []

