# ppl-hr Database Structure

This document is the working database blueprint for the phased `ppl-hr` backend implementation. Existing tables should be preserved unless a migration explicitly replaces them.

## Conventions

- Primary keys use integer `id` unless a table needs a public UUID.
- Foreign keys point to SQL tables, not MongoDB collections.
- Common status fields should use enums where the state machine is fixed.
- Tables with user-created or approval-sensitive data should include `created_at`, `updated_at`, and audit log entries.
- File uploads should store metadata and storage references, not raw file bytes in the database.
- Integration secrets should be stored through a secrets-safe storage layer; database rows should store references and non-sensitive metadata.

## Current Core Tables

### `team_users`

Application login account.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Internal user id |
| `name` | string | Display name |
| `email` | string unique | Lowercase login email |
| `hashed_password` | string | Password hash |
| `role` | enum | Current values: `Employee`, `Manager`, `Admin` |
| `is_active` | boolean | Login/access flag |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

### `employee_profiles`

HR profile linked one-to-one with a user.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Employee profile id |
| `user_id` | FK `team_users.id` unique | Login account |
| `employee_code` | string unique | Company employee id |
| `department` | string nullable | Department name |
| `designation` | string nullable | Job title |
| `business_unit` | string nullable | Business unit |
| `team` | string nullable | Team name |
| `reporting_manager_id` | FK `employee_profiles.id` nullable | Manager profile |
| `location` | string nullable | Work location |
| `shift_name` | string nullable | Current simple shift label |
| `joining_date` | date nullable | Employment start |
| `chart_uid` | string nullable | Existing chart bridge |
| `chart_hashid` | string nullable | Existing chart bridge |
| `parent_hashid` | string nullable | Existing chart bridge |
| `node_type` | string | `employee` or `department` |
| `person` | JSON | Extended profile payload |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

### Attendance Tables

`attendance_temp_swipes`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Temp swipe id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `attendance_date` | date | Swipe date |
| `swipe_type` | enum | `CHECK_IN`, `CHECK_OUT` |
| `swipe_time` | datetime | Actual swipe time |
| `mood` | string nullable | Optional mood |
| `source` | string nullable | Web/mobile/import/etc. |
| `created_at` | datetime | Created timestamp |

`attendance_swipes`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Permanent swipe id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `swipe_type` | enum | `CHECK_IN`, `CHECK_OUT` |
| `swipe_time` | datetime | Actual swipe time |
| `mood` | string nullable | Optional mood |
| `source` | string nullable | Web/mobile/import/etc. |
| `created_at` | datetime | Created timestamp |

`attendance_daily_summaries`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Summary id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `attendance_date` | date | Summary date |
| `first_check_in` | datetime nullable | First check-in |
| `last_check_out` | datetime nullable | Last paired check-out |
| `total_minutes` | integer | Worked minutes |
| `status` | enum | Present/half-day/absent/leave/etc. |
| `late_mark` | boolean | Late flag |
| `overtime_minutes` | integer | Minutes above policy threshold |

Constraint: unique `employee_id`, `attendance_date`.

### Request and Policy Tables

`regularization_requests`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Request id |
| `employee_id` | FK `employee_profiles.id` | Request owner |
| `request_type` | string | Missed check-in/out/etc. |
| `from_date` | date | Start date |
| `to_date` | date | End date |
| `from_time` | time nullable | Requested start time |
| `to_time` | time nullable | Requested end time |
| `emergency_contact` | string nullable | Optional contact |
| `reason` | text | Employee reason |
| `status` | enum | `NEW_REQUEST`, `APPROVED`, `REJECTED`, `ON_HOLD` |
| `manager_note` | text nullable | Approver note |
| `approved_by` | FK `team_users.id` nullable | Approver |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`leave_policies`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Policy id |
| `leave_type` | string unique | Leave type code/name |
| `annual_quota` | float | Annual entitlement |
| `cashable` | boolean | Encashment flag |
| `leave_for` | string nullable | Employee group |
| `balance_level` | string nullable | Balance granularity |
| `status` | string | Active/inactive |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`leave_requests`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Request id |
| `employee_id` | FK `employee_profiles.id` | Request owner |
| `leave_type` | string | Leave type |
| `from_date` | date | Start date |
| `to_date` | date | End date |
| `from_time` | time nullable | Partial-day start |
| `to_time` | time nullable | Partial-day end |
| `emergency_contact` | string nullable | Optional contact |
| `reason` | text | Employee reason |
| `status` | enum | Request status |
| `comp_off_worked_date` | date nullable | Comp-off source date |
| `comp_off_hours` | float nullable | Comp-off hours |
| `approved_by` | FK `team_users.id` nullable | Approver |
| `manager_note` | text nullable | Approver note |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

