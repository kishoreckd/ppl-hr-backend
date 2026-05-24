from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, require_roles, to_dict
from app.models.hr import AdminConfig, RoleEnum, User

router = APIRouter()


@router.get("/config")
def list_config(db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    return success("Admin configuration fetched successfully", [to_dict(item) for item in db.scalars(select(AdminConfig).order_by(AdminConfig.key.asc()))])


@router.patch("/config/{key}")
def upsert_config(key: str, value: dict, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    item = db.scalar(select(AdminConfig).where(AdminConfig.key == key))
    if not item:
        item = AdminConfig(key=key, value=value)
        db.add(item)
        action = "create"
    else:
        item.value = value
        action = "update"
    db.flush()
    audit(db, user.id, action, "AdminConfig", str(item.id), {"key": key})
    db.commit()
    return success("Admin configuration saved successfully", to_dict(item))
