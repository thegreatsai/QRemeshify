"""Replaces 'Patch Panel Diagram'. A PatchPanel is a RackItem specialization
(equipment_type == "patch_panel") with a fixed set of numbered Ports.
Ports are auto-created when the patch panel is created (see
app/routers/rack_items.py) -- Phase 2 wires cable drops to them, replacing
the 'TransposeValuesOnly' macro's manual 24-row copy/paste/transpose."""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PortStatus(str, enum.Enum):
    FREE = "free"
    PATCHED = "patched"
    RESERVED = "reserved"


class PatchPanel(Base):
    __tablename__ = "patch_panel"

    id: Mapped[int] = mapped_column(primary_key=True)
    rack_item_id: Mapped[int] = mapped_column(ForeignKey("rack_item.id"), unique=True, nullable=False)
    port_count: Mapped[int] = mapped_column(Integer, nullable=False)

    rack_item: Mapped["RackItem"] = relationship(back_populates="patch_panel")
    ports: Mapped[list["Port"]] = relationship(
        back_populates="patch_panel", cascade="all, delete-orphan", order_by="Port.port_number"
    )


class Port(Base):
    __tablename__ = "port"
    __table_args__ = (
        UniqueConstraint("patch_panel_id", "port_number", name="uq_port_panel_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    patch_panel_id: Mapped[int] = mapped_column(ForeignKey("patch_panel.id"), nullable=False)
    port_number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[PortStatus] = mapped_column(Enum(PortStatus), default=PortStatus.FREE, nullable=False)

    patch_panel: Mapped["PatchPanel"] = relationship(back_populates="ports")
