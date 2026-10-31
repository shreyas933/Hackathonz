from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.automation import ReminderRule, NotificationLog
from app.models.billing import Invoice
from app.models.commercial import Subscription
from app.models.customer import CustomerBusiness
from app.models.user import User
from app.schemas.automation import ReminderRuleCreate, RunRemindersResult
from app.services.audit_service import AuditService

class ReminderService:
    @classmethod
    def run_reminders_sweep(
        cls,
        db: Session,
        target_date: Optional[datetime] = None,
        user: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> RunRemindersResult:
        now = target_date or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        target_day = now.date()

        active_rules = db.query(ReminderRule).filter(ReminderRule.is_active == True).all()
        if not active_rules:
            return RunRemindersResult(processed_invoices=0, reminders_sent=0, skipped_count=0)

        # Invoices eligible for reminders: confirmed, partially_paid, overdue
        invoices = db.query(Invoice).filter(
            Invoice.status.in_(["confirmed", "partially_paid", "overdue"]),
            Invoice.remaining_balance > Decimal("0.00")
        ).all()

        processed_count = len(invoices)
        reminders_sent = 0
        skipped_count = 0
        errors = []

        for invoice in invoices:
            try:
                # Update overdue status if past due date
                inv_due_date = invoice.due_date.date() if invoice.due_date else target_day
                if inv_due_date < target_day and invoice.status == "confirmed":
                    invoice.status = "overdue"
                    db.flush()

                days_diff = (target_day - inv_due_date).days

                # Evaluate against each active rule
                for rule in active_rules:
                    # Check trigger match
                    is_match = False
                    if rule.trigger_type == "before_due" and days_diff == rule.days_offset:
                        is_match = True
                    elif rule.trigger_type == "on_due" and days_diff == 0 and rule.days_offset == 0:
                        is_match = True
                    elif rule.trigger_type == "after_due_overdue" and days_diff == rule.days_offset:
                        is_match = True

                    if not is_match:
                        continue

                    # Strict deduplication check:
                    existing_log = db.query(NotificationLog).filter(
                        NotificationLog.invoice_id == invoice.id,
                        NotificationLog.reminder_rule_id == rule.id
                    ).first()

                    if existing_log:
                        skipped_count += 1
                        continue

                    # Render templates
                    biz_name = invoice.business.company_name if invoice.business else "Customer"
                    recipient_email = (
                        getattr(invoice.business, "contact_email", None) or "billing@example.com"
                    )

                    template_vars = {
                        "business_name": biz_name,
                        "invoice_number": invoice.invoice_number,
                        "amount_due": f"₹{invoice.remaining_balance:,.2f}",
                        "remaining_balance": f"₹{invoice.remaining_balance:,.2f}",
                        "final_total": f"₹{invoice.final_total:,.2f}",
                        "due_date": invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "",
                        "currency": invoice.currency or "INR"
                    }

                    subject = rule.subject_template
                    body = rule.body_template
                    for k, v in template_vars.items():
                        subject = subject.replace(f"{{{k}}}", str(v))
                        body = body.replace(f"{{{k}}}", str(v))

                    # Create NotificationLog entry
                    notif = NotificationLog(
                        business_id=invoice.business_id,
                        invoice_id=invoice.id,
                        subscription_id=invoice.subscription_id,
                        reminder_rule_id=rule.id,
                        recipient_email=recipient_email,
                        channel=rule.channel,
                        subject=subject,
                        content=body,
                        status="delivered",
                        sent_at=now,
                        is_read=False
                    )
                    db.add(notif)
                    reminders_sent += 1

            except Exception as e:
                errors.append(f"Error processing invoice {invoice.invoice_number}: {str(e)}")

        if user:
            AuditService.log(
                db=db,
                action="reminder_sweep_executed",
                entity_type="automation",
                actor_user_id=user.id,
                actor_email=user.email,
                actor_role=user.user_type,
                after_state={
                    "processed_invoices": processed_count,
                    "reminders_sent": reminders_sent,
                    "skipped_count": skipped_count
                },
                ip_address=ip_address
            )

        db.commit()
        return RunRemindersResult(
            processed_invoices=processed_count,
            reminders_sent=reminders_sent,
            skipped_count=skipped_count,
            errors=errors
        )

    @staticmethod
    def list_rules(db: Session) -> List[ReminderRule]:
        return db.query(ReminderRule).order_by(ReminderRule.days_offset.asc()).all()

    @staticmethod
    def create_rule(db: Session, data: ReminderRuleCreate) -> ReminderRule:
        rule = ReminderRule(**data.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def list_history(
        db: Session,
        business_id: Optional[int] = None,
        invoice_id: Optional[int] = None
    ) -> List[NotificationLog]:
        query = db.query(NotificationLog)
        if business_id is not None:
            query = query.filter(NotificationLog.business_id == business_id)
        if invoice_id is not None:
            query = query.filter(NotificationLog.invoice_id == invoice_id)
        return query.order_by(NotificationLog.created_at.desc()).all()

    @staticmethod
    def list_customer_notifications(
        db: Session,
        business_id: int,
        unread_only: bool = False
    ) -> List[NotificationLog]:
        query = db.query(NotificationLog).filter(NotificationLog.business_id == business_id)
        if unread_only:
            query = query.filter(NotificationLog.is_read == False)
        return query.order_by(NotificationLog.created_at.desc()).all()

    @staticmethod
    def mark_notification_read(
        db: Session,
        notification_id: int,
        business_id: int
    ) -> NotificationLog:
        notif = db.query(NotificationLog).filter(
            NotificationLog.id == notification_id,
            NotificationLog.business_id == business_id
        ).first()
        if not notif:
            raise HTTPException(status_code=404, detail="Notification not found.")

        notif.is_read = True
        db.commit()
        db.refresh(notif)
        return notif
