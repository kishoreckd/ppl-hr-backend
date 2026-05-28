import os
from datetime import date, datetime
from pathlib import Path

os.environ.setdefault("BEARER_TOKEN", "test-bearer")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DOMAIN_URL", "http://testserver")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test")
os.environ["DATABASE_URL"] = "sqlite:///./test_ppl_hr.db"
os.environ["POSTGRES_URI"] = ""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.main import app
from app.core.notifications import queue_notification
from app.core.permissions import has_permission
from app.models.hr import AccessRole, AttendanceDailySummary, AttendanceSwipe, EmployeeProfile, NotificationEvent, Permission, SwipeTypeEnum, User
from app.services.ppl_hr import recalculate_attendance_summary


def setup_module():
    db_path = Path("test_ppl_hr.db")
    if db_path.exists():
        db_path.unlink()
    Base.metadata.create_all(bind=engine)
    with TestClient(app):
        pass


client = TestClient(app)


def login(email: str, password: str):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


def headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_login_and_protected_route_token_validation():
    token = login("employee@cxontology.com", "Employee@123")
    assert client.get("/auth/me", headers=headers(token)).status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_rbac_access_denial_for_employee_policy_creation():
    token = login("employee@cxontology.com", "Employee@123")
    response = client.post(
        "/leave/policies",
        headers=headers(token),
        json={"leave_type": "TEST_DENIED", "annual_quota": 1, "cashable": False},
    )
    assert response.status_code == 403


def test_employee_swipe_in_out_and_attendance_calculation():
    token = login("employee@cxontology.com", "Employee@123")
    assert client.post("/attendance/swipe", headers=headers(token), json={"swipe_type": "CHECK_IN"}).status_code == 201
    assert client.post("/attendance/swipe", headers=headers(token), json={"swipe_type": "CHECK_OUT"}).status_code == 201
    response = client.get("/attendance/today", headers=headers(token))
    assert response.status_code == 200
    assert response.json()["data"]["status"] in {"ABSENT", "HALF_DAY", "PRESENT", "IN_PROGRESS"}


def test_attendance_summary_policy_calculation():
    db = SessionLocal()
    try:
        employee = db.scalar(select(EmployeeProfile).where(EmployeeProfile.employee_code == "EMP001"))
        db.query(AttendanceSwipe).filter(AttendanceSwipe.employee_id == employee.id).delete()
        db.add_all(
            [
                AttendanceSwipe(employee_id=employee.id, swipe_type=SwipeTypeEnum.CHECK_IN, swipe_time=datetime(2026, 5, 24, 9, 45), source="test"),
                AttendanceSwipe(employee_id=employee.id, swipe_type=SwipeTypeEnum.CHECK_OUT, swipe_time=datetime(2026, 5, 24, 18, 50), source="test"),
            ]
        )
        db.flush()
        summary = recalculate_attendance_summary(db, employee.id, date(2026, 5, 24))
        assert summary.status.value == "PRESENT"
        assert summary.late_mark is True
        assert summary.overtime_minutes == 5
    finally:
        db.rollback()
        db.close()


def test_leave_request_creation_and_manager_approval():
    employee_token = login("employee@cxontology.com", "Employee@123")
    manager_token = login("manager@cxontology.com", "Manager@123")
    response = client.post(
        "/leave/requests",
        headers=headers(employee_token),
        json={"leave_type": "CASUAL", "from_date": "2026-06-01", "to_date": "2026-06-01", "reason": "personal work"},
    )
    assert response.status_code == 201, response.text
    request_id = response.json()["data"]["id"]
    approval = client.patch(
        f"/leave/requests/{request_id}/status",
        headers=headers(manager_token),
        json={"status": "APPROVED", "manager_note": "approved"},
    )
    assert approval.status_code == 200, approval.text
    assert approval.json()["data"]["status"] == "APPROVED"


def test_admin_leave_policy_creation_and_holiday_import():
    admin_token = login("Admin@cxontology.com", "Admin@123")
    policy = client.post(
        "/leave/policies",
        headers=headers(admin_token),
        json={"leave_type": "WELLNESS", "annual_quota": 2, "cashable": False, "leave_for": "ALL", "balance_level": "EMPLOYEE"},
    )
    assert policy.status_code in {201, 400}
    csv_data = "date,name,location,holiday_type,shift\n2026-01-01,New Year,All,Public,General\nbad-date,Bad Row,All,Public,General\n"
    response = client.post("/holidays/import", headers=headers(admin_token), files={"file": ("holidays.csv", csv_data, "text/csv")})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["imported_count"] == 1
    assert len(response.json()["data"]["failed_rows"]) == 1


def test_phase1_roles_permissions_are_seeded_and_exposed():
    admin_token = login("Admin@cxontology.com", "Admin@123")
    response = client.get("/admin/roles", headers=headers(admin_token))
    assert response.status_code == 200, response.text
    role_names = {role["name"] for role in response.json()["data"]}
    assert {"Employee", "Manager", "HR", "Recruiter", "Admin"}.issubset(role_names)

    permissions = client.get("/admin/permissions", headers=headers(admin_token))
    assert permissions.status_code == 200, permissions.text
    permission_keys = {item["key"] for item in permissions.json()["data"]}
    assert {"admin.permissions.read", "employees.read_all", "notifications.read"}.issubset(permission_keys)


def test_phase1_permission_helper_and_notification_queue():
    db = SessionLocal()
    try:
        employee = db.scalar(select(User).where(User.email == "employee@cxontology.com"))
        admin = db.scalar(select(User).where(User.email == "admin@cxontology.com"))
        assert db.scalar(select(AccessRole).where(AccessRole.name == "HR")) is not None
        assert db.scalar(select(Permission).where(Permission.key == "employees.read_all")) is not None
        assert has_permission(db, employee, "employees.read_self") is True
        assert has_permission(db, employee, "employees.write") is False
        assert has_permission(db, admin, "employees.write") is True

        event = queue_notification(
            db,
            event_key="phase1.test",
            module="tests",
            actor_id=admin.id,
            recipient_id=employee.id,
            entity_type="User",
            entity_id=str(employee.id),
            payload={"ok": True},
        )
        db.commit()
        stored = db.get(NotificationEvent, event.id)
        assert stored.status.value == "QUEUED"
        assert stored.payload == {"ok": True}
    finally:
        db.close()
