from collections.abc import Iterable
from datetime import date

from fastapi import Query
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session


def pagination_params(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> tuple[int, int]:
    return page, page_size


def paginate_query(db: Session, statement: Select, page: int, page_size: int):
    total = db.scalar(select(func.count()).select_from(statement.order_by(None).subquery())) or 0
    items = list(db.scalars(statement.offset((page - 1) * page_size).limit(page_size)))
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def apply_search(statement: Select, search: str | None, columns: Iterable):
    if not search:
        return statement
    term = f"%{search.strip()}%"
    return statement.where(or_(*(column.ilike(term) for column in columns)))


def apply_date_range(statement: Select, column, from_date: date | None = None, to_date: date | None = None):
    if from_date:
        statement = statement.where(column >= from_date)
    if to_date:
        statement = statement.where(column <= to_date)
    return statement
