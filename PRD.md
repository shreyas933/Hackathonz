# Product Requirements Document (PRD)
## Brightloop Subscription Management System

| | |
|---|---|
| **Product** | Brightloop Subscription Management System (SMS) |
| **Company** | Brightloop Software (fictional) |
| **Document version** | 1.0 |
| **Date** | 31 October 2026 |
| **Status** | Draft for review |

---

## 1. Overview

### 1.1 Purpose
Brightloop Software sells business software through recurring subscriptions (monthly/yearly plans, optional add-ons, products with variants) to customers ranging from small businesses to large enterprises. Today, subscriptions are tracked in spreadsheets, renewals are remembered manually, invoices are created by hand, payments are matched by reading bank statements, and revenue reports are prepared manually.

This PRD defines a single centralized platform that manages the full subscription lifecycle: customer registration, subscription requests, quotations with versioning and mandatory Admin approval, subscriptions, recurring invoicing, tax and discount calculation, payment recording and reconciliation, reminders, renewals, and financial reporting.

### 1.2 Problems Being Solved
- Missed renewals
- Incorrect invoices
- Difficulty tracking payments
- Delayed payment follow-ups
- Poor visibility into recurring revenue
- Excessive manual work for internal employees

### 1.3 Product Structure
Two portals on one platform:

- **Internal Portal**: used by Brightloop Admin and Internal Staff (Sales Representative, Finance Representative).
- **Customer Portal**: used by external customer businesses and their authorized representatives.

---

## 2. Goals, Non-Goals and Success Metrics

### 2.1 Goals
1. Replace spreadsheet-based subscription, invoicing and payment tracking with one system.
2. Provide customers a self-service portal so routine enquiries need no contact with Brightloop.
3. Enforce a controlled, traceable commercial workflow: Request → Quotation → Admin Approval → Customer Acceptance → Invoice → Payment.
4. Make recurring billing reliable and idempotent (no duplicate invoices, no skipped cycles).
5. Maximize automatic payment matching while safely routing ambiguous payments to a Finance review queue.
6. Give Admin, Sales and Finance role-appropriate dashboards.
7. Preserve complete, auditable history of all commercial and financial records.

### 2.2 Non-Goals (initial release)
- Automatic card charging (requires a supported payment provider and customer authorization; may be added later).
- Provisioning individual employee accounts per purchased seat (seat quantity is a number, not user records; invitations may be a future feature).
- Direct bank access without an authorized bank feed or payment gateway integration.
- Automatic suspension or closure of subscriptions due to overdue invoices (only if explicitly configured by Brightloop).

### 2.3 Success Metrics (proposed)
| Metric | Target |
|---|---|
| Page load time (typical page, thousands of subscriptions) | < 2 seconds |
| Duplicate invoices for same subscription and billing period | 0 |
| Duplicate payment records from repeated webhooks | 0 |
| Missed billing cycles | 0 |
| Share of payments auto-matched (with valid integration) | To be baselined, then targeted |
| Manual invoice creation for recurring billing | Eliminated |
| Cross-tenant data exposure incidents | 0 |

---

## 3. Users and Roles

### 3.1 User Categories
1. **Admin**
2. **Internal Staff** (Sales Representative, Finance Representative)
3. **Customer** (business representatives)

### 3.2 Admin
Overall control of the application.
- Manage products and product variants.
- Manage subscription plans.
- Configure taxes.
- Create and manage discount rules.
- Create and manage internal staff accounts (**only Admin can do this**).
- View and manage customer businesses.
- Receive and process quotation approval requests (approve, reject, request changes).
- Apply or authorize discounts.
- View all subscriptions, billing, invoices, payments, reconciliation.
- View outstanding and overdue payments.
- Configure payment reminder rules and escalation policies.
- Configure subscription activation policy options.
- View overall financial information, system activity and audit history.

