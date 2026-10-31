from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.commercial import (
    SubscriptionRequestCreate, SubscriptionRequestUpdate,
    SubscriptionRequestOut, RequestActivityCreate, RequestActivityOut
)
from app.services.request_service import RequestService
from app.api.deps import get_current_customer, get_current_staff, get_current_user
from app.models.user import User

router = APIRouter(tags=["Subscription Requests"])

# --- Customer Endpoints ---
@router.post("/customer/requests", response_model=SubscriptionRequestOut)
def create_customer_request(
    data: SubscriptionRequestCreate,
    request: Request,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    ip = request.client.host if request.client else None
    return RequestService.create_request(db, business_id, current_user, data, ip_address=ip)

@router.get("/customer/requests", response_model=List[SubscriptionRequestOut])
def list_customer_requests(
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return RequestService.list_requests_for_customer(db, business_id)

@router.get("/customer/requests/{request_id}", response_model=SubscriptionRequestOut)
def get_customer_request(
    request_id: int,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return RequestService.get_request(db, request_id, business_id=business_id)

@router.post("/customer/requests/{request_id}/activity", response_model=RequestActivityOut)
def add_customer_request_activity(
    request_id: int,
    data: RequestActivityCreate,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return RequestService.add_activity(db, request_id, current_user, data, business_id=business_id)

# --- Staff Endpoints ---
@router.get("/staff/requests", response_model=List[SubscriptionRequestOut])
def list_staff_requests(
    request_type: Optional[str] = None,
    status_filter: Optional[str] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return RequestService.list_requests_for_staff(db, request_type=request_type, status_filter=status_filter)

@router.get("/staff/requests/{request_id}", response_model=SubscriptionRequestOut)
def get_staff_request(
    request_id: int,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return RequestService.get_request(db, request_id)

@router.patch("/staff/requests/{request_id}", response_model=SubscriptionRequestOut)
def update_staff_request(
    request_id: int,
    data: SubscriptionRequestUpdate,
    request: Request,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else None
    return RequestService.update_request_by_staff(db, request_id, staff_user, data, ip_address=ip)

@router.post("/staff/requests/{request_id}/activity", response_model=RequestActivityOut)
def add_staff_request_activity(
    request_id: int,
    data: RequestActivityCreate,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return RequestService.add_activity(db, request_id, staff_user, data)

