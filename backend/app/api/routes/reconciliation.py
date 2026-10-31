from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.automation import (
    BankFeedItemOut,
    IngestBankFeedRequest,
    ReconciliationMatchRequest,
    ReconciliationDisputeRequest
)
from app.services.reconciliation_service import ReconciliationService
from app.api.deps import get_current_staff

router = APIRouter(prefix="/finance/reconciliation", tags=["Finance Reconciliation"])

@router.post("/feed/ingest", response_model=List[BankFeedItemOut])
def ingest_bank_feed(
    data: IngestBankFeedRequest,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return ReconciliationService.ingest_feed_items(
        db=db,
        items=data.items,
        user=staff_user,
        ip_address=ip
    )

@router.get("/feed", response_model=List[BankFeedItemOut])
def list_bank_feed_items(
    status: Optional[str] = None,
    business_id: Optional[int] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return ReconciliationService.list_feed_items(
        db=db,
        status=status,
        business_id=business_id
    )

@router.post("/feed/{item_id}/match", response_model=BankFeedItemOut)
def confirm_feed_match(
    item_id: int,
    data: ReconciliationMatchRequest,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return ReconciliationService.confirm_match(
        db=db,
        feed_item_id=item_id,
        user=staff_user,
        invoice_id=data.invoice_id,
        allocated_amount=data.allocated_amount,
        notes=data.notes,
        ip_address=ip
    )

@router.post("/feed/{item_id}/dispute", response_model=BankFeedItemOut)
def dispute_feed_item(
    item_id: int,
    data: ReconciliationDisputeRequest,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return ReconciliationService.mark_dispute(
        db=db,
        feed_item_id=item_id,
        reason=data.reason,
        user=staff_user,
        ip_address=ip
    )

