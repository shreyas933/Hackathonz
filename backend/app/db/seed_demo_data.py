import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.customer import CustomerBusiness, CustomerMembership
from app.models.catalog import Product, Plan
from app.models.commercial import (
    SubscriptionRequest,
    RequestActivity,
    Quotation,
    QuotationVersion,
    QuotationVersionLine,
    QuotationDecision,
    Subscription,
    SubscriptionLine,
)
from app.models.billing import (
    Invoice,
    InvoiceLine,
    Payment,
    PaymentAllocation,
)
from app.models.automation import BankFeedItem, NotificationLog
from app.models.audit import AuditLog
from app.core.security import get_password_hash

def seed_demo_data(db: Session):
    """
    Populates rich, realistic dummy data across all system modules:
    - Admin Executive Cockpit: MRR, ARR, collections, overdue exposure, approval queues
    - Sales Commercial Cockpit: Deal pipeline, inbound requests, draft quotes, accepted deals
    - Finance & Receivables Cockpit: Invoices ledger, aging brackets, collections, bank feeds
    - Customer Portal (Acme Corp): Active contracts, provisioned seats, billing milestones, invoices & receipts
    - Finance Copilot: MRR/ARR breakdown, 0-90+ days debtors aging, churn risk, renewal forecasts
    """
    # Check if demo subscriptions already exist
    existing_sub = db.query(Subscription).filter(Subscription.subscription_number == "SUB-2026-001").first()
    if existing_sub:
        print("Demo data already seeded, skipping.")
        return

    print("Seeding rich demo data across all dashboards...")

    now = datetime.now(timezone.utc)
    admin_user = db.query(User).filter(User.email == "admin@brightloop.com").first()
    sales_user = db.query(User).filter(User.email == "sales@brightloop.com").first()
    finance_user = db.query(User).filter(User.email == "finance@brightloop.com").first()
    acme_owner = db.query(User).filter(User.email == "owner@acmecorp.com").first()

    prod_erp = db.query(Product).filter(Product.code == "BL-ERP").first()
    prod_addon = db.query(Product).filter(Product.code == "BL-AI-ADDON").first()
    plan_std_m = db.query(Plan).filter(Plan.code == "PLAN-ERP-STD-M").first()
    plan_std_y = db.query(Plan).filter(Plan.code == "PLAN-ERP-STD-Y").first()
    plan_ent_m = db.query(Plan).filter(Plan.code == "PLAN-ERP-ENT-M").first()
    plan_ai_m = db.query(Plan).filter(Plan.code == "PLAN-AI-M").first()

    acme_biz = db.query(CustomerBusiness).filter(CustomerBusiness.company_name.like("%Acme%")).first()

    # 1. Additional Customer Businesses
    biz_techwave = CustomerBusiness(
        company_name="TechWave Software Labs",
        legal_name="TechWave Innovation Private Limited",
        tax_id="29TECHW5678P1Z3",
        billing_address="Indiranagar 100ft Road, HAL 2nd Stage",
        billing_city="Bengaluru",
        billing_state="Karnataka",
        billing_postal_code="560038",
        billing_country="India",
        contact_email="owner@techwave.io",
        contact_phone="+91 98450 11223",
        status="active"
    )
    biz_logistics = CustomerBusiness(
        company_name="Global Logistics Fleet Ltd",
        legal_name="Global Express Logistics Solutions Ltd",
        tax_id="27GLOBE9012L1Z9",
        billing_address="Bandra Kurla Complex, Commercial Tower 4",
        billing_city="Mumbai",
        billing_state="Maharashtra",
        billing_postal_code="400051",
        billing_country="India",
        contact_email="owner@globallogistics.com",
        contact_phone="+91 91234 56789",
        status="active"
    )
    biz_apex = CustomerBusiness(
        company_name="Apex Financial Technologies",
        legal_name="Apex FinTech Solutions India Ltd",
        tax_id="36APEXF3456F1Z1",
        billing_address="HITEC City, Madhapur",
        billing_city="Hyderabad",
        billing_state="Telangana",
        billing_postal_code="500081",
        billing_country="India",
        contact_email="owner@apexfintech.com",
        contact_phone="+91 99887 76655",
        status="active"
    )
    db.add_all([biz_techwave, biz_logistics, biz_apex])
    db.flush()

    # Create Owner Users for new businesses
    user_techwave = User(
        email="owner@techwave.io",
        hashed_password=get_password_hash("TechWavePass123!"),
        full_name="Tanya TechWave",
        user_type="customer",
        is_active=True
    )
    user_logistics = User(
        email="owner@globallogistics.com",
        hashed_password=get_password_hash("GlobalPass123!"),
        full_name="Gary Global",
        user_type="customer",
        is_active=True
    )
    user_apex = User(
        email="owner@apexfintech.com",
        hashed_password=get_password_hash("ApexPass123!"),
        full_name="Ananya Apex",
        user_type="customer",
        is_active=True
    )
    db.add_all([user_techwave, user_logistics, user_apex])
    db.flush()

    db.add_all([
        CustomerMembership(user_id=user_techwave.id, business_id=biz_techwave.id, role="owner", is_primary=True),
        CustomerMembership(user_id=user_logistics.id, business_id=biz_logistics.id, role="owner", is_primary=True),
        CustomerMembership(user_id=user_apex.id, business_id=biz_apex.id, role="owner", is_primary=True),
    ])

    # 2. Inbound Subscription Requests
    req1 = SubscriptionRequest(
        reference="REQ-2026-001",
        business_id=acme_biz.id,
        request_type="new_subscription",
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        requested_quantity=25,
        notes="Looking to roll out ERP Standard to our sales and supply chain teams across India.",
        status="new",
        created_by_user_id=acme_owner.id if acme_owner else 1,
        created_at=now - timedelta(hours=3)
    )
    req2 = SubscriptionRequest(
        reference="REQ-2026-002",
        business_id=biz_techwave.id,
        request_type="new_subscription",
        product_id=prod_erp.id,
        plan_id=plan_ent_m.id,
        requested_quantity=50,
        notes="High-growth SaaS startup needing multi-currency billing and priority SLA support.",
        status="under_review",
        assigned_sales_user_id=sales_user.id if sales_user else 2,
        created_by_user_id=user_techwave.id,
        created_at=now - timedelta(days=1)
    )
    req3 = SubscriptionRequest(
        reference="REQ-2026-003",
        business_id=biz_logistics.id,
        request_type="new_subscription",
        product_id=prod_erp.id,
        plan_id=plan_std_y.id,
        requested_quantity=100,
        notes="Annual contract requirement with bulk fleet user licensing.",
        status="clarification_required",
        assigned_sales_user_id=sales_user.id if sales_user else 2,
        created_by_user_id=user_logistics.id,
        created_at=now - timedelta(days=2)
    )
    db.add_all([req1, req2, req3])
    db.flush()

    # Request Activity for clarification
    db.add(RequestActivity(
        request_id=req3.id,
        actor_user_id=sales_user.id if sales_user else 2,
        activity_type="clarification_request",
        message="Could you confirm whether all 100 seats will require AI Copilot Add-on or base ERP licenses only?",
        created_at=now - timedelta(days=1, hours=4)
    ))

    # 3. Commercial Quotations in Various Pipeline Stages
    # Quote 1: Pending Admin Approval (Triggers Admin Approval Queue)
    q1 = Quotation(
        quotation_number="Q-2026-001",
        business_id=biz_apex.id,
        current_version_number=1,
        status="submitted_for_approval",
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(hours=5)
    )
    db.add(q1)
    db.flush()

    qv1 = QuotationVersion(
        quotation_id=q1.id,
        version_number=1,
        status="submitted_for_approval",
        subtotal=Decimal("180000.00"),
        discount_total=Decimal("18000.00"),
        tax_total=Decimal("29160.00"),
        final_total=Decimal("191160.00"),
        payment_terms="net_30",
        valid_until=now + timedelta(days=25),
        is_latest=True,
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(hours=5)
    )
    db.add(qv1)
    db.flush()

    db.add(QuotationVersionLine(
        quotation_version_id=qv1.id,
        product_id=prod_erp.id,
        plan_id=plan_ent_m.id,
        description="ERP Enterprise Monthly: 60 Seats with 10% Strategic Discount",
        quantity=60,
        unit_price=Decimal("3000.00"),
        discount_percent=Decimal("10.00"),
        discount_amount=Decimal("18000.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("29160.00"),
        line_total=Decimal("191160.00")
    ))

    # Quote 2: Approved for Customer (Awaiting Customer Signature in Customer Portal)
    q2 = Quotation(
        quotation_number="Q-2026-002",
        business_id=acme_biz.id,
        current_version_number=1,
        status="approved",
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(days=2)
    )
    db.add(q2)
    db.flush()

    qv2 = QuotationVersion(
        quotation_id=q2.id,
        version_number=1,
        status="approved",
        subtotal=Decimal("30000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("5400.00"),
        final_total=Decimal("35400.00"),
        payment_terms="net_30",
        valid_until=now + timedelta(days=20),
        is_latest=True,
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(days=2)
    )
    db.add(qv2)
    db.flush()

    db.add(QuotationVersionLine(
        quotation_version_id=qv2.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        description="ERP Standard Monthly: 20 Seats Expansion License",
        quantity=20,
        unit_price=Decimal("1500.00"),
        discount_percent=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("5400.00"),
        line_total=Decimal("35400.00")
    ))
    db.add(QuotationDecision(
        quotation_version_id=qv2.id,
        decision_maker_user_id=admin_user.id if admin_user else 1,
        decision_type="admin_approved",
        reason="Commercial terms and volume thresholds verified.",
        created_at=now - timedelta(days=1, hours=20)
    ))

    # Quote 3: Draft (in sales drafting)
    q3 = Quotation(
        quotation_number="Q-2026-003",
        business_id=biz_logistics.id,
        current_version_number=1,
        status="draft",
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(days=1)
    )
    db.add(q3)
    db.flush()

    qv3 = QuotationVersion(
        quotation_id=q3.id,
        version_number=1,
        status="draft",
        subtotal=Decimal("1500000.00"),
        discount_total=Decimal("150000.00"),
        tax_total=Decimal("243000.00"),
        final_total=Decimal("1593000.00"),
        payment_terms="net_30",
        valid_until=now + timedelta(days=30),
        is_latest=True,
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(days=1)
    )
    db.add(qv3)
    db.flush()

    db.add(QuotationVersionLine(
        quotation_version_id=qv3.id,
        product_id=prod_erp.id,
        plan_id=plan_std_y.id,
        description="ERP Standard Yearly: 100 Annual Seats with 10% Strategic Rebate",
        quantity=100,
        unit_price=Decimal("15000.00"),
        discount_percent=Decimal("10.00"),
        discount_amount=Decimal("150000.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("243000.00"),
        line_total=Decimal("1593000.00")
    ))

    # Quote 4: Accepted (Awaiting initial invoice generation by Finance)
    q4 = Quotation(
        quotation_number="Q-2026-004",
        business_id=biz_techwave.id,
        current_version_number=1,
        status="accepted",
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(days=4)
    )
    db.add(q4)
    db.flush()

    qv4 = QuotationVersion(
        quotation_id=q4.id,
        version_number=1,
        status="accepted",
        subtotal=Decimal("37500.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("6750.00"),
        final_total=Decimal("44250.00"),
        payment_terms="net_30",
        valid_until=now + timedelta(days=15),
        is_latest=True,
        created_by_user_id=sales_user.id if sales_user else 2,
        created_at=now - timedelta(days=4)
    )
    db.add(qv4)
    db.flush()

    db.add(QuotationVersionLine(
        quotation_version_id=qv4.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        description="ERP Standard Monthly: 25 Seats Engineering License",
        quantity=25,
        unit_price=Decimal("1500.00"),
        discount_percent=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("6750.00"),
        line_total=Decimal("44250.00")
    ))
    db.add(QuotationDecision(
        quotation_version_id=qv4.id,
        decision_maker_user_id=user_techwave.id,
        decision_type="customer_accepted",
        reason="Proposal accepted and authorized for immediate billing.",
        created_at=now - timedelta(days=1, hours=2)
    ))

    # 4. Active & Operational Subscriptions (Powers MRR, ARR, Seats, and Renewal Forecasts)
    # Sub 1: Acme Corp Base ERP (Monthly: 20 seats @ ₹1,500 = ₹30,000/mo)
    sub1 = Subscription(
        subscription_number="SUB-2026-001",
        business_id=acme_biz.id,
        status="active",
        billing_frequency="monthly",
        start_date=now - timedelta(days=60),
        next_billing_date=now + timedelta(days=14),
        expiry_date=now + timedelta(days=305),
        payment_terms="net_30",
        total_recurring_amount=Decimal("30000.00"),
        created_at=now - timedelta(days=60)
    )
    db.add(sub1)
    db.flush()

    db.add(SubscriptionLine(
        subscription_id=sub1.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        quantity=20,
        unit_price=Decimal("1500.00"),
        tax_rate_percent=Decimal("18.00"),
        line_total=Decimal("30000.00")
    ))

    # Sub 2: Acme Corp AI Copilot Add-on (Monthly: 10 seats @ ₹500 = ₹5,000/mo)
    sub2 = Subscription(
        subscription_number="SUB-2026-002",
        business_id=acme_biz.id,
        status="active",
        billing_frequency="monthly",
        start_date=now - timedelta(days=45),
        next_billing_date=now + timedelta(days=20),
        expiry_date=now + timedelta(days=320),
        payment_terms="net_30",
        total_recurring_amount=Decimal("5000.00"),
        created_at=now - timedelta(days=45)
    )
    db.add(sub2)
    db.flush()

    db.add(SubscriptionLine(
        subscription_id=sub2.id,
        product_id=prod_addon.id,
        plan_id=plan_ai_m.id,
        quantity=10,
        unit_price=Decimal("500.00"),
        tax_rate_percent=Decimal("18.00"),
        line_total=Decimal("5000.00")
    ))

    # Sub 3: TechWave ERP Enterprise (Monthly: 30 seats @ ₹3,000 = ₹90,000/mo)
    sub3 = Subscription(
        subscription_number="SUB-2026-003",
        business_id=biz_techwave.id,
        status="active",
        billing_frequency="monthly",
        start_date=now - timedelta(days=90),
        next_billing_date=now + timedelta(days=7),
        expiry_date=now + timedelta(days=275),
        payment_terms="net_30",
        total_recurring_amount=Decimal("90000.00"),
        created_at=now - timedelta(days=90)
    )
    db.add(sub3)
    db.flush()

    db.add(SubscriptionLine(
        subscription_id=sub3.id,
        product_id=prod_erp.id,
        plan_id=plan_ent_m.id,
        quantity=30,
        unit_price=Decimal("3000.00"),
        tax_rate_percent=Decimal("18.00"),
        line_total=Decimal("90000.00")
    ))

    # Sub 4: Global Logistics ERP Yearly (Yearly: 40 seats @ ₹15,000 = ₹600,000/yr -> ₹50,000/mo MRR)
    sub4 = Subscription(
        subscription_number="SUB-2026-004",
        business_id=biz_logistics.id,
        status="active",
        billing_frequency="yearly",
        start_date=now - timedelta(days=120),
        next_billing_date=now + timedelta(days=245),
        expiry_date=now + timedelta(days=245),
        payment_terms="net_30",
        total_recurring_amount=Decimal("600000.00"),
        created_at=now - timedelta(days=120)
    )
    db.add(sub4)
    db.flush()

    db.add(SubscriptionLine(
        subscription_id=sub4.id,
        product_id=prod_erp.id,
        plan_id=plan_std_y.id,
        quantity=40,
        unit_price=Decimal("15000.00"),
        tax_rate_percent=Decimal("18.00"),
        line_total=Decimal("600000.00")
    ))

    # Sub 5: Paused Subscription (For lifecycle testing)
    sub5 = Subscription(
        subscription_number="SUB-2026-005",
        business_id=biz_apex.id,
        status="paused",
        billing_frequency="monthly",
        start_date=now - timedelta(days=100),
        next_billing_date=None,
        expiry_date=now + timedelta(days=200),
        payment_terms="net_30",
        total_recurring_amount=Decimal("15000.00"),
        created_at=now - timedelta(days=100)
    )
    db.add(sub5)
    db.flush()

    db.add(SubscriptionLine(
        subscription_id=sub5.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        quantity=10,
        unit_price=Decimal("1500.00"),
        tax_rate_percent=Decimal("18.00"),
        line_total=Decimal("15000.00")
    ))

    # Sub 6: Churn Risk Candidate (Expiring in 6 days, auto-renew disabled on plan)
    sub6 = Subscription(
        subscription_number="SUB-2026-006",
        business_id=acme_biz.id,
        status="active",
        billing_frequency="monthly",
        start_date=now - timedelta(days=25),
        next_billing_date=now + timedelta(days=6),
        expiry_date=now + timedelta(days=6),
        payment_terms="net_30",
        total_recurring_amount=Decimal("7500.00"),
        created_at=now - timedelta(days=25)
    )
    db.add(sub6)
    db.flush()

    db.add(SubscriptionLine(
        subscription_id=sub6.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        quantity=5,
        unit_price=Decimal("1500.00"),
        tax_rate_percent=Decimal("18.00"),
        line_total=Decimal("7500.00")
    ))

    # 5. Invoices across all Aging Buckets (Current, 31-60d, 61-90d, 90+d)
    # Inv 1: Settled Paid Invoice
    inv1 = Invoice(
        invoice_number="INV-2026-001",
        business_id=acme_biz.id,
        subscription_id=sub1.id,
        billing_period="2026-08",
        issue_date=now - timedelta(days=70),
        due_date=now - timedelta(days=40),
        subtotal=Decimal("30000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("5400.00"),
        final_total=Decimal("35400.00"),
        amount_paid=Decimal("35400.00"),
        remaining_balance=Decimal("0.00"),
        currency="INR",
        payment_terms="net_30",
        status="paid",
        notes="Settled via HDFC NEFT transaction."
    )
    db.add(inv1)
    db.flush()

    db.add(InvoiceLine(
        invoice_id=inv1.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        description="August 2026 Subscription (20 Seats)",
        quantity=20,
        unit_price=Decimal("1500.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("5400.00"),
        line_total=Decimal("35400.00")
    ))

    # Inv 2: Partially Paid (Overdue bracket 31-60 days)
    inv2 = Invoice(
        invoice_number="INV-2026-002",
        business_id=acme_biz.id,
        subscription_id=sub1.id,
        billing_period="2026-09",
        issue_date=now - timedelta(days=75),
        due_date=now - timedelta(days=45),  # 45 days past due -> 31-60 days bracket
        subtotal=Decimal("35000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("6300.00"),
        final_total=Decimal("41300.00"),
        amount_paid=Decimal("20000.00"),
        remaining_balance=Decimal("21300.00"),
        currency="INR",
        payment_terms="net_30",
        status="partially_paid",
        notes="Partial payment of ₹20,000 received via UPI."
    )
    db.add(inv2)
    db.flush()

    db.add(InvoiceLine(
        invoice_id=inv2.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        description="September 2026 Subscription",
        quantity=20,
        unit_price=Decimal("1500.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("5400.00"),
        line_total=Decimal("35400.00")
    ))

    # Inv 3: Overdue (61-90 days bracket)
    inv3 = Invoice(
        invoice_number="INV-2026-003",
        business_id=biz_techwave.id,
        subscription_id=sub3.id,
        billing_period="2026-07",
        issue_date=now - timedelta(days=105),
        due_date=now - timedelta(days=75),  # 75 days past due -> 61-90 days bracket
        subtotal=Decimal("90000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("16200.00"),
        final_total=Decimal("106200.00"),
        amount_paid=Decimal("0.00"),
        remaining_balance=Decimal("106200.00"),
        currency="INR",
        payment_terms="net_30",
        status="overdue",
        notes="First payment follow-up sent."
    )
    db.add(inv3)
    db.flush()

    db.add(InvoiceLine(
        invoice_id=inv3.id,
        product_id=prod_erp.id,
        plan_id=plan_ent_m.id,
        description="July 2026 Enterprise Plan (30 Seats)",
        quantity=30,
        unit_price=Decimal("3000.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("16200.00"),
        line_total=Decimal("106200.00")
    ))

    # Inv 4: Overdue (90+ days bracket)
    inv4 = Invoice(
        invoice_number="INV-2026-004",
        business_id=biz_logistics.id,
        subscription_id=None,
        billing_period="2026-05_audit",
        issue_date=now - timedelta(days=140),
        due_date=now - timedelta(days=110),  # 110 days past due -> 90+ days bracket
        subtotal=Decimal("40000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("7200.00"),
        final_total=Decimal("47200.00"),
        amount_paid=Decimal("0.00"),
        remaining_balance=Decimal("47200.00"),
        currency="INR",
        payment_terms="net_30",
        status="overdue",
        notes="Final notice reminder sent."
    )
    db.add(inv4)
    db.flush()

    db.add(InvoiceLine(
        invoice_id=inv4.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        description="Legacy setup and configuration services",
        quantity=1,
        unit_price=Decimal("40000.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("7200.00"),
        line_total=Decimal("47200.00")
    ))

    # Inv 5: Current (0-30 days bracket)
    inv5 = Invoice(
        invoice_number="INV-2026-005",
        business_id=acme_biz.id,
        subscription_id=sub1.id,
        billing_period="2026-10",
        issue_date=now - timedelta(days=2),
        due_date=now + timedelta(days=14),  # Due in future -> Current 0-30 days
        subtotal=Decimal("30000.00"),
        discount_total=Decimal("0.00"),
        tax_total=Decimal("5400.00"),
        final_total=Decimal("35400.00"),
        amount_paid=Decimal("0.00"),
        remaining_balance=Decimal("35400.00"),
        currency="INR",
        payment_terms="net_30",
        status="confirmed",
        notes="Scheduled cycle invoice."
    )
    db.add(inv5)
    db.flush()

    db.add(InvoiceLine(
        invoice_id=inv5.id,
        product_id=prod_erp.id,
        plan_id=plan_std_m.id,
        description="October 2026 Subscription",
        quantity=20,
        unit_price=Decimal("1500.00"),
        discount_amount=Decimal("0.00"),
        tax_rate_percent=Decimal("18.00"),
        tax_amount=Decimal("5400.00"),
        line_total=Decimal("35400.00")
    ))

    # 6. Payment Receipts & Allocations
    # Payment 1: Full settlement of INV-2026-001
    pay1 = Payment(
        payment_number="PAY-2026-001",
        business_id=acme_biz.id,
        amount=Decimal("35400.00"),
        currency="INR",
        payment_method="bank_transfer",
        payment_date=now - timedelta(days=42),
        reference_number="HDFCN2608159981",
        source="manual",
        reconciliation_status="reconciled",
        notes="Bank transfer received via HDFC corporate gateway.",
        created_by_user_id=finance_user.id if finance_user else 3
    )
    db.add(pay1)
    db.flush()

    db.add(PaymentAllocation(
        payment_id=pay1.id,
        invoice_id=inv1.id,
        allocated_amount=Decimal("35400.00"),
        created_at=now - timedelta(days=42)
    ))

    # Payment 2: Partial payment of INV-2026-002
    pay2 = Payment(
        payment_number="PAY-2026-002",
        business_id=acme_biz.id,
        amount=Decimal("20000.00"),
        currency="INR",
        payment_method="upi",
        payment_date=now - timedelta(days=20),
        reference_number="UPI/260901/778899",
        source="manual",
        reconciliation_status="partially_allocated",
        notes="UPI settlement credited to Current Account.",
        created_by_user_id=finance_user.id if finance_user else 3
    )
    db.add(pay2)
    db.flush()

    db.add(PaymentAllocation(
        payment_id=pay2.id,
        invoice_id=inv2.id,
        allocated_amount=Decimal("20000.00"),
        created_at=now - timedelta(days=20)
    ))

    # Payment 3: TechWave advance payment
    pay3 = Payment(
        payment_number="PAY-2026-003",
        business_id=biz_techwave.id,
        amount=Decimal("50000.00"),
        currency="INR",
        payment_method="bank_transfer",
        payment_date=now - timedelta(days=5),
        reference_number="ICICIN2610250012",
        source="manual",
        reconciliation_status="reconciled",
        notes="Account credit for Q4 billing cycles.",
        created_by_user_id=finance_user.id if finance_user else 3
    )
    db.add(pay3)
    db.flush()

    # 7. Bank Feed Items (Reconciliation Queue)
    feed1 = BankFeedItem(
        transaction_id="TXN-HDFC-8801",
        bank_account_number="HDFC-00998811",
        transaction_date=now - timedelta(hours=8),
        amount=Decimal("35400.00"),
        currency="INR",
        raw_narration="NEFT-ACME CORP-INV2026005-BILLING RECURRING",
        sender_name="Acme Global Solutions Pvt Ltd",
        status="suggested_match",
        confidence_score=Decimal("0.95"),
        suggested_invoice_id=inv5.id,
        suggested_business_id=acme_biz.id,
        reconciliation_notes="Exact amount match with customer narration matching invoice INV-2026-005."
    )
    feed2 = BankFeedItem(
        transaction_id="TXN-HDFC-8802",
        bank_account_number="HDFC-00998811",
        transaction_date=now - timedelta(days=1),
        amount=Decimal("70800.00"),
        currency="INR",
        raw_narration="RTGS-UNIDENTIFIED REMITTANCE-MUMBAI BRANCH",
        sender_name="Unidentified Corporate Sender",
        status="unmatched",
        confidence_score=Decimal("0.00"),
        reconciliation_notes="No matching open invoice found for ₹70,800.00."
    )
    feed3 = BankFeedItem(
        transaction_id="TXN-HDFC-8803",
        bank_account_number="HDFC-00998811",
        transaction_date=now - timedelta(days=42),
        amount=Decimal("35400.00"),
        currency="INR",
        raw_narration="NEFT-ACME CORP-SETTLED-PAY1",
        sender_name="Acme Corporation",
        status="reconciled",
        confidence_score=Decimal("1.00"),
        suggested_invoice_id=inv1.id,
        suggested_business_id=acme_biz.id,
        matched_payment_id=pay1.id,
        reconciled_at=now - timedelta(days=42)
    )
    db.add_all([feed1, feed2, feed3])

    # 8. Notification Logs for Customer Portal
    notif1 = NotificationLog(
        business_id=acme_biz.id,
        subscription_id=sub1.id,
        recipient_email="owner@acmecorp.com",
        channel="email",
        subject="Upcoming Renewal Notice: Subscription SUB-2026-001",
        content="Dear Alice, your subscription SUB-2026-001 for 20 seats will renew on Nov 14, 2026.",
        status="delivered",
        sent_at=now - timedelta(days=2),
        is_read=False
    )
    notif2 = NotificationLog(
        business_id=acme_biz.id,
        invoice_id=inv5.id,
        recipient_email="owner@acmecorp.com",
        channel="email",
        subject="Invoice Issued: INV-2026-005 for ₹35,400.00",
        content="Dear Customer, invoice INV-2026-005 for ₹35,400.00 has been generated and is due on Nov 14, 2026.",
        status="delivered",
        sent_at=now - timedelta(days=1),
        is_read=False
    )
    notif3 = NotificationLog(
        business_id=acme_biz.id,
        invoice_id=inv2.id,
        recipient_email="owner@acmecorp.com",
        channel="email",
        subject="Payment Receipt: ₹20,000.00 credited",
        content="Payment of ₹20,000.00 via UPI (Ref: UPI/260901/778899) has been allocated to Invoice INV-2026-002.",
        status="delivered",
        sent_at=now - timedelta(days=19),
        is_read=True
    )
    db.add_all([notif1, notif2, notif3])

    # 9. Audit Logs for recent activity
    audit_events = [
        ("approve_quotation", "quotation", q2.id, "admin@brightloop.com", "admin", {"status": "approved", "quotation_number": "Q-2026-002"}, now - timedelta(days=1, hours=20)),
        ("accept_quotation", "quotation", q4.id, "owner@techwave.io", "customer", {"status": "accepted", "quotation_number": "Q-2026-004"}, now - timedelta(days=1, hours=2)),
        ("record_payment", "payment", pay3.id, "finance@brightloop.com", "finance", {"amount": "50000.00", "payment_number": "PAY-2026-003"}, now - timedelta(days=5)),
        ("activate_subscription", "subscription", sub3.id, "system@brightloop.local", "system", {"status": "active", "subscription_number": "SUB-2026-003"}, now - timedelta(days=90)),
        ("pause_subscription", "subscription", sub5.id, "admin@brightloop.com", "admin", {"status": "paused", "subscription_number": "SUB-2026-005"}, now - timedelta(days=15)),
        ("ingest_bank_feed", "bank_feed_item", 1, "finance@brightloop.com", "finance", {"count": 3, "status": "completed"}, now - timedelta(hours=8)),
    ]
    for action, entity_type, entity_id, actor_email, actor_role, after_state, ts in audit_events:
        db.add(AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            actor_email=actor_email,
            actor_role=actor_role,
            ip_address="127.0.0.1",
            after_state=json.dumps(after_state) if after_state is not None else None,
            created_at=ts
        ))

    db.commit()
    print("Rich demo data successfully seeded into database!")
