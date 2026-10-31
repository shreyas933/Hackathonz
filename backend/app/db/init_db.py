from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import engine, Base, SessionLocal
from app.models.user import User, StaffProfile
from app.models.customer import CustomerBusiness, CustomerMembership
from app.models.catalog import Product, ProductVariant, Plan, TaxRate, DiscountRule
from app.models.automation import ReminderRule
from app.core.security import get_password_hash
from app.services.audit_service import AuditService
from app.db.seed_demo_data import seed_demo_data

def init_db():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Check if already seeded
        admin = db.query(User).filter(User.email == "admin@brightloop.com").first()
        if admin:
            seed_demo_data(db)
            return

        print("Seeding initial foundation data...")

        # 1. Admin User
        admin_user = User(
            email="admin@brightloop.com",
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Brightloop System Administrator",
            user_type="admin",
            is_active=True
        )
        db.add(admin_user)
        db.flush()

        # 2. Sales Rep
        sales_user = User(
            email="sales@brightloop.com",
            hashed_password=get_password_hash("SalesPass123!"),
            full_name="Sarah Sales",
            user_type="staff",
            is_active=True
        )
        db.add(sales_user)
        db.flush()

        sales_profile = StaffProfile(
            user_id=sales_user.id,
            staff_role="sales",
            department="Direct Sales",
            created_by_user_id=admin_user.id
        )
        db.add(sales_profile)

        # 3. Finance Rep
        finance_user = User(
            email="finance@brightloop.com",
            hashed_password=get_password_hash("FinancePass123!"),
            full_name="Frank Finance",
            user_type="staff",
            is_active=True
        )
        db.add(finance_user)
        db.flush()

        finance_profile = StaffProfile(
            user_id=finance_user.id,
            staff_role="finance",
            department="Accounts & Billing",
            created_by_user_id=admin_user.id
        )
        db.add(finance_profile)

        # 4. Demo Customer Business: Acme Corporation
        acme_biz = CustomerBusiness(
            company_name="Acme Corporation (Demo)",
            legal_name="Acme Global Solutions Pvt Ltd",
            tax_id="29ABCDE1234F1Z5",
            billing_address="Tower B, Prestige Tech Park, Marathahalli",
            billing_city="Bengaluru",
            billing_state="Karnataka",
            billing_postal_code="560103",
            billing_country="India",
            contact_email="owner@acmecorp.com",
            contact_phone="+91 98765 43210",
            status="active"
        )
        db.add(acme_biz)
        db.flush()

        # Customer Owner
        customer_owner = User(
            email="owner@acmecorp.com",
            hashed_password=get_password_hash("OwnerPass123!"),
            full_name="Alice Owner",
            user_type="customer",
            is_active=True
        )
        db.add(customer_owner)
        db.flush()

        customer_membership = CustomerMembership(
            user_id=customer_owner.id,
            business_id=acme_biz.id,
            role="owner",
            is_primary=True
        )
        db.add(customer_membership)

        # Customer Finance Contact
        customer_finance = User(
            email="finance@acmecorp.com",
            hashed_password=get_password_hash("OwnerPass123!"),
            full_name="Carl Finance",
            user_type="customer",
            is_active=True
        )
        db.add(customer_finance)
        db.flush()

        customer_fin_membership = CustomerMembership(
            user_id=customer_finance.id,
            business_id=acme_biz.id,
            role="finance_contact",
            is_primary=False
        )
        db.add(customer_fin_membership)

        # 5. Catalog Products
        product_erp = Product(
            name="Brightloop ERP Suite",
            code="BL-ERP",
            product_type="saas",
            sales_price=Decimal("1500.00"),
            cost_price=Decimal("300.00"),
            description="Complete cloud ERP for fast-growing businesses.",
            notes="Standard seat license includes billing, CRM, and inventory.",
            is_active=True
        )
        db.add(product_erp)
        db.flush()

        v_std = ProductVariant(
            product_id=product_erp.id,
            variant_name="Standard Tier",
            sku="BL-ERP-STD",
            price_adjustment=Decimal("0.00"),
            attributes_json='{"tier": "standard", "storage_gb": 50}',
            is_active=True
        )
        v_ent = ProductVariant(
            product_id=product_erp.id,
            variant_name="Enterprise Tier",
            sku="BL-ERP-ENT",
            price_adjustment=Decimal("1500.00"),
            attributes_json='{"tier": "enterprise", "storage_gb": 500, "priority_support": true}',
            is_active=True
        )
        db.add_all([v_std, v_ent])

        plan_std_monthly = Plan(
            product_id=product_erp.id,
            name="ERP Standard Monthly",
            code="PLAN-ERP-STD-M",
            billing_frequency="monthly",
            base_price=Decimal("1500.00"),
            min_quantity=5,
            can_pause=True,
            can_early_close=True,
            auto_close_at_end=False,
            auto_renew=True,
            trial_days=14,
            is_active=True
        )
        plan_std_yearly = Plan(
            product_id=product_erp.id,
            name="ERP Standard Yearly",
            code="PLAN-ERP-STD-Y",
            billing_frequency="yearly",
            base_price=Decimal("15000.00"),
            min_quantity=5,
            can_pause=False,
            can_early_close=True,
            auto_close_at_end=False,
            auto_renew=True,
            trial_days=14,
            is_active=True
        )
        plan_ent_monthly = Plan(
            product_id=product_erp.id,
            name="ERP Enterprise Monthly",
            code="PLAN-ERP-ENT-M",
            billing_frequency="monthly",
            base_price=Decimal("3000.00"),
            min_quantity=10,
            can_pause=True,
            can_early_close=True,
            auto_close_at_end=False,
            auto_renew=True,
            trial_days=0,
            is_active=True
        )
        db.add_all([plan_std_monthly, plan_std_yearly, plan_ent_monthly])

        # Add-on Product
        product_addon = Product(
            name="AI Copilot & Predictive Analytics",
            code="BL-AI-ADDON",
            product_type="addon",
            sales_price=Decimal("500.00"),
            cost_price=Decimal("100.00"),
            description="Autonomous financial analytics and invoice intelligence.",
            notes="Requires base ERP subscription.",
            is_active=True
        )
        db.add(product_addon)
        db.flush()

        plan_addon_monthly = Plan(
            product_id=product_addon.id,
            name="AI Addon Monthly",
            code="PLAN-AI-M",
            billing_frequency="monthly",
            base_price=Decimal("500.00"),
            min_quantity=1,
            can_pause=True,
            can_early_close=True,
            auto_close_at_end=False,
            auto_renew=True,
            is_active=True
        )
        db.add(plan_addon_monthly)

        # 6. Taxes
        tax_gst = TaxRate(name="GST 18%", rate_percent=Decimal("18.00"), is_compound=False, is_active=True)
        tax_sgst = TaxRate(name="SGST 9%", rate_percent=Decimal("9.00"), is_compound=False, is_active=True)
        tax_cgst = TaxRate(name="CGST 9%", rate_percent=Decimal("9.00"), is_compound=False, is_active=True)
        db.add_all([tax_gst, tax_sgst, tax_cgst])

        # 7. Discount Rules
        disc_vol = DiscountRule(
            name="Volume Discount (10-49 seats)",
            discount_type="percentage",
            value=Decimal("10.00"),
            min_seats=10,
            min_amount=Decimal("0.00"),
            max_allowed_sales_discount=Decimal("10.00"),
            requires_admin_approval=False,
            is_active=True
        )
        disc_ent = DiscountRule(
            name="Enterprise Strategic Discount (>50 seats)",
            discount_type="percentage",
            value=Decimal("20.00"),
            min_seats=50,
            min_amount=Decimal("50000.00"),
            max_allowed_sales_discount=Decimal("10.00"),
            requires_admin_approval=True,
            is_active=True
        )
        db.add_all([disc_vol, disc_ent])

        # 8. Seed Default Reminder Governance Rules
        rule_upcoming = ReminderRule(
            name="Upcoming Invoice Reminder (3 Days Before Due)",
            trigger_type="before_due",
            days_offset=-3,
            channel="email",
            subject_template="Reminder: Brightloop Invoice {invoice_number} is due in 3 days",
            body_template="Dear Customer, this is a reminder that invoice {invoice_number} for ₹{final_total} is due on {due_date}. Remaining balance: ₹{remaining_balance}.",
            escalation_level="standard",
            is_active=True
        )
        rule_due = ReminderRule(
            name="Due Date Notice (On Due Date)",
            trigger_type="on_due",
            days_offset=0,
            channel="email",
            subject_template="Notice: Brightloop Invoice {invoice_number} is due today",
            body_template="Dear Customer, invoice {invoice_number} for ₹{final_total} is due for payment today. Outstanding balance: ₹{remaining_balance}.",
            escalation_level="standard",
            is_active=True
        )
        rule_overdue_7 = ReminderRule(
            name="First Overdue Notice (7 Days Overdue)",
            trigger_type="after_due_overdue",
            days_offset=7,
            channel="email",
            subject_template="Overdue Notice: Brightloop Invoice {invoice_number} is 7 days past due",
            body_template="Dear Customer, invoice {invoice_number} has an outstanding balance of ₹{remaining_balance} and is 7 days overdue. Please remit payment promptly.",
            escalation_level="urgent",
            is_active=True
        )
        rule_overdue_14 = ReminderRule(
            name="Final Notice (14 Days Overdue)",
            trigger_type="after_due_overdue",
            days_offset=14,
            channel="email",
            subject_template="Final Notice: Urgent payment required for Invoice {invoice_number}",
            body_template="Dear Customer, this is a final notice regarding overdue invoice {invoice_number}. Immediate settlement of ₹{remaining_balance} is required to prevent disruption.",
            escalation_level="final_notice",
            is_active=True
        )
        db.add_all([rule_upcoming, rule_due, rule_overdue_7, rule_overdue_14])

        # 9. Audit log for seed
        AuditService.log(
            db=db,
            action="seed_database",
            entity_type="system",
            actor_email="system@brightloop.local",
            actor_role="system",
            after_state={"status": "initial_seed_completed"}
        )

        db.commit()
        print("Initial foundation data seeded successfully.")
        seed_demo_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

