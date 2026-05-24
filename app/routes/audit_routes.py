from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import require_roles, to_dict
from app.models.hr import AuditLog, RoleEnum, User

router = APIRouter()


@router.get("/logs")
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    user: User = Depends(require_roles(RoleEnum.Admin)),
):
    total = db.scalar(select(func.count()).select_from(AuditLog))
    items = list(db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)))
    return success("Audit logs fetched successfully", {"items": [to_dict(item) for item in items], "total": total, "page": page, "page_size": page_size})