### 3.2.1 Internal Staff: Sales Representative
- Receive and review customer subscription requests.
- Review customer requirements and existing subscription history.
- Prepare quotations (product, variant, plan, bulk quantity/seats, unit price, taxes, eligible discounts where authorized, payment terms, validity, start date).
- Use quotation templates.
- Submit quotations for Admin approval; revise on Admin's change requests.
- Maintain quotation history; compare versions.
- Handle customer communication and clarification.
- Track quotations awaiting customer acceptance and follow up on rejections.

### 3.2.2 Internal Staff: Finance Representative
- Receive customer-accepted quotations.
- Review subscription and billing details; verify accepted quotation version.
- Generate, review, confirm, send, cancel and print invoices (per permissions).
- Record and verify payments; monitor incoming payments via supported integrations.
- Review and resolve unmatched payments; handle partial payments and allocations.
- Track outstanding and overdue invoices; monitor reminders and follow up with customers.

### 3.2.3 Staff Restrictions
- Sales has no unrestricted financial or system-administration permissions.
- Finance cannot change global product, plan, tax, discount or staff settings.
- Staff are not read-only: they can perform operations assigned to their role but are blocked from unrelated or sensitive functions.
- Permissions are enforced on the server, not only by hiding UI elements.

### 3.3 Customer Business Users
A **customer business** is the owner of subscriptions, quotations, invoices and payments, not an individual employee. One business has multiple user accounts with different permissions. Example roles (configurable):

| Customer role | Typical access |
|---|---|
| Business Owner | Manages business profile, users, subscriptions, requests, quotations |
| Finance Contact | Views invoices and payment information |
| Subscription Manager | Creates and tracks subscription requests, reviews quotations |

Business-level data isolation is mandatory: a customer user can never see or modify another business's data, even by altering IDs or URLs.

---

## 4. Core Concepts and Separation Rules

The following concepts must remain distinct in data model, UI and logic:

| Concept | Meaning |
|---|---|
| **Subscription Request** | A customer's requirement. Not an active subscription. |
| **Quotation** | An offer from Brightloop. Becomes the commercial basis only after customer acceptance. |
| **Subscription** | Ongoing contract with its own lifecycle. |
| **Invoice** | A bill for a billing period or accepted quotation. |
| **Payment** | Money received, linked to invoices via allocations. |
| **Reconciliation** | Matching incoming transactions to invoices. |
| **Product / Variant / Plan** | Three different things: a product is what is sold; a variant modifies price/attributes; a plan defines billing terms and lifecycle. |

Status families (independent of each other):

- **Subscription status:** Draft, Quotation, Confirmed, Active, Closed (pause handled per plan rules; see 6.5).
- **Request status:** New → Under Review → Clarification Required → Quoted → Approved/Accepted → Processing → Completed; terminal: Rejected, Cancelled, Closed. Exact statuses may vary by request type.
- **Quotation status:** Draft, Submitted for Approval, Changes Requested, Approved, Rejected (by Admin), Sent/Available to Customer, Accepted, Rejected (by Customer), Expired, Superseded.
- **Invoice status:** Draft, Confirmed, Paid, Cancelled, Overdue (or equivalent operational states).
- **Payment status (per invoice):** Unpaid, Partially Paid, Paid.
- **Reconciliation status:** Unmatched, Suggested Match, Under Review, Matched, Partially Allocated, Rejected/Invalid, Requires Investigation.

Example: a subscription can be Active while its latest invoice is Overdue and a payment is Unmatched.

---

## 5. End-to-End Workflow

1. Customer business registers.
2. Customer adds authorized representatives if required.
3. Customer submits a subscription request.
4. Request is categorized by type.
5. Sales receives and reviews the request.
6. Sales prepares a quotation.
7. Admin reviews and approves (mandatory; cannot be bypassed).
8. If changes are requested, Sales creates a new quotation version, which goes back to Admin.
9. Approved quotation is made available to the customer.
10. Customer accepts or rejects the exact quotation version.
11. Accepted quotation is forwarded to Finance.
12. Finance reviews accepted commercial details.
13. Finance generates and confirms the invoice.
14. Customer receives the invoice.
15. Customer pays.
16. Payment is auto-matched where possible via an authorized integration.
17. Unmatched or ambiguous transactions enter the Finance reconciliation queue.
18. Finance resolves unmatched payments.
19. Invoice paid amount and outstanding balance update.
20. Subscription becomes Active per the configured activation policy.
21. Recurring billing generates future invoices.
22. Automated reminders go out for upcoming and overdue payments.
23. Finance monitors outstanding payments and follows up.
24. Customers request additional seats, upgrades, downgrades, renewals or cancellations.
25. All historical records are preserved.

