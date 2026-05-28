# Phase 1 - Foundation and Current Core

## Goal

Stabilize the project identity, backend conventions, security model, and cross-cutting infrastructure before adding larger modules.

## Scope

- Rename public backend identity to `ppl-hr` in app metadata, docs, seed labels, and API examples.
- Keep route structure modular under `app/routes/`.
- Keep domain tables in SQLAlchemy/Alembic and avoid adding new MongoDB dependencies beyond the existing chart feature.
- Standardize envelope responses, pagination, filtering, sorting, and validation errors.
- Extend RBAC beyond `Employee`, `Manager`, and `Admin` where needed for HR/recruiter flows.
- Define permission keys for every module before building routes.
- Keep audit logs for create, update, delete, import, export, approval, and status-change actions.
- Add migration and pytest requirements for every new model and route group.

## Existing coverage to preserve

- Auth: signup, login, refresh, logout, forgot password, reset password, current user.
- Core users and employee profiles.
- Attendance swipes and daily summaries.
- Leave policies and leave requests.
- Holidays.
- Approvals and audit logs.
- Admin configuration.

## Implementation tasks

1. Update API metadata and docs naming to `ppl-hr`.
2. Add role/permission tables or permission config.
3. Add shared query helpers for pagination, search, date ranges, status filters, and ownership constraints.
4. Add a shared file/import/export storage abstraction.
5. Add notification event queue table for email and integration events.
6. Add test fixtures for admin, HR/recruiter, manager, and employee users.

## Acceptance criteria

- API docs and repository docs consistently use `ppl-hr`.
- Every protected route uses dependency-injected current-user checks.
- Permissions are documented and testable.
- Audit logging is consistent across existing write routes.
- New migrations run cleanly on PostgreSQL and SQLite test fallback.
