# Setup Instructions

## Requirements

- Python 3.12+
- pip
- PostgreSQL database for TeamPilot HRMS modules
- MongoDB or MongoDB-compatible URI for the existing org chart module

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env` and update values as needed.

Required keys:

- `BEARER_TOKEN` - internal bearer token used by legacy protected endpoints.
- `JWT_SECRET` - secret string used to sign JWT access and refresh tokens.
- `DATABASE_URL` - SQLAlchemy PostgreSQL URL for TeamPilot HRMS.
- `MONGO_URI` - MongoDB URI for existing org chart routes.
- `DB_NAME` - MongoDB database name.
- `DOMAIN_URL` - application base domain.
- `GOOGLE_CLIENT_ID` - Google OAuth client ID.
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret.

PostgreSQL can be configured with either `DATABASE_URL`, `POSTGRES_URI`, or separate `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` values.

If no PostgreSQL URL is set, the app falls back to local SQLite at `teampilot.db` for lightweight development and tests.

## Run migrations

```bash
alembic upgrade head
```

## Run the application

```bash
python run.py
```

The application runs on `http://127.0.0.1:5002`.

Swagger docs are available at `http://127.0.0.1:5002/docs`.

## Seed users

Seed data is created on startup if the users do not already exist.

| Role | Email | Password |
| --- | --- | --- |
| Admin | `Admin@cxontology.com` | `Admin@123` |
| Manager | `manager@cxontology.com` | `Manager@123` |
| Employee | `employee@cxontology.com` | `Employee@123` |

## TeamPilot module endpoints

- Auth: `/auth/signup`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/microsoft`, `/auth/me`
- Employees: `/employees/me`, `/employees/{employee_id}`, `/employees`
- Attendance: `/attendance/swipe`, `/attendance/today`, `/attendance/history`, `/attendance/calendar`, `/attendance/team`, `/attendance/team/online`
- Regularization: `/regularization`, `/regularization/my`, `/regularization/team`, `/regularization/{request_id}/status`
- Leave: `/leave/balance`, `/leave/requests`, `/leave/requests/my`, `/leave/requests/team`, `/leave/requests/{request_id}/status`, `/leave/policies`
- Holidays: `/holidays`, `/holidays/import`, `/holidays/{holiday_id}`
- Approvals: `/approvals/pending`
- Audit: `/audit/logs`
- Admin configuration: `/admin/config`

## Attendance storage

Swipe in/out uses two SQL tables:

- `attendance_temp_swipes` stores current-day live swipes and is reset lazily when a new day starts.
- `attendance_swipes` stores every swipe as immutable permanent history.

Daily summaries are calculated from `attendance_swipes` and stored in `attendance_daily_summaries`.

## Tests

```bash
python -m pytest -q
```
