# API Reference: Brightloop Subscription Management System

This document outlines key REST API endpoints provided by the FastAPI backend service.

---

## 1. Authentication & Session Management

### `POST /api/auth/login`
Authenticates internal staff or customer business representatives.
- **Request Body**:
  ```json
  {
    "username": "user@example.com",
    "password": "secure_password"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "role": "ADMIN",
    "user_id": 1,
    "business_id": null
  }
  ```

### `GET /api/auth/me`
Retrieves profile metadata for the authenticated user context.

---

## 2. Product Catalog & Plans

### `GET /api/catalog/products`
Lists all available products with variants and active pricing matrices.

### `POST /api/catalog/products` *(Admin Only)*
Creates a new software product entry with configurable pricing tiers and seat limits.

### `GET /api/catalog/plans`
Fetches subscription cadence models (e.g., Monthly, Yearly, Custom Enterprise).

---

## 3. Commercial Engine (Requests & Quotations)

### `POST /api/requests`
Submits a customer subscription request.
- **Payload**:
  ```json
  {
    "product_variant_id": 3,
    "plan_id": 2,
    "requested_seats": 25,
    "notes": "Annual enterprise contract requested"
  }
  ```

### `POST /api/quotations` *(Sales Rep / Admin)*
Generates a new draft quotation linked to a customer request.

### `POST /api/quotations/{id}/submit-approval` *(Sales Rep)*
Submits a quotation draft for mandatory Admin review.

### `POST /api/quotations/{id}/approve` *(Admin Only)*
Approves quotation version for presentation to customer.

### `POST /api/quotations/{id}/accept` *(Customer Only)*
Records binding customer acceptance and logs immutable timestamp and signer context.

---

## 4. Subscriptions & Recurring Billing

### `GET /api/subscriptions`
Lists subscriptions scoped by role (Admin sees all; Customer sees business-owned only).

### `POST /api/subscriptions/{id}/pause`
Pauses subscription billing cycle in accordance with system policy.

### `POST /api/billing/run-recurring` *(Scheduled / Admin)*
Executes the idempotent batch billing engine to issue invoices for due cycles.

---

## 5. Invoicing & Payment Reconciliation

### `GET /api/billing/invoices`
Returns paginated invoice list with balances and due dates.

### `POST /api/reconciliation/manual-match` *(Finance / Admin)*
Manually reconciles ambiguous payments against outstanding invoice line items.

### `GET /api/dashboard/stats`
Returns role-tailored real-time analytics (MRR, ARR, churn rate, outstanding receivables).
