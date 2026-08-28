from pydantic import BaseModel, ConfigDict


class RackCreate(BaseModel):
    rack_number: str
    location: str | None = None
    notes: str | None = None
    total_u: int = 42


class RackRead(RackCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int
