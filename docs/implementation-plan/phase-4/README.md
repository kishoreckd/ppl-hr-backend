# Phase 4 - Company, OKRs, Meetings, and Support

## Goal

Add collaboration-adjacent business modules without building dashboard widgets or social feed behavior.

## Company module

Build:

- People search by name, email, employee code, designation, department, team, and location.
- Starred people list per user.
- My team view.
- Company tree full view and branch view.
- Company tree manager for unlisted employees, manager/department assignment, node creation, move, and removal.

Suggested tables:

- `starred_people`
- `company_tree_nodes`, if the chart module is moved into SQL
- `company_tree_assignments`, if employee-tree assignments need stricter relational queries

## OKRs

Build:

- Objective CRUD.
- Key result CRUD.
- Progress updates.
- Review cycles.
- Visibility levels: private, manager, team, company.
- Owner and contributor assignments.
- Status and confidence tracking.

Suggested tables:

- `okr_cycles`
- `objectives`
- `key_results`
- `okr_progress_updates`
- `okr_contributors`

## Meetings

Build:

- Create meeting.
- Invite employees.
- Accept/reject/tentative attendee responses.
- Meeting list with date range and participant filters.
- Calendar provider sync hooks.
- Meeting provider link storage.

Suggested tables:

- `meetings`
- `meeting_attendees`
- `meeting_provider_links`

## Support tickets

Build:

- Ticket creation.
- Category, priority, status, assignee, requester, due date, and SLA fields.
- Ticket comments and internal notes.
- Attachments metadata.
- Status timeline.
- Assignment and escalation rules.

Suggested tables:

- `support_tickets`
- `support_ticket_comments`
- `support_ticket_attachments`
- `support_ticket_status_events`

## Acceptance criteria

- Users can search people, star people, and browse team/company tree data.
- HR/admin can manage company tree structure.
- Users can create and update OKRs with progress tracking.
- Users can create, find, and respond to meetings.
- Employees can raise support tickets and track status.
- HR/admin/support owners can assign, comment, resolve, and audit tickets.
