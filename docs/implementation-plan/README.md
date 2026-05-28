# ppl-hr Implementation Plan

This folder breaks the backend product build into practical phases. The plan is based on the requested HR platform scope and the current `ppl-hr-backend` codebase.

## Product scope

Build the backend for these modules:

- Authentication, users, roles, permissions, audit logs, and admin settings.
- Employee directory, employee profiles, update requests, onboarding/offboarding checklists, shifts, and company tree.
- Attendance check-in/check-out, recent swipes, calendar/list views, regularization, muster, and exports.
- Leave policies, balances, transactions, leave applications, comp-off, and approvals.
- Holiday calendar and holiday management.
- Recruitment: job openings, referrals, interviews, feedback, hire requests, candidate tracking, direct applicants, and candidate-to-employee conversion.
- Company search, starred people, teams, and organization tree management.
- Email subscriptions and notification preferences.
- OKRs with objectives, key results, progress updates, review cycles, and visibility controls.
- Meetings with invites, attendee responses, calendar/meeting-provider integration hooks.
- Support tickets, comments/internal notes, assignment, status, priorities, and SLAs.
- Import/export framework for shifts, employees, candidates, leave balances, holidays, company tree, and job openings.
- Integrations for Google Calendar and Zoom-style meeting providers.

## Explicit exclusions

- Dashboard screens and dashboard-only aggregation widgets are out of scope.
- Social feed posts, feed comments, feed likes, and feed-style community interactions are out of scope.

## Phase index

- [Database Structure](database-structure.md)
- [Phase 1 - Foundation and Current Core](phase-1/README.md)
- [Phase 2 - People, Attendance, Leave, and Holidays](phase-2/README.md)
- [Phase 3 - Recruitment and Candidate Lifecycle](phase-3/README.md)
- [Phase 4 - Company, OKRs, Meetings, and Support](phase-4/README.md)
- [Phase 5 - Import, Export, Notifications, and Integrations](phase-5/README.md)
- [Phase 6 - Hardening, Reporting, and Release Readiness](phase-6/README.md)

## Current backend baseline

The repo already has useful Phase 1 and Phase 2 foundations:

- FastAPI app setup in `app/main.py`.
- SQLAlchemy 2.x models in `app/models/hr.py`.
- Auth routes for signup, login, refresh, logout, password reset, Microsoft placeholder, and current user.
- Employee, attendance, regularization, leave, holiday, approval, audit, and admin config routes.
- Audit helpers, role checks, JWT/password security, and seed data.
- Existing organization chart routes backed by MongoDB/Motor.

The next implementation work should preserve these patterns and add new modules through SQLAlchemy models, Pydantic schemas, route modules, service functions, Alembic migrations, and focused pytest coverage.
