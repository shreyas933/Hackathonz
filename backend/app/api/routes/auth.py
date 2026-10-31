from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import (
    RegisterCustomerRequest,
    LoginRequest,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.user import UserOut
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register-customer", response_model=TokenResponse)
def register_customer(data: RegisterCustomerRequest, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    user, token, business_id = AuthService.register_customer(db, data, ip_address=ip)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_type=user.user_type,
        role="owner",
        business_id=business_id,
        email=user.email,
        full_name=user.full_name,
    )

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user, token, role, business_id = AuthService.authenticate(db, data)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_type=user.user_type,
        role=role,
        business_id=business_id,
        email=user.email,
        full_name=user.full_name,
    )

@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = current_user.user_type
    business_id = None
    if current_user.user_type == "staff" and current_user.staff_profile:
        role = current_user.staff_profile.staff_role
    elif current_user.user_type == "customer":
        from app.models.customer import CustomerMembership
        mem = db.query(CustomerMembership).filter(CustomerMembership.user_id == current_user.id).first()
        if mem:
            role = mem.role
            business_id = mem.business_id

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "user_type": current_user.user_type,
        "role": role,
        "business_id": business_id,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
    }

