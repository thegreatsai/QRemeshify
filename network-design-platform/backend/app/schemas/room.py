from pydantic import BaseModel, ConfigDict


class RoomCreate(BaseModel):
    name: str
    room_type_value: str | None = None
    floor: str | None = None
    notes: str | None = None


class RoomRead(RoomCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    site_id: int
