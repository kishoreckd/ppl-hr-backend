"""initial ppl-hr schema

Revision ID: 0001_initial_ppl_hr
Revises:
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_ppl_hr"
down_revision = None
branch_labels = None
depends_on = None

role_enum = sa.Enum("Employee", "Manager", "HR", "Recruiter", "Admin", name="roleenum")
swipe_enum = sa.Enum("CHECK_IN", "CHECK_OUT", name="swipetypeenum")
attendance_status_enum = sa.Enum(
    "PRESENT",
    "HALF_DAY",
    "ABSENT",
    "LEAVE",
    "HOLIDAY",
    "WEEKEND",
    "IN_PROGRESS",
    name="attendancestatusenum",
)
request_status_enum = sa.Enum(
    "NEW_REQUEST",
    "APPROVED",
    "REJECTED",
    "ON_HOLD",
    name="requeststatusenum",
)


def json_type():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def create_enums():
    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    swipe_enum.create(bind, checkfirst=True)
    attendance_status_enum.create(bind, checkfirst=True)
    request_status_enum.create(bind, checkfirst=True)


def drop_enums():
    bind = op.get_bind()
    request_status_enum.drop(bind, checkfirst=True)
    attendance_status_enum.drop(bind, checkfirst=True)
    swipe_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)


def create_users_table():
    op.create_table(
        "team_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_team_users_email", "team_users", ["email"])


def create_employee_profiles_table():
    op.create_table(
        "employee_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("team_users.id"), nullable=False, unique=True),
        sa.Column("employee_code", sa.String(50), nullable=False, unique=True),
        sa.Column("department", sa.String(120)),
        sa.Column("designation", sa.String(120)),
        sa.Column("business_unit", sa.String(120)),
        sa.Column("team", sa.String(120)),
        sa.Column("reporting_manager_id", sa.Integer(), sa.ForeignKey("employee_profiles.id")),
        sa.Column("location", sa.String(120)),
        sa.Column("shift_name", sa.String(120)),
        sa.Column("joining_date", sa.Date()),
        sa.Column("chart_uid", sa.String(80)),
        sa.Column("chart_hashid", sa.String(80)),
        sa.Column("parent_hashid", sa.String(80)),
        sa.Column("node_type", sa.String(30), nullable=False),
        sa.Column("person", json_type()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_attendance_temp_swipes_table():
    op.create_table(
        "attendance_temp_swipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("swipe_type", swipe_enum, nullable=False),
        sa.Column("swipe_time", sa.DateTime(), nullable=False),
        sa.Column("mood", sa.String(50)),
        sa.Column("source", sa.String(50)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_attendance_swipes_table():
    op.create_table(
        "attendance_swipes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False),
        sa.Column("swipe_type", swipe_enum, nullable=False),
        sa.Column("swipe_time", sa.DateTime(), nullable=False),
        sa.Column("mood", sa.String(50)),
        sa.Column("source", sa.String(50)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_attendance_daily_summaries_table():
    op.create_table(
        "attendance_daily_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("first_check_in", sa.DateTime()),
        sa.Column("last_check_out", sa.DateTime()),
        sa.Column("total_minutes", sa.Integer(), nullable=False),
        sa.Column("status", attendance_status_enum, nullable=False),
        sa.Column("late_mark", sa.Boolean(), nullable=False),
        sa.Column("overtime_minutes", sa.Integer(), nullable=False),
        sa.UniqueConstraint("employee_id", "attendance_date", name="uq_employee_attendance_date"),
    )


def create_attendance_tables():
    create_attendance_temp_swipes_table()
    create_attendance_swipes_table()
    create_attendance_daily_summaries_table()


def create_regularization_requests_table():
    op.create_table(
        "regularization_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False),
        sa.Column("request_type", sa.String(80), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("from_time", sa.Time()),
        sa.Column("to_time", sa.Time()),
        sa.Column("emergency_contact", sa.String(80)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", request_status_enum, nullable=False),
        sa.Column("manager_note", sa.Text()),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("team_users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_leave_policies_table():
    op.create_table(
        "leave_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("leave_type", sa.String(80), nullable=False, unique=True),
        sa.Column("annual_quota", sa.Float(), nullable=False),
        sa.Column("cashable", sa.Boolean(), nullable=False),
        sa.Column("leave_for", sa.String(80)),
        sa.Column("balance_level", sa.String(80)),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_leave_requests_table():
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False),
        sa.Column("leave_type", sa.String(80), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("from_time", sa.Time()),
        sa.Column("to_time", sa.Time()),
        sa.Column("emergency_contact", sa.String(80)),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", request_status_enum, nullable=False),
        sa.Column("comp_off_worked_date", sa.Date()),
        sa.Column("comp_off_hours", sa.Float()),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("team_users.id")),
        sa.Column("manager_note", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_leave_tables():
    create_leave_policies_table()
    create_leave_requests_table()


def create_holidays_table():
    op.create_table(
        "holidays",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(120)),
        sa.Column("holiday_type", sa.String(80)),
        sa.Column("shift", sa.String(80)),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("team_users.id")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_audit_logs_table():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("team_users.id")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(80)),
        sa.Column("metadata", json_type()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_refresh_tokens_table():
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("team_users.id"), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def create_admin_configurations_table():
    op.create_table(
        "admin_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(120), nullable=False, unique=True),
        sa.Column("value", json_type(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def drop_admin_configurations_table():
    op.drop_table("admin_configurations")


def drop_refresh_tokens_table():
    op.drop_table("refresh_tokens")


def drop_audit_logs_table():
    op.drop_table("audit_logs")


def drop_holidays_table():
    op.drop_table("holidays")


def drop_leave_tables():
    op.drop_table("leave_requests")
    op.drop_table("leave_policies")


def drop_regularization_requests_table():
    op.drop_table("regularization_requests")


def drop_attendance_tables():
    op.drop_table("attendance_daily_summaries")
    op.drop_table("attendance_swipes")
    op.drop_table("attendance_temp_swipes")


def drop_employee_profiles_table():
    op.drop_table("employee_profiles")


def drop_users_table():
    op.drop_index("ix_team_users_email", table_name="team_users")
    op.drop_table("team_users")


def upgrade():
    create_enums()
    create_users_table()
    create_employee_profiles_table()
    create_attendance_tables()
    create_regularization_requests_table()
    create_leave_tables()
    create_holidays_table()
    create_audit_logs_table()
    create_refresh_tokens_table()
    create_admin_configurations_table()


def downgrade():
    drop_admin_configurations_table()
    drop_refresh_tokens_table()
    drop_audit_logs_table()
    drop_holidays_table()
    drop_leave_tables()
    drop_regularization_requests_table()
    drop_attendance_tables()
    drop_employee_profiles_table()
    drop_users_table()
    drop_enums()
