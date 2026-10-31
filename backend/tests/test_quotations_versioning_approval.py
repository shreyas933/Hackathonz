from decimal import Decimal
from datetime import datetime, timedelta, timezone

def test_sales_bulk_seats_quotation_creation(client, sales_headers, admin_headers):
    # 1. Create product and plan first via admin
    p_res = client.post("/api/v1/catalog/products", json={
        "name": "Platform Core",
        "code": "CORE-01",
        "product_type": "saas",
        "sales_price": "1000.00"
    }, headers=admin_headers)
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Monthly Core",
        "code": "PLAN-CORE-M",
        "billing_frequency": "monthly",
        "base_price": "1000.00",
        "min_quantity": 5
    }, headers=admin_headers)
    plan_id = pl_res.json()["id"]

    # Criterion 1: Sales enters quantity 50 in one operation
    quote_payload = {
        "business_id": 1,
        "payment_terms": "net_30",
        "validity_days": 30,
        "lines": [
            {
                "product_id": prod_id,
                "plan_id": plan_id,
                "quantity": 50,  # Bulk seat quantity
                "unit_price": "1000.00",
                "discount_percent": "10.00",
                "tax_rate_percent": "18.00"
            }
        ]
    }
    q_res = client.post("/api/v1/staff/quotations", json=quote_payload, headers=sales_headers)
    assert q_res.status_code == 200
    q_data = q_res.json()
    assert q_data["quotation_number"].startswith("Q-")
    assert q_data["current_version_number"] == 1
    assert q_data["status"] == "submitted_for_approval"

    v1 = q_data["versions"][0]
    # Gross: 50 * 1000 = 50,000; Discount 10% = 5,000; Net = 45,000; Tax 18% = 8,100; Final = 53,100
    assert Decimal(str(v1["subtotal"])) == Decimal("50000.00")
    assert Decimal(str(v1["discount_total"])) == Decimal("5000.00")
    assert Decimal(str(v1["tax_total"])) == Decimal("8100.00")
    assert Decimal(str(v1["final_total"])) == Decimal("53100.00")
    assert v1["lines"][0]["quantity"] == 50

def test_admin_mandatory_approval_and_customer_decision(client, sales_headers, admin_headers, customer_alpha_headers):
    # Setup product and plan
    p_res = client.post("/api/v1/catalog/products", json={
        "name": "Suite Enterprise",
        "code": "SUITE-ENT",
        "product_type": "saas",
        "sales_price": "2000.00"
    }, headers=admin_headers)
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Yearly Enterprise",
        "code": "PLAN-ENT-Y",
        "billing_frequency": "yearly",
        "base_price": "20000.00",
        "min_quantity": 10
    }, headers=admin_headers)
    plan_id = pl_res.json()["id"]

    # Sales creates quotation
    q_res = client.post("/api/v1/staff/quotations", json={
        "business_id": 1,
        "payment_terms": "net_30",
        "validity_days": 30,
        "lines": [{
            "product_id": prod_id,
            "plan_id": plan_id,
            "quantity": 20,
            "unit_price": "20000.00",
            "discount_percent": "5.00",
            "tax_rate_percent": "18.00"
        }]
    }, headers=sales_headers)
    q_id = q_res.json()["id"]

    # Criterion 2: Customer attempts to accept before Admin approves -> Must Fail!
    unapproved_accept = client.post(
        f"/api/v1/customer/quotations/{q_id}/versions/1/decision",
        json={"decision_type": "customer_accepted"},
        headers=customer_alpha_headers
    )
    assert unapproved_accept.status_code == 400
    assert "Only Admin-approved quotations" in unapproved_accept.json()["detail"]

    # Admin approves version 1
    admin_app = client.post(
        f"/api/v1/admin/quotations/{q_id}/versions/1/decision",
        json={"decision_type": "admin_approved", "reason": "Strategic tier discount approved."},
        headers=admin_headers
    )
    assert admin_app.status_code == 200
    assert admin_app.json()["status"] == "approved"

    # Criterion 4 & 5: Customer accepts approved version
    cust_accept = client.post(
        f"/api/v1/customer/quotations/{q_id}/versions/1/decision",
        json={"decision_type": "customer_accepted"},
        headers=customer_alpha_headers
    )
    assert cust_accept.status_code == 200
    assert cust_accept.json()["status"] == "accepted"

    # Verify a Confirmed Subscription was created for Customer Alpha
    subs_res = client.get("/api/v1/customer/subscriptions", headers=customer_alpha_headers)
    assert subs_res.status_code == 200
    subs = subs_res.json()
    assert len(subs) > 0
    sub = subs[0]
    assert sub["status"] == "confirmed"
    assert sub["accepted_quotation_id"] == q_id
    assert sub["accepted_quotation_version_id"] is not None
    assert sub["lines"][0]["quantity"] == 20

