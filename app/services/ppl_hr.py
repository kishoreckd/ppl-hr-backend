from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.hr import (
    AccessRole,
    AttendanceDailySummary,
    AttendanceStatusEnum,
    AttendanceSwipe,
    EmployeeProfile,
    LeavePolicy,
    Permission,
    RoleEnum,
    RolePermission,
    SwipeTypeEnum,
    User,
)


ROLE_PERMISSIONS = {
    "Employee": {
        "employees.read_self",
        "attendance.read_self",
        "attendance.write_self",
        "leave.read_self",
        "leave.write_self",
        "holidays.read",
        "notifications.read",
    },
    "Manager": {
        "employees.read_self",
        "employees.read_team",
        "attendance.read_self",
        "attendance.read_team",
        "attendance.write_self",
        "attendance.regularization.review",
        "leave.read_self",
        "leave.read_team",
        "leave.write_self",
        "leave.requests.review",
        "holidays.read",
        "notifications.read",
    },
    "HR": {
        "employees.read_self",
        "employees.read_team",
        "employees.read_all",
        "employees.write",
        "attendance.read_self",
        "attendance.read_team",
        "attendance.write_self",
        "attendance.regularization.review",
        "leave.read_self",
        "leave.read_team",
        "leave.write_self",
        "leave.requests.review",
        "holidays.read",
        "holidays.write",
        "imports.write",
        "exports.read",
        "notifications.read",
    },
    "Recruiter": {
        "employees.read_self",
        "employees.read_all",
        "holidays.read",
        "imports.write",
        "exports.read",
        "notifications.read",
    },
}


PERMISSION_DESCRIPTIONS = {
    "admin.config.read": ("admin", "Read admin configuration"),
    "admin.config.write": ("admin", "Create or update admin configuration"),
    "admin.permissions.read": ("admin", "Read roles and permissions"),
    "audit.read": ("audit", "Read audit logs"),
    "employees.read_self": ("employees", "Read own employee profile"),
    "employees.read_team": ("employees", "Read direct report profiles"),
    "employees.read_all": ("employees", "Read all employee profiles"),
    "employees.write": ("employees", "Create or update employee profiles"),
    "attendance.read_self": ("attendance", "Read own attendance"),
    "attendance.read_team": ("attendance", "Read team attendance"),
    "attendance.write_self": ("attendance", "Create own attendance swipes"),
    "attendance.regularization.review": ("attendance", "Review regularization requests"),
    "leave.read_self": ("leave", "Read own leave data"),
    "leave.read_team": ("leave", "Read team leave data"),
    "leave.write_self": ("leave", "Create own leave requests"),
    "leave.policies.write": ("leave", "Create or update leave policies"),
    "leave.requests.review": ("leave", "Review leave requests"),
    "holidays.read": ("holidays", "Read holiday calendar"),
    "holidays.write": ("holidays", "Create, update, import, or delete holidays"),
    "imports.write": ("imports", "Create import jobs"),
    "exports.read": ("exports", "Create and download exports"),
    "notifications.read": ("notifications", "Read own notification events"),
}


def seed_roles_and_permissions(db: Session):
    permissions: dict[str, Permission] = {}
    for key, (module, description) in PERMISSION_DESCRIPTIONS.items():
        permission = db.scalar(select(Permission).where(Permission.key == key))
        if not permission:
            permission = Permission(key=key, module=module, description=description)
            db.add(permission)
            db.flush()
        permissions[key] = permission

    role_names = [role.value for role in RoleEnum]
    roles: dict[str, AccessRole] = {}
    for role_name in role_names:
        role = db.scalar(select(AccessRole).where(AccessRole.name == role_name))
        if not role:
            role = AccessRole(name=role_name, description=f"{role_name} role", is_system=True)
            db.add(role)
            db.flush()
        roles[role_name] = role

    admin_permissions = set(permissions)
    all_role_permissions = {**ROLE_PERMISSIONS, "Admin": admin_permissions}
    for role_name, keys in all_role_permissions.items():
        role = roles[role_name]
        for key in keys:
            existing = db.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[key].id,
                )
            )
            if not existing:
                db.add(RolePermission(role_id=role.id, permission_id=permissions[key].id))


def seed_ppl_hr(db: Session):
    seed_roles_and_permissions(db)
    seeds = [
        ("Admin", "Admin@cxontology.com", "Admin@123", RoleEnum.Admin, "ADM001", None),
        ("Manager", "manager@cxontology.com", "Manager@123", RoleEnum.Manager, "MGR001", None),
        ("Employee", "employee@cxontology.com", "Employee@123", RoleEnum.Employee, "EMP001", "MGR001"),
        ("HR", "hr@cxontology.com", "Hr@12345", RoleEnum.HR, "HR001", None),
        ("Recruiter", "recruiter@cxontology.com", "Recruiter@123", RoleEnum.Recruiter, "REC001", None),
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
