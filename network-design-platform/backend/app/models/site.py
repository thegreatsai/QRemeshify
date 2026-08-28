"""Replaces 'School Information' + 'Site CDP Summary' + the per-site .xlsm file
itself: one row per site in a shared database instead of one workbook per site
with fragile external-workbook links between them."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, str_enum


class WorkflowStage(str, enum.Enum):
    """Replaces the password-gated sheet-visibility macros
    (HideForSurvey/HideForDesign/HideForIntegration/HideForPortTrace/HideForValidation)."""

    SURVEY = "survey"
    DESIGN = "design"
    INTEGRATION = "integration"
    PORT_TRACE = "port_trace"
    VALIDATION = "validation"
    COMPLETE = "complete"


class Site(Base):
    __tablename__ = "site"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    rack_id: Mapped[str] = mapped_column(String(32), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    district: Mapped[str] = mapped_column(String(64), nullable=True)
    workflow_stage: Mapped[WorkflowStage] = mapped_column(
        str_enum(WorkflowStage), default=WorkflowStage.SURVEY, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    rooms: Mapped[list["Room"]] = relationship(back_populates="site", cascade="all, delete-orphan")
    racks: Mapped[list["Rack"]] = relationship(back_populates="site", cascade="all, delete-orphan")
