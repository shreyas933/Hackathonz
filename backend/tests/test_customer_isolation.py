def test_customer_isolation_alpha(client, customer_alpha_headers):
    response = client.get("/api/v1/customer/business", headers=customer_alpha_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Alpha Corp"
    assert data["contact_email"] == "owner@alpha.com"

def test_customer_isolation_beta(client, customer_beta_headers):
    response = client.get("/api/v1/customer/business", headers=customer_beta_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "Beta Corp"
    assert data["contact_email"] == "owner@beta.com"

def test_owner_can_add_team_member(client, customer_alpha_headers):
    response = client.post(
        "/api/v1/customer/business/members",
        json={
            "email": "finance_rep@alpha.com",
            "full_name": "Alpha Finance Lead",
            "password": "Password123!",
            "role": "finance_contact"
        },
        headers=customer_alpha_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "finance_rep@alpha.com"
    assert data["role"] == "finance_contact"

    # Verify member appears in business profile
    biz_res = client.get("/api/v1/customer/business", headers=customer_alpha_headers)
    member_emails = [m["email"] for m in biz_res.json()["members"]]
    assert "finance_rep@alpha.com" in member_emails

def test_customer_cannot_access_admin_endpoints(client, customer_alpha_headers):
    res = client.get("/api/v1/admin/staff", headers=customer_alpha_headers)
    assert res.status_code == 403

