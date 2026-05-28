# Phase 5 - Import, Export, Notifications, and Integrations

## Goal

Create reusable data movement, notification, and third-party integration infrastructure across all implemented modules.

## Import framework

Build:

- Module selector for supported imports.
- Sample template download per module.
- File upload and validation.
- Dry-run validation result.
- Import execution.
- Import history with status, row counts, errors, actor, and timestamps.
- View, edit/retry, and delete import records where safe.

Supported import modules:

- shifts
- employees
- candidates
- leave balances
- holidays
- company tree
- job openings

Suggested tables:

- `import_jobs`
- `import_job_errors`
- `import_templates`

## Export framework

Build:

- Module selector for supported exports.
- Filtered export jobs.
- Async export status.
- File metadata and download endpoint.
- Permission checks per module.
- Audit trail for exports.

Supported export modules:

- shifts
- employees
- candidates
- leave balances
- holiday calendar
- company tree
- job openings
- attendance muster

Suggested tables:

- `export_jobs`
- `export_files`

## Email subscriptions and notifications

Build:

- User notification preference backend.
- Company notification defaults.
- Module-level email toggles.
- Notification event creation from domain actions.
- Email delivery provider abstraction.
- Retry and failure logging.

Suggested tables:

- `notification_preferences`
- `notification_events`
- `notification_deliveries`
- `email_templates`

## Calendar and meeting integrations

Build:

- Google Calendar service account settings.
- Secure JSON credential storage reference.
- Calendar sync for events and meetings.
- Zoom-style OAuth token storage and meeting link creation hooks.
- Integration enable/disable per user or company.

Suggested tables:

- `integration_settings`
- `user_integrations`
- `calendar_sync_events`
- `meeting_provider_events`

## Acceptance criteria

- Every import has template, validation, execution, history, and error reporting.
- Every export respects RBAC and records audit logs.
- Notification preferences can be customized at user and company level.
- Domain actions emit notification events without coupling route handlers to email delivery.
- Calendar and meeting integrations can be configured without storing raw secrets in normal JSON fields.
