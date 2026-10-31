from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.billing import Invoice, InvoiceLine
from app.models.commercial import Quotation, QuotationVersion, Subscription, SubscriptionLine
from app.models.user import User
from app.schemas.billing import GenerateInvoiceFromQuotationRequest, RecurringBillingRunResult
from app.services.audit_service import AuditService

class BillingService:
    @staticmethod
    def _generate_invoice_number(db: Session) -> str:
        current_year = datetime.now(timezone.utc).year
        count = db.query(func.count(Invoice.id)).scalar() or 0
        return f"INV-{current_year}-{(count + 1):04d}"

    @classmethod
    def generate_from_quotation(
        cls,
        db: Session,
        user: User,
        request: GenerateInvoiceFromQuotationRequest,
        ip_address: Optional[str] = None
    ) -> Invoice:
        quotation = db.query(Quotation).filter(Quotation.id == request.quotation_id).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found.")

        # Find requested version or the accepted version
        if request.version_number:
            version = db.query(QuotationVersion).filter(
                QuotationVersion.quotation_id == quotation.id,
                QuotationVersion.version_number == request.version_number
            ).first()
        else:
            version = db.query(QuotationVersion).filter(
                QuotationVersion.quotation_id == quotation.id,
                QuotationVersion.status == "accepted"
            ).order_by(QuotationVersion.version_number.desc()).first()

        if not version:
            raise HTTPException(
                status_code=400,
                detail="No matching quotation version found."
            )

        if version.status != "accepted":
            raise HTTPException(
                status_code=400,
                detail=f"Quotation version {version.version_number} is not accepted (status: {version.status}). Only accepted quotations can be invoiced."
            )

        # Check if already invoiced for this quotation version
        existing_invoice = db.query(Invoice).filter(
            Invoice.quotation_version_id == version.id
        ).first()
        if existing_invoice:
            raise HTTPException(
                status_code=400,
                detail=f"Quotation version {version.version_number} has already been invoiced under {existing_invoice.invoice_number}."
            )

        # Find linked subscription
        subscription = db.query(Subscription).filter(
            Subscription.accepted_quotation_version_id == version.id
        ).first()

        now = datetime.now(timezone.utc)
        
        # Calculate due date
        if request.due_date:
            due_date = request.due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
        else:
            days = 30
            if version.payment_terms == "net_15":
                days = 15
            elif version.payment_terms == "net_60":
                days = 60
            elif version.payment_terms == "due_on_receipt":
                days = 0
            due_date = now + timedelta(days=days)

        invoice_number = cls._generate_invoice_number(db)
        billing_period = f"initial_{now.strftime('%Y%m')}"

        invoice = Invoice(
            invoice_number=invoice_number,
            business_id=quotation.business_id,
            subscription_id=subscription.id if subscription else None,
            quotation_version_id=version.id,
            billing_period=billing_period,
            issue_date=now,
            due_date=due_date,
            subtotal=version.subtotal,
            discount_total=version.discount_total,
            tax_total=version.tax_total,
            final_total=version.final_total,
            amount_paid=Decimal("0.00"),
            remaining_balance=version.final_total,
            currency="INR",
            payment_terms=version.payment_terms,
            status="confirmed",
            notes=request.notes
        )
        db.add(invoice)
        db.flush()

        for line in version.lines:
            inv_line = InvoiceLine(
                invoice_id=invoice.id,
                product_id=line.product_id,
                variant_id=line.variant_id,
                plan_id=line.plan_id,
                description=line.description or (line.product.name if line.product else "Software License"),
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_amount=line.discount_amount,
                tax_rate_percent=line.tax_rate_percent,
                tax_amount=line.tax_amount,
                line_total=line.line_total
            )
            db.add(inv_line)

        AuditService.log(
            db=db,
            action="invoice_generated_from_quotation",
            entity_type="invoice",
            entity_id=str(invoice.id),
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=user.user_type,
            after_state={
                "invoice_number": invoice.invoice_number,
                "final_total": str(invoice.final_total),
                "quotation_id": quotation.id,
                "version_number": version.version_number
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(invoice)
        return invoice

    @classmethod
    def run_recurring_billing(
        cls,
        db: Session,
        user: User,
        target_date: Optional[datetime] = None,
        ip_address: Optional[str] = None
    ) -> RecurringBillingRunResult:
        if target_date is None:
            target_date = datetime.now(timezone.utc)
        elif target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone.utc)

        subscriptions = db.query(Subscription).filter(
            Subscription.status.in_(["active", "confirmed"]),
            Subscription.next_billing_date <= target_date
        ).all()

        processed_count = 0
        invoices_generated = 0
        skipped_idempotent = 0
        errors = []

        for sub in subscriptions:
            processed_count += 1
            if not sub.next_billing_date:
                continue

            cycle_date = sub.next_billing_date
            if cycle_date.tzinfo is None:
                cycle_date = cycle_date.replace(tzinfo=timezone.utc)

            period_key = f"cycle_{cycle_date.strftime('%Y-%m')}"

            # Check idempotency constraint
            existing = db.query(Invoice).filter(
                Invoice.subscription_id == sub.id,
                Invoice.billing_period == period_key
            ).first()

            if existing:
                skipped_idempotent += 1
                continue

            try:
                # Calculate totals from subscription lines
                subtotal = Decimal("0.00")
                tax_total = Decimal("0.00")
                final_total = Decimal("0.00")

                for line in sub.lines:
                    subtotal += (line.unit_price * line.quantity)
                    line_tax = (line.unit_price * line.quantity * line.tax_rate_percent) / Decimal("100.00")
                    tax_total += line_tax
                    final_total += line.line_total

                if final_total == Decimal("0.00") and subtotal > Decimal("0.00"):
                    final_total = subtotal + tax_total

                # Calculate due date
                days = 30
                if sub.payment_terms == "net_15":
                    days = 15
                elif sub.payment_terms == "net_60":
                    days = 60
                elif sub.payment_terms == "due_on_receipt":
                    days = 0
                due_date = cycle_date + timedelta(days=days)

                invoice_number = cls._generate_invoice_number(db)
                invoice = Invoice(
                    invoice_number=invoice_number,
                    business_id=sub.business_id,
                    subscription_id=sub.id,
                    quotation_version_id=sub.accepted_quotation_version_id,
                    billing_period=period_key,
                    issue_date=cycle_date,
                    due_date=due_date,
                    subtotal=subtotal,
                    discount_total=Decimal("0.00"),
                    tax_total=tax_total,
                    final_total=final_total,
                    amount_paid=Decimal("0.00"),
                    remaining_balance=final_total,
                    currency="INR",
                    payment_terms=sub.payment_terms,
                    status="confirmed",
                    notes=f"Recurring billing invoice for cycle {period_key}"
                )
                db.add(invoice)
                db.flush()

                for line in sub.lines:
                    line_tax = (line.unit_price * line.quantity * line.tax_rate_percent) / Decimal("100.00")
                    inv_line = InvoiceLine(
                        invoice_id=invoice.id,
                        product_id=line.product_id,
                        variant_id=line.variant_id,
                        plan_id=line.plan_id,
                        description=f"Subscription recurring fee for {line.product.name if line.product else 'Plan'}",
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        discount_amount=Decimal("0.00"),
                        tax_rate_percent=line.tax_rate_percent,
                        tax_amount=line_tax,
                        line_total=line.line_total
                    )
                    db.add(inv_line)

                # Advance next_billing_date
                if sub.billing_frequency == "annual":
                    sub.next_billing_date = cycle_date + timedelta(days=365)
                elif sub.billing_frequency == "quarterly":
                    sub.next_billing_date = cycle_date + timedelta(days=90)
                else:
                    sub.next_billing_date = cycle_date + timedelta(days=30)

                db.flush()
                invoices_generated += 1

                AuditService.log(
                    db=db,
                    action="recurring_invoice_generated",
                    entity_type="invoice",
                    entity_id=str(invoice.id),
                    actor_user_id=user.id,
                    actor_email=user.email,
                    actor_role=user.user_type,
                    after_state={
                        "invoice_number": invoice.invoice_number,
                        "subscription_id": sub.id,
                        "billing_period": period_key,
                        "final_total": str(invoice.final_total)
                    },
                    ip_address=ip_address
                )

            except Exception as e:
                db.rollback()
                errors.append(f"Subscription {sub.subscription_number}: {str(e)}")
                continue

        db.commit()
        return RecurringBillingRunResult(
            processed_count=processed_count,
            invoices_generated=invoices_generated,
            skipped_idempotent=skipped_idempotent,
            errors=errors
        )

    @staticmethod
    def get_invoice(db: Session, invoice_id: int, business_id: Optional[int] = None) -> Invoice:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")
        if business_id is not None and invoice.business_id != business_id:
            raise HTTPException(status_code=403, detail="Access denied to invoice from another business.")
        return invoice

    @staticmethod
    def list_invoices(
        db: Session,
        business_id: Optional[int] = None,
        status: Optional[str] = None,
        subscription_id: Optional[int] = None
    ) -> List[Invoice]:
        query = db.query(Invoice)
        if business_id is not None:
            query = query.filter(Invoice.business_id == business_id)
        if status:
            query = query.filter(Invoice.status == status)
        if subscription_id:
            query = query.filter(Invoice.subscription_id == subscription_id)
        return query.order_by(Invoice.issue_date.desc(), Invoice.id.desc()).all()

    @staticmethod
    def update_invoice_status(
        db: Session,
        invoice_id: int,
        new_status: str,
        notes: Optional[str],
        user: User,
        ip_address: Optional[str] = None
    ) -> Invoice:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found.")

        old_status = invoice.status
        invoice.status = new_status
        if notes:
            invoice.notes = f"{invoice.notes or ''}\nStatus update: {notes}".strip()

        AuditService.log(
            db=db,
            action="invoice_status_updated",
            entity_type="invoice",
            entity_id=str(invoice.id),
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=user.user_type,
            before_state={"status": old_status},
            after_state={"status": new_status, "notes": notes},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(invoice)
        return invoice

