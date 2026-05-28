from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, current_user, direct_report_ids, get_profile, to_dict
from app.models.hr import RegularizationRequest, RequestStatusEnum, RoleEnum, User
from app.schema.hr_schema import RegularizationRequestCreate, StatusUpdate

router = APIRouter()


@router.post("", status_code=201)
def create_regularization(request: RegularizationRequestCreate, db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    item = RegularizationRequest(employee_id=profile.id, status=RequestStatusEnum.NEW_REQUEST, **request.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "create", "RegularizationRequest", str(item.id))
    db.commit()
    return success("Regularization request submitted successfully", to_dict(item), status_code=201)


@router.get("/my")
def my_regularizations(db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    items = [] if not profile else list(db.scalars(select(RegularizationRequest).where(RegularizationRequest.employee_id == profile.id).order_by(RegularizationRequest.created_at.desc())))
    return success("Regularization requests fetched successfully", [to_dict(item) for item in items])


@router.get("/team")
def team_regularizations(db: Session = Depends(get_session), user: User = Depends(current_user)):
    if user.role == RoleEnum.Employee:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    ids = direct_report_ids(db, user)
    items = list(db.scalars(select(RegularizationRequest).where(RegularizationRequest.employee_id.in_(ids or [0])).order_by(RegularizationRequest.created_at.desc())))
    return success("Team regularization requests fetched successfully", [to_dict(item) for item in items])


@router.patch("/{request_id}/status")
def update_regularization_status(request_id: int, request: StatusUpdate, db: Session = Depends(get_session), user: User = Depends(current_user)):
    if user.role not in {RoleEnum.Manager, RoleEnum.Admin}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item = db.get(RegularizationRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Regularization request not found")
    if user.role != RoleEnum.Admin and item.employee_id not in direct_report_ids(db, user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item.status = RequestStatusEnum(request.status.value)
    item.manager_note = request.manager_note
    item.approved_by = user.id
    audit(db, user.id, "approval", "RegularizationRequest", str(item.id), request.model_dump(mode="json"))
    db.commit()
    return success("Regularization request status updated successfully", to_dict(item))
