# Testing Strategy & Verification Guide

## 1. Overview
The Brightloop SMS test suite provides automated regression protection across security boundaries, multi-tenant data isolation, quotation approval states, billing idempotency, and reconciliation edge cases.

---

## 2. Test Architecture

The tests are organized under `backend/tests/`:

| Test Suite | Scope & Coverage |
|---|---|
| `test_auth.py` | JWT generation, token verification, password hashing, and role checks |
| `test_customer_isolation.py` | Cross-tenant access prevention, unauthorized resource retrieval |
| `test_quotations_versioning_approval.py` | Quotation drafting, version comparison, mandatory Admin sign-off, customer acceptance locking |
| `test_billing_and_payments.py` | Invoice generation, partial payments, idempotency of recurring billing runs |
| `test_automation_and_reconciliation.py` | Webhook deduplication, five reconciliation scenarios, automated reminder escalations |
| `test_staff_rbac.py` | Segregation of duties between Admin, Sales Reps, and Finance Reps |
| `test_phase5_dashboards_and_hardening.py` | Analytics calculations, performance, and operational integrity |

---

## 3. Running Test Suites

### Run All Tests
```bash
cd backend
pytest -v
```

### Run Tenant Security & Isolation Tests Specifically
```bash
pytest backend/tests/test_customer_isolation.py -v
```

### Run Commercial & Quotation Approval Tests
```bash
pytest backend/tests/test_quotations_versioning_approval.py -v
```

### Test Coverage Report
```bash
pytest --cov=app --cov-report=term-missing
```

---

## 4. Acceptance Verification Checklist
- **Idempotency**: Running billing batch cycles consecutively must never produce duplicate invoices for the same subscription period.
- **Webhook Safety**: Replaying the same external payment webhook notification must result in exactly one recorded payment transaction.
- **Audit Logging**: Every status transition across commercial, invoicing, and reconciliation entities must generate an unmodifiable audit trail entry.