---

## 6. Functional Requirements

### 6.1 Authentication, Accounts and Access Control (FR-AUTH)
- FR-AUTH-1: Customers register with email and password; email must be unique across accounts.
- FR-AUTH-2: Password rules follow the original problem statement's requirements (**to be specified; see Open Questions**).
- FR-AUTH-3: Login, logout, and password reset for all users.
- FR-AUTH-4: Only Admin can create internal staff accounts; staff are assigned Sales or Finance roles.
- FR-AUTH-5: Role-based access control enforced server-side for all internal and customer endpoints.
- FR-AUTH-6: Admin can modify staff permissions; each change is audit-logged.
- FR-AUTH-7: After login, users are routed to the correct portal (Internal or Customer).

### 6.2 Customer Business and Users (FR-CUST)
- FR-CUST-1: Registration creates a customer business record and the first user (Business Owner) with business and contact details.
- FR-CUST-2: Business Owner (or users with permission) can add or invite additional representatives and assign customer-side roles.
- FR-CUST-3: Customer-side permissions control access to subscriptions, requests, quotations, invoices and payments.
- FR-CUST-4: Every customer-facing query is scoped to the authenticated user's business on the server.
- FR-CUST-5: Admin can view and manage customer businesses.
- FR-CUST-6: Seat quantities are numeric on subscription lines; purchasing N seats does not create N portal accounts.

### 6.3 Catalog: Products, Variants, Plans, Taxes, Discounts (FR-CAT)
**Products**
- FR-CAT-1: Product fields: name, type, sales price, cost price, notes. Admin-only management.
- FR-CAT-2: Products may have variants that affect pricing.

**Plans**
- FR-CAT-3: Plan fields: price, billing frequency (daily, weekly, monthly, yearly), minimum quantity, availability dates, lifecycle options (pause, early closure, automatic closure, renewal).
- FR-CAT-4: Optional add-ons are supported as additional lines.

**Taxes**
- FR-CAT-5: Admin configures taxes; taxes are calculated automatically on quotations and invoices.

**Discounts**
- FR-CAT-6: Admin creates discount rules (fixed amount or percentage, with eligibility conditions).
- FR-CAT-7: Discounts apply only if authorized under configured rules; Sales can apply only discounts they are permitted to.
- FR-CAT-8: Discounts are revalidated at invoice generation time.

### 6.4 Subscription Request Management (FR-REQ)
Centralized module for all request types.

- FR-REQ-1: Supported types: New Subscription, Additional Seats / Quantity Increase, Upgrade, Downgrade, Renewal, Cancellation.
- FR-REQ-2: Every request has: unique reference, customer business, type, related subscription (if applicable), requested product/plan/variant, requested quantity/seats, notes, submission date, assigned Sales rep, current status, activity history.
- FR-REQ-3: **New Subscription:** customer selects product, plan (if available), variant (if applicable), quantity (e.g., 50), notes.
- FR-REQ-4: **Additional Seats:** references the existing subscription and the extra quantity (e.g., +20).
- FR-REQ-5: **Upgrade / Downgrade:** references the existing subscription and the requested new plan; Sales reviews commercial implications.
- FR-REQ-6: **Renewal:** references the existing subscription and intended renewal period.
- FR-REQ-7: **Cancellation:** records the subscription, requested cancellation date, optional reason, and immediate vs end-of-term preference; processed under configured business and plan rules; **never deletes** historical subscription, invoice or payment data.
- FR-REQ-8: On submission the request is stored, a reference is generated, Sales is notified, it appears in the Sales section, and the customer can track progress.
- FR-REQ-9: Request status must not be confused with quotation or subscription status.
- FR-REQ-10: Sales can mark a request as Clarification Required and communicate with the customer.
- FR-REQ-11: When commercial terms change (seats, plan change, renewal pricing), the request must go through Sales quotation creation and mandatory Admin approval.

