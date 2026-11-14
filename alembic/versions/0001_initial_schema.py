"""initial schema: roles, users, projects, members, tasks, comments, activity logs

Revision ID: 0001
Revises:
Create Date: 2026-11-05
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.func.now()


def upgrade() -> None:
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(30), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
        sa.Column("permissions", sa.JSON, nullable=False),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW),
    )
    op.create_index("ix_projects_name", "projects", ["name"])

    op.create_table(
        "project_members",
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=NOW),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(20), nullable=False, server_default="todo"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("due_date", sa.Date),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("assignee_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("updated_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW),
    )
    for col in ("title", "status", "priority", "due_date", "project_id", "assignee_id"):
        op.create_index(f"ix_tasks_{col}", "tasks", [col])

    op.create_table(
        "task_comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW),
    )
    op.create_index("ix_task_comments_task_id", "task_comments", ["task_id"])

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("task_id", sa.Integer, sa.ForeignKey("tasks.id", ondelete="SET NULL")),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.Integer),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("details", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW),
    )
    for col in ("user_id", "project_id", "task_id"):
        op.create_index(f"ix_activity_logs_{col}", "activity_logs", [col])

    # Seed default roles (snapshot of app/core/permissions.py at the time of this migration)
    op.bulk_insert(roles, [
        {"name": "admin", "description": "Full access to every resource", "permissions": ["*"]},
        {"name": "project_manager",
         "description": "Creates and manages projects, tasks and assignments",
         "permissions": ["user:read", "project:create", "project:read", "project:update",
                         "project:delete", "task:create", "task:read", "task:update",
                         "task:delete", "comment:create"]},
        {"name": "team_member", "description": "Works on assigned tasks",
         "permissions": ["project:read", "task:read", "task:update_status", "comment:create"]},
    ])


def downgrade() -> None:
    for table in ("activity_logs", "task_comments", "tasks", "project_members", "projects",
                  "users", "roles"):
        op.drop_table(table)
