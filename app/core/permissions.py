from datetime import date, datetime, time

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import decode_token
from app.models.hr import AccessRole, AuditLog, EmployeeProfile, Permission, PermissionEffectEnum, RoleEnum, RolePermission, User, UserRoleOverride


PERMISSION_KEYS = {
    "admin.config.read",
    "admin.config.write",
    "admin.permissions.read",
    "audit.read",
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
    "leave.policies.write",
    "leave.requests.review",
    "holidays.read",
    "holidays.write",
    "imports.write",
    "exports.read",
    "notifications.read",
}


def to_dict(obj):
    if obj is None:
        return None
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.key)
        if isinstance(value, (datetime, date, time)):
            value = value.isoformat()
        elif hasattr(value, "value"):
            value = value.value
        data[column.key] = value
    return data


def page(items, total: int, page_number: int, page_size: int):
    return {"items": [to_dict(item) for item in items], "total": total, "page": page_number, "page_size": page_size}


def audit(db: Session, actor_id: int | None, action: str, entity_type: str, entity_id: str | None, metadata=None):
    db.add(AuditLog(actor_id=actor_id, action=action, entity_type=entity_type, entity_id=entity_id, metadata_json=metadata or {}))


def current_user(authorization: str = Header(None), db: Session = Depends(get_session)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization bearer token is required")
    try:
        payload = decode_token(authorization.removeprefix("Bearer ").strip())
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    if payload.get("token_type") not in {None, "access"}:
        raise HTTPException(status_code=401, detail="Invalid access token")
    user = db.get(User, int(payload["id"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(*roles: RoleEnum):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


def has_permission(db: Session, user: User, permission_key: str) -> bool:
    if user.role == RoleEnum.Admin:
        return True

    permission = db.scalar(select(Permission).where(Permission.key == permission_key))
    if not permission:
        return False

    override = db.scalar(
        select(UserRoleOverride).where(
            UserRoleOverride.user_id == user.id,
            UserRoleOverride.permission_id == permission.id,
        )
    )
    if override:
        return override.effect == PermissionEffectEnum.ALLOW

    role = db.scalar(select(AccessRole).where(AccessRole.name == user.role.value))
    if not role:
        return False
    return (
        db.scalar(
            select(RolePermission.permission_id).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
        )
        is not None
    )


def require_permission(permission_key: str):
    def dependency(user: User = Depends(current_user), db: Session = Depends(get_session)) -> User:
        if not has_permission(db, user, permission_key):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


def get_profile(db: Session, user_id: int) -> EmployeeProfile | None:
    return db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user_id))


def direct_report_ids(db: Session, user: User) -> list[int]:
    profile = get_profile(db, user.id)
    if user.role == RoleEnum.Admin:
        return list(db.scalars(select(EmployeeProfile.id)).all())
    if not profile:
        return []
    ids = [profile.id]
    if user.role == RoleEnum.Manager:
        ids.extend(db.scalars(select(EmployeeProfile.id).where(EmployeeProfile.reporting_manager_id == profile.id)).all())
    return ids


def can_access_employee(db: Session, user: User, employee_id: int) -> bool:
    if user.role == RoleEnum.Admin:
        return True
    profile = get_profile(db, user.id)
    if not profile:
        return False
    if profile.id == employee_id:
        return True
    if user.role == RoleEnum.Manager:
        return db.scalar(
            select(EmployeeProfile.id).where(
                EmployeeProfile.id == employee_id,
                EmployeeProfile.reporting_manager_id == profile.id,
            )
        ) is not None
    return False
