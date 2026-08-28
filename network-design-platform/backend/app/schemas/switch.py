from pydantic import BaseModel, ConfigDict

from app.models.switch import PortMode
from app.schemas.patch_panel import CableDropSummary
from app.schemas.vlan import VlanRead


class SwitchCreate(BaseModel):
    model: str
    port_count: int
    management_ip: str | None = None


class SwitchPortUpdate(BaseModel):
    vlan_id: int | None = None
    mode: PortMode | None = None
    description: str | None = None


class SwitchPortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    port_number: int
    mode: PortMode
    description: str | None
    vlan: VlanRead | None = None
    cable_drop: CableDropSummary | None = None


class SwitchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rack_item_id: int
    model: str
    management_ip: str | None
    port_count: int
    ports: list[SwitchPortRead] = []
