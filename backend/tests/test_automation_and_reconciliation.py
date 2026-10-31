import hmac
import hashlib
import json
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.core.config import settings

def _setup_invoice(client, admin_headers, sales_headers, customer_headers, business_id=1, total_price="50000.00"):
    # 1. Product & Plan
    p_res = client.post("/api/v1/catalog/products", json={
        "name": f"Enterprise Suite {business_id}",
        "code": f"ENT-{business_id}-{datetime.now().timestamp()}",
        "product_type": "saas",
        "sales_price": total_price
    }, headers=admin_headers)
    assert p_res.status_code == 200
    prod_id = p_res.json()["id"]

    pl_res = client.post("/api/v1/catalog/plans", json={
        "product_id": prod_id,
        "name": "Standard Plan",
        "code": f"PLAN-{business_id}-{datetime.now().timestamp()}",
        "billing_frequency": "monthly",
        "base_price": total_price
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
            "quantity": 1,
            "unit_price": total_price,
            "discount_percent": "0.00",
            "tax_rate_percent": "0.00"
        }]
    }, headers=sales_headers)
    assert q_res.status_code == 200
    quotation = q_res.json()
    q_id = quotation["id"]

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

    # 4. Generate Invoice
    inv_res = client.post("/api/v1/finance/invoices/generate-from-quotation", json={
        "quotation_id": q_id,
        "quotation_version_id": 1,
        "payment_terms": "net_30"
    }, headers=sales_headers)
    assert inv_res.status_code == 200
    return inv_res.json()

def test_bank_feed_ingestion_and_auto_matching(client, admin_headers, sales_headers, customer_alpha_headers):
    invoice = _setup_invoice(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="30000.00")
    inv_number = invoice["invoice_number"]

    # Ingest feed items
    feed_payload = {
        "items": [
            {
                "transaction_id": f"TX-NEFT-{datetime.now().timestamp()}",
                "amount": "30000.00",
                "currency": "INR",
                "raw_narration": f"NEFT CR-CITI001-KARTIK CORP-{inv_number}-RECON REF",
                "bank_account_number": "HDFC-991188",
                "sender_name": "Acme Corp"
            }
        ]
    }

    ingest_res = client.post("/api/v1/finance/reconciliation/feed/ingest", json=feed_payload, headers=sales_headers)
    assert ingest_res.status_code == 200
    items = ingest_res.json()
    assert len(items) == 1
    item = items[0]

    assert item["status"] == "suggested_match"
    assert item["parsed_reference"] == inv_number
    assert item["suggested_invoice_id"] == invoice["id"]
    assert float(item["confidence_score"]) >= 0.90

def test_confirm_reconciliation_match(client, admin_headers, sales_headers, customer_alpha_headers):
    invoice = _setup_invoice(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="25000.00")
    inv_number = invoice["invoice_number"]

    feed_payload = {
        "items": [
            {
                "transaction_id": f"TX-MATCH-{datetime.now().timestamp()}",
                "amount": "25000.00",
                "currency": "INR",
                "raw_narration": f"RTGS FROM CLIENT {inv_number}",
                "sender_name": "Test Customer"
            }
        ]
    }
    ingest_res = client.post("/api/v1/finance/reconciliation/feed/ingest", json=feed_payload, headers=sales_headers)
    item_id = ingest_res.json()[0]["id"]

    # Confirm match
    match_res = client.post(f"/api/v1/finance/reconciliation/feed/{item_id}/match", json={
        "invoice_id": invoice["id"],
        "notes": "Verified against bank statement credit confirmation"
    }, headers=sales_headers)
    assert match_res.status_code == 200
    reconciled_item = match_res.json()
    assert reconciled_item["status"] == "reconciled"
    assert reconciled_item["matched_payment_id"] is not None

    # Check invoice status
    inv_check = client.get(f"/api/v1/finance/invoices/{invoice['id']}", headers=sales_headers)
    assert inv_check.status_code == 200
    assert inv_check.json()["status"] == "paid"
    assert float(inv_check.json()["remaining_balance"]) == 0.00

def test_unmatched_feed_item_and_dispute(client, sales_headers):
    tx_id = f"TX-DISP-{datetime.now().timestamp()}"
    feed_payload = {
        "items": [
            {
                "transaction_id": tx_id,
                "amount": "7777.00",
                "currency": "INR",
                "raw_narration": "UPI/UNKNOWN/UNIDENTIFIABLE REF 881231",
                "sender_name": "Random Anonymous"
            }
        ]
    }
    ingest_res = client.post("/api/v1/finance/reconciliation/feed/ingest", json=feed_payload, headers=sales_headers)
    item_id = ingest_res.json()[0]["id"]
    assert ingest_res.json()[0]["status"] == "unmatched"

    # Mark as disputed
    disp_res = client.post(f"/api/v1/finance/reconciliation/feed/{item_id}/dispute", json={
        "reason": "Customer unidentified and narration contains invalid reference"
    }, headers=sales_headers)
    assert disp_res.status_code == 200
    assert disp_res.json()["status"] == "disputed"
    assert "Customer unidentified" in disp_res.json()["reconciliation_notes"]