### 6.5 Subscriptions (FR-SUB)
- FR-SUB-1: Fields: unique subscription number, customer, plan, product lines (product, variant, quantity/seats, unit price, taxes), start date, expiry date, billing frequency, payment terms, accepted quotation reference and version, status.
- FR-SUB-2: Lifecycle: Draft → Quotation → Confirmed → Active → Closed.
- FR-SUB-3: Acceptance of a quotation creates or updates a Confirmed subscription based on that exact quotation version.
- FR-SUB-4: **Activation policy** is configurable and explicit, supporting:
  - *Prepaid:* Active after required payment is received.
  - *Credit terms:* Active after acceptance and agreed start date, even if payment is pending.
  - *Scheduled start:* Active on the agreed start date, subject to configured conditions.
- FR-SUB-5: Plan lifecycle options: renewal, automatic closure at end of term, pause, early closure.
- FR-SUB-6: Closed subscriptions retain all history (quotations, invoices, payments).
- FR-SUB-7: Overdue invoices **do not** automatically suspend or close a subscription unless Brightloop explicitly configures that policy.
- FR-SUB-8: Upcoming expiry and renewal dates are monitored with customer notifications.

### 6.6 Quotations and Version Control (FR-QUO)
**Creation (Sales)**
- FR-QUO-1: Create quotation from a request; select product, variant, plan, quantity/seats, unit price, taxes, eligible discount, payment terms, validity period, start date.
- FR-QUO-2: **Bulk quantity entry:** a single quantity field (e.g., 50) rather than repeated lines or per-employee records.
- FR-QUO-3: Totals (subtotal, discount, tax, final) calculated automatically.
- FR-QUO-4: Quotation templates are supported.
- FR-QUO-5: For existing subscriptions, Sales can view historical subscription and quotation data.
- FR-QUO-6: Sales submits the quotation for Admin approval.

**Admin approval (mandatory)**
- FR-QUO-7: Admin has a dedicated approval section and notifications.
- FR-QUO-8: Admin reviews customer/business, request type, existing subscription, product/plan, quantity, pricing, taxes, discounts, payment terms, validity, special requirements.
- FR-QUO-9: Actions: **Approve**, **Reject** (reason required), **Request Changes** (reason required), **Apply/Authorize Discount** (fixed or percentage, subject to discount rules).
- FR-QUO-10: Record: decision, decision maker, timestamp, version reviewed, reason.
- FR-QUO-11: Approved quotation is made available to the customer (portal and notification).
- FR-QUO-12: Admin approval cannot be removed or bypassed.

**Versioning**
- FR-QUO-13: Every quotation has a number and version number (e.g., Q-001 v1, v2).
- FR-QUO-14: Each version stores: quotation number, version, customer, product/plan details, quantity/seats, unit prices, discounts, taxes, final total, payment terms, validity, created by, creation timestamp, revision reason, admin approval status/approver/timestamp, customer acceptance or rejection status and timestamp.
- FR-QUO-15: Older versions are **never overwritten**; every meaningful revision creates a new version.
- FR-QUO-16: Every new version goes through Admin approval again.
- FR-QUO-17: Customer sees the latest approved version; previous versions viewable where appropriate.
- FR-QUO-18: Authorized internal users can compare versions and see field-level differences (quantity, discount, payment terms, plan, unit price, etc.).
- FR-QUO-19: An accepted version is immutable. Post-acceptance changes require a new amendment or quotation.

**Customer decision**
- FR-QUO-20: Customer reviews product/variant, plan, seats, unit price, discount, tax, total, payment terms, validity, version.
- FR-QUO-21: **Accept:** record who accepted, when, and the exact version; create/confirm subscription; forward to Finance.
- FR-QUO-22: **Reject:** record rejection; notify Sales; Sales may follow up and prepare a revision (which requires Admin approval again).
- FR-QUO-23: Acceptance is not payment.
- FR-QUO-24: Expired quotations (past validity) cannot be accepted.