### Admin and Audit Tables

`holidays`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Holiday id |
| `name` | string | Holiday name |
| `date` | date | Holiday date |
| `location` | string nullable | Applicable location |
| `holiday_type` | string nullable | Public/restricted/etc. |
| `shift` | string nullable | Applicable shift |
| `created_by` | FK `team_users.id` nullable | Creator |
| `created_at` | datetime | Created timestamp |

`audit_logs`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Audit id |
| `actor_id` | FK `team_users.id` nullable | Acting user |
| `action` | string | Action key |
| `entity_type` | string | Entity/table/module |
| `entity_id` | string nullable | Entity id |
| `metadata` | JSON | Change metadata |
| `created_at` | datetime | Created timestamp |

`refresh_tokens`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Token row id |
| `user_id` | FK `team_users.id` | Owner |
| `token` | text | Refresh token |
| `revoked` | boolean | Revocation flag |
| `created_at` | datetime | Created timestamp |

`admin_configurations`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Config id |
| `key` | string unique | Config key |
| `value` | JSON | Config payload |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

## Phase 1 Additions

### `roles`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Role id |
| `name` | string unique | Role name: Employee, Manager, HR, Recruiter, Admin |
| `description` | text nullable | Role description |
| `is_system` | boolean | Prevent deletion of core roles |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

### `permissions`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Permission id |
| `key` | string unique | Example: `employees.read_all` |
| `module` | string | Module key |
| `description` | text nullable | Human-readable description |
| `created_at` | datetime | Created timestamp |

### `role_permissions`

| Column | Type | Notes |
| --- | --- | --- |
| `role_id` | FK `roles.id` | Role |
| `permission_id` | FK `permissions.id` | Permission |
| `created_at` | datetime | Created timestamp |

Primary key: `role_id`, `permission_id`.

### `user_role_overrides`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Override id |
| `user_id` | FK `team_users.id` | User |
| `permission_id` | FK `permissions.id` | Permission |
| `effect` | enum | `ALLOW`, `DENY` |
| `created_by` | FK `team_users.id` | Admin user |
| `created_at` | datetime | Created timestamp |

## Phase 2 Additions

### Employee Operations

`employee_update_requests`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Request id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `field_key` | string | Requested field |
| `old_value` | JSON nullable | Current value snapshot |
| `new_value` | JSON | Requested value |
| `status` | enum | New/approved/rejected/on hold |
| `reviewed_by` | FK `team_users.id` nullable | Reviewer |
| `review_note` | text nullable | Reviewer note |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`checklist_templates`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Template id |
| `name` | string | Template name |
| `checklist_type` | enum | `ONBOARDING`, `OFFBOARDING`, `GENERAL` |
| `department` | string nullable | Optional department scope |
| `is_active` | boolean | Active flag |
| `created_by` | FK `team_users.id` | Creator |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`checklist_template_items`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Item id |
| `template_id` | FK `checklist_templates.id` | Template |
| `title` | string | Item title |
| `description` | text nullable | Instructions |
| `default_owner_role` | string nullable | HR/manager/employee/etc. |
| `sort_order` | integer | Display order |
| `is_required` | boolean | Required flag |

`employee_checklists`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Checklist id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `template_id` | FK `checklist_templates.id` nullable | Source template |
| `checklist_type` | enum | Onboarding/offboarding/general |
| `status` | enum | Open/in progress/completed/cancelled |
| `due_date` | date nullable | Overall due date |
| `created_by` | FK `team_users.id` | Creator |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`employee_checklist_items`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Assigned item id |
| `checklist_id` | FK `employee_checklists.id` | Checklist |
| `title` | string | Item title snapshot |
| `description` | text nullable | Item description snapshot |
| `owner_id` | FK `team_users.id` nullable | Responsible user |
| `status` | enum | Pending/completed/skipped |
| `due_date` | date nullable | Item due date |
| `completed_at` | datetime nullable | Completion timestamp |
| `completed_by` | FK `team_users.id` nullable | Completing user |

