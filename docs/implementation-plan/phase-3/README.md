# Phase 3 - Recruitment and Candidate Lifecycle

## Goal

Add recruitment workflows from workforce request through candidate conversion into an employee profile.

## Job openings

Build:

- Job opening CRUD.
- Filters by urgency, status, job type, department, location, recruiter, and hiring manager.
- Public/internal visibility flags.
- Opening details with description, requirements, interview plan, headcount, and timeline.

Suggested tables:

- `job_openings`
- `job_opening_skills`
- `job_opening_stages`

## Referrals

Build:

- Employee referral submission.
- Referral tracking by employee and opening.
- Duplicate candidate detection by email/phone.
- Referral status timeline.

Suggested table:

- `candidate_referrals`

## Hire requests

Build:

- Manager/team-head hire request submission.
- HR review and approval workflow.
- Status timeline.
- Link approved hire requests to job openings.

Suggested tables:

- `hire_requests`
- `hire_request_approval_steps`

## Candidates and direct applicants

Build:

- Candidate profile CRUD.
- Source tracking: referral, direct applicant, recruiter sourced, import, agency.
- Direct applicant intake endpoint.
- Candidate status timeline.
- Candidate documents/resume metadata.
- Candidate notes.
- Candidate-to-employee conversion that creates user account, employee profile, reporting manager assignment, shift assignment, and onboarding checklist.

Suggested tables:

- `candidates`
- `candidate_documents`
- `candidate_status_events`
- `candidate_notes`
- `direct_applications`

## Interviews and feedback

Build:

- Interview scheduling.
- Interview panel members.
- Candidate interview list.
- Interviewer-specific upcoming/conducted views.
- Feedback submission.
- Scorecard fields and recommendation.
- Meeting/calendar integration event hooks.

Suggested tables:

- `interviews`
- `interview_attendees`
- `interview_feedback`
- `interview_scorecards`

## Acceptance criteria

- Employees can browse openings and refer candidates.
- Managers can raise and track hire requests.
- HR/recruiters can manage openings, candidates, direct applicants, interviews, and feedback.
- Interviewers can view assigned interviews and submit feedback.
- Hiring a candidate creates the correct employee records and audit trail.
