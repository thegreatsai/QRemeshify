"""Replaces the password-gated `HideForDesign`/`HideForIntegration`/... macros
with real role-based permissions instead of sheet visibility toggling."""

import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    DESIGNER = "designer"
    INTEGRATOR = "integrator"
    VALIDATOR = "validator"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.VIEWER, nullable=False)
