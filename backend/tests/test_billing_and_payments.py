import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta

def _setup_accepted_quotation(client, admin_headers, sales_headers, customer_headers, business_id=1, total_price="50000.00"):
    # 1. Admin creates product & plan
    p_res = client.post("/api/v1/catalog/products", json={
        "name": "Cloud Pro ERP",
        "code": f"ERP-TEST-{business_id}",
        "product_type": "saas",
        "sales_price": total_price
    }, headers=admin_headers)
    assert p_res.status_code == 200
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Annual Business",
        "code": f"PLAN-TEST-{business_id}",
        "billing_frequency": "monthly",
        "base_price": total_price
    }, headers=admin_headers)
    assert pl_res.status_code == 200
    plan_id = pl_res.json()["id"]

    # 2. Sales creates quotation
    q_payload = {
        "business_id": business_id,
        "payment_terms": "net_30",
        "validity_days": 30,
        "lines": [
            {
                "product_id": prod_id,
                "plan_id": plan_id,
                "quantity": 1,
                "unit_price": total_price,
                "discount_percent": "0.00",
                "tax_rate_percent": "0.00"
            }
        ]
    }
    q_res = client.post("/api/v1/staff/quotations", json=q_payload, headers=sales_headers)
    assert q_res.status_code == 200
    quotation = q_res.json()
    q_id = quotation["id"]

    # 3. Admin mandatory approval
    app_res = client.post(f"/api/v1/admin/quotations/{q_id}/versions/1/decision", json={
        "decision_type": "admin_approved",
        "reason": "Commercial terms verified"
    }, headers=admin_headers)
    assert app_res.status_code == 200

    # 4. Customer accepts exact version
    dec_res = client.post(f"/api/v1/customer/quotations/{q_id}/versions/1/decision", json={
        "decision_type": "customer_accepted"
    }, headers=customer_headers)
    assert dec_res.status_code == 200
    accepted_version = dec_res.json()

    return q_id, 1, accepted_version


def test_generate_invoice_from_accepted_quotation(client, admin_headers, sales_headers, finance_headers, customer_alpha_headers):
    q_id, v_num, _ = _setup_accepted_quotation(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="50000.00")

    # Finance generates invoice
    inv_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "version_number": v_num,
        "notes": "Initial implementation invoice"
    }, headers=finance_headers)
    assert inv_res.status_code == 200
    inv = inv_res.json()
    assert inv["invoice_number"].startswith("INV-")
    assert Decimal(str(inv["final_total"])) == Decimal("50000.00")
    assert Decimal(str(inv["amount_paid"])) == Decimal("0.00")
    assert Decimal(str(inv["remaining_balance"])) == Decimal("50000.00")
    assert inv["status"] == "confirmed"
    assert len(inv["lines"]) == 1
    assert inv["lines"][0]["quantity"] == 1

    # Attempting to invoice the same accepted quotation version again must be rejected
    dup_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "version_number": v_num
    }, headers=finance_headers)
    assert dup_res.status_code == 400
    assert "already been invoiced" in dup_res.json()["detail"]


def test_partial_payment_and_customer_view_consistency(client, admin_headers, sales_headers, finance_headers, customer_alpha_headers):
    """
    PRD Criterion 10:
    Partial payment of ₹20,000 on ₹50,000 invoice updates status to partially_paid
    with ₹30,000 remaining balance in both Finance and Customer views.
    """
    q_id, v_num, _ = _setup_accepted_quotation(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="50000.00")

    # Generate invoice
    inv_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "version_number": v_num
    }, headers=finance_headers)
    assert inv_res.status_code == 200
    inv_id = inv_res.json()["id"]

    # Record partial payment of ₹20,000
    pay_payload = {
        "business_id": 1,
        "amount": "20000.00",
        "payment_method": "bank_transfer",
        "reference_number": "UTR-ALPHA-00129",
        "notes": "First milestone 40% payment",
        "allocations": [
            {
                "invoice_id": inv_id,
                "amount": "20000.00"
            }
        ]
    }
    pay_res = client.post("/api/v1/finance/payments", json=pay_payload, headers=finance_headers)
    assert pay_res.status_code == 200
    pay = pay_res.json()
    assert pay["payment_number"].startswith("PAY-")
    assert pay["reconciliation_status"] == "reconciled"

    # Verify Finance view
    fin_inv = client.get(f"/api/v1/finance/invoices/{inv_id}", headers=finance_headers).json()
    assert fin_inv["status"] == "partially_paid"
    assert Decimal(str(fin_inv["amount_paid"])) == Decimal("20000.00")
    assert Decimal(str(fin_inv["remaining_balance"])) == Decimal("30000.00")

    # Verify Customer view
    cust_inv = client.get(f"/api/v1/customer/invoices/{inv_id}", headers=customer_alpha_headers).json()
    assert cust_inv["status"] == "partially_paid"
    assert Decimal(str(cust_inv["amount_paid"])) == Decimal("20000.00")
    assert Decimal(str(cust_inv["remaining_balance"])) == Decimal("30000.00")

    # Customer list invoices includes this invoice with updated balances
    cust_list = client.get("/api/v1/customer/invoices", headers=customer_alpha_headers).json()
    matching = [i for i in cust_list if i["id"] == inv_id]
    assert len(matching) == 1
    assert Decimal(str(matching[0]["remaining_balance"])) == Decimal("30000.00")

    # Complete the remaining balance: record payment of ₹30,000
    pay2_payload = {
        "business_id": 1,
        "amount": "30000.00",
        "payment_method": "upi",
        "reference_number": "UPI-ALPHA-99881",
        "notes": "Final settlement",
        "allocations": [
            {
                "invoice_id": inv_id,
                "amount": "30000.00"
            }
        ]
    }
    pay2_res = client.post("/api/v1/finance/payments", json=pay2_payload, headers=finance_headers)
    assert pay2_res.status_code == 200

    # Invoice should now be paid
    fin_inv_paid = client.get(f"/api/v1/finance/invoices/{inv_id}", headers=finance_headers).json()
    assert fin_inv_paid["status"] == "paid"
    assert Decimal(str(fin_inv_paid["amount_paid"])) == Decimal("50000.00")
    assert Decimal(str(fin_inv_paid["remaining_balance"])) == Decimal("0.00")


