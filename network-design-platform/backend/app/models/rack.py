"""Replaces 'Rack Elevations' (Phase 1 stub: full patch-panel/port model lands
in Phase 1 of the roadmap, see ROADMAP.md)."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Rack(Base):
    __tablename__ = "rack"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), nullable=False)
    rack_number: Mapped[str] = mapped_column(String(32), nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=True)
    notes: Mapped[str] = mapped_column(String(1024), nullable=True)

    site: Mapped["Site"] = relationship(back_populates="racks")
