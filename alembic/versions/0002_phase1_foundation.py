"""phase 1 foundation tables

Revision ID: 0002_phase1_foundation
Revises: 0001_initial_ppl_hr
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_phase1_foundation"
down_revision = "0001_initial_ppl_hr"
branch_labels = None
depends_on = None

permission_effect_enum = sa.Enum("ALLOW", "DENY", name="permissioneffectenum")
notification_status_enum = sa.Enum("QUEUED", "SENT", "FAILED", "SKIPPED", name="notificationstatusenum")


def json_type():
    return postgresql.JSONB().with_variant(sa.JSON(), "sqlite")


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'HR'")
        op.execute("ALTER TYPE roleenum ADD VALUE IF NOT EXISTS 'Recruiter'")
    permission_effect_enum.create(bind, checkfirst=True)
    notification_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(120), nullable=False, unique=True),
        sa.Column("module", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_permissions_key", "permissions", ["key"])
    op.create_index("ix_permissions_module", "permissions", ["module"])

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "user_role_overrides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("team_users.id"), nullable=False),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), nullable=False),
        sa.Column("effect", permission_effect_enum, nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("team_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "permission_id", name="uq_user_permission_override"),
    )
    op.create_index("ix_user_role_overrides_user_id", "user_role_overrides", ["user_id"])
    op.create_index("ix_user_role_overrides_permission_id", "user_role_overrides", ["permission_id"])

    op.create_table(
        "notification_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_key", sa.String(120), nullable=False),
        sa.Column("module", sa.String(80), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("team_users.id")),
        sa.Column("recipient_id", sa.Integer(), sa.ForeignKey("team_users.id")),
        sa.Column("entity_type", sa.String(80)),
        sa.Column("entity_id", sa.String(80)),
        sa.Column("payload", json_type(), nullable=False),
        sa.Column("status", notification_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notification_events_event_key", "notification_events", ["event_key"])
    op.create_index("ix_notification_events_module", "notification_events", ["module"])
    op.create_index("ix_notification_events_recipient_id", "notification_events", ["recipient_id"])


def downgrade():
    op.drop_index("ix_notification_events_recipient_id", table_name="notification_events")
    op.drop_index("ix_notification_events_module", table_name="notification_events")
    op.drop_index("ix_notification_events_event_key", table_name="notification_events")
    op.drop_table("notification_events")

    op.drop_index("ix_user_role_overrides_permission_id", table_name="user_role_overrides")
    op.drop_index("ix_user_role_overrides_user_id", table_name="user_role_overrides")
    op.drop_table("user_role_overrides")

    op.drop_table("role_permissions")

    op.drop_index("ix_permissions_module", table_name="permissions")
    op.drop_index("ix_permissions_key", table_name="permissions")
    op.drop_table("permissions")

    op.drop_index("ix_roles_name", table_name="roles")
    op.drop_table("roles")

    bind = op.get_bind()
    notification_status_enum.drop(bind, checkfirst=True)
    permission_effect_enum.drop(bind, checkfirst=True)
