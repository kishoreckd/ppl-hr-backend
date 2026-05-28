# Phase 2 - People, Attendance, Leave, and Holidays

## Goal

Complete the operational HR core around employees, shifts, attendance, regularization, leave, and holidays.

## Employee module

Build or complete:

- Employee list with search by name, email, employee code, role, designation, department, team, status, and location.
- Employee detail with account, profile, contact, employment, reporting, shift, and custom field sections.
- Employee self-service profile update requests.
- HR approval workflow for profile update requests.
- Onboarding/offboarding checklist templates.
- Checklist assignment per employee.
- Checklist item status tracking, due dates, owners, and completion audit.
- Shift CRUD with start/end time, break rules, grace period, weekly offs, location, and assigned employees.

Suggested tables:

- `employee_update_requests`
- `checklist_templates`
- `checklist_template_items`
- `employee_checklists`
- `employee_checklist_items`
- `shifts`
- `shift_assignments`

## Attendance module

Build or complete:

- Check-in/check-out with source, mood, IP/device metadata, and duplicate-swipe protection.
- Recent swipes API.
- Monthly calendar view.
- List view with first in, last out, total hours, break hours, excess hours, and shortfall hours.
- Team attendance view for managers.
- Online/team-present view.
- Attendance muster for HR/admin with employee/month filters.
- Attendance export job.
- Regularization request creation, team review, approve, reject, delete/cancel, and audit.

## Leave module

Build or complete:

- Leave type CRUD.
- Leave balance per employee/year.
- Leave transactions for credits, debits, adjustments, imports, and carry-forward.
- Employee leave detail by year.
- Leave application creation and status tracking.
- Comp-off application and approval.
- Regularization application under the same application surface.
- Manager/HR approval workflow with comments and audit.
- Leave conflict checks against holidays, weekly offs, overlapping leaves, and attendance records.

Suggested tables:

- `leave_balances`
- `leave_transactions`
- `leave_approval_steps`
- `comp_off_requests`, unless comp-off remains in `leave_requests`

## Holiday module

Build or complete:

- Holiday calendar by year.
- Holiday manager CRUD.
- Holiday filters by location, shift, type, and employee eligibility.
- Import holidays from a file.
- Export holiday calendar.

## Acceptance criteria

- Employees can view self profile and submit editable-field update requests.
- HR/admin can manage employees, checklists, shifts, and holidays.
- Employees can check in/out, view attendance calendar/list, apply regularization, and track status.
- Managers can review direct-report regularizations and leave requests.
- HR/admin can view/download attendance muster.
- Leave balances are transaction-backed and reproducible.