`shifts`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Shift id |
| `name` | string unique | Shift name |
| `timezone` | string | IANA timezone |
| `start_time` | time | Shift start |
| `end_time` | time | Shift end |
| `break_minutes` | integer | Default break |
| `grace_minutes` | integer | Late grace |
| `weekly_off_days` | JSON | Days off |
| `is_active` | boolean | Active flag |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`shift_assignments`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Assignment id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `shift_id` | FK `shifts.id` | Shift |
| `effective_from` | date | Start date |
| `effective_to` | date nullable | End date |
| `assigned_by` | FK `team_users.id` | Assigning user |
| `created_at` | datetime | Created timestamp |

### Leave Accounting

`leave_balances`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Balance id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `leave_policy_id` | FK `leave_policies.id` | Leave type |
| `year` | integer | Balance year |
| `opening_balance` | float | Opening balance |
| `credited` | float | Total credits |
| `used` | float | Approved usage |
| `adjusted` | float | Manual/import adjustments |
| `available` | float | Current available balance |
| `updated_at` | datetime | Updated timestamp |

Constraint: unique `employee_id`, `leave_policy_id`, `year`.

`leave_transactions`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Transaction id |
| `employee_id` | FK `employee_profiles.id` | Employee |
| `leave_policy_id` | FK `leave_policies.id` | Leave type |
| `leave_request_id` | FK `leave_requests.id` nullable | Related request |
| `transaction_type` | enum | Credit/debit/adjustment/carry-forward/import |
| `quantity` | float | Days or hours |
| `balance_after` | float | Balance snapshot |
| `reason` | text nullable | Reason |
| `created_by` | FK `team_users.id` nullable | Actor/import job |
| `created_at` | datetime | Created timestamp |

`leave_approval_steps`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Step id |
| `leave_request_id` | FK `leave_requests.id` | Leave request |
| `approver_id` | FK `team_users.id` | Approver |
| `step_order` | integer | Approval order |
| `status` | enum | Pending/approved/rejected/skipped |
| `note` | text nullable | Approver note |
| `acted_at` | datetime nullable | Action timestamp |

## Phase 3 Additions

### Recruitment

`job_openings`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Opening id |
| `title` | string | Job title |
| `department` | string nullable | Department |
| `location` | string nullable | Location |
| `job_type` | string nullable | Full-time/intern/contract/etc. |
| `urgency` | enum | Low/medium/high |
| `status` | enum | Draft/open/on hold/closed |
| `headcount` | integer | Positions |
| `description` | text nullable | Job description |
| `requirements` | text nullable | Requirements |
| `hiring_manager_id` | FK `team_users.id` nullable | Hiring manager |
| `recruiter_id` | FK `team_users.id` nullable | Recruiter |
| `is_public` | boolean | Public applicant visibility |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`hire_requests`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Request id |
| `title` | string | Role title |
| `department` | string nullable | Department |
| `requested_by` | FK `team_users.id` | Requester |
| `headcount` | integer | Requested positions |
| `reason` | text | Business reason |
| `status` | enum | New/approved/rejected/on hold/converted |
| `job_opening_id` | FK `job_openings.id` nullable | Created opening |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`candidates`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Candidate id |
| `first_name` | string | First name |
| `last_name` | string nullable | Last name |
| `email` | string | Candidate email |
| `phone` | string nullable | Candidate phone |
| `current_company` | string nullable | Current employer |
| `current_role` | string nullable | Current role |
| `notice_period_days` | integer nullable | Notice period |
| `source` | enum | Referral/direct/recruiter/import/agency |
| `status` | enum | New/screening/interview/offer/hired/rejected |
| `job_opening_id` | FK `job_openings.id` nullable | Applied opening |
| `owner_id` | FK `team_users.id` nullable | Recruiter |
| `converted_employee_id` | FK `employee_profiles.id` nullable | Hired employee |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`candidate_referrals`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Referral id |
| `candidate_id` | FK `candidates.id` | Candidate |
| `referred_by` | FK `team_users.id` | Referring employee |
| `job_opening_id` | FK `job_openings.id` nullable | Opening |
| `relationship` | string nullable | Relationship note |
| `status` | enum | Submitted/accepted/rejected/hired |
| `created_at` | datetime | Created timestamp |

