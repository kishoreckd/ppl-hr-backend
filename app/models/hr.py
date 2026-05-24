import enum
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

JsonType = JSONB().with_variant(JSON(), "sqlite")


class RoleEnum(str, enum.Enum):
    Employee = "Employee"
    Manager = "Manager"
    Admin = "Admin"


class SwipeTypeEnum(str, enum.Enum):
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"


class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "PRESENT"
    HALF_DAY = "HALF_DAY"
    ABSENT = "ABSENT"
    LEAVE = "LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"
    IN_PROGRESS = "IN_PROGRESS"


class RequestStatusEnum(str, enum.Enum):
    NEW_REQUEST = "NEW_REQUEST"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"


class User(Base):
    __tablename__ = "team_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.Employee, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    employee_profile: Mapped["EmployeeProfile"] = relationship(back_populates="user", uselist=False)


class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("team_users.id"), unique=True, nullable=False)
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    department: Mapped[str | None] = mapped_column(String(120))
    designation: Mapped[str | None] = mapped_column(String(120))
    business_unit: Mapped[str | None] = mapped_column(String(120))
    team: Mapped[str | None] = mapped_column(String(120))
    reporting_manager_id: Mapped[int | None] = mapped_column(ForeignKey("employee_profiles.id"))
    location: Mapped[str | None] = mapped_column(String(120))
    shift_name: Mapped[str | None] = mapped_column(String(120))
    joining_date: Mapped[date | None] = mapped_column(Date)
    chart_uid: Mapped[str | None] = mapped_column(String(80))
    chart_hashid: Mapped[str | None] = mapped_column(String(80))
    parent_hashid: Mapped[str | None] = mapped_column(String(80))
    node_type: Mapped[str] = mapped_column(String(30), default="employee", nullable=False)
    person: Mapped[dict | None] = mapped_column(JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="employee_profile")
    reporting_manager: Mapped["EmployeeProfile"] = relationship(remote_side=[id])


class AttendanceTempSwipe(Base):
    __tablename__ = "attendance_temp_swipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profiles.id"), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    swipe_type: Mapped[SwipeTypeEnum] = mapped_column(Enum(SwipeTypeEnum), nullable=False)
    swipe_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    mood: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class AttendanceSwipe(Base):
    __tablename__ = "attendance_swipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profiles.id"), nullable=False, index=True)
    swipe_type: Mapped[SwipeTypeEnum] = mapped_column(Enum(SwipeTypeEnum), nullable=False)
    swipe_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    mood: Mapped[str | None] = mapped_column(String(50))
    source: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class AttendanceDailySummary(Base):
    __tablename__ = "attendance_daily_summaries"
    __table_args__ = (UniqueConstraint("employee_id", "attendance_date", name="uq_employee_attendance_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profiles.id"), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    first_check_in: Mapped[datetime | None] = mapped_column(DateTime)
    last_check_out: Mapped[datetime | None] = mapped_column(DateTime)
    total_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[AttendanceStatusEnum] = mapped_column(Enum(AttendanceStatusEnum), nullable=False)
    late_mark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class RegularizationRequest(Base):
    __tablename__ = "regularization_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profiles.id"), nullable=False, index=True)
    request_type: Mapped[str] = mapped_column(String(80), nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    from_time: Mapped[time | None] = mapped_column(Time)
    to_time: Mapped[time | None] = mapped_column(Time)
    emergency_contact: Mapped[str | None] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatusEnum] = mapped_column(Enum(RequestStatusEnum), default=RequestStatusEnum.NEW_REQUEST, nullable=False)
    manager_note: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("team_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class LeavePolicy(Base):
    __tablename__ = "leave_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    leave_type: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    annual_quota: Mapped[float] = mapped_column(Float, nullable=False)
    cashable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    leave_for: Mapped[str | None] = mapped_column(String(80))
    balance_level: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employee_profiles.id"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(80), nullable=False)
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    from_time: Mapped[time | None] = mapped_column(Time)
    to_time: Mapped[time | None] = mapped_column(Time)
    emergency_contact: Mapped[str | None] = mapped_column(String(80))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatusEnum] = mapped_column(Enum(RequestStatusEnum), default=RequestStatusEnum.NEW_REQUEST, nullable=False)
    comp_off_worked_date: Mapped[date | None] = mapped_column(Date)
    comp_off_hours: Mapped[float | None] = mapped_column(Float)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("team_users.id"))
    manager_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(120))
    holiday_type: Mapped[str | None] = mapped_column(String(80))
    shift: Mapped[str | None] = mapped_column(String(80))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("team_users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("team_users.id"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JsonType)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("team_users.id"), nullable=False, index=True)
    token: Mapped[str] = mapped_column(Text, nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class AdminConfig(Base):
    __tablename__ = "admin_configurations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JsonType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
