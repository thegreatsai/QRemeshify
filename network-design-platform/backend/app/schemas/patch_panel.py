from pydantic import BaseModel, ConfigDict

from app.models.cable_drop import DropStatus
from app.models.patch_panel import PortStatus


class PatchPanelCreate(BaseModel):
    port_count: int


class PortUpdate(BaseModel):
    label: str | None = None
    status: PortStatus | None = None


class CableDropSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    drop_number: str
    status: DropStatus
    room_id: int | None


class PortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    port_number: int
    label: str | None
    status: PortStatus
    cable_drop: CableDropSummary | None = None


class PatchPanelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rack_item_id: int
    port_count: int
    ports: list[PortRead] = []
