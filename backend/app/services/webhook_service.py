import hmac
import hashlib
import json
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.automation import WebhookEvent
from app.models.billing import Invoice
from app.models.user import User
from app.schemas.automation import WebhookPaymentPayload, WebhookResponse
from app.schemas.billing import RecordPaymentRequest, InvoicePaymentAllocationInput
from app.services.payment_service import PaymentService
from app.services.audit_service import AuditService

class WebhookService:
    @staticmethod
    def verify_signature(raw_body: bytes, signature_header: Optional[str]) -> bool:
        if not signature_header:
            return False
        
        # Support both raw hex or sha256=hex format
        clean_signature = signature_header
        if clean_signature.startswith("sha256="):
            clean_signature = clean_signature.split("sha256=")[-1]

        expected = hmac.new(
            settings.WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(clean_signature.strip(), expected.strip())

    @classmethod
    def handle_payment_webhook(
        cls,
        db: Session,
        raw_body: bytes,
        signature_header: Optional[str],
        ip_address: Optional[str] = None
    ) -> WebhookResponse:
        # Step 1: Verify HMAC signature
        if not cls.verify_signature(raw_body, signature_header):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature."
            )

        # Step 2: Parse JSON payload
        try:
            payload_dict = json.loads(raw_body.decode("utf-8"))
            payload = WebhookPaymentPayload(**payload_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Malformed webhook payload: {str(e)}"
            )

        # Step 3: Check Idempotency via WebhookEvent.event_id
        existing_event = db.query(WebhookEvent).filter(
            WebhookEvent.event_id == payload.event_id
        ).first()

        if existing_event:
            # Already processed idempotently
            return WebhookResponse(
                status="idempotent_success",
                message=f"Event {payload.event_id} was already processed.",
                event_id=payload.event_id
            )

        # Record incoming event in webhook_events
        event_record = WebhookEvent(
            event_id=payload.event_id,
            source="payment_gateway",
            event_type=payload.event_type,
            payload_json=json.dumps(payload_dict),
            status="pending"
        )
        db.add(event_record)
        db.flush()

        # Step 4: Process event according to event_type
        if payload.event_type == "payment.captured":
            data = payload.data
            invoice = None
            if data.invoice_number:
                invoice = db.query(Invoice).filter(
                    Invoice.invoice_number == data.invoice_number
                ).first()

            if not invoice:
                event_record.status = "failed"
                event_record.processing_result = f"Invoice {data.invoice_number} not found."
                db.commit()
                return WebhookResponse(
                    status="ignored",
                    message=f"Invoice {data.invoice_number} not found.",
                    event_id=payload.event_id
                )

            # Find system/admin user to record payment actor
            admin_user = db.query(User).filter(User.user_type == "admin").first()
            if not admin_user:
                admin_user = db.query(User).first()

            alloc_amt = min(data.amount, invoice.remaining_balance)
            if alloc_amt > Decimal("0.00"):
                pay_request = RecordPaymentRequest(
                    business_id=invoice.business_id,
                    amount=data.amount,
                    payment_method=data.payment_method or "card",
                    reference_number=data.transaction_id,
                    notes=f"Webhook captured transaction {data.transaction_id}",
                    allocations=[InvoicePaymentAllocationInput(invoice_id=invoice.id, amount=alloc_amt)]
                )

                payment = PaymentService.record_manual_payment(
                    db=db,
                    user=admin_user,
                    request=pay_request,
                    ip_address=ip_address
                )

                event_record.status = "processed"
                event_record.processing_result = (
                    f"Payment {payment.payment_number} created and allocated ₹{alloc_amt} to invoice {invoice.invoice_number}."
                )
            else:
                event_record.status = "processed"
                event_record.processing_result = (
                    f"Invoice {invoice.invoice_number} already has 0 remaining balance. Payment recorded as unallocated balance."
                )

            AuditService.log(
                db=db,
                action="webhook_payment_captured",
                entity_type="webhook_event",
                entity_id=payload.event_id,
                actor_email="system@payment_gateway",
                actor_role="system",
                after_state={
                    "event_id": payload.event_id,
                    "transaction_id": data.transaction_id,
                    "invoice_number": invoice.invoice_number,
                    "amount": str(data.amount)
                },
                ip_address=ip_address
            )

        elif payload.event_type == "payment.failed":
            event_record.status = "processed"
            event_record.processing_result = f"Payment failure registered for transaction {payload.data.transaction_id}."
            
            AuditService.log(
                db=db,
                action="webhook_payment_failed",
                entity_type="webhook_event",
                entity_id=payload.event_id,
                actor_email="system@payment_gateway",
                actor_role="system",
                after_state={
                    "event_id": payload.event_id,
                    "transaction_id": payload.data.transaction_id,
                    "reason": "Payment gateway failure"
                },
                ip_address=ip_address
            )

        db.commit()
        return WebhookResponse(
            status="processed",
            message=event_record.processing_result or "Event processed successfully.",
            event_id=payload.event_id
        )

