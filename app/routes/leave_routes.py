from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, current_user, direct_report_ids, get_profile, require_roles, to_dict
from app.models.hr import LeavePolicy, LeaveRequest, RequestStatusEnum, RoleEnum, User
from app.schema.hr_schema import LeavePolicyCreate, LeavePolicyUpdate, LeaveRequestCreate, StatusUpdate

router = APIRouter()


@router.get("/balance")
def leave_balance(db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    policies = list(db.scalars(select(LeavePolicy).where(LeavePolicy.status != "INACTIVE")))
    approved = list(db.scalars(select(LeaveRequest).where(LeaveRequest.employee_id == profile.id, LeaveRequest.status == RequestStatusEnum.APPROVED)))
    used = {}
    for item in approved:
        used[item.leave_type] = used.get(item.leave_type, 0) + ((item.to_date - item.from_date).days + 1)
    return success("Leave balance fetched successfully", [{"leave_type": p.leave_type, "annual_quota": p.annual_quota, "used": used.get(p.leave_type, 0), "balance": p.annual_quota - used.get(p.leave_type, 0)} for p in policies])


@router.post("/requests", status_code=201)
def create_leave_request(request: LeaveRequestCreate, db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    item = LeaveRequest(employee_id=profile.id, status=RequestStatusEnum.NEW_REQUEST, **request.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "create", "LeaveRequest", str(item.id))
    db.commit()
    return success("Leave request submitted successfully", to_dict(item), status_code=201)


@router.get("/requests/my")
def my_leave_requests(db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    items = [] if not profile else list(db.scalars(select(LeaveRequest).where(LeaveRequest.employee_id == profile.id).order_by(LeaveRequest.created_at.desc())))
    return success("Leave requests fetched successfully", [to_dict(item) for item in items])


@router.get("/requests/team")
def team_leave_requests(db: Session = Depends(get_session), user: User = Depends(current_user)):
    if user.role == RoleEnum.Employee:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    ids = direct_report_ids(db, user)
    items = list(db.scalars(select(LeaveRequest).where(LeaveRequest.employee_id.in_(ids or [0])).order_by(LeaveRequest.created_at.desc())))
    return success("Team leave requests fetched successfully", [to_dict(item) for item in items])


@router.patch("/requests/{request_id}/status")
def update_leave_status(request_id: int, request: StatusUpdate, db: Session = Depends(get_session), user: User = Depends(current_user)):
    if user.role not in {RoleEnum.Manager, RoleEnum.Admin}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item = db.get(LeaveRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if user.role != RoleEnum.Admin and item.employee_id not in direct_report_ids(db, user):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    item.status = RequestStatusEnum(request.status.value)
    item.manager_note = request.manager_note
    item.approved_by = user.id
    audit(db, user.id, "approval", "LeaveRequest", str(item.id), request.model_dump(mode="json"))
    db.commit()
    return success("Leave request status updated successfully", to_dict(item))


@router.get("/policies")
def list_policies(db: Session = Depends(get_session), user: User = Depends(current_user)):
    return success("Leave policies fetched successfully", [to_dict(item) for item in db.scalars(select(LeavePolicy).order_by(LeavePolicy.leave_type.asc()))])


@router.post("/policies", status_code=201)
def create_policy(request: LeavePolicyCreate, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    if db.scalar(select(LeavePolicy).where(LeavePolicy.leave_type == request.leave_type)):
        raise HTTPException(status_code=400, detail="Leave policy already exists")
    item = LeavePolicy(**request.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "create", "LeavePolicy", str(item.id))
    db.commit()
    return success("Leave policy created successfully", to_dict(item), status_code=201)


@router.patch("/policies/{policy_id}")
def update_policy(policy_id: int, request: LeavePolicyUpdate, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    item = db.get(LeavePolicy, policy_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave policy not found")
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    audit(db, user.id, "update", "LeavePolicy", str(item.id), request.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    return success("Leave policy updated successfully", to_dict(item))


@router.delete("/policies/{policy_id}")
def delete_policy(policy_id: int, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    item = db.get(LeavePolicy, policy_id)
    if not item:
        raise HTTPException(status_code=404, detail="Leave policy not found")
    db.delete(item)
    audit(db, user.id, "delete", "LeavePolicy", str(policy_id))
    db.commit()
    return success("Leave policy deleted successfully")
