from pydantic import BaseModel, ConfigDict

from app.models.site import WorkflowStage


class SiteCreate(BaseModel):
    building_code: str
    rack_id: str | None = None
    name: str
    address: str | None = None
    district: str | None = None
    workflow_stage: WorkflowStage = WorkflowStage.SURVEY


class SiteUpdate(BaseModel):
    rack_id: str | None = None
    name: str | None = None
    address: str | None = None
    district: str | None = None
    workflow_stage: WorkflowStage | None = None


class SiteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    building_code: str
    rack_id: str | None
    name: str
    address: str | None
    district: str | None
    workflow_stage: WorkflowStage
