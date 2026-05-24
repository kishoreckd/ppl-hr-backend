from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, can_access_employee, current_user, direct_report_ids, get_profile, page, require_roles, to_dict
from app.core.security import hash_password
from app.models.hr import EmployeeProfile, RoleEnum, User
from app.schema.hr_schema import EmployeeProfileCreate, EmployeeProfileUpdate

router = APIRouter()


def employee_payload(profile: EmployeeProfile):
    data = to_dict(profile)
    data["user"] = {
        "id": profile.user.id,
        "name": profile.user.name,
        "email": profile.user.email,
        "role": profile.user.role.value,
        "is_active": profile.user.is_active,
    }
    return data


@router.get("/me")
def get_my_employee_profile(db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    return success("Employee profile fetched successfully", employee_payload(profile))


@router.get("/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_session), user: User = Depends(current_user)):
    if not can_access_employee(db, user, employee_id):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    profile = db.get(EmployeeProfile, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee not found")
    return success("Employee fetched successfully", employee_payload(profile))


@router.get("")
def list_employees(
    page_number: int = Query(1, alias="page", ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    query = select(EmployeeProfile)
    if user.role != RoleEnum.Admin:
        ids = direct_report_ids(db, user)
        query = query.where(EmployeeProfile.id.in_(ids or [0]))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.offset((page_number - 1) * page_size).limit(page_size)))
    return success("Employees fetched successfully", {"items": [employee_payload(item) for item in items], "total": total, "page": page_number, "page_size": page_size})


@router.post("", status_code=201)
def create_employee(request: EmployeeProfileCreate, db: Session = Depends(get_session), actor: User = Depends(require_roles(RoleEnum.Admin))):
    user_id = int(request.user_id) if request.user_id else None
    if not user_id:
        if db.scalar(select(User).where(User.email == request.email.lower())):
            raise HTTPException(status_code=400, detail="Email already exists")
        new_user = User(name=request.name, email=request.email.lower(), hashed_password=hash_password(request.password), role=RoleEnum(request.role.value))
        db.add(new_user)
        db.flush()
        user_id = new_user.id
    elif db.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user_id)):
        raise HTTPException(status_code=400, detail="Employee profile already exists for user")

    profile = EmployeeProfile(
        user_id=user_id,
        employee_code=request.employee_code,
        department=request.department,
        designation=request.designation,
        business_unit=request.business_unit,
        team=request.team,
        reporting_manager_id=int(request.reporting_manager_id) if request.reporting_manager_id else None,
        location=request.location,
        shift_name=request.shift_name,
        joining_date=request.joining_date,
        chart_uid=request.chart_uid,
        chart_hashid=request.chart_hashid,
        parent_hashid=request.parent_hashid,
        node_type=request.node_type,
        person=request.person,
    )
    db.add(profile)
    db.flush()
    audit(db, actor.id, "create", "EmployeeProfile", str(profile.id))
    db.commit()
    db.refresh(profile)
    return success("Employee created successfully", employee_payload(profile))


@router.patch("/{employee_id}")
def update_employee(employee_id: int, request: EmployeeProfileUpdate, db: Session = Depends(get_session), actor: User = Depends(require_roles(RoleEnum.Admin))):
    profile = db.get(EmployeeProfile, employee_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee not found")
    data = request.model_dump(exclude_unset=True)
    for key in ["name", "role", "is_active"]:
        if key in data:
            setattr(profile.user, key, RoleEnum(data[key].value) if key == "role" else data[key])
            data.pop(key)
    if "reporting_manager_id" in data and data["reporting_manager_id"] is not None:
        data["reporting_manager_id"] = int(data["reporting_manager_id"])
    for key, value in data.items():
        setattr(profile, key, value)
    audit(db, actor.id, "update", "EmployeeProfile", str(profile.id), request.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    db.refresh(profile)
    return success("Employee updated successfully", employee_payload(profile))
