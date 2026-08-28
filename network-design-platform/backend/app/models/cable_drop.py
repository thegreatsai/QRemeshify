"""Replaces 'Drop List Draft' / 'Drop List As-Built' / 'Patch Panel Diagram'.

The old workbook kept these as separate sheets and used the
'TransposeValuesOnly' macro to manually copy+transpose 24-row chunks from
the drop list into the patch panel diagram whenever they needed to line up
-- a step easy to forget, and one that left two copies of the same fact
(which port a drop lands on) that could silently drift apart.

Here a drop's port assignment lives in exactly one place: CableDrop.port_id.
The "Drop List" view and the "Patch Panel" port grid both read the same
row, so moving a drop from one port (on any patch panel) to another is a
single update with nothing else to reconcile -- there is no second copy to
fall out of sync.
"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DropStatus(str, enum.Enum):
    DRAFT = "draft"
    AS_BUILT = "as_built"


class CableDrop(Base):
    __tablename__ = "cable_drop"
    __table_args__ = (UniqueConstraint("site_id", "drop_number", name="uq_cable_drop_site_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("room.id"), nullable=True)
    drop_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[DropStatus] = mapped_column(Enum(DropStatus), default=DropStatus.DRAFT, nullable=False)
    # Free text, not reference-list-backed: the real workbook's VLAN Designation
    # column draws from several different VLAN lists depending on room type
    # (instructional_vlans / service_vlans / hd_vlans / vlans_for_sgt), and
    # nothing in the workbook pins down which one governs this column, so
    # picking one would be a guess dressed up as a dropdown.
    vlan: Mapped[str] = mapped_column(String(32), nullable=True)
    voice_vlan: Mapped[str] = mapped_column(String(32), nullable=True)
    notes: Mapped[str] = mapped_column(String(1024), nullable=True)

    # The single source of truth for "which port is this drop patched
    # into" -- unique, so a port can hold at most one drop, enforced by the
    # database, not by an application-level sync routine.
    port_id: Mapped[int] = mapped_column(ForeignKey("port.id"), unique=True, nullable=True)

    site: Mapped["Site"] = relationship()
    room: Mapped["Room"] = relationship()
    port: Mapped["Port"] = relationship(back_populates="cable_drop")
