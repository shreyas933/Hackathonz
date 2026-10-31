def test_admin_can_create_staff(client, admin_headers):
    payload = {
        "email": "new_sales_rep@brightloop.com",
        "full_name": "New Salesperson",
        "password": "SecurePassword123!",
        "staff_role": "sales",
        "department": "Regional Sales"
    }
    response = client.post("/api/v1/admin/staff", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new_sales_rep@brightloop.com"
    assert data["user_type"] == "staff"
    assert data["staff_profile"]["staff_role"] == "sales"

def test_sales_cannot_create_staff(client, sales_headers):
    payload = {
        "email": "another_rep@brightloop.com",
        "full_name": "Rogue Sales",
        "password": "SecurePassword123!",
        "staff_role": "sales"
    }
    response = client.post("/api/v1/admin/staff", json=payload, headers=sales_headers)
    assert response.status_code == 403
    assert "Admin privilege required" in response.json()["detail"]

def test_finance_cannot_create_staff(client, finance_headers):
    payload = {
        "email": "another_fin@brightloop.com",
        "full_name": "Rogue Finance",
        "password": "SecurePassword123!",
        "staff_role": "finance"
    }
    response = client.post("/api/v1/admin/staff", json=payload, headers=finance_headers)
    assert response.status_code == 403

def test_customer_cannot_create_staff(client, customer_alpha_headers):
    payload = {
        "email": "intruder@brightloop.com",
        "full_name": "Intruder",
        "password": "SecurePassword123!",
        "staff_role": "sales"
    }
    response = client.post("/api/v1/admin/staff", json=payload, headers=customer_alpha_headers)
    assert response.status_code == 403

def test_admin_can_update_staff_permissions(client, admin_headers, db_session):
    from app.models.user import User
    sales = db_session.query(User).filter(User.email == "test_sales@brightloop.com").first()

    response = client.patch(
        f"/api/v1/admin/staff/{sales.id}/permissions",
        json={"department": "Key Accounts", "is_active": True},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["staff_profile"]["department"] == "Key Accounts"

