"""rack elevation: rack.total_u + rack_item/patch_panel/port

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

port_status = sa.Enum("free", "patched", "reserved", name="portstatus")


def upgrade() -> None:
    op.add_column("rack", sa.Column("total_u", sa.Integer, nullable=False, server_default="42"))

    op.create_table(
        "rack_item",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rack_id", sa.Integer, sa.ForeignKey("rack.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("equipment_type", sa.String(64), nullable=False),
        sa.Column("start_u", sa.Integer, nullable=False),
        sa.Column("size_u", sa.Integer, nullable=False, server_default="1"),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.CheckConstraint("start_u >= 1", name="ck_rack_item_start_u_positive"),
        sa.CheckConstraint("size_u >= 1", name="ck_rack_item_size_u_positive"),
    )

    op.create_table(
        "patch_panel",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rack_item_id", sa.Integer, sa.ForeignKey("rack_item.id"), nullable=False, unique=True),
        sa.Column("port_count", sa.Integer, nullable=False),
    )

    op.create_table(
        "port",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("patch_panel_id", sa.Integer, sa.ForeignKey("patch_panel.id"), nullable=False),
        sa.Column("port_number", sa.Integer, nullable=False),
        sa.Column("label", sa.String(128), nullable=True),
        sa.Column("status", port_status, nullable=False, server_default="free"),
        sa.UniqueConstraint("patch_panel_id", "port_number", name="uq_port_panel_number"),
    )


def downgrade() -> None:
    op.drop_table("port")
    op.drop_table("patch_panel")
    op.drop_table("rack_item")
    op.drop_column("rack", "total_u")
    port_status.drop(op.get_bind(), checkfirst=True)