def test_webhook_payment_captured_and_idempotency(client, admin_headers, sales_headers, customer_alpha_headers):
    invoice = _setup_invoice(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="40000.00")
    inv_number = invoice["invoice_number"]

    event_id = f"evt_webhook_{datetime.now().timestamp()}"
    payload_dict = {
        "event_id": event_id,
        "event_type": "payment.captured",
        "data": {
            "transaction_id": f"pay_gw_{datetime.now().timestamp()}",
            "amount": "40000.00",
            "currency": "INR",
            "invoice_number": inv_number,
            "payment_method": "card"
        }
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    signature = hmac.new(settings.WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    # First call: processes payment
    res1 = client.post(
        "/api/v1/webhooks/payments",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": signature}
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"

    # Check invoice status is now paid
    inv_res = client.get(f"/api/v1/finance/invoices/{invoice['id']}", headers=sales_headers)
    assert inv_res.status_code == 200
    assert inv_res.json()["status"] == "paid"
    assert float(inv_res.json()["remaining_balance"]) == 0.00

    # Second call with identical event_id: must be idempotent
    res2 = client.post(
        "/api/v1/webhooks/payments",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": signature}
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "idempotent_success"

def test_webhook_signature_rejection(client):
    payload_dict = {
        "event_id": "evt_tampered_123",
        "event_type": "payment.captured",
        "data": {
            "transaction_id": "tx_fake",
            "amount": "100.00",
            "currency": "INR"
        }
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    bad_signature = "bad_invalid_hmac_hash"

    res = client.post(
        "/api/v1/webhooks/payments",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": bad_signature}
    )
    assert res.status_code == 401

def test_reminder_rules_and_sweep(client, admin_headers, sales_headers, customer_alpha_headers):
    # Verify reminder rules seeded
    rules_res = client.get("/api/v1/reminders/rules", headers=sales_headers)
    assert rules_res.status_code == 200
    rules = rules_res.json()
    assert len(rules) >= 4  # -3, 0, 7, 14

    # Create an invoice
    invoice = _setup_invoice(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="15000.00")
    
    # We simulate a sweep on the day that is 3 days before due date
    # In _setup_invoice, due_date is 30 days from creation
    inv_due_dt = datetime.fromisoformat(invoice["due_date"].replace("Z", "+00:00"))
    simulated_today = inv_due_dt - timedelta(days=3)

    sweep_res = client.post("/api/v1/reminders/run", json={
        "target_date": simulated_today.isoformat()
    }, headers=sales_headers)
    assert sweep_res.status_code == 200
    result = sweep_res.json()
    assert result["reminders_sent"] >= 1

    # Check notification history
    hist_res = client.get(f"/api/v1/reminders/history?invoice_id={invoice['id']}", headers=sales_headers)
    assert hist_res.status_code == 200
    logs = hist_res.json()
    assert len(logs) == 1
    assert invoice["invoice_number"] in logs[0]["subject"] or invoice["invoice_number"] in logs[0]["content"]

    # Re-running sweep on the exact same target date must be deduplicated
    sweep_res_2 = client.post("/api/v1/reminders/run", json={
        "target_date": simulated_today.isoformat()
    }, headers=sales_headers)
    assert sweep_res_2.status_code == 200
    assert sweep_res_2.json()["skipped_count"] >= 1

def test_paid_invoices_excluded_from_reminders(client, admin_headers, sales_headers, customer_alpha_headers):
    invoice = _setup_invoice(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="10000.00")

    # Pay in full
    pay_res = client.post("/api/v1/finance/payments", json={
        "business_id": 1,
        "amount": "10000.00",
        "payment_method": "bank_transfer",
        "allocations": [{"invoice_id": invoice["id"], "amount": "10000.00"}]
    }, headers=sales_headers)
    assert pay_res.status_code == 200

    inv_due_dt = datetime.fromisoformat(invoice["due_date"].replace("Z", "+00:00"))
    simulated_today = inv_due_dt - timedelta(days=3)

    # Run sweep
    sweep_res = client.post("/api/v1/reminders/run", json={
        "target_date": simulated_today.isoformat()
    }, headers=sales_headers)
    assert sweep_res.status_code == 200

    # Ensure no reminder was logged for this invoice
    hist_res = client.get(f"/api/v1/reminders/history?invoice_id={invoice['id']}", headers=sales_headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) == 0

def test_customer_notification_tenant_isolation(client, admin_headers, sales_headers, customer_alpha_headers, customer_beta_headers):
    # Customer 1 notification (Alpha)
    invoice1 = _setup_invoice(client, admin_headers, sales_headers, customer_alpha_headers, business_id=1, total_price="12000.00")
    inv_due_dt = datetime.fromisoformat(invoice1["due_date"].replace("Z", "+00:00"))
    simulated_today = inv_due_dt - timedelta(days=3)

    client.post("/api/v1/reminders/run", json={"target_date": simulated_today.isoformat()}, headers=sales_headers)

    # Customer 1 (Alpha) retrieves their notifications
    c1_res = client.get("/api/v1/customer/notifications", headers=customer_alpha_headers)
    assert c1_res.status_code == 200
    c1_notifs = c1_res.json()
    assert any(n["business_id"] == 1 for n in c1_notifs)

    # Customer 2 (Beta) should NOT see Customer 1's notifications
    c2_res = client.get("/api/v1/customer/notifications", headers=customer_beta_headers)
    assert c2_res.status_code == 200
    c2_notifs = c2_res.json()
    assert not any(n["business_id"] == 1 for n in c2_notifs)

    # Mark as read by Customer 1
    target_notif_id = c1_notifs[0]["id"]
    read_res = client.patch(f"/api/v1/customer/notifications/{target_notif_id}/read", headers=customer_alpha_headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Customer 2 cannot mark Customer 1's notification as read
    unauth_read = client.patch(f"/api/v1/customer/notifications/{target_notif_id}/read", headers=customer_beta_headers)
    assert unauth_read.status_code == 404
