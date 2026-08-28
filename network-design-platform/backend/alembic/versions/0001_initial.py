"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

workflow_stage = sa.Enum(
    "survey", "design", "integration", "port_trace", "validation", "complete", name="workflowstage"
)
role = sa.Enum("admin", "designer", "integrator", "validator", "viewer", name="role")


def upgrade() -> None:
    op.create_table(
        "reference_list",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("key", sa.String(64), nullable=False, unique=True),
        sa.Column("label", sa.String(128), nullable=False),
    )

    op.create_table(
        "reference_item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("list_id", sa.Integer, sa.ForeignKey("reference_list.id"), nullable=False),
        sa.Column("value", sa.String(128), nullable=False),
        sa.Column("label", sa.String(128), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("list_id", "value", name="uq_reference_item_list_value"),
    )

    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", role, nullable=False, server_default="viewer"),
    )

    op.create_table(
        "site",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("building_code", sa.String(32), nullable=False, unique=True),
        sa.Column("rack_id", sa.String(32), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("district", sa.String(64), nullable=True),
        sa.Column("workflow_stage", workflow_stage, nullable=False, server_default="survey"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "room",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("site_id", sa.Integer, sa.ForeignKey("site.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("room_type_value", sa.String(128), nullable=True),
        sa.Column("floor", sa.String(32), nullable=True),
        sa.Column("notes", sa.String(1024), nullable=True),
    )

    op.create_table(
        "rack",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("site_id", sa.Integer, sa.ForeignKey("site.id"), nullable=False),
        sa.Column("rack_number", sa.String(32), nullable=False),
        sa.Column("location", sa.String(128), nullable=True),
        sa.Column("notes", sa.String(1024), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("rack")
    op.drop_table("room")
    op.drop_table("site")
    op.drop_table("app_user")
    op.drop_table("reference_item")
    op.drop_table("reference_list")
    workflow_stage.drop(op.get_bind(), checkfirst=True)
    role.drop(op.get_bind(), checkfirst=True)
