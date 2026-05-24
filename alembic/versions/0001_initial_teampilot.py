"""initial teampilot schema

Revision ID: 0001_initial_teampilot
Revises: 
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_teampilot"
down_revision = None
branch_labels = None
depends_on = None

role_enum = sa.Enum("Employee", "Manager", "Admin", name="roleenum")
swipe_enum = sa.Enum("CHECK_IN", "CHECK_OUT", name="swipetypeenum")
attendance_status_enum = sa.Enum("PRESENT", "HALF_DAY", "ABSENT", "LEAVE", "HOLIDAY", "WEEKEND", "IN_PROGRESS", name="attendancestatusenum")
request_status_enum = sa.Enum("NEW_REQUEST", "APPROVED", "REJECTED", "ON_HOLD", name="requeststatusenum")


def json_type():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade():
    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    swipe_enum.create(bind, checkfirst=True)
    attendance_status_enum.create(bind, checkfirst=True)
    request_status_enum.create(bind, checkfirst=True)

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

    for table_name in ["attendance_temp_swipes", "attendance_swipes"]:
        columns = [
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False),
            sa.Column("swipe_type", swipe_enum, nullable=False),
            sa.Column("swipe_time", sa.DateTime(), nullable=False),
            sa.Column("mood", sa.String(50)),
            sa.Column("source", sa.String(50)),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        ]
        if table_name == "attendance_temp_swipes":
            columns.insert(2, sa.Column("attendance_date", sa.Date(), nullable=False))
        op.create_table(table_name, *columns)

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

    op.create_table("leave_policies", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("leave_type", sa.String(80), nullable=False, unique=True), sa.Column("annual_quota", sa.Float(), nullable=False), sa.Column("cashable", sa.Boolean(), nullable=False), sa.Column("leave_for", sa.String(80)), sa.Column("balance_level", sa.String(80)), sa.Column("status", sa.String(40), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_table("holidays", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(150), nullable=False), sa.Column("date", sa.Date(), nullable=False), sa.Column("location", sa.String(120)), sa.Column("holiday_type", sa.String(80)), sa.Column("shift", sa.String(80)), sa.Column("created_by", sa.Integer(), sa.ForeignKey("team_users.id")), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_table("audit_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("actor_id", sa.Integer(), sa.ForeignKey("team_users.id")), sa.Column("action", sa.String(80), nullable=False), sa.Column("entity_type", sa.String(80), nullable=False), sa.Column("entity_id", sa.String(80)), sa.Column("metadata", json_type()), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_table("refresh_tokens", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("team_users.id"), nullable=False), sa.Column("token", sa.Text(), nullable=False), sa.Column("revoked", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.create_table("admin_configurations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("key", sa.String(120), nullable=False, unique=True), sa.Column("value", json_type(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))

    op.create_table("leave_requests", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employee_profiles.id"), nullable=False), sa.Column("leave_type", sa.String(80), nullable=False), sa.Column("from_date", sa.Date(), nullable=False), sa.Column("to_date", sa.Date(), nullable=False), sa.Column("from_time", sa.Time()), sa.Column("to_time", sa.Time()), sa.Column("emergency_contact", sa.String(80)), sa.Column("reason", sa.Text(), nullable=False), sa.Column("status", request_status_enum, nullable=False), sa.Column("comp_off_worked_date", sa.Date()), sa.Column("comp_off_hours", sa.Float()), sa.Column("approved_by", sa.Integer(), sa.ForeignKey("team_users.id")), sa.Column("manager_note", sa.Text()), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))


def downgrade():
    for table in ["leave_requests", "admin_configurations", "refresh_tokens", "audit_logs", "holidays", "leave_policies", "regularization_requests", "attendance_daily_summaries", "attendance_swipes", "attendance_temp_swipes", "employee_profiles", "team_users"]:
        op.drop_table(table)
    bind = op.get_bind()
    request_status_enum.drop(bind, checkfirst=True)
    attendance_status_enum.drop(bind, checkfirst=True)
    swipe_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)
