from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class AdminDashboardMetrics(BaseModel):
    mrr: Decimal
    arr: Decimal
    total_customers: int
    active_subscriptions: int
    total_invoiced: Decimal
    total_collected: Decimal
    total_overdue: Decimal
    pending_admin_approvals: int
    accepted_awaiting_invoice: int
    unmatched_bank_feeds: int
    recent_activity: List[Dict[str, Any]] = []

class SalesDashboardMetrics(BaseModel):
    new_requests_count: int
    draft_quotations_count: int
    pending_approval_quotations_count: int
    approved_awaiting_customer_count: int
    accepted_quotations_count: int
    pipeline_estimated_value: Decimal
    recent_requests: List[Dict[str, Any]] = []

class FinanceDashboardMetrics(BaseModel):
    accepted_awaiting_invoice_count: int
    total_invoices_count: int
    unpaid_invoices_count: int
    overdue_invoices_count: int
    total_outstanding_balance: Decimal
    total_collected_amount: Decimal
    unmatched_feed_items_count: int
    suggested_feed_matches_count: int
    recent_payments: List[Dict[str, Any]] = []

class CustomerDashboardMetrics(BaseModel):
    company_name: str
    active_subscriptions_count: int
    total_seats: int
    next_billing_date: Optional[datetime] = None
    total_invoiced: Decimal
    total_paid: Decimal
    outstanding_balance: Decimal
    overdue_balance: Decimal
    pending_quotations_count: int
    unread_notifications_count: int

class CopilotQueryRequest(BaseModel):
    query_type: str = Field(..., pattern="^(mrr_arr_summary|debtors_aging|churn_risk_analysis|renewal_forecast)$")
    parameters: Optional[Dict[str, Any]] = None

class CopilotQueryResponse(BaseModel):
    query_type: str
    headline: str
    summary: str
    data_points: Dict[str, Any]
    recommendations: List[str]
    timestamp: datetime

