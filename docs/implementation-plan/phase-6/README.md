# Phase 6 - Hardening, Reporting, and Release Readiness

## Goal

Prepare the backend for production use after the functional modules are implemented.

## Security and compliance

- Review RBAC and ownership checks for every endpoint.
- Add permission matrix documentation.
- Add audit coverage tests for sensitive actions.
- Add rate limits for auth, imports, exports, and public applicant endpoints.
- Add secure file validation for uploads.
- Add secret handling rules for integration credentials.
- Add data retention policies for logs, import files, export files, and deleted records.

## Reporting APIs

Build non-dashboard reporting endpoints where needed:

- Attendance monthly reports.
- Leave yearly reports.
- Recruitment pipeline reports.
- Employee headcount reports.
- Ticket SLA reports.
- OKR cycle progress reports.

These APIs should serve reports and exports, not dashboard widgets.

## Observability

- Structured logs with request IDs.
- Error tracking hooks.
- Health check and readiness endpoints.
- Database migration status check.
- Background job status metrics.

## Performance

- Add indexes for high-volume filters.
- Paginate all list endpoints.
- Add database-level uniqueness constraints for duplicate-prone records.
- Optimize company tree and employee search queries.
- Add background jobs for imports, exports, notification delivery, and calendar sync.

## Testing

- Unit tests for services and validators.
- Route tests for auth, permissions, and ownership.
- Migration tests.
- Import/export fixture tests.
- Integration contract tests with mocked providers.
- Regression tests for attendance and leave calculations.

## Release checklist

- API documentation generated and reviewed.
- Postman collection or OpenAPI examples updated.
- Alembic migrations tested from empty database and previous release database.
- Seed data updated for all roles.
- Environment variables documented.
- CI runs lint, tests, and migration checks.
- Production settings documented.
