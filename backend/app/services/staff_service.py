from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, StaffProfile
from app.schemas.user import CreateStaffRequest, UpdateStaffPermissionsRequest
from app.core.security import get_password_hash
from app.services.audit_service import AuditService

class StaffService:
    @staticmethod
    def create_staff(
        db: Session,
        admin_user: User,
        data: CreateStaffRequest,
        ip_address: Optional[str] = None
    ) -> User:
        if admin_user.user_type != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can create internal staff accounts."
            )

        existing_user = db.query(User).filter(User.email == data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists."
            )

        user = User(
            email=data.email.lower(),
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            user_type="staff",
            is_active=True
        )
        db.add(user)
        db.flush()

        profile = StaffProfile(
            user_id=user.id,
            staff_role=data.staff_role,
            department=data.department,
            permissions_override=data.permissions_override,
            created_by_user_id=admin_user.id
        )
        db.add(profile)
        db.flush()

        AuditService.log(
            db=db,
            action="create_staff_account",
            entity_type="staff_profile",
            entity_id=str(profile.id),
            actor_user_id=admin_user.id,
            actor_email=admin_user.email,
            actor_role="admin",
            after_state={
                "email": user.email,
                "staff_role": profile.staff_role,
                "department": profile.department,
                "permissions_override": profile.permissions_override
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_staff(db: Session, admin_user: User) -> List[User]:
        if admin_user.user_type != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can view the internal staff directory."
            )
        return db.query(User).filter(User.user_type == "staff").all()

    @staticmethod
    def update_staff_permissions(
        db: Session,
        admin_user: User,
        staff_id: int,
        data: UpdateStaffPermissionsRequest,
        ip_address: Optional[str] = None
    ) -> User:
        if admin_user.user_type != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can modify staff permissions."
            )

        user = db.query(User).filter(User.id == staff_id, User.user_type == "staff").first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff account not found."
            )

        profile = db.query(StaffProfile).filter(StaffProfile.user_id == user.id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff profile not found."
            )

        before_state = {
            "staff_role": profile.staff_role,
            "department": profile.department,
            "permissions_override": profile.permissions_override,
            "is_active": user.is_active
        }

        if data.staff_role is not None:
            profile.staff_role = data.staff_role
        if data.department is not None:
            profile.department = data.department
        if data.permissions_override is not None:
            profile.permissions_override = data.permissions_override
        if data.is_active is not None:
            user.is_active = data.is_active

        after_state = {
            "staff_role": profile.staff_role,
            "department": profile.department,
            "permissions_override": profile.permissions_override,
            "is_active": user.is_active
        }

        AuditService.log(
            db=db,
            action="update_staff_permissions",
            entity_type="staff_profile",
            entity_id=str(profile.id),
            actor_user_id=admin_user.id,
            actor_email=admin_user.email,
            actor_role="admin",
            before_state=before_state,
            after_state=after_state,
            ip_address=ip_address
        )

        db.commit()
        db.refresh(user)
        return user

