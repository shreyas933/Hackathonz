# Deployment and Environment Setup Guide

## 1. Prerequisites
- **Python**: 3.11+
- **Node.js**: 18.x or 20.x LTS
- **Package Managers**: `pip` (Python), `npm` / `pnpm` (Frontend)
- **Database**: PostgreSQL 15+ (Production) or SQLite (Local Development)

---

## 2. Configuration & Environment Variables

Create `.env` files in `backend/` and `frontend/` derived from the templates provided.

### Backend `.env` Options
```ini
# Core Application
APP_NAME="Brightloop Subscription Management System"
ENVIRONMENT="production"
DEBUG=False
SECRET_KEY="replace-with-cryptographically-secure-random-key"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
DATABASE_URL="postgresql+asyncpg://brightloop:secret_pass@localhost:5432/brightloop_sms"
# SQLite Alternative for local quick-runs:
# DATABASE_URL="sqlite+aiosqlite:///./brightloop.db"

# Background Job Queue
REDIS_URL="redis://localhost:6379/0"

# Mail & Notification Config
SMTP_HOST="smtp.mailgun.org"
SMTP_PORT=587
SMTP_USER="postmaster@brightloop.local"
SMTP_PASSWORD="smtp_password"
EMAILS_FROM_EMAIL="notifications@brightloop.com"
```

### Frontend `.env` Options
```ini
VITE_API_BASE_URL="http://localhost:8000/api"
VITE_APP_TITLE="Brightloop SMS Portal"
```

---

## 3. Production Deployment Architecture

For high-availability containerized deployments:
1. **Reverse Proxy (Nginx / Traefik)**: Terminates TLS, handles CORS, routes `/api/*` to FastAPI upstream and `/` to Vite SPA static assets.
2. **Backend API Pods**: Managed via Uvicorn workers behind Gunicorn:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
3. **Background Worker**: Dedicated Celery worker for recurring billing cycles and automated email reminders:
   ```bash
   celery -A app.core.celery_app worker -l info -B
   ```
4. **Health Checks**:
   - `/api/health`: Validates database connectivity and service availability.
