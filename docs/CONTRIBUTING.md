# Contributing Guide: Brightloop Subscription Management System

Welcome to the Brightloop SMS contributor repository. This document establishes technical conventions, PR workflows, and quality standards for team contributors.

---

## 1. Code of Conduct & Core Principles
- **Documentation Integrity**: Maintain clear inline docstrings and architectural notes for all core business logic.
- **Workflow Compliance**: Never bypass the mandatory commercial state transitions:
  `Request -> Quotation -> Admin Approval -> Customer Acceptance -> Active Subscription -> Invoicing -> Reconciliation`.
- **Tenant Isolation**: Always enforce customer-business scoping at the database access layer. Never trust frontend ID parameters without backend verification.

---

## 2. Branching Strategy & Git Workflow

We adhere to standard feature-branch workflows:
- `main`: Production-ready, stable codebase.
- `feature/<feature-name>`: Scoped functional additions.
- `fix/<bug-description>`: Defect resolutions and patches.
- `docs/<topic>`: Documentation, architecture updates, and developer guides.

### Commit Message Conventions
We follow the Conventional Commits specification:
- `feat:` Introduces a new feature or endpoint.
- `fix:` Patches a bug or regression.
- `docs:` Documentation additions or updates only.
- `refactor:` Code improvements without behavioral changes.
- `test:` Adding or updating unit/integration test coverage.
- `chore:` Build scripts, dependency bumps, or tool configurations.

---

## 3. Development Setup

### Backend (FastAPI + SQLAlchemy)
1. Navigate to `/backend`:
   ```bash
   cd backend
   ```
2. Activate Python virtual environment:
   ```bash
   # Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations and start API server:
   ```bash
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend (React + Vite + TypeScript)
1. Navigate to `/frontend`:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start development server:
   ```bash
   npm run dev
   ```

---

## 4. Code Quality & Testing Checklist

Before opening a pull request, ensure the following checks pass:
- [ ] Backend test suite succeeds: `pytest`
- [ ] No regression in customer-business isolation checks (`test_customer_isolation.py`).
- [ ] New quotation versions properly retain historical immutable records.
- [ ] All database schema changes have corresponding Alembic migration scripts.
- [ ] Code formatting conforms to project linters (Black / Flake8 / ESLint / Prettier).
