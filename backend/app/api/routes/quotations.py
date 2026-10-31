from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.commercial import (
    QuotationCreate, QuotationRevise, QuotationOut, QuotationVersionOut,
    QuotationDecisionInput, QuotationDecisionOut, VersionDiffOut
)
from app.services.quotation_service import QuotationService
from app.api.deps import get_current_customer, get_current_staff, get_current_admin
from app.models.user import User

router = APIRouter(tags=["Quotations & Versions"])

# --- Staff Endpoints ---
@router.post("/staff/quotations", response_model=QuotationOut)
def create_quotation(
    data: QuotationCreate,
    request: Request,
    submit_for_approval: bool = True,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return QuotationService.create_quotation(db, staff_user, data, submit_for_approval=submit_for_approval, ip_address=ip)

@router.get("/staff/quotations", response_model=List[QuotationOut])
def list_staff_quotations(
    status_filter: Optional[str] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return QuotationService.list_quotations_for_staff(db, status_filter=status_filter)

@router.get("/staff/quotations/{quotation_id}", response_model=QuotationOut)
def get_staff_quotation(
    quotation_id: int,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return QuotationService.get_quotation(db, quotation_id)

@router.post("/staff/quotations/{quotation_id}/versions", response_model=QuotationVersionOut)
def revise_quotation(
    quotation_id: int,
    data: QuotationRevise,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return QuotationService.revise_quotation(db, staff_user, quotation_id, data, ip_address=ip)

@router.get("/staff/quotations/{quotation_id}/compare", response_model=VersionDiffOut)
def compare_quotation_versions(
    quotation_id: int,
    base_version: int = Query(..., ge=1),
    target_version: int = Query(..., ge=1),
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return QuotationService.compare_versions(db, quotation_id, base_version, target_version)

# --- Admin Mandatory Approval Endpoint ---
@router.post("/admin/quotations/{quotation_id}/versions/{version_number}/decision", response_model=QuotationVersionOut)
def admin_quotation_decision(
    quotation_id: int,
    version_number: int,
    data: QuotationDecisionInput,
    request: Request,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return QuotationService.admin_process_decision(
        db, admin_user, quotation_id, version_number, data, ip_address=ip
    )

# --- Customer Portal Endpoints ---
@router.get("/customer/quotations", response_model=List[QuotationOut])
def list_customer_quotations(
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return QuotationService.list_quotations_for_customer(db, business_id)

@router.get("/customer/quotations/{quotation_id}", response_model=QuotationOut)
def get_customer_quotation(
    quotation_id: int,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return QuotationService.get_quotation(db, quotation_id, business_id=business_id)

@router.post("/customer/quotations/{quotation_id}/versions/{version_number}/decision", response_model=QuotationVersionOut)
def customer_quotation_decision(
    quotation_id: int,
    version_number: int,
    data: QuotationDecisionInput,
    request: Request,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    ip = request.client.host if request.client else None
    version, _ = QuotationService.customer_process_decision(
        db, current_user, business_id, quotation_id, version_number,
        decision_type=data.decision_type, reason=data.reason, ip_address=ip
    )
    return version

