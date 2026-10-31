from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardMetrics,
    SalesDashboardMetrics,
    FinanceDashboardMetrics,
    CustomerDashboardMetrics,
    CopilotQueryRequest,
    CopilotQueryResponse
)
from app.services.dashboard_service import DashboardService
from app.api.deps import get_current_admin, get_current_staff, get_current_customer

router = APIRouter(prefix="/dashboard", tags=["Dashboards & Analytics"])

@router.get("/admin", response_model=AdminDashboardMetrics)
def get_admin_dashboard(
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return DashboardService.get_admin_dashboard(db)

@router.get("/sales", response_model=SalesDashboardMetrics)
def get_sales_dashboard(
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return DashboardService.get_sales_dashboard(db, staff_user)

@router.get("/finance", response_model=FinanceDashboardMetrics)
def get_finance_dashboard(
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return DashboardService.get_finance_dashboard(db)

@router.get("/customer", response_model=CustomerDashboardMetrics)
def get_customer_dashboard(
    customer_ctx: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = customer_ctx
    return DashboardService.get_customer_dashboard(db, business_id)

@router.post("/analytics/copilot", response_model=CopilotQueryResponse)
def execute_finance_copilot_query(
    data: CopilotQueryRequest,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return DashboardService.query_finance_intelligence(db, data)

