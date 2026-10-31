def test_audit_logs_recorded_and_admin_accessible(client, admin_headers):
    # Trigger an auditable action: create a product
    client.post("/api/v1/catalog/products", json={
        "name": "Audit Tracked Tool",
        "code": "AUDIT-01",
        "product_type": "saas",
        "sales_price": "500.00"
    }, headers=admin_headers)

    # Retrieve audit logs as admin
    res = client.get("/api/v1/audit/logs", headers=admin_headers)
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) > 0
    actions = [l["action"] for l in logs]
    assert "create_product" in actions

def test_sales_cannot_view_audit_logs(client, sales_headers):
    res = client.get("/api/v1/audit/logs", headers=sales_headers)
    assert res.status_code == 403

def test_customer_cannot_view_audit_logs(client, customer_alpha_headers):
    res = client.get("/api/v1/audit/logs", headers=customer_alpha_headers)
    assert res.status_code == 403