### 6.7 Invoicing (FR-INV)
**From accepted quotation**
- FR-INV-1: Finance sees accepted quotations in its queue and verifies product, plan, quantity, price, discounts, taxes, payment terms and exact accepted version.
- FR-INV-2: Invoice is generated automatically from accepted quotation/subscription data; no re-entry of products, quantities, prices or customer details.
- FR-INV-3: Invoice contents: unique invoice number, customer/business details, related subscription, accepted quotation reference and version, product and plan information, quantity/seats, unit price, taxes, discounts, total, issue date, due date, payment terms.
- FR-INV-4: Finance can review, confirm, send, cancel and print invoices (per permissions).
- FR-INV-5: Confirmed invoices appear in the Customer Portal with a notification, showing invoice amount, amount paid, remaining amount, due date, status and payment history.
- FR-INV-6: Historical invoice amounts are never changed retroactively.

**Recurring billing**
- FR-INV-7: System monitors subscription billing dates and generates due invoices automatically.
- FR-INV-8: Taxes and eligible discounts applied automatically; discounts revalidated at generation.
- FR-INV-9: Invoice is sent to customer; Finance dashboard updates.
- FR-INV-10: **Idempotency:** no duplicate invoice for the same subscription and billing period (enforced with a database-level uniqueness constraint).
- FR-INV-11: No due billing cycle is skipped; missed runs are detected and caught up.
- FR-INV-12: Billing failures are logged; failed jobs are retryable safely.
- FR-INV-13: Reminder logic triggers if the invoice becomes overdue.

### 6.8 Payments and Reconciliation (FR-PAY)
**Recording**
- FR-PAY-1: Payment fields: method, amount received, payment date, transaction/reference number, note, related invoice(s), payment source, reconciliation status.
- FR-PAY-2: Manual payment recording is always available (transfers, cash, unsupported methods).
- FR-PAY-3: Automatic detection requires an authorized bank feed or payment gateway integration. The system must not assume bank access without one.
- FR-PAY-4: On a successful match: record payment, update invoice paid amount and balance, update invoice and payment status, update Finance dashboard and Customer Portal, send confirmation/receipt to customer.
- FR-PAY-5: Partial payments show amount received and remaining balance.
- FR-PAY-6: Automatic payment recording is distinct from automatic card charging.

**Matching scenarios**
| # | Scenario | System action |
|---|---|---|
| 1 | Exact match (correct invoice reference, customer, amount) | Auto-match, record, update balance/status, notify Finance and customer |
| 2 | Amount matches but reference missing (e.g., ₹25,000) | Identify candidate invoices, flag for Finance review, never auto-assign arbitrarily |
| 3 | Partial payment (₹20,000 against ₹50,000) | Record ₹20,000, show ₹30,000 outstanding, status Partially Paid |
| 4 | Amount mismatch (₹45,000 against ₹50,000) | Flag for review, show difference; Finance determines partial, deduction or error |
| 5 | Duplicate notification | Detect via unique transaction identifier, do not record twice, retain a record of the duplicate |

**Reconciliation queue (Finance Portal)**
- FR-PAY-7: Unmatched Payments section shows transaction reference, payment date, customer (if identifiable), amount, method/source, possible matching invoices, confidence or reason for flagging, status.
- FR-PAY-8: Finance can review, match to invoice, record as partial payment, reject a suggested match, mark as Requires Investigation, add internal notes, and view reconciliation history.
- FR-PAY-9: Where business rules permit, one payment can be allocated across multiple invoices and multiple payments to one invoice; all allocations are recorded accurately.
- FR-PAY-10: A payment is not Reconciled until correctly linked and recorded.
- FR-PAY-11: Duplicate payment records and duplicate webhook processing are prevented (unique transaction ID constraint, idempotent webhook handler).

