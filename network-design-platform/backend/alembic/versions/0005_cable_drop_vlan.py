"""cable_drop: vlan + voice_vlan fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cable_drop", sa.Column("vlan", sa.String(32), nullable=True))
    op.add_column("cable_drop", sa.Column("voice_vlan", sa.String(32), nullable=True))


def downgrade() -> None:
    op.drop_column("cable_drop", "voice_vlan")
    op.drop_column("cable_drop", "vlan")
