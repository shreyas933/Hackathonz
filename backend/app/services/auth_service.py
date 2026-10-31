from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, StaffProfile
from app.models.customer import CustomerBusiness, CustomerMembership
from app.schemas.auth import RegisterCustomerRequest, LoginRequest
from app.core.security import verify_password, get_password_hash, create_access_token
from app.services.audit_service import AuditService

class AuthService:
    @staticmethod
    def register_customer(db: Session, data: RegisterCustomerRequest, ip_address: Optional[str] = None) -> Tuple[User, str, int]:
        # Check if email exists
        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

        # 1. Create Business
        business = CustomerBusiness(
            company_name=data.company_name,
            legal_name=data.legal_name or data.company_name,
            tax_id=data.tax_id,
            billing_address=data.billing_address,
            billing_city=data.billing_city,
            billing_state=data.billing_state,
            billing_postal_code=data.billing_postal_code,
            billing_country=data.billing_country,
            contact_email=data.email.lower(),
            contact_phone=data.contact_phone,
            status="active"
        )
        db.add(business)
        db.flush()

        # 2. Create User
        user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            user_type="customer",
            is_active=True
        )
        db.add(user)
        db.flush()

        # 3. Create Membership
        membership = CustomerMembership(
            user_id=user.id,
            business_id=business.id,
            role="owner",
            is_primary=True
        )
        db.add(membership)
        db.flush()

        # 4. Audit Log
        AuditService.log(
            db=db,
            action="customer_registered",
            entity_type="customer_business",
            entity_id=str(business.id),
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role="owner",
            after_state={"company_name": business.company_name, "owner_email": user.email},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(user)

        # Generate JWT
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "user_type": user.user_type,
            "role": "owner",
            "business_id": business.id
        }
        token = create_access_token(token_payload)
        return user, token, business.id

    @staticmethod
    def authenticate(db: Session, data: LoginRequest) -> Tuple[User, str, str, Optional[int]]:
        user = db.query(User).filter(User.email == data.email.lower()).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support."
            )

        role = user.user_type
        business_id: Optional[int] = None

        if user.user_type == "staff":
            staff_profile = db.query(StaffProfile).filter(StaffProfile.user_id == user.id).first()
            if not staff_profile:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Staff profile not configured."
                )
            role = staff_profile.staff_role

        elif user.user_type == "customer":
            membership = db.query(CustomerMembership).filter(
                CustomerMembership.user_id == user.id
            ).first()
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No business membership found for this user."
                )
            role = membership.role
            business_id = membership.business_id

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "user_type": user.user_type,
            "role": role,
            "business_id": business_id
        }
        token = create_access_token(token_payload)
        return user, token, role, business_id

