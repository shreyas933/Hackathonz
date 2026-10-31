from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.billing import Payment, PaymentAllocation, Invoice
from app.models.customer import CustomerBusiness
from app.models.commercial import Subscription
from app.models.user import User
from app.schemas.billing import RecordPaymentRequest
from app.services.audit_service import AuditService

class PaymentService:
    @staticmethod
    def _generate_payment_number(db: Session) -> str:
        current_year = datetime.now(timezone.utc).year
        count = db.query(func.count(Payment.id)).scalar() or 0
        return f"PAY-{current_year}-{(count + 1):04d}"

    @classmethod
    def record_manual_payment(
        cls,
        db: Session,
        user: User,
        request: RecordPaymentRequest,
        ip_address: Optional[str] = None
    ) -> Payment:
        business = db.query(CustomerBusiness).filter(CustomerBusiness.id == request.business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Customer business not found.")

        # Validate total allocation does not exceed payment amount
        total_allocated = sum((alloc.amount for alloc in request.allocations), Decimal("0.00"))
        if total_allocated > request.amount:
            raise HTTPException(
                status_code=400,
                detail=f"Total allocated amount (₹{total_allocated}) cannot exceed total payment amount (₹{request.amount})."
            )

        now = datetime.now(timezone.utc)
        pay_date = request.payment_date or now
        if pay_date.tzinfo is None:
            pay_date = pay_date.replace(tzinfo=timezone.utc)

        payment_number = cls._generate_payment_number(db)

        # Determine initial reconciliation status
        if total_allocated == request.amount:
            recon_status = "reconciled"
        elif total_allocated > Decimal("0.00"):
            recon_status = "partially_allocated"
        else:
            recon_status = "unmatched"

        payment = Payment(
            payment_number=payment_number,
            business_id=business.id,
            amount=request.amount,
            currency="INR",
            payment_method=request.payment_method,
            payment_date=pay_date,
            reference_number=request.reference_number,
            source="manual",
            reconciliation_status=recon_status,
            notes=request.notes,
            created_by_user_id=user.id
        )
        db.add(payment)
        db.flush()

        for alloc_input in request.allocations:
            invoice = db.query(Invoice).filter(Invoice.id == alloc_input.invoice_id).first()
            if not invoice:
                raise HTTPException(status_code=404, detail=f"Invoice ID {alloc_input.invoice_id} not found.")

            if invoice.business_id != business.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invoice {invoice.invoice_number} does not belong to business {business.company_name}."
                )

            if alloc_input.amount > invoice.remaining_balance:
                raise HTTPException(
                    status_code=400,
                    detail=f"Allocation amount ₹{alloc_input.amount} exceeds invoice {invoice.invoice_number} remaining balance of ₹{invoice.remaining_balance}."
                )

            # Create allocation record
            allocation = PaymentAllocation(
                payment_id=payment.id,
                invoice_id=invoice.id,
                allocated_amount=alloc_input.amount
            )
            db.add(allocation)

            # Update invoice balance and status
            invoice.amount_paid += alloc_input.amount
            invoice.remaining_balance = invoice.final_total - invoice.amount_paid

            if invoice.remaining_balance == Decimal("0.00"):
                invoice.status = "paid"
                # If subscription is prepaid, activate it upon full payment
                if invoice.subscription_id:
                    sub = db.query(Subscription).filter(Subscription.id == invoice.subscription_id).first()
                    if sub and sub.status in ["confirmed", "draft"]:
                        sub.status = "active"
                        AuditService.log(
                            db=db,
                            action="subscription_activated_by_payment",
                            entity_type="subscription",
                            entity_id=str(sub.id),
                            actor_user_id=user.id,
                            actor_email=user.email,
                            actor_role=user.user_type,
                            after_state={
                                "status": "active",
                                "invoice_number": invoice.invoice_number,
                                "payment_number": payment.payment_number
                            },
                            ip_address=ip_address
                        )
            else:
                invoice.status = "partially_paid"

        AuditService.log(
            db=db,
            action="payment_recorded",
            entity_type="payment",
            entity_id=str(payment.id),
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=user.user_type,
            after_state={
                "payment_number": payment.payment_number,
                "amount": str(payment.amount),
                "business_id": business.id,
                "reconciliation_status": recon_status
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def list_payments(
        db: Session,
        business_id: Optional[int] = None,
        reconciliation_status: Optional[str] = None
    ) -> List[Payment]:
        query = db.query(Payment)
        if business_id is not None:
            query = query.filter(Payment.business_id == business_id)
        if reconciliation_status:
            query = query.filter(Payment.reconciliation_status == reconciliation_status)
        return query.order_by(Payment.payment_date.desc(), Payment.id.desc()).all()

    @staticmethod
    def get_payment(db: Session, payment_id: int, business_id: Optional[int] = None) -> Payment:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found.")
        if business_id is not None and payment.business_id != business_id:
            raise HTTPException(status_code=403, detail="Access denied to payment from another business.")
        return payment