def test_recurring_billing_idempotency(client, admin_headers, sales_headers, finance_headers, customer_alpha_headers):
    """
    PRD Criterion 7:
    Running recurring billing twice produces exactly one invoice.
    """
    q_id, v_num, _ = _setup_accepted_quotation(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="25000.00")

    # First recurring billing run
    # Note: Subscription start_date / next_billing_date is now (today)
    target = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    run1 = client.post("/api/v1/finance/invoices/run-recurring", json={"target_date": target}, headers=finance_headers)
    assert run1.status_code == 200
    res1 = run1.json()
    assert res1["invoices_generated"] >= 1
    generated_first = res1["invoices_generated"]

    # Immediately run recurring billing a second time with the same target date
    run2 = client.post("/api/v1/finance/invoices/run-recurring", json={"target_date": target}, headers=finance_headers)
    assert run2.status_code == 200
    res2 = run2.json()
    # It must not generate duplicate invoices
    assert res2["invoices_generated"] == 0


def test_invoice_tenant_isolation(client, admin_headers, sales_headers, finance_headers, customer_alpha_headers, customer_beta_headers):
    # Create quotation & invoice for Alpha Corp (business 1)
    q_id, v_num, _ = _setup_accepted_quotation(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="15000.00")
    inv_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "version_number": v_num
    }, headers=finance_headers)
    assert inv_res.status_code == 200
    inv_id = inv_res.json()["id"]

    # Alpha customer can view it
    alpha_view = client.get(f"/api/v1/customer/invoices/{inv_id}", headers=customer_alpha_headers)
    assert alpha_view.status_code == 200

    # Beta customer attempting to view Alpha invoice must receive 403 Forbidden
    beta_view = client.get(f"/api/v1/customer/invoices/{inv_id}", headers=customer_beta_headers)
    assert beta_view.status_code == 403

    # Beta customer invoice list must not contain Alpha's invoice
    beta_list = client.get("/api/v1/customer/invoices", headers=customer_beta_headers).json()
    assert all(i["id"] != inv_id for i in beta_list)


def test_pdf_generation_endpoints(client, admin_headers, sales_headers, finance_headers, customer_alpha_headers):
    q_id, v_num, _ = _setup_accepted_quotation(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="40000.00")
    inv_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "version_number": v_num
    }, headers=finance_headers)
    assert inv_res.status_code == 200
    inv_id = inv_res.json()["id"]

    # Staff invoice PDF
    pdf_staff = client.get(f"/api/v1/finance/invoices/{inv_id}/pdf", headers=finance_headers)
    assert pdf_staff.status_code == 200
    assert pdf_staff.headers["content-type"] == "application/pdf"
    assert pdf_staff.content.startswith(b"%PDF-")

    # Customer invoice PDF
    pdf_cust = client.get(f"/api/v1/customer/invoices/{inv_id}/pdf", headers=customer_alpha_headers)
    assert pdf_cust.status_code == 200
    assert pdf_cust.headers["content-type"] == "application/pdf"
    assert pdf_cust.content.startswith(b"%PDF-")

    # Staff quotation PDF
    q_pdf_staff = client.get(f"/api/v1/staff/quotations/{q_id}/pdf", headers=sales_headers)
    assert q_pdf_staff.status_code == 200
    assert q_pdf_staff.headers["content-type"] == "application/pdf"
    assert q_pdf_staff.content.startswith(b"%PDF-")

    # Customer quotation PDF
    q_pdf_cust = client.get(f"/api/v1/customer/quotations/{q_id}/pdf", headers=customer_alpha_headers)
    assert q_pdf_cust.status_code == 200
    assert q_pdf_cust.headers["content-type"] == "application/pdf"
    assert q_pdf_cust.content.startswith(b"%PDF-")
