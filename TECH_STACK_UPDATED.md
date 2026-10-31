# Brightloop Subscription Management System
## Updated Technical Stack

**Purpose:** Implementation technologies and technical conventions aligned with the revised PRD.

## 1. Stack at a Glance

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React + TypeScript + Vite | Internal and Customer portals |
| Styling | Tailwind CSS | Responsive design system |
| UI components | shadcn/ui, selectively | Accessible, composable components |
| Icons | Lucide React | Consistent icons; no emoji icons |
| Charts | Recharts | Role-based dashboards and reporting |
| API | Python + FastAPI | REST API and business workflows |
| Validation | Pydantic | Request/response validation |
| ORM | SQLAlchemy 2.x | Database access |
| Migrations | Alembic | Versioned schema changes |
| Database | PostgreSQL | Transactional source of truth |
| Authentication | JWT access tokens + secure password hashing | Authenticated API access |
| Authorization | Server-side RBAC and business-scope checks | Access control and tenant isolation |
| Background jobs | Celery + Redis | Recurring billing, reminders, retries |
| PDF generation | ReportLab | Quotation and invoice PDFs |
| Backend tests | Pytest | Unit, integration, workflow tests |
| Frontend tests | Vitest + React Testing Library | Component and frontend logic tests |
| E2E tests | Playwright | Critical role-based journeys |
| Local services | Docker Compose | Reproducible development environment |

Use repository-compatible versions and lock them in dependency files. Avoid major-version upgrades without compatibility checks.

## 2. Architecture

Use a modular, API-driven application:

- React SPA with separate route groups/layouts for Internal and Customer portals.
- FastAPI backend organized by domain.
- PostgreSQL as the authoritative store for commercial, financial, access-control, and audit records.
- Celery workers with Redis for scheduled and retryable tasks.
- Generate PDFs from persisted approved/issued records.
- Isolate payment gateway and bank-feed integrations behind adapters. Do not assume integrations are configured.

The frontend must not connect directly to PostgreSQL. Sensitive business rules and permissions must be enforced by the backend.

## 3. Suggested Backend Structure

```text
backend/
  app/
    api/routes/
    core/                 # config, security, permissions
    db/                   # session, base
    models/
    schemas/
    services/
    repositories/
    jobs/
    integrations/
    audit/
    main.py
  alembic/
  tests/
```

Organize domain logic around identity and membership, catalog, subscription requests, quotations and approvals, subscriptions, invoices and billing, payments and allocations, reconciliation, reminders, audit, and reporting. Keep business logic out of route handlers.

## 4. Database and Data Integrity

Use PostgreSQL, SQLAlchemy 2.x, and Alembic.

- Use transactions for multi-step financial and commercial operations.
- Store money using `NUMERIC`/decimal types, never binary floating-point.
- Store currency explicitly. Confirm the PRD’s currency assumption before production.
- Store timestamps in UTC and convert consistently for display.
- Add foreign keys, indexes, and database constraints.
- Enforce uniqueness for subscription + billing period to prevent duplicate invoices.
- Use durable idempotency for billing and payment-processing operations.
- Deduplicate gateway webhooks by provider event ID when a gateway is configured.
- Preserve historical records and quotation versions; never overwrite an accepted quote version.
- Keep audit logs append-only through application controls and restricted database permissions.
- Scope customer-facing queries by the authenticated user’s business. Never rely on frontend filtering for tenant isolation.

## 5. Authentication and Authorization

Roles in the revised PRD:

- Admin
- Sales Rep
- Finance Rep
- Customer Owner
- Customer Finance Contact
- Customer Subscription Manager

Enforce permissions on every protected API operation. Admin creates internal staff accounts. Resolve customer business membership from trusted server-side identity data; do not trust client-supplied role or business IDs without validation. Use secure password hashing, short-lived access tokens, and configurable session/token behavior. Keep secrets in environment variables or a secrets manager.

Customer-role permissions and the password policy remain PRD decisions; do not invent production rules.

## 6. Frontend Structure

Suggested structure:

```text
frontend/
  src/
    app/
    routes/
    layouts/
    features/
      auth/
      catalog/
      requests/
      quotations/
      subscriptions/
      invoices/
      payments/
      reconciliation/
      reminders/
      dashboards/
    components/
    hooks/
    services/
    types/
    styles/
```

Use typed API clients and shared request/response types. Keep portal navigation and permissions distinct. Route guards are useful for navigation, but do not replace backend authorization. Represent each domain’s statuses independently—request, quotation, subscription, invoice, payment, and reconciliation. Provide loading, empty, validation, error, and success states. Prevent accidental duplicate form submissions and display server-side validation errors.

### Visual direction

- Restrained professional SaaS UI: neutral base, deliberate blue/navy accent.
- Clear typography, meaningful whitespace, compact information hierarchy.
- Modest rectangular buttons; avoid excessive pill-shaped controls.
- Avoid purple gradients, vague hero copy, fake reviews/metrics/counters, excessive scroll animations, “made with AI” labels, and generic AI-generated stock imagery.
- Charts must reflect real records or be clearly marked as demo/seeded data.
- Do not present fabricated financial or churn figures as live metrics.

