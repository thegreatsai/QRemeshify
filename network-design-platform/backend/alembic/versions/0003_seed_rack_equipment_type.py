"""seed rack_equipment_type reference list

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-28

The old workbook never had a dropdown for "what kind of thing is mounted in
this rack slot" -- 'Rack Elevations' just had free-text merged cells, and
'Switch & Port Allocation'/'In-House Configuration' tracked switches by
model number in prose. This is a genuinely new, app-level list rather than
one lifted from a workbook column; it's editable via the reference-data API
without a code change (POST /reference-lists/rack_equipment_type/items),
so the values below are a sensible starting set, not a fixed enum.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LIST_KEY = "rack_equipment_type"
LIST_LABEL = "Rack Equipment Type"
# (value, label) -- value is the stable slug the frontend matches on
# (e.g. RackElevation.jsx checks equipment_type === "patch_panel" to decide
# whether an item gets a port grid), label is what's shown in the dropdown.
ITEMS = [
    ("patch_panel", "Patch Panel"),
    ("switch", "Switch"),
    ("router", "Router"),
    ("firewall", "Firewall"),
    ("ups", "UPS"),
    ("cable_management", "Cable Management"),
    ("shelf", "Shelf"),
    ("blank_panel", "Blank Panel"),
]

reference_list = sa.table(
    "reference_list", sa.column("id", sa.Integer), sa.column("key", sa.String), sa.column("label", sa.String)
)
reference_item = sa.table(
    "reference_item",
    sa.column("id", sa.Integer),
    sa.column("list_id", sa.Integer),
    sa.column("value", sa.String),
    sa.column("label", sa.String),
    sa.column("sort_order", sa.Integer),
)


def upgrade() -> None:
    bind = op.get_bind()
    list_id = bind.execute(
        reference_list.insert().values(key=LIST_KEY, label=LIST_LABEL).returning(reference_list.c.id)
    ).scalar_one()
    bind.execute(
        reference_item.insert(),
        [
            {"list_id": list_id, "value": value, "label": label, "sort_order": i}
            for i, (value, label) in enumerate(ITEMS)
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    list_id = bind.execute(
        sa.select(reference_list.c.id).where(reference_list.c.key == LIST_KEY)
    ).scalar_one_or_none()
    if list_id is not None:
        bind.execute(reference_item.delete().where(reference_item.c.list_id == list_id))
        bind.execute(reference_list.delete().where(reference_list.c.id == list_id))
