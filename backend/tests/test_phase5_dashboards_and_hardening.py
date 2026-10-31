import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

def _setup_active_subscription(client, admin_headers, sales_headers, customer_headers, business_id=1, base_price="2000.00", qty=10, can_pause=True):
    # 1. Product & Plan
    p_res = client.post("/api/v1/catalog/products", json={
        "name": f"Cloud SaaS {business_id}",
        "code": f"SAAS-{business_id}-{datetime.now().timestamp()}",
        "product_type": "saas",
        "sales_price": base_price
    }, headers=admin_headers)
    assert p_res.status_code == 200
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Standard Plan",
        "code": f"PLAN-{business_id}-{datetime.now().timestamp()}",
        "billing_frequency": "monthly",
        "base_price": base_price,
        "can_pause": can_pause,
        "can_early_close": True
    }, headers=admin_headers)
    assert pl_res.status_code == 200
    plan_id = pl_res.json()["id"]

    # 2. Quotation
    q_res = client.post("/api/v1/staff/quotations", json={
        "business_id": business_id,
        "payment_terms": "net_30",
        "validity_days": 30,
        "lines": [{
            "product_id": prod_id,
            "plan_id": plan_id,
            "quantity": qty,
            "unit_price": base_price,
            "discount_percent": "0.00",
            "tax_rate_percent": "0.00"
        }]
    }, headers=sales_headers)
    assert q_res.status_code == 200
    quote = q_res.json()
    q_id = quote["id"]

    # 3. Approve and Accept
    app_res = client.post(f"/api/v1/admin/quotations/{q_id}/versions/1/decision", json={
        "decision_type": "admin_approved",
        "reason": "Approved"
    }, headers=admin_headers)
    assert app_res.status_code == 200

    acc_res = client.post(f"/api/v1/customer/quotations/{q_id}/versions/1/decision", json={
        "decision_type": "customer_accepted"
    }, headers=customer_headers)
    assert acc_res.status_code == 200

    # 4. Generate Invoice and Pay to activate subscription
    inv_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "quotation_version_id": 1,
        "payment_terms": "net_30"
    }, headers=sales_headers)
    assert inv_res.status_code == 200
    inv = inv_res.json()

    # Pay invoice to activate subscription
    tot_amt = str(Decimal(base_price) * qty)
    pay_res = client.post("/api/v1/finance/payments", json={
        "business_id": business_id,
        "amount": tot_amt,
        "payment_method": "bank_transfer",
        "allocations": [{"invoice_id": inv["id"], "amount": tot_amt}]
    }, headers=sales_headers)
    assert pay_res.status_code == 200

    # Find subscription
    subs_res = client.get("/api/v1/staff/subscriptions", headers=sales_headers)
    assert subs_res.status_code == 200
    active_sub = [s for s in subs_res.json() if s["business_id"] == business_id and s["status"] == "active"]
    assert len(active_sub) >= 1

    return active_sub[0], inv

