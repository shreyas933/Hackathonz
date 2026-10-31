from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List, Any

# --- Subscription Requests ---
class SubscriptionRequestCreate(BaseModel):
    request_type: str = Field(..., pattern="^(new_subscription|additional_seats|upgrade|downgrade|renewal|cancellation)$")
    related_subscription_id: Optional[int] = None
    product_id: Optional[int] = None
    plan_id: Optional[int] = None
    variant_id: Optional[int] = None
    requested_quantity: int = Field(1, ge=1)
    notes: Optional[str] = None

class SubscriptionRequestUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(new|under_review|clarification_required|quoted|approved_accepted|processing|completed|rejected|cancelled)$")
    assigned_sales_user_id: Optional[int] = None
    notes: Optional[str] = None

class RequestActivityCreate(BaseModel):
    activity_type: str = Field(..., pattern="^(status_change|sales_note|clarification_request|customer_response|quotation_linked)$")
    message: str

class RequestActivityOut(BaseModel):
    id: int
    request_id: int
    actor_user_id: Optional[int] = None
    activity_type: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionRequestOut(BaseModel):
    id: int
    reference: str
    business_id: int
    request_type: str
    related_subscription_id: Optional[int] = None
    product_id: Optional[int] = None
    plan_id: Optional[int] = None
    variant_id: Optional[int] = None
    requested_quantity: int
    notes: Optional[str] = None
    status: str
    assigned_sales_user_id: Optional[int] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    activities: List[RequestActivityOut] = []

    class Config:
        from_attributes = True

# --- Quotation Lines ---
class QuotationLineInput(BaseModel):
    product_id: int
    plan_id: int
    variant_id: Optional[int] = None
    description: Optional[str] = None
    quantity: int = Field(..., ge=1)  # Single bulk seats entry
    unit_price: Decimal
    discount_percent: Decimal = Decimal("0.00")
    tax_rate_percent: Decimal = Decimal("0.00")

class QuotationLineOut(BaseModel):
    id: int
    product_id: int
    plan_id: int
    variant_id: Optional[int] = None
    description: Optional[str] = None
    quantity: int
    unit_price: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    tax_rate_percent: Decimal
    tax_amount: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True

# --- Quotation Decisions ---
class QuotationDecisionInput(BaseModel):
    decision_type: str = Field(..., pattern="^(admin_approved|admin_rejected|admin_changes_requested|customer_accepted|customer_rejected)$")
    reason: Optional[str] = None

class QuotationDecisionOut(BaseModel):
    id: int
    decision_maker_user_id: Optional[int] = None
    decision_type: str
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Quotation Versions ---
class QuotationVersionOut(BaseModel):
    id: int
    quotation_id: int
    version_number: int
    status: str
    revision_reason: Optional[str] = None
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    final_total: Decimal
    payment_terms: str
    valid_until: Optional[datetime] = None
    start_date: Optional[datetime] = None
    is_latest: bool
    created_by_user_id: Optional[int] = None
    created_at: datetime
    lines: List[QuotationLineOut] = []
    decisions: List[QuotationDecisionOut] = []

    class Config:
        from_attributes = True

class QuotationCreate(BaseModel):
    business_id: int
    request_id: Optional[int] = None
    payment_terms: str = "net_30"
    validity_days: int = Field(30, ge=1, le=365)
    start_date: Optional[datetime] = None
    lines: List[QuotationLineInput]

class QuotationRevise(BaseModel):
    revision_reason: str = Field(..., min_length=3)
    payment_terms: Optional[str] = None
    validity_days: Optional[int] = Field(None, ge=1, le=365)
    start_date: Optional[datetime] = None
    lines: List[QuotationLineInput]

class QuotationOut(BaseModel):
    id: int
    quotation_number: str
    business_id: int
    request_id: Optional[int] = None
    current_version_number: int
    status: str
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    versions: List[QuotationVersionOut] = []

    class Config:
        from_attributes = True

# Version Diff comparison schema
class VersionDiffOut(BaseModel):
    quotation_number: str
    base_version_number: int
    target_version_number: int
    subtotal_diff: Decimal
    discount_diff: Decimal
    tax_diff: Decimal
    final_total_diff: Decimal
    changed_fields: List[str]
    lines_comparison: List[dict]

# --- Subscriptions ---
class SubscriptionLineOut(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    plan_id: int
    quantity: int
    unit_price: Decimal
    tax_rate_percent: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True

class SubscriptionOut(BaseModel):
    id: int
    subscription_number: str
    business_id: int
    accepted_quotation_id: Optional[int] = None
    accepted_quotation_version_id: Optional[int] = None
    status: str
    activation_policy: str
    start_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    billing_frequency: str
    payment_terms: str
    total_recurring_amount: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[SubscriptionLineOut] = []

    class Config:
        from_attributes = True

class SubscriptionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(confirmed|active|paused|closed)$")
    reason: Optional[str] = None

