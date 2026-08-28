from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.cable_drop import CableDrop
from app.models.patch_panel import PatchPanel, Port, PortStatus
from app.models.rack import Rack
from app.models.rack_item import RackItem
from app.models.site import Site
from app.schemas.cable_drop import (
    CableDropCreate,
    CableDropRead,
    CableDropUpdate,
    DropAssign,
    PortLocation,
)

router = APIRouter(tags=["cable-drops"])


def _to_read(drop: CableDrop) -> CableDropRead:
    """Builds the port_location the Drop List displays from the same Port
    row the Patch Panel view renders -- one query path, one truth."""
    location = None
    if drop.port is not None:
        rack_item = drop.port.patch_panel.rack_item
        location = PortLocation(
            port_id=drop.port.id,
            port_number=drop.port.port_number,
            patch_panel_id=drop.port.patch_panel_id,
            rack_item_name=rack_item.name,
            rack_id=rack_item.rack_id,
            rack_number=rack_item.rack.rack_number,
        )
    data = CableDropRead.model_validate(drop)
    data.port_location = location
    return data


def _query(db: Session):
    return db.query(CableDrop).options(
        joinedload(CableDrop.port)
        .joinedload(Port.patch_panel)
        .joinedload(PatchPanel.rack_item)
        .joinedload(RackItem.rack)
    )


@router.get("/sites/{site_id}/cable-drops", response_model=list[CableDropRead])
def list_cable_drops(site_id: int, db: Session = Depends(get_db)):
    drops = _query(db).filter(CableDrop.site_id == site_id).order_by(CableDrop.drop_number).all()
    return [_to_read(d) for d in drops]


@router.post("/sites/{site_id}/cable-drops", response_model=CableDropRead, status_code=201)
def create_cable_drop(site_id: int, payload: CableDropCreate, db: Session = Depends(get_db)):
    if db.get(Site, site_id) is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    if db.query(CableDrop).filter_by(site_id=site_id, drop_number=payload.drop_number).first():
        raise HTTPException(
            status_code=409, detail=f"Drop number '{payload.drop_number}' already exists at this site"
        )
    drop = CableDrop(site_id=site_id, **payload.model_dump())
    db.add(drop)
    db.commit()
    db.refresh(drop)
    return _to_read(drop)


def _get_drop_or_404(drop_id: int, db: Session) -> CableDrop:
    drop = _query(db).filter(CableDrop.id == drop_id).first()
    if drop is None:
        raise HTTPException(status_code=404, detail=f"Cable drop {drop_id} not found")
    return drop


@router.patch("/cable-drops/{drop_id}", response_model=CableDropRead)
def update_cable_drop(drop_id: int, payload: CableDropUpdate, db: Session = Depends(get_db)):
    drop = _get_drop_or_404(drop_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(drop, field, value)
    db.commit()
    db.refresh(drop)
    return _to_read(drop)


@router.delete("/cable-drops/{drop_id}", status_code=204)
def delete_cable_drop(drop_id: int, db: Session = Depends(get_db)):
    drop = _get_drop_or_404(drop_id, db)
    if drop.port is not None:
        drop.port.status = PortStatus.FREE
    db.delete(drop)
    db.commit()


@router.post("/cable-drops/{drop_id}/assign", response_model=CableDropRead)
def assign_cable_drop(drop_id: int, payload: DropAssign, db: Session = Depends(get_db)):
    """Patch this drop into a port -- and, since port_id is the only place
    a drop's location is stored, moving it from one patch panel to another
    is just this same call with a different port_id. The Drop List and the
    Patch Panel view both re-read this row, so there's no separate 'apply
    to drop list' step."""
    drop = _get_drop_or_404(drop_id, db)
    target_port = db.get(Port, payload.port_id)
    if target_port is None:
        raise HTTPException(status_code=404, detail=f"Port {payload.port_id} not found")

    occupant = db.query(CableDrop).filter(CableDrop.port_id == payload.port_id).first()
    if occupant is not None and occupant.id != drop.id:
        raise HTTPException(
            status_code=409,
            detail=f"Port {target_port.port_number} is already patched to drop '{occupant.drop_number}'",
        )

    previous_port = drop.port
    drop.port_id = target_port.id
    db.flush()
    target_port.status = PortStatus.PATCHED
    if previous_port is not None and previous_port.id != target_port.id:
        previous_port.status = PortStatus.FREE
    db.commit()
    db.refresh(drop)
    return _to_read(drop)


@router.post("/cable-drops/{drop_id}/unassign", response_model=CableDropRead)
def unassign_cable_drop(drop_id: int, db: Session = Depends(get_db)):
    drop = _get_drop_or_404(drop_id, db)
    if drop.port is not None:
        drop.port.status = PortStatus.FREE
        drop.port_id = None
    db.commit()
    db.refresh(drop)
    return _to_read(drop)


@router.get("/sites/{site_id}/ports", response_model=list[PortLocation])
def list_site_ports(site_id: int, free_only: bool = False, db: Session = Depends(get_db)):
    """Every port across every rack/patch panel at a site, for populating
    an 'assign this drop to a port' picker. Backs the Drop List UI's
    move/assign control."""
    ports = (
        db.query(Port)
        .join(Port.patch_panel)
        .join(PatchPanel.rack_item)
        .join(RackItem.rack)
        .options(
            joinedload(Port.patch_panel).joinedload(PatchPanel.rack_item).joinedload(RackItem.rack),
            joinedload(Port.cable_drop),
        )
        .filter(Rack.site_id == site_id)
        .all()
    )
    results = []
    for port in ports:
        if free_only and port.cable_drop is not None:
            continue
        rack_item = port.patch_panel.rack_item
        results.append(
            PortLocation(
                port_id=port.id,
                port_number=port.port_number,
                patch_panel_id=port.patch_panel_id,
                rack_item_name=rack_item.name,
                rack_id=rack_item.rack_id,
                rack_number=rack_item.rack.rack_number,
                cable_drop_id=port.cable_drop.id if port.cable_drop else None,
            )
        )
    return results