def test_admin_dashboard_metrics(client, admin_headers, sales_headers, customer_alpha_headers):
    sub, inv = _setup_active_subscription(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, base_price="1500.00", qty=10)

    res = client.get("/api/v1/dashboard/admin", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    # MRR should be at least 1500 * 10 = 15,000.00
    assert float(data["mrr"]) >= 15000.00
    assert float(data["arr"]) == float(data["mrr"]) * 12.00
    assert data["active_subscriptions"] >= 1
    assert data["total_customers"] >= 1
    assert float(data["total_invoiced"]) >= 15000.00
    assert "recent_activity" in data

def test_sales_dashboard_metrics(client, admin_headers, sales_headers, customer_alpha_headers):
    # Post a new request
    req_res = client.post("/api/v1/customer/requests", json={
        "request_type": "new_subscription",
        "requested_quantity": 25,
        "notes": "Need high volume enterprise pricing"
    }, headers=customer_alpha_headers)
    assert req_res.status_code == 200

    res = client.get("/api/v1/dashboard/sales", headers=sales_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["new_requests_count"] >= 1
    assert "pipeline_estimated_value" in data
    assert len(data["recent_requests"]) >= 1

def test_finance_dashboard_metrics(client, admin_headers, sales_headers, customer_alpha_headers):
    sub, inv = _setup_active_subscription(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, base_price="3000.00", qty=5)

    res = client.get("/api/v1/dashboard/finance", headers=sales_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_invoices_count"] >= 1
    assert "total_outstanding_balance" in data
    assert "unmatched_feed_items_count" in data

def test_customer_dashboard_metrics_and_tenant_isolation(client, admin_headers, sales_headers, customer_alpha_headers, customer_beta_headers):
    sub_alpha, inv_alpha = _setup_active_subscription(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, base_price="2000.00", qty=8)

    # Customer 1 (Alpha) Dashboard
    res1 = client.get("/api/v1/dashboard/customer", headers=customer_alpha_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["company_name"] == "Alpha Corp"
    assert data1["active_subscriptions_count"] >= 1
    assert data1["total_seats"] >= 8

    # Customer 2 (Beta) Dashboard
    res2 = client.get("/api/v1/dashboard/customer", headers=customer_beta_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["company_name"] == "Beta Corp"
    # Beta has not created subscriptions yet in this test session
    assert data2["active_subscriptions_count"] == 0

def test_subscription_pause_resume_cancel_lifecycle(client, admin_headers, sales_headers, customer_alpha_headers):
    sub, inv = _setup_active_subscription(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, base_price="1000.00", qty=5, can_pause=True)
    sub_id = sub["id"]

    # 1. Customer pauses active subscription
    pause_res = client.post(f"/api/v1/customer/subscriptions/{sub_id}/pause", headers=customer_alpha_headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # 2. Cannot pause already paused subscription
    double_pause = client.post(f"/api/v1/customer/subscriptions/{sub_id}/pause", headers=customer_alpha_headers)
    assert double_pause.status_code == 400

    # 3. Customer resumes subscription
    resume_res = client.post(f"/api/v1/customer/subscriptions/{sub_id}/resume", headers=customer_alpha_headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "active"

    # 4. Customer cancels subscription
    cancel_res = client.post(f"/api/v1/customer/subscriptions/{sub_id}/cancel", json={
        "reason": "Project concluded"
    }, headers=customer_alpha_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # 5. Cannot resume cancelled subscription
    bad_resume = client.post(f"/api/v1/customer/subscriptions/{sub_id}/resume", headers=customer_alpha_headers)
    assert bad_resume.status_code == 400

def test_subscription_pause_rejected_if_plan_disallows(client, admin_headers, sales_headers, customer_alpha_headers):
    # Create subscription where can_pause = False
    sub, inv = _setup_active_subscription(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, base_price="5000.00", qty=2, can_pause=False)
    sub_id = sub["id"]

    pause_res = client.post(f"/api/v1/customer/subscriptions/{sub_id}/pause", headers=customer_alpha_headers)
    assert pause_res.status_code == 400
    assert "does not allow pausing" in pause_res.json()["detail"]

def test_finance_copilot_intelligence_queries(client, admin_headers, sales_headers, customer_alpha_headers):
    sub, inv = _setup_active_subscription(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, base_price="2500.00", qty=4)

    # 1. MRR/ARR summary
    q1 = client.post("/api/v1/dashboard/analytics/copilot", json={"query_type": "mrr_arr_summary"}, headers=sales_headers)
    assert q1.status_code == 200
    r1 = q1.json()
    assert "Monthly Recurring Revenue" in r1["headline"]
    assert "mrr" in r1["data_points"]
    assert len(r1["recommendations"]) >= 1

    # 2. Debtors aging
    q2 = client.post("/api/v1/dashboard/analytics/copilot", json={"query_type": "debtors_aging"}, headers=sales_headers)
    assert q2.status_code == 200
    r2 = q2.json()
    assert "Overdue Exposure" in r2["headline"]
    assert "current_due" in r2["data_points"]

    # 3. Churn risk analysis
    q3 = client.post("/api/v1/dashboard/analytics/copilot", json={"query_type": "churn_risk_analysis"}, headers=sales_headers)
    assert q3.status_code == 200
    r3 = q3.json()
    assert "Flagged for Retention Review" in r3["headline"]
    assert "at_risk_accounts" in r3["data_points"]

    # 4. Renewal forecast
    q4 = client.post("/api/v1/dashboard/analytics/copilot", json={"query_type": "renewal_forecast"}, headers=sales_headers)
    assert q4.status_code == 200
    r4 = q4.json()
    assert "Contract Renewals" in r4["headline"]
    assert "total_renewal_value" in r4["data_points"]

def test_security_role_hardening(client, customer_alpha_headers, sales_headers):
    # Customer cannot access Admin Dashboard
    c_res = client.get("/api/v1/dashboard/admin", headers=customer_alpha_headers)
    assert c_res.status_code == 403

    # Sales cannot access Admin Dashboard
    s_res = client.get("/api/v1/dashboard/admin", headers=sales_headers)
    assert s_res.status_code == 403

    # Unauthenticated request rejected
    u_res = client.get("/api/v1/dashboard/admin")
    assert u_res.status_code == 401
