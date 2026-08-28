"""Equipment mounted in a rack -- the direct replacement for the merged-cell
blocks on the old 'Rack Elevations' sheet. `start_u`/`size_u` place it on the
rack's U-slot grid (U1 at the bottom, matching real elevation convention);
the frontend's drag-to-place UI moves an item by PATCHing `start_u`, which
the API validates against overlap with every other item in the same rack.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RackItem(Base):
    __tablename__ = "rack_item"
    __table_args__ = (
        CheckConstraint("start_u >= 1", name="ck_rack_item_start_u_positive"),
        CheckConstraint("size_u >= 1", name="ck_rack_item_size_u_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rack_id: Mapped[int] = mapped_column(ForeignKey("rack.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    equipment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    start_u: Mapped[int] = mapped_column(Integer, nullable=False)
    size_u: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    notes: Mapped[str] = mapped_column(String(1024), nullable=True)

    rack: Mapped["Rack"] = relationship(back_populates="items")
    patch_panel: Mapped["PatchPanel"] = relationship(
        back_populates="rack_item", uselist=False, cascade="all, delete-orphan"
    )
    switch: Mapped["Switch"] = relationship(
        back_populates="rack_item", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def end_u(self) -> int:
        return self.start_u + self.size_u - 1
