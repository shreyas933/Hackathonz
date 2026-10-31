from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.automation import (
    ReminderRuleCreate,
    ReminderRuleOut,
    NotificationLogOut,
    RunRemindersRequest,
    RunRemindersResult
)
from app.services.reminder_service import ReminderService
from app.api.deps import get_current_admin, get_current_staff, get_current_customer

router = APIRouter(tags=["Reminders & Notifications"])

# --- Internal Staff & Admin Routes ---

@router.get("/reminders/rules", response_model=List[ReminderRuleOut])
def get_reminder_rules(
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return ReminderService.list_rules(db=db)

@router.post("/reminders/rules", response_model=ReminderRuleOut)
def create_reminder_rule(
    data: ReminderRuleCreate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return ReminderService.create_rule(db=db, data=data)

@router.post("/reminders/run", response_model=RunRemindersResult)
def trigger_reminders_run(
    data: Optional[RunRemindersRequest] = None,
    request: Request = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ip = request.client.host if request and request.client else None
    target_date = data.target_date if data else None
    return ReminderService.run_reminders_sweep(
        db=db,
        target_date=target_date,
        user=staff_user,
        ip_address=ip
    )

@router.get("/reminders/history", response_model=List[NotificationLogOut])
def get_reminder_history(
    business_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    staff_user: User = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return ReminderService.list_history(
        db=db,
        business_id=business_id,
        invoice_id=invoice_id
    )

# --- Customer Portal Routes ---

@router.get("/customer/notifications", response_model=List[NotificationLogOut])
def get_customer_notifications(
    unread_only: bool = False,
    customer_ctx: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = customer_ctx
    return ReminderService.list_customer_notifications(
        db=db,
        business_id=business_id,
        unread_only=unread_only
    )

@router.patch("/customer/notifications/{notification_id}/read", response_model=NotificationLogOut)
def mark_notification_read(
    notification_id: int,
    customer_ctx: tuple[User, int, str] = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    current_user, business_id, role = customer_ctx
    return ReminderService.mark_notification_read(
        db=db,
        notification_id=notification_id,
        business_id=business_id
    )

