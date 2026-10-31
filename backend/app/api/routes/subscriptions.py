from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.commercial import SubscriptionOut, SubscriptionStatusUpdate, SubscriptionActionRequest
from app.services.subscription_service import SubscriptionService
from app.api.deps import get_current_customer, get_current_staff
from app.models.user import User

router = APIRouter(tags=["Subscriptions"])

# --- Customer Endpoints ---
@router.get("/customer/subscriptions", response_model=List[SubscriptionOut])
def list_customer_subscriptions(
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return SubscriptionService.list_for_customer(db, business_id)

@router.get("/customer/subscriptions/{subscription_id}", response_model=SubscriptionOut)
def get_customer_subscription(
    subscription_id: int,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return SubscriptionService.get_subscription(db, subscription_id, business_id=business_id)

@router.post("/customer/subscriptions/{subscription_id}/pause", response_model=SubscriptionOut)
def customer_pause_subscription(
    subscription_id: int,
    request: Request,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    ip = request.client.host if request.client else None
    return SubscriptionService.pause_subscription(
        db=db,
        subscription_id=subscription_id,
        actor=current_user,
        business_id=business_id,
        ip_address=ip
    )

@router.post("/customer/subscriptions/{subscription_id}/resume", response_model=SubscriptionOut)
def customer_resume_subscription(
    subscription_id: int,
    request: Request,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    ip = request.client.host if request.client else None
    return SubscriptionService.resume_subscription(
        db=db,
        subscription_id=subscription_id,
        actor=current_user,
        business_id=business_id,
        ip_address=ip
    )

@router.post("/customer/subscriptions/{subscription_id}/cancel", response_model=SubscriptionOut)
def customer_cancel_subscription(
    subscription_id: int,
    data: Optional[SubscriptionActionRequest] = None,
    request: Request = None,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    ip = request.client.host if request and request.client else None
    reason = data.reason if data else None
    return SubscriptionService.cancel_subscription(
        db=db,
        subscription_id=subscription_id,
        actor=current_user,
        reason=reason,
        business_id=business_id,
        ip_address=ip
    )

# --- Staff Endpoints ---
@router.get("/staff/subscriptions", response_model=List[SubscriptionOut])
def list_staff_subscriptions(
    status_filter: Optional[str] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return SubscriptionService.list_for_staff(db, status_filter=status_filter)

@router.get("/staff/subscriptions/{subscription_id}", response_model=SubscriptionOut)
def get_staff_subscription(
    subscription_id: int,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return SubscriptionService.get_subscription(db, subscription_id)

@router.post("/staff/subscriptions/{subscription_id}/pause", response_model=SubscriptionOut)
def staff_pause_subscription(
    subscription_id: int,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return SubscriptionService.pause_subscription(
        db=db,
        subscription_id=subscription_id,
        actor=staff_user,
        ip_address=ip
    )

@router.post("/staff/subscriptions/{subscription_id}/resume", response_model=SubscriptionOut)
def staff_resume_subscription(
    subscription_id: int,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return SubscriptionService.resume_subscription(
        db=db,
        subscription_id=subscription_id,
        actor=staff_user,
        ip_address=ip
    )

@router.post("/staff/subscriptions/{subscription_id}/cancel", response_model=SubscriptionOut)
def staff_cancel_subscription(
    subscription_id: int,
    data: Optional[SubscriptionActionRequest] = None,
    request: Request = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request and request.client else None
    reason = data.reason if data else None
    return SubscriptionService.cancel_subscription(
        db=db,
        subscription_id=subscription_id,
        actor=staff_user,
        reason=reason,
        ip_address=ip
    )

@router.patch("/staff/subscriptions/{subscription_id}/status", response_model=SubscriptionOut)
def update_subscription_status(
    subscription_id: int,
    data: SubscriptionStatusUpdate,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return SubscriptionService.update_status(
        db, subscription_id, staff_user, new_status=data.status, reason=data.reason, ip_address=ip
    )