`interviews`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Interview id |
| `candidate_id` | FK `candidates.id` | Candidate |
| `job_opening_id` | FK `job_openings.id` nullable | Opening |
| `title` | string | Interview title |
| `scheduled_start` | datetime | Start |
| `scheduled_end` | datetime | End |
| `mode` | enum | Online/offline/phone |
| `location_or_link` | string nullable | Meeting room/link |
| `status` | enum | Scheduled/completed/cancelled/no-show |
| `created_by` | FK `team_users.id` | Scheduler |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`interview_attendees`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Attendee id |
| `interview_id` | FK `interviews.id` | Interview |
| `user_id` | FK `team_users.id` | Interviewer/participant |
| `attendee_role` | string | Interviewer/coordinator/etc. |
| `response_status` | enum | Pending/accepted/rejected/tentative |

`interview_feedback`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Feedback id |
| `interview_id` | FK `interviews.id` | Interview |
| `reviewer_id` | FK `team_users.id` | Interviewer |
| `rating` | integer nullable | Numeric score |
| `recommendation` | enum | Hire/no hire/hold/strong hire |
| `feedback` | text | Feedback text |
| `scorecard` | JSON nullable | Structured answers |
| `submitted_at` | datetime | Submission timestamp |

## Phase 4 Additions

### Company, OKR, Meetings, Support

`starred_people`

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | FK `team_users.id` | User who starred |
| `employee_id` | FK `employee_profiles.id` | Starred employee |
| `created_at` | datetime | Created timestamp |

Primary key: `user_id`, `employee_id`.

`okr_cycles`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Cycle id |
| `name` | string | Cycle name |
| `start_date` | date | Cycle start |
| `end_date` | date | Cycle end |
| `status` | enum | Draft/active/closed |
| `created_at` | datetime | Created timestamp |

`objectives`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Objective id |
| `cycle_id` | FK `okr_cycles.id` | OKR cycle |
| `owner_id` | FK `team_users.id` | Owner |
| `title` | string | Objective title |
| `description` | text nullable | Details |
| `visibility` | enum | Private/manager/team/company |
| `status` | enum | Draft/active/completed/archived |
| `progress_percent` | float | Current progress |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`key_results`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Key result id |
| `objective_id` | FK `objectives.id` | Objective |
| `title` | string | Key result |
| `target_value` | float nullable | Target |
| `current_value` | float nullable | Current |
| `unit` | string nullable | Percent/count/currency/etc. |
| `status` | enum | Not started/on track/at risk/done |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`meetings`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Meeting id |
| `title` | string | Meeting title |
| `description` | text nullable | Agenda/details |
| `organizer_id` | FK `team_users.id` | Organizer |
| `starts_at` | datetime | Start |
| `ends_at` | datetime | End |
| `location` | string nullable | Room/location |
| `provider` | string nullable | Calendar/meeting provider |
| `provider_event_id` | string nullable | External calendar id |
| `meeting_link` | string nullable | Online meeting link |
| `status` | enum | Scheduled/cancelled/completed |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`meeting_attendees`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Attendee id |
| `meeting_id` | FK `meetings.id` | Meeting |
| `user_id` | FK `team_users.id` | Attendee |
| `response_status` | enum | Pending/accepted/rejected/tentative |
| `responded_at` | datetime nullable | Response time |

`support_tickets`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Ticket id |
| `ticket_number` | string unique | Human-readable number |
| `requester_id` | FK `team_users.id` | Requester |
| `assignee_id` | FK `team_users.id` nullable | Owner |
| `category` | string | HR/IT/payroll/etc. |
| `priority` | enum | Low/medium/high/urgent |
| `status` | enum | Open/in progress/on hold/resolved/closed |
| `subject` | string | Ticket subject |
| `description` | text | Ticket body |
| `due_at` | datetime nullable | SLA due time |
| `resolved_at` | datetime nullable | Resolution time |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

