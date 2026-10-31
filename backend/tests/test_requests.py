def test_customer_can_create_request(client, customer_alpha_headers):
    payload = {
        "request_type": "new_subscription",
        "requested_quantity": 25,
        "notes": "Looking to onboard our 25-person engineering team."
    }
    res = client.post("/api/v1/customer/requests", json=payload, headers=customer_alpha_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["reference"].startswith("REQ-")
    assert data["requested_quantity"] == 25
    assert data["status"] == "new"
    assert len(data["activities"]) == 1

def test_request_tenant_isolation(client, customer_alpha_headers, customer_beta_headers):
    # Alpha creates a request
    payload = {
        "request_type": "new_subscription",
        "requested_quantity": 10,
        "notes": "Alpha secret project"
    }
    res_alpha = client.post("/api/v1/customer/requests", json=payload, headers=customer_alpha_headers)
    alpha_req_id = res_alpha.json()["id"]

    # Beta attempts to read Alpha's request
    res_beta = client.get(f"/api/v1/customer/requests/{alpha_req_id}", headers=customer_beta_headers)
    assert res_beta.status_code == 404

    # Alpha lists requests
    alpha_list = client.get("/api/v1/customer/requests", headers=customer_alpha_headers)
    assert alpha_list.status_code == 200
    assert any(r["id"] == alpha_req_id for r in alpha_list.json())

    # Beta lists requests
    beta_list = client.get("/api/v1/customer/requests", headers=customer_beta_headers)
    assert beta_list.status_code == 200
    assert all(r["id"] != alpha_req_id for r in beta_list.json())

def test_staff_request_clarification_workflow(client, customer_alpha_headers, sales_headers):
    # Customer submits
    res = client.post("/api/v1/customer/requests", json={
        "request_type": "additional_seats",
        "requested_quantity": 15,
        "notes": "Need more seats"
    }, headers=customer_alpha_headers)
    req_id = res.json()["id"]

    # Sales asks for clarification
    act_res = client.post(f"/api/v1/staff/requests/{req_id}/activity", json={
        "activity_type": "clarification_request",
        "message": "Which product edition and department are these seats for?"
    }, headers=sales_headers)
    assert act_res.status_code == 200

    # Verify status transitioned to clarification_required
    staff_view = client.get(f"/api/v1/staff/requests/{req_id}", headers=sales_headers)
    assert staff_view.json()["status"] == "clarification_required"

    # Customer responds
    cust_act = client.post(f"/api/v1/customer/requests/{req_id}/activity", json={
        "activity_type": "customer_response",
        "message": "These are for the ERP Standard edition, Sales team."
    }, headers=customer_alpha_headers)
    assert cust_act.status_code == 200

    # Verify status transitioned back to under_review
    staff_view2 = client.get(f"/api/v1/staff/requests/{req_id}", headers=sales_headers)
    assert staff_view2.json()["status"] == "under_review"