## 7. Required Workflow Support

The backend must enforce this sequence:

1. Customer registration and subscription request
2. Sales review and quotation creation
3. Mandatory Admin approval of the quotation version
4. Customer acceptance of that exact approved version
5. Finance review and invoice creation
6. Payment recording and allocation
7. Reconciliation
8. Subscription activation according to configured policy
9. Recurring billing

Use explicit, validated state transitions. Do not allow clients to bypass approval by submitting arbitrary status values.

### Quotation versioning

- Each revision creates a new immutable version.
- Every version requires Admin approval.
- Acceptance references the exact version and records accepting user and timestamp.
- Expired quotes cannot be accepted.
- Preserve approval history and enable version comparison.

### Billing and payment correctness

- Prevent duplicate invoices per subscription and billing period with a DB constraint and idempotent service logic.
- Support safe catch-up for missed billing cycles.
- Support manual payments, partial payments, multiple payments per invoice, and allocations across invoices.
- Reconciliation must handle exact match, missing reference, partial amount, mismatch, and duplicate webhook cases.
- Never arbitrarily match an unmatched payment.
- Do not automatically suspend or terminate subscriptions for overdue invoices unless an explicit configured policy permits it.
- No automatic card charging or direct bank access unless an authorized integration is configured.

## 8. Background Jobs and Notifications

Use Celery + Redis for recurring invoice generation, catch-up billing, configured reminders, notification delivery, retryable integration tasks, and periodic consistency checks.

Jobs must be safe to retry and record outcomes. Stop reminders when the invoice is paid or the relevant record is cancelled, according to the PRD. Notification channels/providers are undecided; do not claim delivery if no provider is configured.

## 9. Financial PDFs

Use ReportLab for quotation and invoice PDFs.

- Generate from persisted records and approved/issued versions.
- Include relevant IDs, dates, customer details, line items, quantities, taxes, discounts, totals, and payment terms.
- Keep PDFs consistent with stored financial data.
- Do not rebuild historical documents from mutable current catalog settings.
- Confirm invoice numbering, layout, and jurisdiction-specific compliance before production.

## 10. Testing

### Pytest

Test role permissions, cross-business access denial, quote approval/versioning/expiry/acceptance, request transitions, invoice uniqueness, recurring billing idempotency, catch-up billing, partial payments, allocation math, reconciliation cases, webhook deduplication, reminder stop conditions, activation policy, no unintended suspension, and audit behavior.

### Vitest + React Testing Library

Test key components, forms, validation, status displays, and role-aware navigation.

### Playwright

Cover critical journeys for Admin, Sales Rep, Finance Rep, and customer users. Include negative permission tests and confirm unauthorized actions are rejected by the API.

## 11. Performance, Reliability, and Security

- Target page loads under 2 seconds for thousands of subscriptions, subject to measurement and infrastructure.
- Use pagination and server-side filtering/sorting for large tables.
- Index according to query patterns; inspect slow queries and avoid N+1 access.
- Use structured logs and actionable error handling.
- Do not expose stack traces, secrets, or sensitive financial data in client errors.
- Apply input validation, suitable rate limits, and secure CORS configuration.
- Define backups and recovery before production.
- Treat financial correctness, auditability, and tenant isolation as release blockers.

## 12. Environment and Deployment

Use Docker Compose for local PostgreSQL and Redis services. Provide an `.env.example` with placeholders only.

Example configuration categories:

```text
DATABASE_URL
REDIS_URL
JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES
FRONTEND_ORIGIN
APP_ENV
```

Add integration credentials only after selecting and authorizing an integration. Hosting, email provider, payment gateway, bank-feed provider, and observability stack are not specified by the PRD and require separate decisions.

## 13. Implementation Order

Follow the revised PRD phases:

1. **Foundation:** authentication, RBAC, staff accounts, customer multi-user businesses, catalog, taxes, discounts, audit.
2. **Requests and quotations:** request lifecycle, quote creation, bulk quantity/seats, versioning, mandatory Admin approval, customer acceptance, subscription records.
3. **Finance:** invoices, manual and partial payments, allocations, recurring billing, idempotency, finance queue.
4. **Operations:** reminders, selected integrations, webhook deduplication, reconciliation, notifications.
5. **Reporting and hardening:** role dashboards, renewals, performance, security, E2E testing.

Do not prioritize AI finance insights, forecasting, pricing simulation, or usage-based billing ahead of the core commercial and financial workflow. Treat these as later enhancements, and ground any AI-generated insight in actual system data.

## 14. Decisions to Confirm Before Production

The PRD leaves these unresolved; do not silently invent behavior:

- Currency and localization
- Customer-role permissions
- Password/account security policy
- Payment gateway or bank-feed provider and authorization
- Proration rules
- Default activation and reminder policies
- Pause/resume billing and date behavior
- Discount limits and approval rules
- Invoice numbering, layout, and compliance requirements
- Data retention and compliance requirements
- Notification channels/providers
- Hosting, backup, and monitoring approach

---

**Source of truth:** The revised PRD defines product behavior and acceptance criteria. This file defines the recommended implementation stack and technical conventions. Keep unresolved choices configurable and document decisions before release.
