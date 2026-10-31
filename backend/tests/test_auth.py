def test_customer_registration(client):
    response = client.post("/api/v1/auth/register-customer", json={
        "full_name": "New Customer Owner",
        "email": "owner@newcorp.com",
        "password": "Password123!",
        "company_name": "NewCorp Technologies",
        "tax_id": "GSTIN99887766",
        "billing_country": "India"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_type"] == "customer"
    assert data["role"] == "owner"
    assert data["business_id"] is not None
    assert data["email"] == "owner@newcorp.com"

def test_duplicate_registration_fails(client):
    payload = {
        "full_name": "Duplicate Owner",
        "email": "owner@alpha.com",
        "password": "Password123!",
        "company_name": "Alpha Two",
        "billing_country": "India"
    }
    response = client.post("/api/v1/auth/register-customer", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()

def test_login_success(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "test_admin@brightloop.com",
        "password": "Admin123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["user_type"] == "admin"
    assert data["role"] == "admin"
    assert "access_token" in data

def test_login_invalid_password(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "test_admin@brightloop.com",
        "password": "WrongPassword!"
    })
    assert response.status_code == 401

def test_get_me(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test_admin@brightloop.com"
    assert data["user_type"] == "admin"

