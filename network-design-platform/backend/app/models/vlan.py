"""Replaces the tally columns on 'VLAN Counts' / the VLAN identity implied
by 'VLAN Config (9300)' and 'VLAN Config (2960)'. Scoped per-site because
the workbook is one file per site and VLAN 10 at one school has no
guaranteed relationship to VLAN 10 at another -- there's nothing in the
workbook that establishes a district-wide VLAN registry."""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vlan(Base):
    __tablename__ = "vlan"
    __table_args__ = (UniqueConstraint("site_id", "vlan_number", name="uq_vlan_site_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), nullable=False)
    vlan_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    purpose: Mapped[str] = mapped_column(String(64), nullable=True)
    notes: Mapped[str] = mapped_column(String(1024), nullable=True)

    site: Mapped["Site"] = relationship()
