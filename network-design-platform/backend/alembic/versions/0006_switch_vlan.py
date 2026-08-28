"""switch/vlan engine: vlan, switch, switch_port + cable_drop cross-connect

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

port_mode = sa.Enum("access", "trunk", name="portmode")


def upgrade() -> None:
    op.create_table(
        "vlan",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("site_id", sa.Integer, sa.ForeignKey("site.id"), nullable=False),
        sa.Column("vlan_number", sa.Integer, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("purpose", sa.String(64), nullable=True),
        sa.Column("notes", sa.String(1024), nullable=True),
        sa.UniqueConstraint("site_id", "vlan_number", name="uq_vlan_site_number"),
    )

    op.create_table(
        "switch",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rack_item_id", sa.Integer, sa.ForeignKey("rack_item.id"), nullable=False, unique=True),
        sa.Column("model", sa.String(64), nullable=False),
        sa.Column("management_ip", sa.String(64), nullable=True),
        sa.Column("port_count", sa.Integer, nullable=False),
    )

    op.create_table(
        "switch_port",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("switch_id", sa.Integer, sa.ForeignKey("switch.id"), nullable=False),
        sa.Column("port_number", sa.Integer, nullable=False),
        sa.Column("vlan_id", sa.Integer, sa.ForeignKey("vlan.id"), nullable=True),
        sa.Column("mode", port_mode, nullable=False, server_default="access"),
        sa.Column("description", sa.String(128), nullable=True),
        sa.UniqueConstraint("switch_id", "port_number", name="uq_switch_port_number"),
    )

    # NOTE: adding a column with a FOREIGN KEY/UNIQUE constraint via plain
    # ALTER is not supported by SQLite outside of batch (copy-and-move)
    # mode, and batch mode chokes trying to name this table's pre-existing
    # unnamed constraints during reflection. This is a SQLite-only
    # limitation -- Postgres (the target in docker-compose.yml) applies
    # this in a single ALTER with no rebuild. Verify locally against
    # Postgres, or with `alembic upgrade head --sql` to render the DDL
    # without executing it.
    op.add_column(
        "cable_drop",
        sa.Column("switch_port_id", sa.Integer, sa.ForeignKey("switch_port.id"), unique=True, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cable_drop", "switch_port_id")
    op.drop_table("switch_port")
    op.drop_table("switch")
    op.drop_table("vlan")
    port_mode.drop(op.get_bind(), checkfirst=True)
