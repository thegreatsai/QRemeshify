"""Generic replacement for the workbook's 'Data Lists' sheet.

Every dropdown in the old template (Cable Type, Room Type, VLAN, AP Type,
Electrical Receptacle Type, ...) was a fixed column on one sheet. Here each
becomes a `ReferenceList` (identified by `key`, e.g. "cable_type") holding
any number of `ReferenceItem` rows — new options are added with a database
row, not a spreadsheet edit distributed to every site file.
"""

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReferenceList(Base):
    __tablename__ = "reference_list"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)

    items: Mapped[list["ReferenceItem"]] = relationship(
        back_populates="list", cascade="all, delete-orphan", order_by="ReferenceItem.sort_order"
    )


class ReferenceItem(Base):
    __tablename__ = "reference_item"
    __table_args__ = (UniqueConstraint("list_id", "value", name="uq_reference_item_list_value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("reference_list.id"), nullable=False)
    value: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    list: Mapped["ReferenceList"] = relationship(back_populates="items")
