from pydantic import BaseModel, ConfigDict, field_validator


class RackItemCreate(BaseModel):
    name: str
    equipment_type: str
    start_u: int
    size_u: int = 1
    notes: str | None = None

    @field_validator("start_u")
    @classmethod
    def start_u_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("start_u must be >= 1")
        return v

    @field_validator("size_u")
    @classmethod
    def size_u_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("size_u must be >= 1")
        return v


class RackItemMove(BaseModel):
    """Used by the drag-to-place UI: only position changes, not identity."""

    start_u: int

    @field_validator("start_u")
    @classmethod
    def start_u_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("start_u must be >= 1")
        return v


class PatchPanelSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    port_count: int


class SwitchSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    model: str
    port_count: int


class RackItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rack_id: int
    name: str
    equipment_type: str
    start_u: int
    size_u: int
    notes: str | None
    patch_panel: PatchPanelSummary | None = None
    switch: SwitchSummary | None = None
