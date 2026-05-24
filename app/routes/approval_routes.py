from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import current_user, direct_report_ids, to_dict
from app.models.hr import LeaveRequest, RegularizationRequest, RequestStatusEnum, RoleEnum, User

router = APIRouter()


@router.get("/pending")
def pending_approvals(db: Session = Depends(get_session), user: User = Depends(current_user)):
    if user.role == RoleEnum.Employee:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    ids = direct_report_ids(db, user)
    leave_requests = list(db.scalars(select(LeaveRequest).where(LeaveRequest.employee_id.in_(ids or [0]), LeaveRequest.status == RequestStatusEnum.NEW_REQUEST)))
    regularization_requests = list(db.scalars(select(RegularizationRequest).where(RegularizationRequest.employee_id.in_(ids or [0]), RegularizationRequest.status == RequestStatusEnum.NEW_REQUEST)))
    return success("Pending approvals fetched successfully", {"leave_requests": [to_dict(item) for item in leave_requests], "regularization_requests": [to_dict(item) for item in regularization_requests]})
