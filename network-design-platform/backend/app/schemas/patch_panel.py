from pydantic import BaseModel, ConfigDict

from app.models.patch_panel import PortStatus


class PatchPanelCreate(BaseModel):
    port_count: int


class PortUpdate(BaseModel):
    label: str | None = None
    status: PortStatus | None = None


class PortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    port_number: int
    label: str | None
    status: PortStatus


class PatchPanelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rack_item_id: int
    port_count: int
    ports: list[PortRead] = []
