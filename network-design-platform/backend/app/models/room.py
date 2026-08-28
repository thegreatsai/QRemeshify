"""Replaces 'Room Layout' / 'Room Detail & Access Points'."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("site.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    room_type_value: Mapped[str] = mapped_column(String(128), nullable=True)
    floor: Mapped[str] = mapped_column(String(32), nullable=True)
    notes: Mapped[str] = mapped_column(String(1024), nullable=True)

    site: Mapped["Site"] = relationship(back_populates="rooms")
