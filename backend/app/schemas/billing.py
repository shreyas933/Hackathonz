from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Optional, List

# --- Invoice Line Schemas ---
class InvoiceLineOut(BaseModel):
    id: int
    product_id: int
    variant_id: Optional[int] = None
    plan_id: int
    description: Optional[str] = None
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal
    tax_rate_percent: Decimal
    tax_amount: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True

# --- Payment Allocation Schemas ---
class PaymentAllocationOut(BaseModel):
    id: int
    payment_id: int
    invoice_id: int
    allocated_amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

# --- Invoice Schemas ---
class InvoiceOut(BaseModel):
    id: int
    invoice_number: str
    business_id: int
    subscription_id: Optional[int] = None
    quotation_version_id: Optional[int] = None
    billing_period: str
    issue_date: datetime
    due_date: datetime
    subtotal: Decimal
    discount_total: Decimal
    tax_total: Decimal
    final_total: Decimal
    amount_paid: Decimal
    remaining_balance: Decimal
    currency: str
    payment_terms: str
    status: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineOut] = []
    allocations: List[PaymentAllocationOut] = []

    class Config:
        from_attributes = True

class GenerateInvoiceFromQuotationRequest(BaseModel):
    quotation_id: int
    version_number: Optional[int] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None

class InvoiceStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(draft|confirmed|paid|partially_paid|cancelled|overdue)$")
    notes: Optional[str] = None

# --- Payment Schemas ---
class InvoicePaymentAllocationInput(BaseModel):
    invoice_id: int
    amount: Decimal = Field(..., gt=Decimal("0.00"))

class RecordPaymentRequest(BaseModel):
    business_id: int
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    payment_method: str = Field(..., pattern="^(cash|bank_transfer|upi|card|other)$")
    reference_number: Optional[str] = None
    payment_date: Optional[datetime] = None
    allocations: List[InvoicePaymentAllocationInput]
    notes: Optional[str] = None

class PaymentOut(BaseModel):
    id: int
    payment_number: str
    business_id: int
    amount: Decimal
    currency: str
    payment_method: str
    payment_date: datetime
    reference_number: Optional[str] = None
    source: str
    reconciliation_status: str
    notes: Optional[str] = None
    created_at: datetime
    allocations: List[PaymentAllocationOut] = []

    class Config:
        from_attributes = True

# --- Recurring Billing Schemas ---
class RecurringBillingRunRequest(BaseModel):
    target_date: Optional[datetime] = None

class RecurringBillingRunResult(BaseModel):
    processed_count: int
    invoices_generated: int
    skipped_idempotent: int
    errors: List[str] = []

