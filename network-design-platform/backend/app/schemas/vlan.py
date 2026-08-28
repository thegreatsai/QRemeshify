from pydantic import BaseModel, ConfigDict


class VlanCreate(BaseModel):
    vlan_number: int
    name: str
    purpose: str | None = None
    notes: str | None = None


class VlanUpdate(BaseModel):
    name: str | None = None
    purpose: str | None = None
    notes: str | None = None


class VlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int
    vlan_number: int
    name: str
    purpose: str | None
    notes: str | None