def test_quotation_versioning_and_diff_comparison(client, sales_headers, admin_headers):
    # Setup product and plan
    p_res = client.post("/api/v1/catalog/products", json={
        "name": "Cloud Storage",
        "code": "STOR-01",
        "product_type": "saas",
        "sales_price": "500.00"
    }, headers=admin_headers)
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Storage Monthly",
        "code": "PLAN-STOR-M",
        "billing_frequency": "monthly",
        "base_price": "500.00"
    }, headers=admin_headers)
    plan_id = pl_res.json()["id"]

    # Sales creates Version 1 (quantity 10)
    q_res = client.post("/api/v1/staff/quotations", json={
        "business_id": 1,
        "payment_terms": "net_30",
        "validity_days": 15,
        "lines": [{
            "product_id": prod_id,
            "plan_id": plan_id,
            "quantity": 10,
            "unit_price": "500.00",
            "discount_percent": "0.00",
            "tax_rate_percent": "18.00"
        }]
    }, headers=sales_headers)
    q_id = q_res.json()["id"]

    # Admin requests changes on Version 1
    client.post(
        f"/api/v1/admin/quotations/{q_id}/versions/1/decision",
        json={"decision_type": "admin_changes_requested", "reason": "Customer requested 15 seats and 5% discount."},
        headers=admin_headers
    )

    # Criterion 3: Sales creates Version 2 (quantity 15, discount 5%)
    rev_res = client.post(f"/api/v1/staff/quotations/{q_id}/versions", json={
        "revision_reason": "Increased seats to 15 and applied approved 5% discount.",
        "payment_terms": "net_15",
        "validity_days": 30,
        "lines": [{
            "product_id": prod_id,
            "plan_id": plan_id,
            "quantity": 15,
            "unit_price": "500.00",
            "discount_percent": "5.00",
            "tax_rate_percent": "18.00"
        }]
    }, headers=sales_headers)
    assert rev_res.status_code == 200
    v2_data = rev_res.json()
    assert v2_data["version_number"] == 2
    assert v2_data["status"] == "submitted_for_approval"

    # Verify Version 1 is intact and untouched
    q_full = client.get(f"/api/v1/staff/quotations/{q_id}", headers=sales_headers).json()
    assert len(q_full["versions"]) == 2
    v1_check = next(v for v in q_full["versions"] if v["version_number"] == 1)
    v2_check = next(v for v in q_full["versions"] if v["version_number"] == 2)
    assert v1_check["lines"][0]["quantity"] == 10
    assert v2_check["lines"][0]["quantity"] == 15

    # Check field-level diff comparison
    diff_res = client.get(f"/api/v1/staff/quotations/{q_id}/compare?base_version=1&target_version=2", headers=sales_headers)
    assert diff_res.status_code == 200
    diff = diff_res.json()
    assert "subtotal" in diff["changed_fields"]
    assert "final_total" in diff["changed_fields"]
    assert diff["lines_comparison"][0]["quantity_diff"] == 5

