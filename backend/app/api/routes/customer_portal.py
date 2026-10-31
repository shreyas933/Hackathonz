from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.customer import (
    CustomerBusinessOut,
    UpdateCustomerBusinessRequest,
    CustomerMemberOut,
    AddCustomerMemberRequest,
)
from app.services.customer_service import CustomerService
from app.api.deps import get_current_customer, get_current_admin, get_current_staff
from app.models.user import User
from typing import List

router = APIRouter(prefix="/customer", tags=["Customer Portal"])

@router.get("/business", response_model=CustomerBusinessOut)
def get_my_business(
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    return CustomerService.get_business_with_members(db, business_id)

@router.patch("/business", response_model=CustomerBusinessOut)
def update_my_business(
    data: UpdateCustomerBusinessRequest,
    request: Request,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Business Owner can update business information."
        )
    ip = request.client.host if request.client else None
    CustomerService.update_business(db, business_id, current_user, data, ip_address=ip)
    return CustomerService.get_business_with_members(db, business_id)

@router.post("/business/members", response_model=CustomerMemberOut)
def add_team_member(
    data: AddCustomerMemberRequest,
    request: Request,
    auth: tuple = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = auth
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the Business Owner can invite or add team members."
        )
    ip = request.client.host if request.client else None
    return CustomerService.add_business_member(db, business_id, current_user, data, ip_address=ip)

# Staff & Admin endpoint to list all customer businesses
@router.get("/admin/businesses", response_model=List[CustomerBusinessOut])
def list_all_businesses_for_staff(
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    businesses = CustomerService.list_businesses_for_admin(db)
    result = []
    for b in businesses:
        result.append(CustomerService.get_business_with_members(db, b.id))
    return result

