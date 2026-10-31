from decimal import Decimal

def test_admin_can_create_product_and_plan(client, admin_headers):
    # 1. Create product
    prod_payload = {
        "name": "Cloud CRM Pro",
        "code": "CRM-PRO",
        "product_type": "saas",
        "sales_price": "2000.00",
        "cost_price": "400.00",
        "description": "Comprehensive customer relationship management",
        "is_active": True
    }
    prod_res = client.post("/api/v1/catalog/products", json=prod_payload, headers=admin_headers)
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert prod_data["code"] == "CRM-PRO"
    prod_id = prod_data["id"]

    # 2. Create variant
    var_payload = {
        "variant_name": "Premium Tier",
        "sku": "CRM-PRO-PREM",
        "price_adjustment": "500.00",
        "attributes_json": '{"storage": "100GB"}',
        "is_active": True
    }
    var_res = client.post(f"/api/v1/catalog/products/{prod_id}/variants", json=var_payload, headers=admin_headers)
    assert var_res.status_code == 200
    assert var_res.json()["sku"] == "CRM-PRO-PREM"

    # 3. Create plan
    plan_payload = {
        "product_id": prod_id,
        "name": "CRM Pro Monthly",
        "code": "PLAN-CRM-M",
        "billing_frequency": "monthly",
        "base_price": "2000.00",
        "min_quantity": 5,
        "can_pause": True,
        "can_early_close": True,
        "auto_close_at_end": False,
        "auto_renew": True,
        "is_active": True
    }
    plan_res = client.post("/api/v1/catalog/plans", json=plan_payload, headers=admin_headers)
    assert plan_res.status_code == 200
    assert plan_res.json()["code"] == "PLAN-CRM-M"

def test_sales_cannot_create_product(client, sales_headers):
    prod_payload = {
        "name": "Unauthorized Product",
        "code": "UNAUTH-01",
        "product_type": "saas",
        "sales_price": "1000.00"
    }
    res = client.post("/api/v1/catalog/products", json=prod_payload, headers=sales_headers)
    assert res.status_code == 403

def test_finance_cannot_create_product(client, finance_headers):
    prod_payload = {
        "name": "Unauthorized Product Fin",
        "code": "UNAUTH-02",
        "product_type": "saas",
        "sales_price": "1000.00"
    }
    res = client.post("/api/v1/catalog/products", json=prod_payload, headers=finance_headers)
    assert res.status_code == 403

def test_tax_and_discount_creation(client, admin_headers):
    # Tax
    tax_res = client.post("/api/v1/catalog/taxes", json={
        "name": "Special Cess 2%",
        "rate_percent": "2.00",
        "is_compound": False,
        "is_active": True
    }, headers=admin_headers)
    assert tax_res.status_code == 200
    assert tax_res.json()["name"] == "Special Cess 2%"

    # Discount
    disc_res = client.post("/api/v1/catalog/discounts", json={
        "name": "Quarterly Promo",
        "discount_type": "percentage",
        "value": "15.00",
        "min_seats": 5,
        "min_amount": "10000.00",
        "max_allowed_sales_discount": "10.00",
        "requires_admin_approval": True,
        "is_active": True
    }, headers=admin_headers)
    assert disc_res.status_code == 200
    assert disc_res.json()["requires_admin_approval"] is True

