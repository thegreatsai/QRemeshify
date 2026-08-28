"""cable_drop: single source of truth for a drop's port assignment

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

drop_status = sa.Enum("draft", "as_built", name="dropstatus")


def upgrade() -> None:
    op.create_table(
        "cable_drop",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("site_id", sa.Integer, sa.ForeignKey("site.id"), nullable=False),
        sa.Column("room_id", sa.Integer, sa.ForeignKey("room.id"), nullable=True),
        sa.Column("drop_number", sa.String(32), nullable=False),
        sa.Column("status", drop_status, nullable=False, server_default="draft"),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.Column("port_id", sa.Integer, sa.ForeignKey("port.id"), nullable=True, unique=True),
        sa.UniqueConstraint("site_id", "drop_number", name="uq_cable_drop_site_number"),
    )


def downgrade() -> None:
    op.drop_table("cable_drop")
    drop_status.drop(op.get_bind(), checkfirst=True)
