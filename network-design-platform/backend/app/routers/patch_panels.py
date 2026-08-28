from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.patch_panel import PatchPanel, Port
from app.models.rack_item import RackItem
from app.schemas.patch_panel import PatchPanelCreate, PatchPanelRead, PortRead, PortUpdate

router = APIRouter(tags=["patch-panels"])


@router.post("/racks/{rack_id}/items/{item_id}/patch-panel", response_model=PatchPanelRead, status_code=201)
def create_patch_panel(rack_id: int, item_id: int, payload: PatchPanelCreate, db: Session = Depends(get_db)):
    item = db.get(RackItem, item_id)
    if item is None or item.rack_id != rack_id:
        raise HTTPException(status_code=404, detail=f"Rack item {item_id} not found in rack {rack_id}")
    if item.patch_panel is not None:
        raise HTTPException(status_code=409, detail=f"Rack item {item_id} already has a patch panel")
    if payload.port_count < 1:
        raise HTTPException(status_code=422, detail="port_count must be >= 1")

    panel = PatchPanel(rack_item_id=item_id, port_count=payload.port_count)
    db.add(panel)
    db.flush()
    for n in range(1, payload.port_count + 1):
        db.add(Port(patch_panel_id=panel.id, port_number=n))
    db.commit()
    db.refresh(panel)
    return panel


@router.get("/patch-panels/{panel_id}", response_model=PatchPanelRead)
def get_patch_panel(panel_id: int, db: Session = Depends(get_db)):
    panel = db.get(PatchPanel, panel_id)
    if panel is None:
        raise HTTPException(status_code=404, detail=f"Patch panel {panel_id} not found")
    return panel


@router.patch("/patch-panels/{panel_id}/ports/{port_id}", response_model=PortRead)
def update_port(panel_id: int, port_id: int, payload: PortUpdate, db: Session = Depends(get_db)):
    port = db.get(Port, port_id)
    if port is None or port.patch_panel_id != panel_id:
        raise HTTPException(status_code=404, detail=f"Port {port_id} not found on patch panel {panel_id}")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(port, field, value)
    db.commit()
    db.refresh(port)
    return port
