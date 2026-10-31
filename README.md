# Brightloop Subscription Management System (SMS)

A modern, centralized B2B SaaS platform engineered to manage the complete commercial subscription lifecycle: customer requests, quotation versioning with mandatory Admin approvals, automated idempotent recurring billing, and payment reconciliation.

---

## Key Features

- **Commercial Workflow**: Seamless transitions from customer requests to itemized quotes, version diffing, and binding customer acceptance.
- **Mandatory Admin Authorization**: Multi-stage approval safeguards before quotations reach clients.
- **Idempotent Recurring Billing**: Reliable scheduled invoice creation without risk of duplicate cycles.
- **Payment Reconciliation**: Automatic matching and Finance review queues for full financial traceability.
- **Multi-Tenant Security**: Server-side business scoping preventing cross-tenant data leakage.

---

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL / SQLite
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide React
- **Background Jobs**: Celery, Redis
- **Testing**: Pytest

---

## Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Documentation

Detailed documentation is available in the [`docs/`](./docs/) directory:
- [System Architecture](./docs/ARCHITECTURE.md)
- [API Reference](./docs/API_DOCUMENTATION.md)
- [Contributing Guide](./docs/CONTRIBUTING.md)
- [Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)
- [Testing Strategy](./docs/TESTING_STRATEGY.md)
- [Project FAQ](./docs/FAQ.md)
