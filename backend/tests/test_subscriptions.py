from datetime import datetime, timezone

def test_subscription_tenant_isolation(client, customer_alpha_headers, customer_beta_headers, admin_headers):
    # Setup and create a subscription for Alpha
    p_res = client.post("/api/v1/catalog/products", json={
        "name": "Sub Product",
        "code": "SUB-P1",
        "product_type": "saas",
        "sales_price": "100.00"
    }, headers=admin_headers)
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Sub Plan",
        "code": "PLAN-SUB-1",
        "billing_frequency": "monthly",
        "base_price": "100.00"
    }, headers=admin_headers)
    plan_id = pl_res.json()["id"]

    q_res = client.post("/api/v1/staff/quotations", json={
        "business_id": 1,
        "lines": [{
            "product_id": prod_id,
            "plan_id": plan_id,
            "quantity": 5,
            "unit_price": "100.00"
        }]
    }, headers=admin_headers)
    q_id = q_res.json()["id"]

    client.post(
        f"/api/v1/admin/quotations/{q_id}/versions/1/decision",
        json={"decision_type": "admin_approved"},
        headers=admin_headers
    )

    client.post(
        f"/api/v1/customer/quotations/{q_id}/versions/1/decision",
        json={"decision_type": "customer_accepted"},
        headers=customer_alpha_headers
    )

    # Alpha views their subscriptions
    alpha_subs = client.get("/api/v1/customer/subscriptions", headers=customer_alpha_headers).json()
    assert len(alpha_subs) > 0
    alpha_sub_id = alpha_subs[0]["id"]

    # Beta attempts to read Alpha's subscription
    beta_get = client.get(f"/api/v1/customer/subscriptions/{alpha_sub_id}", headers=customer_beta_headers)
    assert beta_get.status_code == 404

    # Staff can update status to paused
    pause_res = client.patch(
        f"/api/v1/staff/subscriptions/{alpha_sub_id}/status",
        json={"status": "paused", "reason": "Customer seasonal suspension"},
        headers=admin_headers
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

