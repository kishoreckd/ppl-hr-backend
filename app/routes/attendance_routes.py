from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, can_access_employee, current_user, direct_report_ids, get_profile, to_dict
from app.models.hr import AttendanceDailySummary, AttendanceStatusEnum, AttendanceSwipe, AttendanceTempSwipe, EmployeeProfile, RoleEnum, SwipeTypeEnum, User
from app.schema.hr_schema import SwipeRequest
from app.services.ppl_hr import recalculate_attendance_summary

router = APIRouter()


@router.post("/swipe", status_code=201)
def swipe(request: SwipeRequest, db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    now = datetime.utcnow()
    today = now.date()
    db.execute(delete(AttendanceTempSwipe).where(AttendanceTempSwipe.attendance_date != today))
    temp_swipe = AttendanceTempSwipe(
        employee_id=profile.id,
        attendance_date=today,
        swipe_type=SwipeTypeEnum(request.swipe_type.value),
        swipe_time=now,
        mood=request.mood,
        source=request.source,
    )
    swipe_history = AttendanceSwipe(
        employee_id=profile.id,
        swipe_type=SwipeTypeEnum(request.swipe_type.value),
        swipe_time=now,
        mood=request.mood,
        source=request.source,
    )
    db.add_all([temp_swipe, swipe_history])
    db.flush()
    summary = recalculate_attendance_summary(db, profile.id, today)
    audit(db, user.id, "create", "AttendanceSwipe", str(swipe_history.id), {"temp_swipe_id": temp_swipe.id})
    db.commit()
    return success("Attendance swipe recorded successfully", {"swipe": to_dict(swipe_history), "temp_swipe_id": temp_swipe.id, "summary": to_dict(summary)}, status_code=201)


@router.get("/today")
def today(db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    summary = recalculate_attendance_summary(db, profile.id, date.today())
    db.commit()
    return success("Today attendance fetched successfully", to_dict(summary))


@router.get("/history")
def history(
    employee_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    profile = get_profile(db, user.id)
    target_id = employee_id or (profile.id if profile else None)
    if not target_id or not can_access_employee(db, user, target_id):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    query = select(AttendanceDailySummary).where(AttendanceDailySummary.employee_id == target_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = list(db.scalars(query.order_by(AttendanceDailySummary.attendance_date.desc()).offset((page - 1) * page_size).limit(page_size)))
    return success("Attendance history fetched successfully", {"items": [to_dict(item) for item in items], "total": total, "page": page, "page_size": page_size})


@router.get("/calendar")
def calendar(month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2000), db: Session = Depends(get_session), user: User = Depends(current_user)):
    profile = get_profile(db, user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Employee profile not found")
    start = date(year, month, 1)
    end = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
    items = list(
        db.scalars(
            select(AttendanceDailySummary)
            .where(AttendanceDailySummary.employee_id == profile.id, AttendanceDailySummary.attendance_date >= start, AttendanceDailySummary.attendance_date < end)
            .order_by(AttendanceDailySummary.attendance_date.asc())
        )
    )
    return success("Attendance calendar fetched successfully", [to_dict(item) for item in items])


@router.get("/team")
def team_attendance(db: Session = Depends(get_session), user: User = Depends(current_user)):
    ids = direct_report_ids(db, user)
    if user.role == RoleEnum.Employee:
        ids = ids[:1]
    items = list(db.scalars(select(AttendanceDailySummary).where(AttendanceDailySummary.employee_id.in_(ids or [0])).order_by(AttendanceDailySummary.attendance_date.desc()).limit(100)))
    return success("Team attendance fetched successfully", [to_dict(item) for item in items])


@router.get("/team/online")
def team_online(db: Session = Depends(get_session), user: User = Depends(current_user)):
    ids = direct_report_ids(db, user)
    today_date = date.today()
    start = datetime.combine(today_date, time.min)
    end = datetime.combine(today_date, time.max)
    summaries = list(
        db.scalars(
            select(AttendanceDailySummary)
            .where(AttendanceDailySummary.employee_id.in_(ids or [0]), AttendanceDailySummary.attendance_date == today_date, AttendanceDailySummary.status == AttendanceStatusEnum.IN_PROGRESS)
        )
    )
    swipes = list(
        db.scalars(
            select(AttendanceTempSwipe)
            .where(AttendanceTempSwipe.employee_id.in_(ids or [0]), AttendanceTempSwipe.swipe_time >= start, AttendanceTempSwipe.swipe_time <= end)
            .order_by(AttendanceTempSwipe.swipe_time.desc())
        )
    )
    return success("Online team members fetched successfully", {"summaries": [to_dict(item) for item in summaries], "latest_swipes": [to_dict(item) for item in swipes]})
