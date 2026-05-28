# Architecture Overview

## Project structure

- `run.py` - Uvicorn entrypoint.
- `app/main.py` - FastAPI app setup, CORS, exception handlers, route registration, and seed startup.
- `app/core/` - SQLAlchemy database setup, JWT/password security, permissions, and response/error helpers.
- `app/models/hr.py` - `ppl-hr` SQLAlchemy 2.x models.
- `app/schema/hr_schema.py` - Pydantic v2 request validation schemas.
- `app/routes/` - `ppl-hr` modules plus existing user/chart routes.
- `app/services/team_pilot.py` - seed data and attendance summary calculation.
- `alembic/` - PostgreSQL migration environment and initial schema migration.
- `tests/` - pytest coverage for required Phase 1 workflows.

## Persistence

`ppl-hr` modules use PostgreSQL through SQLAlchemy 2.x. The default local fallback is SQLite for lightweight development and tests when `DATABASE_URL`/`POSTGRES_URI` is not set.

The original organizational chart routes are preserved and continue to use the existing MongoDB/Motor dependency in `app/database.py`.

## Current `ppl-hr` SQL tables

- `team_users`
- `employee_profiles`
- `attendance_temp_swipes`
- `attendance_swipes`
- `attendance_daily_summaries`
- `regularization_requests`
- `leave_policies`
- `leave_requests`
- `holidays`
- `audit_logs`
- `refresh_tokens`
- `admin_configurations`

`audit_logs.metadata`, `employee_profiles.person`, and `admin_configurations.value` use PostgreSQL JSONB with a SQLite JSON fallback for tests.

## Attendance design

- `attendance_temp_swipes` stores current-day live swipe state and is reset lazily when a new day starts.
- `attendance_swipes` stores every swipe as an immutable permanent history record.
- `attendance_daily_summaries` is recalculated from permanent swipes.

Rules:

- First check-in is the first `CHECK_IN` of the day.
- Last check-out is the last paired `CHECK_OUT` of the day.
- 8+ hours is `PRESENT`.
- 4+ hours is `HALF_DAY`.
- Less than 4 hours is `ABSENT`.
- Open check-in is `IN_PROGRESS`.
- Check-in after 09:30 is late.
- Work above 9 hours is overtime.

## Security

- Passwords are hashed with passlib/bcrypt.
- JWT access and refresh token expiration are configurable.
- Protected routes use dependency-injected current user validation.
- RBAC rules are enforced in `app/core/permissions.py`.
- Create/update/delete/approval actions write audit logs.
