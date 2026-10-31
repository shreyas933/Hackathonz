from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserOut, CreateStaffRequest, UpdateStaffPermissionsRequest
from app.services.staff_service import StaffService
from app.api.deps import get_current_admin
from app.models.user import User

router = APIRouter(prefix="/admin/staff", tags=["Admin Staff Management"])

@router.get("", response_model=List[UserOut])
def list_staff(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    return StaffService.list_staff(db, admin_user)

@router.post("", response_model=UserOut)
def create_staff(
    data: CreateStaffRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return StaffService.create_staff(db, admin_user, data, ip_address=ip)

@router.patch("/{staff_id}/permissions", response_model=UserOut)
def update_staff_permissions(
    staff_id: int,
    data: UpdateStaffPermissionsRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin)
):
    ip = request.client.host if request.client else None
    return StaffService.update_staff_permissions(db, admin_user, staff_id, data, ip_address=ip)

