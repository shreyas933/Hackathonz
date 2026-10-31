from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.models.customer import CustomerBusiness, CustomerMembership
from app.schemas.customer import (
    CustomerBusinessOut,
    UpdateCustomerBusinessRequest,
    CustomerMemberOut,
    AddCustomerMemberRequest,
)
from app.core.security import get_password_hash
from app.services.audit_service import AuditService

class CustomerService:
    @staticmethod
    def get_business(db: Session, business_id: int) -> CustomerBusiness:
        business = db.query(CustomerBusiness).filter(CustomerBusiness.id == business_id).first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer business not found."
            )
        return business

    @staticmethod
    def get_business_with_members(db: Session, business_id: int) -> dict:
        business = CustomerService.get_business(db, business_id)
        memberships = db.query(CustomerMembership).filter(
            CustomerMembership.business_id == business_id
        ).all()

        members_data = []
        for m in memberships:
            user = db.query(User).filter(User.id == m.user_id).first()
            if user:
                members_data.append({
                    "id": m.id,
                    "user_id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": m.role,
                    "is_primary": m.is_primary,
                    "created_at": m.created_at
                })

        return {
            "id": business.id,
            "company_name": business.company_name,
            "legal_name": business.legal_name,
            "tax_id": business.tax_id,
            "billing_address": business.billing_address,
            "billing_city": business.billing_city,
            "billing_state": business.billing_state,
            "billing_postal_code": business.billing_postal_code,
            "billing_country": business.billing_country,
            "contact_email": business.contact_email,
            "contact_phone": business.contact_phone,
            "status": business.status,
            "created_at": business.created_at,
            "members": members_data
        }

    @staticmethod
    def update_business(
        db: Session,
        business_id: int,
        actor: User,
        data: UpdateCustomerBusinessRequest,
        ip_address: Optional[str] = None
    ) -> CustomerBusiness:
        business = CustomerService.get_business(db, business_id)
        before_state = {
            "company_name": business.company_name,
            "tax_id": business.tax_id,
            "billing_address": business.billing_address,
            "contact_phone": business.contact_phone
        }

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(business, field, value)

        after_state = {
            "company_name": business.company_name,
            "tax_id": business.tax_id,
            "billing_address": business.billing_address,
            "contact_phone": business.contact_phone
        }

        AuditService.log(
            db=db,
            action="update_customer_business",
            entity_type="customer_business",
            entity_id=str(business.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role="owner",
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address
        )

        db.commit()
        db.refresh(business)
        return business

    @staticmethod
    def add_business_member(
        db: Session,
        business_id: int,
        actor: User,
        data: AddCustomerMemberRequest,
        ip_address: Optional[str] = None
    ) -> CustomerMemberOut:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            # Check if already a member of this business
            existing_mem = db.query(CustomerMembership).filter(
                CustomerMembership.user_id == existing_user.id,
                CustomerMembership.business_id == business_id
            ).first()
            if existing_mem:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This user is already a member of this business."
                )
            user = existing_user
        else:
            user = User(
                email=data.email.lower(),
                hashed_password=get_password_hash(data.password),
                full_name=data.full_name,
                user_type="customer",
                is_active=True
            )
            db.add(user)
            db.flush()

        membership = CustomerMembership(
            user_id=user.id,
            business_id=business_id,
            role=data.role,
            is_primary=False
        )
        db.add(membership)
        db.flush()

        AuditService.log(
            db=db,
            action="add_customer_member",
            entity_type="customer_membership",
            entity_id=str(membership.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role="owner",
            after_state={
                "email": user.email,
                "role": membership.role,
                "business_id": business_id
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(membership)

        return CustomerMemberOut(
            id=membership.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role,
            is_primary=membership.is_primary,
            created_at=membership.created_at
        )

    @staticmethod
    def list_businesses_for_admin(db: Session) -> List[CustomerBusiness]:
        return db.query(CustomerBusiness).order_by(CustomerBusiness.created_at.desc()).all()

