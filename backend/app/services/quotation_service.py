from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.commercial import (
    Quotation, QuotationVersion, QuotationVersionLine,
    QuotationDecision, SubscriptionRequest, Subscription, SubscriptionLine
)
from app.models.catalog import Product, Plan
from app.models.customer import CustomerBusiness
from app.models.user import User
from app.schemas.commercial import (
    QuotationCreate, QuotationRevise,
    QuotationDecisionInput, VersionDiffOut
)
from app.services.audit_service import AuditService

class QuotationService:
    @staticmethod
    def _generate_number(db: Session) -> str:
        count = db.query(Quotation).count() + 1
        year = datetime.now(timezone.utc).year
        return f"Q-{year}-{count:04d}"

    @staticmethod
    def _calculate_lines_and_totals(
        db: Session,
        lines_input: list
    ) -> Tuple[Decimal, Decimal, Decimal, Decimal, list]:
        subtotal = Decimal("0.00")
        discount_total = Decimal("0.00")
        tax_total = Decimal("0.00")
        processed_lines = []

        for line in lines_input:
            product = db.query(Product).filter(Product.id == line.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product #{line.product_id} not found.")

            plan = db.query(Plan).filter(Plan.id == line.plan_id).first()
            if not plan:
                raise HTTPException(status_code=404, detail=f"Plan #{line.plan_id} not found.")

            qty = Decimal(str(line.quantity))
            unit_price = Decimal(str(line.unit_price))
            disc_pct = Decimal(str(line.discount_percent))
            tax_pct = Decimal(str(line.tax_rate_percent))

            line_gross = qty * unit_price
            line_disc = (line_gross * disc_pct) / Decimal("100.00")
            line_net = line_gross - line_disc
            line_tax = (line_net * tax_pct) / Decimal("100.00")
            line_tot = line_net + line_tax

            subtotal += line_gross
            discount_total += line_disc
            tax_total += line_tax

            processed_lines.append({
                "product_id": line.product_id,
                "variant_id": line.variant_id,
                "plan_id": line.plan_id,
                "description": line.description or f"{product.name} ({plan.name})",
                "quantity": line.quantity,
                "unit_price": unit_price,
                "discount_percent": disc_pct,
                "discount_amount": line_disc,
                "tax_rate_percent": tax_pct,
                "tax_amount": line_tax,
                "line_total": line_tot
            })

        final_total = subtotal - discount_total + tax_total
        return subtotal, discount_total, tax_total, final_total, processed_lines

    @staticmethod
    def create_quotation(
        db: Session,
        creator: User,
        data: QuotationCreate,
        submit_for_approval: bool = True,
        ip_address: Optional[str] = None
    ) -> Quotation:
        # Check business exists
        biz = db.query(CustomerBusiness).filter(CustomerBusiness.id == data.business_id).first()
        if not biz:
            raise HTTPException(status_code=404, detail="Customer business not found.")

        if len(data.lines) == 0:
            raise HTTPException(status_code=400, detail="Quotation must contain at least one line item.")

        subtotal, disc_total, tax_total, final_total, lines = QuotationService._calculate_lines_and_totals(
            db, data.lines
        )

        q_number = QuotationService._generate_number(db)
        valid_until = datetime.now(timezone.utc) + timedelta(days=data.validity_days)

        quotation = Quotation(
            quotation_number=q_number,
            business_id=data.business_id,
            request_id=data.request_id,
            current_version_number=1,
            status="submitted_for_approval" if submit_for_approval else "draft",
            created_by_user_id=creator.id
        )
        db.add(quotation)
        db.flush()

        version = QuotationVersion(
            quotation_id=quotation.id,
            version_number=1,
            status="submitted_for_approval" if submit_for_approval else "draft",
            revision_reason="Initial quotation version",
            subtotal=subtotal,
            discount_total=disc_total,
            tax_total=tax_total,
            final_total=final_total,
            payment_terms=data.payment_terms,
            valid_until=valid_until,
            start_date=data.start_date or datetime.now(timezone.utc),
            is_latest=True,
            created_by_user_id=creator.id
        )
        db.add(version)
        db.flush()

        for l in lines:
            line_obj = QuotationVersionLine(
                quotation_version_id=version.id,
                **l
            )
            db.add(line_obj)

        # If linked to a request, update request status
        if data.request_id:
            req = db.query(SubscriptionRequest).filter(SubscriptionRequest.id == data.request_id).first()
            if req:
                req.status = "quoted"

        AuditService.log(
            db=db,
            action="create_quotation",
            entity_type="quotation",
            entity_id=str(quotation.id),
            actor_user_id=creator.id,
            actor_email=creator.email,
            actor_role=creator.user_type,
            after_state={
                "quotation_number": quotation.quotation_number,
                "version": 1,
                "final_total": str(final_total),
                "status": quotation.status
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def admin_process_decision(
        db: Session,
        admin_user: User,
        quotation_id: int,
        version_number: int,
        data: QuotationDecisionInput,
        ip_address: Optional[str] = None
    ) -> QuotationVersion:
        if admin_user.user_type != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can approve, reject, or request changes on quotations."
            )

        quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found.")

        version = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == version_number
        ).first()
        if not version:
            raise HTTPException(status_code=404, detail="Quotation version not found.")

        if version.status not in ["submitted_for_approval", "draft"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot process decision on quotation in '{version.status}' status."
            )

        if data.decision_type in ["admin_rejected", "admin_changes_requested"] and not data.reason:
            raise HTTPException(
                status_code=400,
                detail="A valid explanation reason is mandatory for rejection or change requests."
            )

        # Map decision to statuses
        if data.decision_type == "admin_approved":
            version.status = "approved"
            quotation.status = "approved"

            # Auto-provision active Subscription for customer upon Admin approval
            existing_sub = db.query(Subscription).filter(
                Subscription.accepted_quotation_id == quotation.id
            ).first()

            if not existing_sub:
                sub_count = db.query(Subscription).count() + 1
                year = datetime.now(timezone.utc).year
                sub_number = f"SUB-{year}-{sub_count:04d}"

                st_date = version.start_date or datetime.now(timezone.utc)
                if st_date.tzinfo is None:
                    st_date = st_date.replace(tzinfo=timezone.utc)
                exp_date = st_date + timedelta(days=365)

                subscription = Subscription(
                    subscription_number=sub_number,
                    business_id=quotation.business_id,
                    accepted_quotation_id=quotation.id,
                    accepted_quotation_version_id=version.id,
                    status="confirmed",
                    activation_policy="prepaid",
                    start_date=st_date,
                    expiry_date=exp_date,
                    next_billing_date=st_date,
                    billing_frequency="monthly",
                    payment_terms=version.payment_terms or "net_30",
                    total_recurring_amount=version.final_total
                )
                db.add(subscription)
                db.flush()

                for line in version.lines:
                    sub_line = SubscriptionLine(
                        subscription_id=subscription.id,
                        product_id=line.product_id,
                        variant_id=line.variant_id,
                        plan_id=line.plan_id,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        tax_rate_percent=line.tax_rate_percent,
                        line_total=line.line_total
                    )
                    db.add(sub_line)

                # Link and update customer request if tied
                if quotation.request_id:
                    req = db.query(SubscriptionRequest).filter(SubscriptionRequest.id == quotation.request_id).first()
                    if req:
                        req.status = "approved_accepted"
        elif data.decision_type == "admin_rejected":
            version.status = "rejected_by_admin"
            quotation.status = "rejected_by_admin"
        elif data.decision_type == "admin_changes_requested":
            version.status = "changes_requested"
            quotation.status = "changes_requested"

        decision = QuotationDecision(
            quotation_version_id=version.id,
            decision_maker_user_id=admin_user.id,
            decision_type=data.decision_type,
            reason=data.reason
        )
        db.add(decision)

        AuditService.log(
            db=db,
            action=data.decision_type,
            entity_type="quotation_version",
            entity_id=str(version.id),
            actor_user_id=admin_user.id,
            actor_email=admin_user.email,
            actor_role="admin",
            after_state={"decision": data.decision_type, "reason": data.reason, "version": version_number},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(version)
        return version

    @staticmethod
    def revise_quotation(
        db: Session,
        actor: User,
        quotation_id: int,
        data: QuotationRevise,
        ip_address: Optional[str] = None
    ) -> QuotationVersion:
        quotation = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found.")

        # Ensure quotation is in a revisable state
        if quotation.status == "accepted":
            raise HTTPException(
                status_code=400,
                detail="Accepted quotations are immutable. Post-acceptance amendments require a new quotation."
            )

        current_ver = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == quotation.current_version_number
        ).first()

        # Mark current version as not latest, but do not delete or modify its contents
        if current_ver:
            current_ver.is_latest = False

        new_version_num = quotation.current_version_number + 1

        subtotal, disc_total, tax_total, final_total, lines = QuotationService._calculate_lines_and_totals(
            db, data.lines
        )

        valid_days = data.validity_days or 30
        valid_until = datetime.now(timezone.utc) + timedelta(days=valid_days)

        new_version = QuotationVersion(
            quotation_id=quotation.id,
            version_number=new_version_num,
            status="submitted_for_approval",  # Every new version MUST be approved by Admin
            revision_reason=data.revision_reason,
            subtotal=subtotal,
            discount_total=disc_total,
            tax_total=tax_total,
            final_total=final_total,
            payment_terms=data.payment_terms or (current_ver.payment_terms if current_ver else "net_30"),
            valid_until=valid_until,
            start_date=data.start_date or (current_ver.start_date if current_ver else datetime.now(timezone.utc)),
            is_latest=True,
            created_by_user_id=actor.id
        )
        db.add(new_version)
        db.flush()

        for l in lines:
            line_obj = QuotationVersionLine(
                quotation_version_id=new_version.id,
                **l
            )
            db.add(line_obj)

        quotation.current_version_number = new_version_num
        quotation.status = "submitted_for_approval"

        AuditService.log(
            db=db,
            action="revise_quotation_create_version",
            entity_type="quotation_version",
            entity_id=str(new_version.id),
            actor_user_id=actor.id,
            actor_email=actor.email,
            actor_role=actor.user_type,
            after_state={
                "quotation_number": quotation.quotation_number,
                "version": new_version_num,
                "reason": data.revision_reason,
                "final_total": str(final_total)
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(new_version)
        return new_version

    @staticmethod
    def customer_process_decision(
        db: Session,
        customer_user: User,
        business_id: int,
        quotation_id: int,
        version_number: int,
        decision_type: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[QuotationVersion, Optional[Subscription]]:
        quotation = db.query(Quotation).filter(
            Quotation.id == quotation_id,
            Quotation.business_id == business_id  # Enforce tenant isolation
        ).first()
        if not quotation:
            raise HTTPException(status_code=404, detail="Quotation not found or access denied.")

        version = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == version_number
        ).first()
        if not version:
            raise HTTPException(status_code=404, detail="Quotation version not found.")

        # Check that quotation was approved by Admin
        if version.status != "approved":
            raise HTTPException(
                status_code=400,
                detail=f"Only Admin-approved quotations can be acted upon by customer (current: {version.status})."
            )

        # Check quotation expiry
        if version.valid_until:
            v_until = version.valid_until
            if v_until.tzinfo is None:
                v_until = v_until.replace(tzinfo=timezone.utc)
            if v_until < datetime.now(timezone.utc):
                version.status = "expired"
                quotation.status = "expired"
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail="This quotation has expired past its validity date and can no longer be accepted."
                )

        subscription: Optional[Subscription] = None

        if decision_type == "customer_accepted":
            version.status = "accepted"
            quotation.status = "accepted"

            # Create Confirmed Subscription based on this exact accepted version
            sub_count = db.query(Subscription).count() + 1
            year = datetime.now(timezone.utc).year
            sub_number = f"SUB-{year}-{sub_count:04d}"

            # Calculate billing and start date
            st_date = version.start_date or datetime.now(timezone.utc)
            if st_date.tzinfo is None:
                st_date = st_date.replace(tzinfo=timezone.utc)
            exp_date = st_date + timedelta(days=365)

            subscription = Subscription(
                subscription_number=sub_number,
                business_id=business_id,
                accepted_quotation_id=quotation.id,
                accepted_quotation_version_id=version.id,
                status="confirmed",
                activation_policy="prepaid",
                start_date=st_date,
                expiry_date=exp_date,
                next_billing_date=st_date,
                billing_frequency="monthly",
                payment_terms=version.payment_terms,
                total_recurring_amount=version.final_total
            )
            db.add(subscription)
            db.flush()

            for line in version.lines:
                sub_line = SubscriptionLine(
                    subscription_id=subscription.id,
                    product_id=line.product_id,
                    variant_id=line.variant_id,
                    plan_id=line.plan_id,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    tax_rate_percent=line.tax_rate_percent,
                    line_total=line.line_total
                )
                db.add(sub_line)

            # If tied to request, update request
            if quotation.request_id:
                req = db.query(SubscriptionRequest).filter(SubscriptionRequest.id == quotation.request_id).first()
                if req:
                    req.status = "approved_accepted"

        elif decision_type == "customer_rejected":
            version.status = "rejected_by_customer"
            quotation.status = "rejected_by_customer"

        decision = QuotationDecision(
            quotation_version_id=version.id,
            decision_maker_user_id=customer_user.id,
            decision_type=decision_type,
            reason=reason
        )
        db.add(decision)

        AuditService.log(
            db=db,
            action=decision_type,
            entity_type="quotation_version",
            entity_id=str(version.id),
            actor_user_id=customer_user.id,
            actor_email=customer_user.email,
            actor_role="customer",
            after_state={
                "decision": decision_type,
                "version": version_number,
                "accepted_subscription_number": subscription.subscription_number if subscription else None
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(version)
        if subscription:
            db.refresh(subscription)
        return version, subscription

    @staticmethod
    def compare_versions(
        db: Session,
        quotation_id: int,
        base_v: int,
        target_v: int
    ) -> VersionDiffOut:
        q = db.query(Quotation).filter(Quotation.id == quotation_id).first()
        if not q:
            raise HTTPException(status_code=404, detail="Quotation not found.")

        v_base = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == base_v
        ).first()
        v_target = db.query(QuotationVersion).filter(
            QuotationVersion.quotation_id == quotation_id,
            QuotationVersion.version_number == target_v
        ).first()

        if not v_base or not v_target:
            raise HTTPException(status_code=404, detail="Specified quotation versions not found.")

        sub_diff = v_target.subtotal - v_base.subtotal
        disc_diff = v_target.discount_total - v_base.discount_total
        tax_diff = v_target.tax_total - v_base.tax_total
        tot_diff = v_target.final_total - v_base.final_total

        changed_fields = []
        if sub_diff != Decimal("0.00"):
            changed_fields.append("subtotal")
        if disc_diff != Decimal("0.00"):
            changed_fields.append("discount_total")
        if tax_diff != Decimal("0.00"):
            changed_fields.append("tax_total")
        if tot_diff != Decimal("0.00"):
            changed_fields.append("final_total")
        if v_base.payment_terms != v_target.payment_terms:
            changed_fields.append("payment_terms")

        # Compare lines
        lines_comp = []
        base_lines_map = {l.plan_id: l for l in v_base.lines}
        for tl in v_target.lines:
            bl = base_lines_map.get(tl.plan_id)
            lines_comp.append({
                "plan_id": tl.plan_id,
                "description": tl.description,
                "base_quantity": bl.quantity if bl else 0,
                "target_quantity": tl.quantity,
                "quantity_diff": tl.quantity - (bl.quantity if bl else 0),
                "base_unit_price": str(bl.unit_price) if bl else "0.00",
                "target_unit_price": str(tl.unit_price),
                "base_line_total": str(bl.line_total) if bl else "0.00",
                "target_line_total": str(tl.line_total)
            })

        return VersionDiffOut(
            quotation_number=q.quotation_number,
            base_version_number=base_v,
            target_version_number=target_v,
            subtotal_diff=sub_diff,
            discount_diff=disc_diff,
            tax_diff=tax_diff,
            final_total_diff=tot_diff,
            changed_fields=changed_fields,
            lines_comparison=lines_comp
        )

    @staticmethod
    def list_quotations_for_customer(db: Session, business_id: int) -> List[Quotation]:
        return db.query(Quotation).filter(
            Quotation.business_id == business_id
        ).order_by(Quotation.created_at.desc()).all()

    @staticmethod
    def list_quotations_for_staff(db: Session, status_filter: Optional[str] = None) -> List[Quotation]:
        query = db.query(Quotation)
        if status_filter:
            query = query.filter(Quotation.status == status_filter)
        return query.order_by(Quotation.created_at.desc()).all()

    @staticmethod
    def get_quotation(db: Session, quotation_id: int, business_id: Optional[int] = None) -> Quotation:
        query = db.query(Quotation).filter(Quotation.id == quotation_id)
        if business_id is not None:
            query = query.filter(Quotation.business_id == business_id)
        q = query.first()
        if not q:
            raise HTTPException(status_code=404, detail="Quotation not found or access denied.")
        return q