`support_ticket_comments`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Comment id |
| `ticket_id` | FK `support_tickets.id` | Ticket |
| `author_id` | FK `team_users.id` | Author |
| `body` | text | Comment text |
| `is_internal` | boolean | Internal note flag |
| `created_at` | datetime | Created timestamp |

## Phase 5 Additions

### Import, Export, Notifications, Integrations

`import_jobs`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Import id |
| `module` | string | Import module |
| `file_name` | string | Original file |
| `storage_key` | string nullable | File reference |
| `status` | enum | Uploaded/validating/failed/completed |
| `total_rows` | integer | Total rows |
| `success_rows` | integer | Imported rows |
| `failed_rows` | integer | Failed rows |
| `created_by` | FK `team_users.id` | Actor |
| `created_at` | datetime | Created timestamp |
| `completed_at` | datetime nullable | Completion time |

`import_job_errors`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Error id |
| `import_job_id` | FK `import_jobs.id` | Import job |
| `row_number` | integer nullable | Source row |
| `field_name` | string nullable | Field |
| `message` | text | Validation/import error |
| `raw_data` | JSON nullable | Row snapshot |

`export_jobs`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Export id |
| `module` | string | Export module |
| `filters` | JSON | Export filters |
| `status` | enum | Queued/running/failed/completed |
| `file_name` | string nullable | Generated file |
| `storage_key` | string nullable | File reference |
| `created_by` | FK `team_users.id` | Actor |
| `created_at` | datetime | Created timestamp |
| `completed_at` | datetime nullable | Completion time |

`notification_preferences`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Preference id |
| `user_id` | FK `team_users.id` | User |
| `module` | string | Module key |
| `event_key` | string | Event key |
| `email_enabled` | boolean | Email toggle |
| `in_app_enabled` | boolean | In-app toggle |
| `updated_at` | datetime | Updated timestamp |

Constraint: unique `user_id`, `module`, `event_key`.

`notification_events`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Event id |
| `event_key` | string | Event key |
| `module` | string | Module |
| `actor_id` | FK `team_users.id` nullable | Actor |
| `recipient_id` | FK `team_users.id` nullable | Recipient |
| `entity_type` | string nullable | Entity |
| `entity_id` | string nullable | Entity id |
| `payload` | JSON | Event payload |
| `status` | enum | Queued/sent/failed/skipped |
| `created_at` | datetime | Created timestamp |

`integration_settings`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer PK | Setting id |
| `provider` | string | Google Calendar/Zoom/etc. |
| `scope` | enum | Company/user |
| `scope_id` | integer nullable | User id for user scope |
| `is_enabled` | boolean | Enabled flag |
| `secret_ref` | string nullable | Secret storage reference |
| `config` | JSON | Non-secret config |
| `created_at` | datetime | Created timestamp |
| `updated_at` | datetime | Updated timestamp |

## Indexing Priorities

- `team_users.email`
- `employee_profiles.employee_code`
- `employee_profiles.reporting_manager_id`
- `employee_profiles.department`, `designation`, `team`, `location`
- `attendance_swipes.employee_id`, `swipe_time`
- `attendance_daily_summaries.employee_id`, `attendance_date`
- `regularization_requests.employee_id`, `status`
- `leave_requests.employee_id`, `status`, `from_date`, `to_date`
- `leave_balances.employee_id`, `year`
- `holidays.date`, `location`
- `job_openings.status`, `department`, `recruiter_id`
- `candidates.email`, `phone`, `status`, `job_opening_id`
- `interviews.candidate_id`, `scheduled_start`
- `support_tickets.status`, `priority`, `assignee_id`, `requester_id`
- `import_jobs.module`, `status`
- `export_jobs.module`, `status`

## Relationship Notes

- `team_users` owns authentication; `employee_profiles` owns HR identity.
- Managers are represented by `employee_profiles.reporting_manager_id`.
- Approval flows should store both current status on the request and individual approval steps when multi-step approvals are needed.
- Leave balances must be derived from `leave_transactions`; the balance table is a cached summary.
- Recruitment candidate conversion should be transactional so user, employee, shift, checklist, and audit records are created together.
- Company tree can remain bridged to the existing chart module initially, then move to SQL tables when relational querying becomes necessary.
