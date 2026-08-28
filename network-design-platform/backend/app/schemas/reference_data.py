from pydantic import BaseModel, ConfigDict


class ReferenceItemCreate(BaseModel):
    value: str
    label: str
    sort_order: int = 0


class ReferenceItemRead(ReferenceItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ReferenceListCreate(BaseModel):
    key: str
    label: str


class ReferenceListRead(ReferenceListCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    items: list[ReferenceItemRead] = []
