from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.commercial import Subscription, SubscriptionLine, Quotation, QuotationVersion, SubscriptionRequest
from app.models.billing import Invoice, Payment
from app.models.customer import CustomerBusiness
from app.models.automation import BankFeedItem, NotificationLog
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardMetrics,
    SalesDashboardMetrics,
    FinanceDashboardMetrics,
    CustomerDashboardMetrics,
    CopilotQueryRequest,
    CopilotQueryResponse
)

class DashboardService:
    @classmethod
    def get_admin_dashboard(cls, db: Session) -> AdminDashboardMetrics:
        now = datetime.now(timezone.utc)
        
        # Subscriptions & MRR calculation
        active_subs = db.query(Subscription).filter(Subscription.status == "active").all()
        mrr = Decimal("0.00")
        for sub in active_subs:
            for line in sub.lines:
                freq = line.plan.billing_frequency if line.plan else "monthly"
                line_val = line.unit_price * line.quantity
                if freq == "monthly":
                    mrr += line_val
                elif freq == "yearly":
                    mrr += (line_val / Decimal("12.00"))
                elif freq == "weekly":
                    mrr += (line_val * Decimal("4.00"))
                elif freq == "daily":
                    mrr += (line_val * Decimal("30.00"))

        arr = mrr * Decimal("12.00")
        total_customers = db.query(CustomerBusiness).filter(CustomerBusiness.status == "active").count()
        
        # Financial aggregates
        invoices = db.query(Invoice).filter(Invoice.status != "cancelled").all()
        total_invoiced = sum((inv.final_total for inv in invoices), Decimal("0.00"))
        
        payments = db.query(Payment).all()
        total_collected = sum((pay.amount for pay in payments), Decimal("0.00"))

        overdue_invoices = [
            inv for inv in invoices 
            if inv.remaining_balance > Decimal("0.00") and (
                inv.status == "overdue" or (inv.due_date and inv.due_date.replace(tzinfo=timezone.utc if inv.due_date.tzinfo is None else None) < now)
            )
        ]
        total_overdue = sum((inv.remaining_balance for inv in overdue_invoices), Decimal("0.00"))

        # Pipeline counters
        pending_admin_approvals = db.query(Quotation).filter(Quotation.status == "submitted_for_approval").count()
        
        # Accepted quotes awaiting invoice
        accepted_quotes = db.query(Quotation).filter(Quotation.status == "accepted").all()
        invoiced_quote_ids = {inv.quotation_version.quotation_id for inv in invoices if inv.quotation_version}
        accepted_awaiting_invoice = len([q for q in accepted_quotes if q.id not in invoiced_quote_ids])

        unmatched_bank_feeds = db.query(BankFeedItem).filter(
            BankFeedItem.status.in_(["unmatched", "suggested_match"])
        ).count()

        recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(8).all()
        recent_activity = [
            {
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "actor_email": log.actor_email or "system",
                "timestamp": log.created_at.isoformat()
            }
            for log in recent_logs
        ]

        return AdminDashboardMetrics(
            mrr=mrr.quantize(Decimal("0.01")),
            arr=arr.quantize(Decimal("0.01")),
            total_customers=total_customers,
            active_subscriptions=len(active_subs),
            total_invoiced=total_invoiced.quantize(Decimal("0.01")),
            total_collected=total_collected.quantize(Decimal("0.01")),
            total_overdue=total_overdue.quantize(Decimal("0.01")),
            pending_admin_approvals=pending_admin_approvals,
            accepted_awaiting_invoice=accepted_awaiting_invoice,
            unmatched_bank_feeds=unmatched_bank_feeds,
            recent_activity=recent_activity
        )

    @classmethod
    def get_sales_dashboard(cls, db: Session, user: User) -> SalesDashboardMetrics:
        new_requests_count = db.query(SubscriptionRequest).filter(SubscriptionRequest.status == "new").count()
        draft_quotations_count = db.query(Quotation).filter(Quotation.status == "draft").count()
        pending_approval_quotations_count = db.query(Quotation).filter(Quotation.status == "submitted_for_approval").count()
        approved_awaiting_customer_count = db.query(Quotation).filter(Quotation.status == "approved").count()
        accepted_quotations_count = db.query(Quotation).filter(Quotation.status == "accepted").count()

        # Pipeline value from non-rejected, non-expired quotes
        open_quotes = db.query(Quotation).filter(
            Quotation.status.in_(["draft", "submitted_for_approval", "approved"])
        ).all()
        pipeline_val = Decimal("0.00")
        for q in open_quotes:
            if q.current_version:
                pipeline_val += q.current_version.final_total

        recent_reqs = db.query(SubscriptionRequest).order_by(SubscriptionRequest.created_at.desc()).limit(5).all()
        recent_requests_list = [
            {
                "id": req.id,
                "reference": req.reference,
                "request_type": req.request_type,
                "quantity": req.requested_quantity,
                "status": req.status,
                "company_name": req.business.company_name if req.business else "Unknown",
                "created_at": req.created_at.isoformat()
            }
            for req in recent_reqs
        ]

        return SalesDashboardMetrics(
            new_requests_count=new_requests_count,
            draft_quotations_count=draft_quotations_count,
            pending_approval_quotations_count=pending_approval_quotations_count,
            approved_awaiting_customer_count=approved_awaiting_customer_count,
            accepted_quotations_count=accepted_quotations_count,
            pipeline_estimated_value=pipeline_val.quantize(Decimal("0.01")),
            recent_requests=recent_requests_list
        )

    @classmethod
    def get_finance_dashboard(cls, db: Session) -> FinanceDashboardMetrics:
        now = datetime.now(timezone.utc)
        
        # Accepted awaiting invoice
        accepted_quotes = db.query(Quotation).filter(Quotation.status == "accepted").all()
        invoices = db.query(Invoice).filter(Invoice.status != "cancelled").all()
        invoiced_quote_ids = {inv.quotation_version.quotation_id for inv in invoices if inv.quotation_version}
        accepted_awaiting_invoice = len([q for q in accepted_quotes if q.id not in invoiced_quote_ids])

        unpaid = [i for i in invoices if i.remaining_balance > Decimal("0.00")]
        overdue = [
            i for i in unpaid 
            if i.status == "overdue" or (i.due_date and i.due_date.replace(tzinfo=timezone.utc if i.due_date.tzinfo is None else None) < now)
        ]

        total_outstanding = sum((i.remaining_balance for i in unpaid), Decimal("0.00"))
        
        payments = db.query(Payment).all()
        total_collected = sum((p.amount for p in payments), Decimal("0.00"))

        unmatched_count = db.query(BankFeedItem).filter(BankFeedItem.status == "unmatched").count()
        suggested_count = db.query(BankFeedItem).filter(BankFeedItem.status == "suggested_match").count()

        recent_pays = db.query(Payment).order_by(Payment.payment_date.desc(), Payment.id.desc()).limit(6).all()
        recent_payments_list = [
            {
                "id": p.id,
                "payment_number": p.payment_number,
                "amount": str(p.amount),
                "payment_method": p.payment_method,
                "payment_date": p.payment_date.isoformat(),
                "business_name": p.business.company_name if p.business else "Unknown",
                "reconciliation_status": p.reconciliation_status
            }
            for p in recent_pays
        ]

        return FinanceDashboardMetrics(
            accepted_awaiting_invoice_count=accepted_awaiting_invoice,
            total_invoices_count=len(invoices),
            unpaid_invoices_count=len(unpaid),
            overdue_invoices_count=len(overdue),
            total_outstanding_balance=total_outstanding.quantize(Decimal("0.01")),
            total_collected_amount=total_collected.quantize(Decimal("0.01")),
            unmatched_feed_items_count=unmatched_count,
            suggested_feed_matches_count=suggested_count,
            recent_payments=recent_payments_list
        )

    @classmethod
    def get_customer_dashboard(cls, db: Session, business_id: int) -> CustomerDashboardMetrics:
        now = datetime.now(timezone.utc)
        biz = db.query(CustomerBusiness).filter(CustomerBusiness.id == business_id).first()
        comp_name = biz.company_name if biz else "My Business"

        subs = db.query(Subscription).filter(
            Subscription.business_id == business_id,
            Subscription.status.in_(["active", "confirmed"])
        ).all()
        
        total_seats = sum((
            sum((l.quantity for l in s.lines)) for s in subs
        ), 0)

        # Next billing date
        billing_dates = [s.next_billing_date or s.expiry_date for s in subs if s.next_billing_date or s.expiry_date]
        next_billing_date = min(billing_dates) if billing_dates else None

        invoices = db.query(Invoice).filter(
            Invoice.business_id == business_id,
            Invoice.status != "cancelled"
        ).all()

        total_inv = sum((i.final_total for i in invoices), Decimal("0.00"))
        total_paid = sum((i.amount_paid for i in invoices), Decimal("0.00"))
        outstanding = sum((i.remaining_balance for i in invoices), Decimal("0.00"))
        
        overdue_invoices = [
            i for i in invoices 
            if i.remaining_balance > Decimal("0.00") and (
                i.status == "overdue" or (i.due_date and i.due_date.replace(tzinfo=timezone.utc if i.due_date.tzinfo is None else None) < now)
            )
        ]
        overdue_bal = sum((i.remaining_balance for i in overdue_invoices), Decimal("0.00"))

        pending_quotes = db.query(Quotation).filter(
            Quotation.business_id == business_id,
            Quotation.status == "approved"
        ).count()

        unread_notifs = db.query(NotificationLog).filter(
            NotificationLog.business_id == business_id,
            NotificationLog.is_read == False
        ).count()

        return CustomerDashboardMetrics(
            company_name=comp_name,
            active_subscriptions_count=len(subs),
            total_seats=total_seats,
            next_billing_date=next_billing_date,
            total_invoiced=total_inv.quantize(Decimal("0.01")),
            total_paid=total_paid.quantize(Decimal("0.01")),
            outstanding_balance=outstanding.quantize(Decimal("0.01")),
            overdue_balance=overdue_bal.quantize(Decimal("0.01")),
            pending_quotations_count=pending_quotes,
            unread_notifications_count=unread_notifs
        )

    @classmethod
    def query_finance_intelligence(cls, db: Session, request: CopilotQueryRequest) -> CopilotQueryResponse:
        now = datetime.now(timezone.utc)
        qtype = request.query_type

        if qtype == "mrr_arr_summary":
            active_subs = db.query(Subscription).filter(Subscription.status == "active").all()
            mrr = Decimal("0.00")
            plan_breakdown = {}
            for s in active_subs:
                for l in s.lines:
                    pname = l.plan.name if l.plan else "Standard Plan"
                    val = l.unit_price * l.quantity
                    freq = l.plan.billing_frequency if l.plan else "monthly"
                    norm_val = val if freq == "monthly" else (val / Decimal("12.00"))
                    mrr += norm_val
                    plan_breakdown[pname] = str((Decimal(plan_breakdown.get(pname, "0.00")) + norm_val).quantize(Decimal("0.01")))

            arr = mrr * Decimal("12.00")
            biz_count = db.query(CustomerBusiness).filter(CustomerBusiness.status == "active").count()
            arpu = (mrr / Decimal(biz_count)) if biz_count > 0 else Decimal("0.00")

            return CopilotQueryResponse(
                query_type=qtype,
                headline=f"Current Monthly Recurring Revenue is ₹{mrr:,.2f}",
                summary=f"Annualized Run Rate stands at ₹{arr:,.2f} across {len(active_subs)} active enterprise subscriptions. Average Revenue Per User (ARPU) is ₹{arpu:,.2f}.",
                data_points={
                    "mrr": str(mrr.quantize(Decimal("0.01"))),
                    "arr": str(arr.quantize(Decimal("0.01"))),
                    "active_subscriptions": len(active_subs),
                    "arpu": str(arpu.quantize(Decimal("0.01"))),
                    "plan_distribution": plan_breakdown
                },
                recommendations=[
                    "Promote annual commitment plans for higher cash flow predictability.",
                    "Review volume discount utilization on seat upgrades above 20 seats."
                ],
                timestamp=now
            )

        elif qtype == "debtors_aging":
            unpaid_invoices = db.query(Invoice).filter(
                Invoice.status.in_(["confirmed", "partially_paid", "overdue"]),
                Invoice.remaining_balance > Decimal("0.00")
            ).all()

            bucket_current = Decimal("0.00")
            bucket_1_7 = Decimal("0.00")
            bucket_8_14 = Decimal("0.00")
            bucket_15_plus = Decimal("0.00")
            debtor_map = {}

            for inv in unpaid_invoices:
                due_dt = inv.due_date.replace(tzinfo=timezone.utc if inv.due_date.tzinfo is None else None) if inv.due_date else now
                diff_days = (now.date() - due_dt.date()).days
                bal = inv.remaining_balance
                bname = inv.business.company_name if inv.business else f"Business #{inv.business_id}"
                debtor_map[bname] = str((Decimal(debtor_map.get(bname, "0.00")) + bal).quantize(Decimal("0.01")))

                if diff_days <= 0:
                    bucket_current += bal
                elif 1 <= diff_days <= 7:
                    bucket_1_7 += bal
                elif 8 <= diff_days <= 14:
                    bucket_8_14 += bal
                else:
                    bucket_15_plus += bal

            total_overdue = bucket_1_7 + bucket_8_14 + bucket_15_plus

            return CopilotQueryResponse(
                query_type=qtype,
                headline=f"Total Overdue Exposure is ₹{total_overdue:,.2f}",
                summary=f"₹{bucket_current:,.2f} remains within payment terms. ₹{bucket_15_plus:,.2f} is in critical 15+ days overdue status requiring immediate dunning escalation.",
                data_points={
                    "current_due": str(bucket_current.quantize(Decimal("0.01"))),
                    "overdue_1_to_7_days": str(bucket_1_7.quantize(Decimal("0.01"))),
                    "overdue_8_to_14_days": str(bucket_8_14.quantize(Decimal("0.01"))),
                    "overdue_15_plus_days": str(bucket_15_plus.quantize(Decimal("0.01"))),
                    "top_debtors": dict(sorted(debtor_map.items(), key=lambda item: Decimal(item[1]), reverse=True)[:5])
                },
                recommendations=[
                    "Trigger automated reminder sweep with Final Notice template for accounts over 14 days.",
                    "Review credit hold policy for accounts in the 15+ days overdue bracket."
                ],
                timestamp=now
            )

        elif qtype == "churn_risk_analysis":
            # Explainable rule-based churn risk
            unpaid_invoices = db.query(Invoice).filter(
                Invoice.remaining_balance > Decimal("0.00")
            ).all()
            chronic_debtor_biz_ids = set()
            for inv in unpaid_invoices:
                due_dt = inv.due_date.replace(tzinfo=timezone.utc if inv.due_date.tzinfo is None else None) if inv.due_date else now
                if (now.date() - due_dt.date()).days > 14:
                    chronic_debtor_biz_ids.add(inv.business_id)

            active_subs = db.query(Subscription).filter(Subscription.status == "active").all()
            at_risk_list = []
            for s in active_subs:
                risk_factors = []
                if s.business_id in chronic_debtor_biz_ids:
                    risk_factors.append("Chronic payment delay (>14 days overdue)")
                auto_renew = all((l.plan.auto_renew for l in s.lines if l.plan))
                if not auto_renew:
                    risk_factors.append("Auto-renew disabled")
                end_dt = s.expiry_date or s.next_billing_date
                if end_dt and (end_dt.replace(tzinfo=timezone.utc if end_dt.tzinfo is None else None) - now).days <= 14:
                    risk_factors.append("Contract expiring within 14 days")

                if risk_factors:
                    at_risk_list.append({
                        "subscription_id": s.id,
                        "business_name": s.business.company_name if s.business else "Unknown",
                        "risk_level": "High" if len(risk_factors) >= 2 else "Medium",
                        "reasons": risk_factors
                    })

            return CopilotQueryResponse(
                query_type=qtype,
                headline=f"{len(at_risk_list)} Subscription(s) Flagged for Retention Review",
                summary=f"Identified {len(at_risk_list)} accounts exhibiting payment friction or pending non-renewal flags based on deterministic rules.",
                data_points={
                    "flagged_accounts_count": len(at_risk_list),
                    "at_risk_accounts": at_risk_list
                },
                recommendations=[
                    "Assign dedicated Sales Rep follow-ups for high-risk accounts.",
                    "Propose commercial terms restructuring or discount incentives on annual renewals."
                ],
                timestamp=now
            )

        else: # renewal_forecast
            future_30 = now + timedelta(days=30)
            subs = db.query(Subscription).filter(
                Subscription.status == "active"
            ).all()

            upcoming_renewals = []
            forecasted_mrr = Decimal("0.00")
            for s in subs:
                end_dt = s.next_billing_date or s.expiry_date
                if not end_dt:
                    continue
                pend = end_dt.replace(tzinfo=timezone.utc if end_dt.tzinfo is None else None)
                if now <= pend <= future_30:
                    sub_val = sum((l.unit_price * l.quantity for l in s.lines), Decimal("0.00"))
                    forecasted_mrr += sub_val
                    auto_renew = all((l.plan.auto_renew for l in s.lines if l.plan))
                    upcoming_renewals.append({
                        "subscription_id": s.id,
                        "business_name": s.business.company_name if s.business else "Unknown",
                        "renewal_date": pend.strftime("%Y-%m-%d"),
                        "contract_value": str(sub_val.quantize(Decimal("0.01"))),
                        "auto_renew": auto_renew
                    })

            return CopilotQueryResponse(
                query_type=qtype,
                headline=f"₹{forecasted_mrr:,.2f} in Contract Renewals Over Next 30 Days",
                summary=f"{len(upcoming_renewals)} subscriptions are scheduled for renewal within the next 30 days.",
                data_points={
                    "total_renewal_value": str(forecasted_mrr.quantize(Decimal("0.01"))),
                    "upcoming_renewals": upcoming_renewals
                },
                recommendations=[
                    "Send automated renewal reminder notices 14 days prior to period end.",
                    "Verify billing details and credit card validity ahead of auto-charge cycles."
                ],
                timestamp=now
            )
