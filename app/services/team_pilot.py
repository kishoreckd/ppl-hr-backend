from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.hr import (
    AttendanceDailySummary,
    AttendanceStatusEnum,
    AttendanceSwipe,
    EmployeeProfile,
    LeavePolicy,
    RoleEnum,
    SwipeTypeEnum,
    User,
)


def seed_team_pilot(db: Session):
    seeds = [
        ("Admin", "Admin@cxontology.com", "Admin@123", RoleEnum.Admin, "ADM001", None),
        ("Manager", "manager@cxontology.com", "Manager@123", RoleEnum.Manager, "MGR001", None),
        ("Employee", "employee@cxontology.com", "Employee@123", RoleEnum.Employee, "EMP001", "MGR001"),
    ]
    profiles = {}
    for name, email, password, role, code, _manager_code in seeds:
        user = db.scalar(select(User).where(User.email == email.lower()))
        if not user:
            user = User(name=name, email=email.lower(), hashed_password=hash_password(password), role=role, is_active=True)
            db.add(user)
            db.flush()
        profile = db.scalar(select(EmployeeProfile).where(EmployeeProfile.employee_code == code))
        if not profile:
            profile = EmployeeProfile(
                user_id=user.id,
                employee_code=code,
                department="People Operations",
                designation=role.value,
                business_unit="ppl-hr",
                team="Core HR",
                location="Chennai",
                shift_name="General",
                joining_date=date.today(),
                node_type="employee",
                person={"name": name, "email": email.lower(), "role": role.value},
            )
            db.add(profile)
            db.flush()
        profiles[code] = profile

    if profiles["EMP001"].reporting_manager_id is None:
        profiles["EMP001"].reporting_manager_id = profiles["MGR001"].id

    if db.scalar(select(LeavePolicy.id).limit(1)) is None:
        db.add_all(
            [
                LeavePolicy(leave_type="CASUAL", annual_quota=12, cashable=False, leave_for="ALL", balance_level="EMPLOYEE", status="ACTIVE"),
                LeavePolicy(leave_type="SICK", annual_quota=10, cashable=False, leave_for="ALL", balance_level="EMPLOYEE", status="ACTIVE"),
            ]
        )
    db.commit()


def recalculate_attendance_summary(db: Session, employee_id: int, attendance_date: date) -> AttendanceDailySummary:
    start = datetime.combine(attendance_date, time.min)
    end = datetime.combine(attendance_date, time.max)
    swipes = list(
        db.scalars(
            select(AttendanceSwipe)
            .where(AttendanceSwipe.employee_id == employee_id, AttendanceSwipe.swipe_time >= start, AttendanceSwipe.swipe_time <= end)
            .order_by(AttendanceSwipe.swipe_time.asc())
        )
    )
    first_check_in = next((item.swipe_time for item in swipes if item.swipe_type == SwipeTypeEnum.CHECK_IN), None)
    last_check_out = None
    open_check_in = None
    unmatched_check_in = False
    total_minutes = 0

    for swipe in swipes:
        if swipe.swipe_type == SwipeTypeEnum.CHECK_IN:
            open_check_in = swipe.swipe_time
            unmatched_check_in = True
        elif swipe.swipe_type == SwipeTypeEnum.CHECK_OUT and open_check_in:
            last_check_out = swipe.swipe_time
            total_minutes += max(0, int((swipe.swipe_time - open_check_in).total_seconds() // 60))
            open_check_in = None
            unmatched_check_in = False

    if unmatched_check_in:
        status = AttendanceStatusEnum.IN_PROGRESS
    elif total_minutes >= 480:
        status = AttendanceStatusEnum.PRESENT
    elif total_minutes >= 240:
        status = AttendanceStatusEnum.HALF_DAY
    else:
        status = AttendanceStatusEnum.ABSENT

    summary = db.scalar(
        select(AttendanceDailySummary).where(
            AttendanceDailySummary.employee_id == employee_id,
            AttendanceDailySummary.attendance_date == attendance_date,
        )
    )
    if not summary:
        summary = AttendanceDailySummary(employee_id=employee_id, attendance_date=attendance_date, status=status)
        db.add(summary)
    summary.first_check_in = first_check_in
    summary.last_check_out = last_check_out
    summary.total_minutes = total_minutes
    summary.status = status
    summary.late_mark = bool(first_check_in and first_check_in.time() > time(9, 30))
    summary.overtime_minutes = max(0, total_minutes - 540)
    db.flush()
    return summary
