from datetime import date, datetime, time
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class Role(str, Enum):
    EMPLOYEE = "Employee"
    MANAGER = "Manager"
    ADMIN = "Admin"


class SwipeType(str, Enum):
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    HALF_DAY = "HALF_DAY"
    ABSENT = "ABSENT"
    LEAVE = "LEAVE"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"
    IN_PROGRESS = "IN_PROGRESS"


class RequestStatus(str, Enum):
    NEW_REQUEST = "NEW_REQUEST"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class SignupRequest(LoginRequest):
    name: str = Field(..., min_length=1)
    role: Role = Role.EMPLOYEE


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class EmployeeProfileCreate(BaseModel):
    user_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    role: Role = Role.EMPLOYEE
    employee_code: str
    department: Optional[str] = None
    designation: Optional[str] = None
    business_unit: Optional[str] = None
    team: Optional[str] = None
    reporting_manager_id: Optional[str] = None
    location: Optional[str] = None
    shift_name: Optional[str] = None
    joining_date: Optional[date] = None
    chart_uid: Optional[str] = None
    chart_hashid: Optional[str] = None
    parent_hashid: Optional[str] = None
    node_type: Literal["employee", "department"] = "employee"
    person: Optional[dict] = None

    @model_validator(mode="after")
    def validate_user_source(self):
        if not self.user_id and not (self.name and self.email and self.password):
            raise ValueError("Provide user_id or name, email, and password")
        return self


class EmployeeProfileUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    business_unit: Optional[str] = None
    team: Optional[str] = None
    reporting_manager_id: Optional[str] = None
    location: Optional[str] = None
    shift_name: Optional[str] = None
    joining_date: Optional[date] = None
    chart_uid: Optional[str] = None
    chart_hashid: Optional[str] = None
    parent_hashid: Optional[str] = None
    node_type: Optional[Literal["employee", "department"]] = None
    person: Optional[dict] = None


class SwipeRequest(BaseModel):
    swipe_type: SwipeType
    mood: Optional[str] = None
    source: str = "web"


class DateRangeFilter(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_range(self):
        if self.from_date and self.to_date and self.to_date < self.from_date:
            raise ValueError("to_date cannot be before from_date")
        return self


class RegularizationRequestCreate(BaseModel):
    request_type: str
    from_date: date
    to_date: date
    from_time: Optional[time] = None
    to_time: Optional[time] = None
    emergency_contact: Optional[str] = None
    reason: str = Field(..., min_length=3)

    @model_validator(mode="after")
    def validate_range(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date cannot be before from_date")
        return self


class StatusUpdate(BaseModel):
    status: RequestStatus
    manager_note: Optional[str] = None

    @field_validator("status")
    @classmethod
    def status_must_be_final_or_hold(cls, value):
        if value == RequestStatus.NEW_REQUEST:
            raise ValueError("status cannot be NEW_REQUEST for approval updates")
        return value


class LeavePolicyCreate(BaseModel):
    leave_type: str
    annual_quota: float = Field(..., ge=0)
    cashable: bool = False
    leave_for: Optional[str] = None
    balance_level: Optional[str] = None
    status: str = "ACTIVE"


class LeavePolicyUpdate(BaseModel):
    annual_quota: Optional[float] = Field(None, ge=0)
    cashable: Optional[bool] = None
    leave_for: Optional[str] = None
    balance_level: Optional[str] = None
    status: Optional[str] = None


class LeaveRequestCreate(BaseModel):
    leave_type: str
    from_date: date
    to_date: date
    from_time: Optional[time] = None
    to_time: Optional[time] = None
    emergency_contact: Optional[str] = None
    reason: str = Field(..., min_length=3)
    comp_off_worked_date: Optional[date] = None
    comp_off_hours: Optional[float] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_range(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date cannot be before from_date")
        return self


class HolidayCreate(BaseModel):
    name: str
    date: date
    location: Optional[str] = None
    holiday_type: Optional[str] = None
    shift: Optional[str] = None


class HolidayUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    location: Optional[str] = None
    holiday_type: Optional[str] = None
    shift: Optional[str] = None


class Envelope(BaseModel):
    success: bool
    message: str
    data: Any = None
