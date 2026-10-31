import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.automation import BankFeedItem
from app.models.billing import Invoice, Payment, PaymentAllocation
from app.models.customer import CustomerBusiness
from app.models.user import User
from app.schemas.automation import BankFeedItemInput, IngestBankFeedRequest
from app.services.payment_service import PaymentService
from app.services.audit_service import AuditService

class ReconciliationService:
    @staticmethod
    def _parse_invoice_reference(narration: str) -> Optional[str]:
        # Match patterns like INV-2026-0001 or INV-0001
        match = re.search(r'(INV-\d{4}-\d{4}|INV-\d+)', narration, re.IGNORECASE)
        return match.group(1).upper() if match else None

    @classmethod
    def ingest_feed_items(
        cls,
        db: Session,
        items: List[BankFeedItemInput],
        user: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> List[BankFeedItem]:
        imported_items = []
        now = datetime.now(timezone.utc)

        for input_item in items:
            # Check duplicate by transaction_id
            existing = db.query(BankFeedItem).filter(
                BankFeedItem.transaction_id == input_item.transaction_id
            ).first()
            if existing:
                continue

            tx_date = input_item.transaction_date or now
            if tx_date.tzinfo is None:
                tx_date = tx_date.replace(tzinfo=timezone.utc)

            parsed_ref = cls._parse_invoice_reference(input_item.raw_narration)
            
            # Auto-matching evaluation
            feed_status = "unmatched"
            confidence = Decimal("0.00")
            sugg_invoice_id = None
            sugg_business_id = None

            # Pass 1: Exact reference match from narration
            if parsed_ref:
                matched_inv = db.query(Invoice).filter(
                    Invoice.invoice_number == parsed_ref
                ).first()
                if matched_inv:
                    sugg_invoice_id = matched_inv.id
                    sugg_business_id = matched_inv.business_id
                    feed_status = "suggested_match"
                    # If amount also matches open balance, confidence is 1.00
                    if matched_inv.remaining_balance == input_item.amount:
                        confidence = Decimal("1.00")
                    else:
                        confidence = Decimal("0.90")

            # Pass 2: Amount match if no exact reference found
            if not sugg_invoice_id:
                candidate_invoices = db.query(Invoice).filter(
                    Invoice.status.in_(["confirmed", "partially_paid", "overdue"]),
                    Invoice.remaining_balance == input_item.amount
                ).all()

                if len(candidate_invoices) == 1:
                    cand = candidate_invoices[0]
                    sugg_invoice_id = cand.id
                    sugg_business_id = cand.business_id
                    feed_status = "suggested_match"
                    confidence = Decimal("0.75")
                elif len(candidate_invoices) > 1 and input_item.sender_name:
                    # Filter by sender name matching business company name
                    for cand in candidate_invoices:
                        if cand.business and (
                            input_item.sender_name.lower() in cand.business.company_name.lower() or
                            cand.business.company_name.lower() in input_item.sender_name.lower()
                        ):
                            sugg_invoice_id = cand.id
                            sugg_business_id = cand.business_id
                            feed_status = "suggested_match"
                            confidence = Decimal("0.85")
                            break

            item_obj = BankFeedItem(
                transaction_id=input_item.transaction_id,
                bank_account_number=input_item.bank_account_number,
                transaction_date=tx_date,
                amount=input_item.amount,
                currency=input_item.currency,
                raw_narration=input_item.raw_narration,
                parsed_reference=parsed_ref,
                sender_name=input_item.sender_name,
                status=feed_status,
                confidence_score=confidence,
                suggested_invoice_id=sugg_invoice_id,
                suggested_business_id=sugg_business_id
            )
            db.add(item_obj)
            imported_items.append(item_obj)

        if user:
            AuditService.log(
                db=db,
                action="bank_feed_ingested",
                entity_type="bank_feed",
                actor_user_id=user.id,
                actor_email=user.email,
                actor_role=user.user_type,
                after_state={"imported_count": len(imported_items)},
                ip_address=ip_address
            )

        db.commit()
        for itm in imported_items:
            db.refresh(itm)
        return imported_items

    @classmethod
    def confirm_match(
        cls,
        db: Session,
        feed_item_id: int,
        user: User,
        invoice_id: Optional[int] = None,
        allocated_amount: Optional[Decimal] = None,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> BankFeedItem:
        feed_item = db.query(BankFeedItem).filter(BankFeedItem.id == feed_item_id).first()
        if not feed_item:
            raise HTTPException(status_code=404, detail="Bank feed item not found.")

        if feed_item.status == "reconciled":
            raise HTTPException(status_code=400, detail="Transaction has already been reconciled.")

        target_inv_id = invoice_id or feed_item.suggested_invoice_id
        if not target_inv_id:
            raise HTTPException(
                status_code=400,
                detail="No target invoice specified for reconciliation match."
            )

        invoice = db.query(Invoice).filter(Invoice.id == target_inv_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Target invoice ID {target_inv_id} not found.")

        # Determine allocated amount
        alloc_amt = allocated_amount or min(feed_item.amount, invoice.remaining_balance)
        if alloc_amt <= Decimal("0.00"):
            raise HTTPException(status_code=400, detail="Allocated amount must be positive.")
        if alloc_amt > invoice.remaining_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Allocated amount ₹{alloc_amt} exceeds invoice remaining balance of ₹{invoice.remaining_balance}."
            )

        # Record realized payment through PaymentService
        from app.schemas.billing import RecordPaymentRequest, InvoicePaymentAllocationInput
        pay_request = RecordPaymentRequest(
            business_id=invoice.business_id,
            amount=feed_item.amount,
            payment_method="bank_transfer",
            reference_number=feed_item.transaction_id,
            payment_date=feed_item.transaction_date,
            notes=f"Reconciled from bank feed item {feed_item.transaction_id}: {notes or feed_item.raw_narration}",
            allocations=[InvoicePaymentAllocationInput(invoice_id=invoice.id, amount=alloc_amt)]
        )

        payment = PaymentService.record_manual_payment(
            db=db,
            user=user,
            request=pay_request,
            ip_address=ip_address
        )

        now = datetime.now(timezone.utc)
        feed_item.status = "reconciled"
        feed_item.matched_payment_id = payment.id
        feed_item.suggested_invoice_id = invoice.id
        feed_item.suggested_business_id = invoice.business_id
        feed_item.reconciliation_notes = notes
        feed_item.reconciled_by_user_id = user.id
        feed_item.reconciled_at = now

        AuditService.log(
            db=db,
            action="reconciliation_confirmed",
            entity_type="bank_feed_item",
            entity_id=str(feed_item.id),
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=user.user_type,
            after_state={
                "transaction_id": feed_item.transaction_id,
                "invoice_number": invoice.invoice_number,
                "allocated_amount": str(alloc_amt),
                "payment_number": payment.payment_number
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(feed_item)
        return feed_item

    @staticmethod
    def mark_dispute(
        db: Session,
        feed_item_id: int,
        reason: str,
        user: User,
        ip_address: Optional[str] = None
    ) -> BankFeedItem:
        feed_item = db.query(BankFeedItem).filter(BankFeedItem.id == feed_item_id).first()
        if not feed_item:
            raise HTTPException(status_code=404, detail="Bank feed item not found.")

        feed_item.status = "disputed"
        feed_item.reconciliation_notes = reason

        AuditService.log(
            db=db,
            action="reconciliation_disputed",
            entity_type="bank_feed_item",
            entity_id=str(feed_item.id),
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=user.user_type,
            after_state={"status": "disputed", "reason": reason},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(feed_item)
        return feed_item

    @staticmethod
    def list_feed_items(
        db: Session,
        status: Optional[str] = None,
        business_id: Optional[int] = None
    ) -> List[BankFeedItem]:
        query = db.query(BankFeedItem)
        if status:
            query = query.filter(BankFeedItem.status == status)
        if business_id is not None:
            query = query.filter(BankFeedItem.suggested_business_id == business_id)
        return query.order_by(BankFeedItem.transaction_date.desc(), BankFeedItem.id.desc()).all()

