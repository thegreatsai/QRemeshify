from pydantic import BaseModel, ConfigDict

from app.models.cable_drop import DropStatus


class CableDropCreate(BaseModel):
    drop_number: str
    room_id: int | None = None
    status: DropStatus = DropStatus.DRAFT
    notes: str | None = None


class CableDropUpdate(BaseModel):
    drop_number: str | None = None
    room_id: int | None = None
    status: DropStatus | None = None
    notes: str | None = None


class DropAssign(BaseModel):
    port_id: int


class PortLocation(BaseModel):
    """Flattened Port -> PatchPanel -> RackItem -> Rack chain, so the Drop
    List view doesn't need four round trips to say where a drop lives."""

    port_id: int
    port_number: int
    patch_panel_id: int
    rack_item_name: str
    rack_id: int
    rack_number: str
    cable_drop_id: int | None = None


class CableDropRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int
    room_id: int | None
    drop_number: str
    status: DropStatus
    notes: str | None
    port_location: PortLocation | None = None
