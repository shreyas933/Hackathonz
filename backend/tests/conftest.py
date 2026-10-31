import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base, get_db
from app.main import app
from app.core.security import get_password_hash, create_access_token
from app.models.user import User, StaffProfile
from app.models.customer import CustomerBusiness, CustomerMembership
from app.models.catalog import Product, Plan, TaxRate, DiscountRule
from app.models.automation import ReminderRule

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        # Seed test admin
        admin = User(
            email="test_admin@brightloop.com",
            hashed_password=get_password_hash("Admin123!"),
            full_name="Test Administrator",
            user_type="admin",
            is_active=True
        )
        session.add(admin)

        # Seed test sales
        sales = User(
            email="test_sales@brightloop.com",
            hashed_password=get_password_hash("Sales123!"),
            full_name="Test Sales",
            user_type="staff",
            is_active=True
        )
        session.add(sales)
        session.flush()

        sales_prof = StaffProfile(
            user_id=sales.id,
            staff_role="sales",
            department="Sales"
        )
        session.add(sales_prof)

        # Seed test finance
        finance = User(
            email="test_finance@brightloop.com",
            hashed_password=get_password_hash("Finance123!"),
            full_name="Test Finance",
            user_type="staff",
            is_active=True
        )
        session.add(finance)
        session.flush()

        fin_prof = StaffProfile(
            user_id=finance.id,
            staff_role="finance",
            department="Finance"
        )
        session.add(fin_prof)

        # Seed test customer business 1
        biz1 = CustomerBusiness(
            company_name="Alpha Corp",
            billing_country="India",
            contact_email="owner@alpha.com",
            status="active"
        )
        session.add(biz1)
        session.flush()

        cust1 = User(
            email="owner@alpha.com",
            hashed_password=get_password_hash("Alpha123!"),
            full_name="Alpha Owner",
            user_type="customer",
            is_active=True
        )
        session.add(cust1)
        session.flush()

        mem1 = CustomerMembership(
            user_id=cust1.id,
            business_id=biz1.id,
            role="owner",
            is_primary=True
        )
        session.add(mem1)

        # Seed test customer business 2
        biz2 = CustomerBusiness(
            company_name="Beta Corp",
            billing_country="India",
            contact_email="owner@beta.com",
            status="active"
        )
        session.add(biz2)
        session.flush()

        cust2 = User(
            email="owner@beta.com",
            hashed_password=get_password_hash("Beta123!"),
            full_name="Beta Owner",
            user_type="customer",
            is_active=True
        )
        session.add(cust2)
        session.flush()

        mem2 = CustomerMembership(
            user_id=cust2.id,
            business_id=biz2.id,
            role="owner",
            is_primary=True
        )
        session.add(mem2)

        # Seed reminder rules
        session.add_all([
            ReminderRule(
                name="Upcoming Invoice Reminder (3 Days Before Due)",
                trigger_type="before_due",
                days_offset=-3,
                channel="email",
                subject_template="Reminder: Brightloop Invoice {invoice_number} is due in 3 days",
                body_template="Dear Customer, invoice {invoice_number} for ₹{final_total} is due on {due_date}. Remaining balance: ₹{remaining_balance}.",
                escalation_level="standard",
                is_active=True
            ),
            ReminderRule(
                name="Due Date Notice (On Due Date)",
                trigger_type="on_due",
                days_offset=0,
                channel="email",
                subject_template="Notice: Brightloop Invoice {invoice_number} is due today",
                body_template="Dear Customer, invoice {invoice_number} is due today. Outstanding balance: ₹{remaining_balance}.",
                escalation_level="standard",
                is_active=True
            ),
            ReminderRule(
                name="First Overdue Notice (7 Days Overdue)",
                trigger_type="after_due_overdue",
                days_offset=7,
                channel="email",
                subject_template="Overdue Notice: Brightloop Invoice {invoice_number} is 7 days past due",
                body_template="Dear Customer, invoice {invoice_number} is 7 days overdue. Balance: ₹{remaining_balance}.",
                escalation_level="urgent",
                is_active=True
            ),
            ReminderRule(
                name="Final Notice (14 Days Overdue)",
                trigger_type="after_due_overdue",
                days_offset=14,
                channel="email",
                subject_template="Final Notice: Urgent payment required for Invoice {invoice_number}",
                body_template="Dear Customer, urgent payment required for invoice {invoice_number}.",
                escalation_level="final_notice",
                is_active=True
            )
        ])

        session.commit()
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_headers(db_session):
    admin = db_session.query(User).filter(User.email == "test_admin@brightloop.com").first()
    token = create_access_token({"sub": str(admin.id), "email": admin.email, "user_type": "admin", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sales_headers(db_session):
    sales = db_session.query(User).filter(User.email == "test_sales@brightloop.com").first()
    token = create_access_token({"sub": str(sales.id), "email": sales.email, "user_type": "staff", "role": "sales"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def finance_headers(db_session):
    finance = db_session.query(User).filter(User.email == "test_finance@brightloop.com").first()
    token = create_access_token({"sub": str(finance.id), "email": finance.email, "user_type": "staff", "role": "finance"})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def customer_alpha_headers(db_session):
    cust = db_session.query(User).filter(User.email == "owner@alpha.com").first()
    token = create_access_token({"sub": str(cust.id), "email": cust.email, "user_type": "customer", "role": "owner", "business_id": 1})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def customer_beta_headers(db_session):
    cust = db_session.query(User).filter(User.email == "owner@beta.com").first()
    token = create_access_token({"sub": str(cust.id), "email": cust.email, "user_type": "customer", "role": "owner", "business_id": 2})
    return {"Authorization": f"Bearer {token}"}
