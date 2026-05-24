import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.exceptions import success
from app.core.permissions import audit, current_user, require_roles, to_dict
from app.models.hr import Holiday, RoleEnum, User
from app.schema.hr_schema import HolidayCreate, HolidayUpdate

router = APIRouter()


@router.get("")
def list_holidays(db: Session = Depends(get_session), user: User = Depends(current_user)):
    return success("Holidays fetched successfully", [to_dict(item) for item in db.scalars(select(Holiday).order_by(Holiday.date.asc()))])


@router.post("", status_code=201)
def create_holiday(request: HolidayCreate, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    item = Holiday(created_by=user.id, **request.model_dump())
    db.add(item)
    db.flush()
    audit(db, user.id, "create", "Holiday", str(item.id))
    db.commit()
    return success("Holiday created successfully", to_dict(item))


@router.post("/import")
def import_holidays(file: UploadFile = File(...), db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    content = file.file.read().decode("utf-8-sig")
    reader = csv.DictReader(StringIO(content))
    required = {"date", "name", "location", "holiday_type", "shift"}
    if set(reader.fieldnames or []) < required:
        raise HTTPException(status_code=400, detail="CSV format must include date,name,location,holiday_type,shift")
    imported = 0
    failed_rows = []
    for index, row in enumerate(reader, start=2):
        try:
            parsed = HolidayCreate(**row)
            db.add(Holiday(created_by=user.id, **parsed.model_dump()))
            imported += 1
        except Exception as exc:
            failed_rows.append({"row": index, "data": row, "error": str(exc)})
    audit(db, user.id, "import", "Holiday", None, {"imported": imported, "failed": len(failed_rows)})
    db.commit()
    return success("Holiday import completed", {"imported_count": imported, "failed_rows": failed_rows})


@router.patch("/{holiday_id}")
def update_holiday(holiday_id: int, request: HolidayUpdate, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    item = db.get(Holiday, holiday_id)
    if not item:
        raise HTTPException(status_code=404, detail="Holiday not found")
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    audit(db, user.id, "update", "Holiday", str(item.id), request.model_dump(exclude_unset=True, mode="json"))
    db.commit()
    return success("Holiday updated successfully", to_dict(item))


@router.delete("/{holiday_id}")
def delete_holiday(holiday_id: int, db: Session = Depends(get_session), user: User = Depends(require_roles(RoleEnum.Admin))):
    item = db.get(Holiday, holiday_id)
    if not item:
        raise HTTPException(status_code=404, detail="Holiday not found")
    db.delete(item)
    audit(db, user.id, "delete", "Holiday", str(holiday_id))
    db.commit()
    return success("Holiday deleted successfully")