### 6.9 Reminders and Notifications (FR-NOT)
- FR-NOT-1: Admin configures reminder policies. Default illustrative timeline (all intervals configurable):
  1. Invoice generated: customer receives invoice and due date.
  2. 3 days before due: upcoming payment reminder.
  3. Due date: payment due notification.
  4. 7 days overdue: overdue notice to customer and alert to Finance.
  5. 15 days overdue: escalation to Finance/Admin.
- FR-NOT-2: System monitors due dates, identifies unpaid and partially paid invoices, calculates outstanding amounts, and notifies relevant customer business contacts.
- FR-NOT-3: Reminders stop automatically when the invoice is fully paid or cancelled.
- FR-NOT-4: Reminder history stores: invoice reference, customer business, reminder type, date/time, outstanding amount at the time, channel, delivery status, failure reason.
- FR-NOT-5: Finance can see which invoices have reminders sent, which are overdue, which customers were reminded, which notifications failed, and which need manual follow-up.
- FR-NOT-6: Channels: email and in-portal notifications at launch; other channels via future integrations.
- FR-NOT-7: Notifications are also sent for: new quotations, quotation decisions, accepted quotations (to Finance), new invoices, payments and receipts, partial payments, renewals, expiry, plan changes, unmatched payments, failed notifications.
- FR-NOT-8: Payment reminders and subscription lifecycle rules are independent.

### 6.10 Dashboards (FR-DASH)
Dashboards support filters and summary views and load within the performance target.

**Customer dashboard**
Active subscriptions with details (quantity/seats, billing frequency, start/expiry, next renewal or billing date); pending requests with type and status; quotations awaiting acceptance with version info; invoice history; total invoiced, paid, outstanding; overdue invoices; payment history and reconciliation status where relevant; notifications and upcoming reminders; actions to request new subscription, upgrade, downgrade, renewal, additional seats, cancellation.

**Admin dashboard**
Total customers; active subscriptions; new requests and requests by type; requests awaiting Sales review; quotations awaiting Admin approval; quotations awaiting customer acceptance; accepted quotations waiting for Finance; invoices generated, paid, outstanding, overdue; payments received; unmatched payments; upcoming renewals/expiries; revenue received; total owed; reminder activity; system activity and audit history.

**Sales dashboard**
New requests; requests awaiting review or clarification; requests by category; quotations being prepared, awaiting Admin approval, returned for changes, awaiting customer acceptance, rejected; revision history; customer follow-up tasks.

**Finance dashboard**
Accepted quotations awaiting processing; invoices generated, paid, unpaid, partially paid, overdue; outstanding balances; payments received; unmatched payments and payments awaiting reconciliation; reconciliation history; upcoming due dates; reminders sent; failed notifications; customers needing follow-up. Also covers active subscriptions, revenue received, outstanding amounts and overdue invoices per the original problem statement.

### 6.11 Audit Logging (FR-AUD)
- FR-AUD-1: Log quotation creation and revision; Admin approvals and rejections; customer acceptance; discount application; invoice confirmation and cancellation; payment recording; reconciliation; subscription activation and closure; staff permission changes; reminder activity.
- FR-AUD-2: Each entry records actor, action, affected record, timestamp (and before/after values where meaningful).
- FR-AUD-3: Audit records are append-only; ordinary users cannot edit or delete them.

---

## 7. Business Rules Summary

1. Two portals; three user categories.
2. Staff have task-specific permissions; Sales and Finance permissions are separate.
3. Only Admin creates staff accounts.
4. A customer business supports multiple users with different permissions.
5. A request is not a subscription.
6. A quotation is an offer; it becomes the basis for a confirmed subscription only upon customer acceptance.
7. Admin approval and customer acceptance are separate steps; Admin approval is mandatory for every version.
8. Every revision is a new, preserved version; acceptance binds to one exact version; accepted versions are immutable.
9. Finance handles invoicing and payments after acceptance.
10. Bulk seat entry is required.
11. Product, variant and plan are distinct.
12. Subscription, invoice, payment and reconciliation statuses are tracked independently.
13. Auto-reconciliation requires an authorized integration.
14. Unmatched payments go to the Finance reconciliation queue.
15. No duplicate payments, webhooks, invoices or skipped billing cycles.
16. Reminders are Admin-configurable, logged, and stop on full payment or cancellation.
17. Overdue status never auto-suspends a subscription unless explicitly configured.
18. Customers access only their own business data.
19. All significant financial and commercial actions are traceable.
20. Historical records are never deleted or silently altered.

