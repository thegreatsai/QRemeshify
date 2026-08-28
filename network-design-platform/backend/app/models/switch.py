"""Replaces 'Switch Diagram' / 'Switch Status' / 'VLAN Config (9300)' /
'VLAN Config (2960)' / 'In-House Configuration CL & DS'.

A Switch is a RackItem specialization (equipment_type == "switch"), the
same pattern PatchPanel uses -- see app/models/patch_panel.py. Its ports
carry the actual per-port config (VLAN + mode) that the old workbook
generated as literal Cisco CLI strings by hand in cells; here that's
relational data, and the CLI text is generated on demand (see
app/services/cli_export.py) instead of being typed once and left to rot.
"""

import enum

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, str_enum


class PortMode(str, enum.Enum):
    ACCESS = "access"
    TRUNK = "trunk"


class Switch(Base):
    __tablename__ = "switch"

    id: Mapped[int] = mapped_column(primary_key=True)
    rack_item_id: Mapped[int] = mapped_column(ForeignKey("rack_item.id"), unique=True, nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    management_ip: Mapped[str] = mapped_column(String(64), nullable=True)
    port_count: Mapped[int] = mapped_column(Integer, nullable=False)

    rack_item: Mapped["RackItem"] = relationship(back_populates="switch")
    ports: Mapped[list["SwitchPort"]] = relationship(
        back_populates="switch", cascade="all, delete-orphan", order_by="SwitchPort.port_number"
    )


class SwitchPort(Base):
    __tablename__ = "switch_port"
    __table_args__ = (UniqueConstraint("switch_id", "port_number", name="uq_switch_port_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    switch_id: Mapped[int] = mapped_column(ForeignKey("switch.id"), nullable=False)
    port_number: Mapped[int] = mapped_column(Integer, nullable=False)
    vlan_id: Mapped[int] = mapped_column(ForeignKey("vlan.id"), nullable=True)
    mode: Mapped[PortMode] = mapped_column(str_enum(PortMode), default=PortMode.ACCESS, nullable=False)
    description: Mapped[str] = mapped_column(String(128), nullable=True)

    switch: Mapped["Switch"] = relationship(back_populates="ports")
    vlan: Mapped["Vlan"] = relationship()
    cable_drop: Mapped["CableDrop"] = relationship(back_populates="switch_port", uselist=False)
