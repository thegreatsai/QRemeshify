"""Replaces 'Rack Elevations'. Equipment placement lives in RackItem
(app/models/rack_item.py) -- see ROADMAP.md Phase 1."""

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
    total_u: Mapped[int] = mapped_column(Integer, default=42, nullable=False)

    site: Mapped["Site"] = relationship(back_populates="racks")
    items: Mapped[list["RackItem"]] = relationship(back_populates="rack", cascade="all, delete-orphan")