---

## 8. Proposed Data Model (Logical)

| Entity | Key notes |
|---|---|
| User | Unique email, password hash, type (Admin / Staff / Customer), role, business (for customers), active flag |
| Role / Permission | Internal role permissions; customer-side role permissions |
| CustomerBusiness | Business details, contacts, status |
| Product, ProductVariant | Price effects on variants; cost price |
| Plan | Billing frequency, price, min quantity, availability dates, lifecycle flags |
| TaxRate | Configurable rates and applicability |
| DiscountRule | Type (fixed/percent), eligibility, authorization limits |
| SubscriptionRequest, RequestActivity | Type, status, assigned Sales rep, activity history |
| QuotationTemplate | Reusable line sets |
| Quotation, QuotationVersion, QuotationVersionLine | Version immutable once approved/accepted; lines hold product, variant, plan, quantity, unit price, discount, tax |
| QuotationDecision | Admin and customer decisions, actor, timestamp, version, reason |
| Subscription, SubscriptionLine | Linked to accepted quotation version; activation policy |
| Invoice, InvoiceLine | Snapshot of amounts; unique (subscription, billing period) |
| Payment, PaymentAllocation | Allocation table supports many-to-many between payments and invoices |
| BankTransaction / WebhookEvent | Unique external transaction ID; raw payload; duplicate flag |
| ReconciliationRecord | Status, suggested matches, confidence, notes, history |
| ReminderPolicy, ReminderLog | Policy steps; delivery tracking |
| Notification | In-portal and email, read state, delivery status |
| BillingJobRun | Run log, retries, failures |
| AuditLog | Append-only |

Key constraints: unique email; unique invoice number; unique (subscription_id, billing_period); unique external transaction ID; foreign keys scoping every customer-owned record to a business.

---

## 9. Non-Functional Requirements

### 9.1 Security
- Server-side authorization on every endpoint; customer queries always filtered by business.
- Protection against ID/URL tampering (IDOR).
- Secure password storage (strong hashing), password reset with expiring tokens.
- Webhook endpoints authenticated (signature verification) and idempotent.
- Input validation, CSRF/XSS protection, rate limiting on authentication.

### 9.2 Reliability
- Recurring billing is idempotent and retry-safe.
- Webhooks processed safely with deduplication.
- Failed jobs logged, alertable and retryable.
- Notification delivery tracked.
- Financial writes use transactions so invoice and payment balances never drift.

### 9.3 Performance
- Under 2 seconds per page at thousands of subscriptions.
- Indexed queries; pagination for lists; dashboard aggregates computed efficiently (e.g., pre-aggregated or cached summaries).
- Load testing with realistic data volumes before release.

### 9.4 Usability
- Clear, user-friendly workflows for both portals; consistent status labels; filters on lists and dashboards.

### 9.5 Data Integrity and Retention
- Historical quotations, invoices, payments and subscriptions are retained after closure.
- Money stored as exact decimals (or minor units), with a defined currency (INR assumed; see open questions).

---

## 10. Integrations

| Integration | Purpose | Notes |
|---|---|---|
| Email service | Invoices, reminders, notifications | Delivery status tracked |
| Bank feed / payment gateway | Automatic payment detection | Must be authorized and supported; not assumed |
| Manual entry | Fallback for all payment types | Always available |
| Future | Other notification channels, card auto-charge, seat provisioning | Out of initial scope |

---

## 11. Release Plan (Proposed)

| Phase | Scope |
|---|---|
| **1. Foundation** | Auth, RBAC, staff creation, customer business + multi-user, catalog (products, variants, plans, taxes, discounts), audit log framework |
| **2. Commercial workflow** | Request management, quotation creation with bulk seats, versioning and comparison, Admin approval, customer accept/reject, subscriptions |
| **3. Billing and payments** | Invoice generation from accepted quotations, manual payment recording, partial payments, recurring billing engine (idempotent), Finance queue |
| **4. Automation** | Reminder engine and history, payment integration + webhooks, reconciliation queue, notifications |
| **5. Dashboards and hardening** | Role dashboards, renewals/expiry handling, performance testing, security review, end-to-end testing |

---

## 12. Acceptance Criteria (Key)

1. A Sales rep can enter quantity 50 in one operation on a quotation.
2. A quotation cannot reach the customer without Admin approval; each new version requires re-approval.
3. Quotation v1 remains intact after v2 is created; version diff shows changed fields.
4. A customer's acceptance is stored with the user, timestamp and exact version, and that version cannot be edited afterwards.
5. Accepted quotations appear in Finance; the invoice is auto-populated from the accepted version.
6. A customer cannot retrieve another business's records by changing IDs or URLs (verified by tests).
7. Running the billing job twice for the same period produces one invoice.
8. Replaying the same payment webhook creates one payment and records the duplicate notification.
9. The five reconciliation scenarios behave as specified in 6.8.
10. A ₹20,000 payment on a ₹50,000 invoice shows Partially Paid with ₹30,000 outstanding in Finance and Customer views.
11. Reminders follow the Admin-configured schedule, are logged with delivery status, and stop when the invoice is paid or cancelled.
12. An overdue invoice does not change subscription status unless the policy is explicitly enabled.
13. Subscription, invoice, payment and reconciliation statuses are independently visible and updated.
14. Only Admin can create staff accounts; Sales cannot access Finance-only functions and vice versa.
15. Key pages load in under 2 seconds with a dataset of several thousand subscriptions and proportional invoices.
16. All audit-listed actions produce audit entries that ordinary users cannot alter.

---

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Bank/payment integration unavailable or limited | Manual recording always available; reconciliation queue; design integration behind an adapter |
| Duplicate invoices or payments | DB uniqueness constraints, idempotency keys, transactional processing |
| Cross-business data leakage | Mandatory business scoping in data-access layer; automated isolation tests |
| Dashboard slowness at scale | Indexing, pagination, aggregate caching, load tests |
| Status confusion in UI/logic | Separate status fields and clearly labeled UI components |
| Over-complex permissions | Start with role presets, allow Admin tuning |
| Missed billing runs | Scheduler monitoring, catch-up logic, failure alerts |

---

## 14. Assumptions

- Currency is INR (₹) unless otherwise specified.
- Email is the primary external notification channel at launch.
- Quotation validity periods are enforced; expired quotations cannot be accepted.
- Tax rules (e.g., GST) are configured by Admin rather than hardcoded.

## 15. Open Questions

1. What are the exact password requirements from the original problem statement?
2. Which bank feed or payment gateway will be integrated first?
3. Which customer-side permission sets are required by default (Owner, Finance Contact, Subscription Manager) and can the Business Owner customize them?
4. Is multi-currency required, or INR only?
5. How should proration be handled for mid-term seat additions, upgrades, downgrades and early cancellation?
6. What are the default activation policy and the default reminder schedule per customer segment?
7. Are pauses billing-free, and how do they affect expiry dates?
8. Which discount authorization limits apply to Sales vs Admin?
9. What invoice delivery format is required (PDF, print layout, numbering scheme)?
10. Are there data retention or compliance requirements (e.g., tax record retention periods)?

---

## 16. Implementation Guidance

- Understand the whole workflow before changing any part of it.
- Do not remove existing functionality or the mandatory Admin approval step.
- Do not treat requests as subscriptions or acceptance as payment.
- Keep the four status families separate.
- Preserve quotation versions and accepted commercial terms.
- Implement customer-business isolation server-side.
- Keep Sales and Finance permissions separate.
- Do not assume bank access; do not auto-suspend on overdue.
- Prevent duplicate billing and duplicate payment processing.
- For work in an existing codebase, inspect the structure and current implementation first, preserve working features, avoid unnecessary rewrites, and test the complete workflow after changes.
- Prioritize correctness, security and reliability over adding features.
