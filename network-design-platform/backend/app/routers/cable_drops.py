from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.cable_drop import CableDrop
from app.models.patch_panel import PatchPanel, Port, PortStatus
from app.models.rack import Rack
from app.models.rack_item import RackItem
from app.models.room import Room
from app.models.site import Site
from app.models.switch import Switch, SwitchPort
from app.schemas.cable_drop import (
    BulkImportRequest,
    BulkImportResult,
    BulkImportRowResult,
    CableDropCreate,
    CableDropRead,
    CableDropUpdate,
    DropAssign,
    PortLocation,
    SwitchPortAssign,
    SwitchPortLocation,
)

router = APIRouter(tags=["cable-drops"])


def _to_read(drop: CableDrop) -> CableDropRead:
    """Builds port_location/switch_port_location the Drop List displays
    from the same Port/SwitchPort rows the Patch Panel and Switch views
    render -- one query path, one truth, for both hops of the physical
    chain (jack -> patch panel port -> switch port)."""
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

    switch_location = None
    if drop.switch_port is not None:
        sp = drop.switch_port
        rack_item = sp.switch.rack_item
        switch_location = SwitchPortLocation(
            switch_port_id=sp.id,
            port_number=sp.port_number,
            switch_id=sp.switch_id,
            switch_model=sp.switch.model,
            rack_item_name=rack_item.name,
            rack_id=rack_item.rack_id,
            rack_number=rack_item.rack.rack_number,
            vlan_number=sp.vlan.vlan_number if sp.vlan else None,
        )

    data = CableDropRead.model_validate(drop)
    data.port_location = location
    data.switch_port_location = switch_location
    return data


def _query(db: Session):
    return db.query(CableDrop).options(
        joinedload(CableDrop.port)
        .joinedload(Port.patch_panel)
        .joinedload(PatchPanel.rack_item)
        .joinedload(RackItem.rack),
        joinedload(CableDrop.switch_port)
        .joinedload(SwitchPort.switch)
        .joinedload(Switch.rack_item)
        .joinedload(RackItem.rack),
        joinedload(CableDrop.switch_port).joinedload(SwitchPort.vlan),
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


@router.post("/sites/{site_id}/cable-drops/bulk", response_model=BulkImportResult)
def bulk_import_cable_drops(site_id: int, payload: BulkImportRequest, db: Session = Depends(get_db)):
    """Upsert-by-drop_number, so re-importing a revised drop list (a new
    export from the field survey, say) updates existing rows instead of
    failing on the duplicate drop numbers. Room is resolved by name against
    this site's existing rooms; a name that doesn't match is reported as an
    error for that row rather than silently creating a new room or leaving
    it ambiguous which room was meant."""
    if db.get(Site, site_id) is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")

    rooms_by_name = {r.name: r.id for r in db.query(Room).filter(Room.site_id == site_id).all()}
    existing_by_number = {
        d.drop_number: d for d in db.query(CableDrop).filter(CableDrop.site_id == site_id).all()
    }

    results: list[BulkImportRowResult] = []
    created = updated = errors = 0

    for row in payload.rows:
        try:
            room_id = None
            if row.room_name:
                room_id = rooms_by_name.get(row.room_name)
                if room_id is None:
                    raise ValueError(f"Room '{row.room_name}' not found at this site")

            existing = existing_by_number.get(row.drop_number)
            if existing is not None:
                existing.room_id = room_id
                existing.status = row.status
                existing.vlan = row.vlan
                existing.voice_vlan = row.voice_vlan
                existing.notes = row.notes
                results.append(BulkImportRowResult(drop_number=row.drop_number, action="updated"))
                updated += 1
            else:
                new_drop = CableDrop(
                    site_id=site_id,
                    drop_number=row.drop_number,
                    room_id=room_id,
                    status=row.status,
                    vlan=row.vlan,
                    voice_vlan=row.voice_vlan,
                    notes=row.notes,
                )
                db.add(new_drop)
                existing_by_number[row.drop_number] = new_drop
                results.append(BulkImportRowResult(drop_number=row.drop_number, action="created"))
                created += 1
        except ValueError as exc:
            results.append(
                BulkImportRowResult(drop_number=row.drop_number, action="error", detail=str(exc))
            )
            errors += 1

    db.commit()
    return BulkImportResult(results=results, created=created, updated=updated, errors=errors)


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


@router.post("/cable-drops/{drop_id}/assign-switch-port", response_model=CableDropRead)
def assign_switch_port(drop_id: int, payload: SwitchPortAssign, db: Session = Depends(get_db)):
    """Cross-connect this drop to a switch port -- the same
    single-source-of-truth pattern as /assign, one hop further down the
    physical chain. Independent of the patch-panel port assignment: a drop
    can be terminated at a patch panel without yet being cross-connected."""
    drop = _get_drop_or_404(drop_id, db)
    target = db.get(SwitchPort, payload.switch_port_id)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Switch port {payload.switch_port_id} not found")

    occupant = db.query(CableDrop).filter(CableDrop.switch_port_id == payload.switch_port_id).first()
    if occupant is not None and occupant.id != drop.id:
        raise HTTPException(
            status_code=409,
            detail=f"Switch port {target.port_number} is already cross-connected to drop "
            f"'{occupant.drop_number}'",
        )

    drop.switch_port_id = target.id
    db.commit()
    db.refresh(drop)
    return _to_read(drop)


@router.post("/cable-drops/{drop_id}/unassign-switch-port", response_model=CableDropRead)
def unassign_switch_port(drop_id: int, db: Session = Depends(get_db)):
    drop = _get_drop_or_404(drop_id, db)
    drop.switch_port_id = None
    db.commit()
    db.refresh(drop)
    return _to_read(drop)


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


@router.get("/sites/{site_id}/switch-ports", response_model=list[SwitchPortLocation])
def list_site_switch_ports(site_id: int, free_only: bool = False, db: Session = Depends(get_db)):
    """Every switch port across every switch at a site, for populating a
    'cross-connect this drop to a switch port' picker."""
    ports = (
        db.query(SwitchPort)
        .join(SwitchPort.switch)
        .join(Switch.rack_item)
        .join(RackItem.rack)
        .options(
            joinedload(SwitchPort.switch).joinedload(Switch.rack_item).joinedload(RackItem.rack),
            joinedload(SwitchPort.vlan),
            joinedload(SwitchPort.cable_drop),
        )
        .filter(Rack.site_id == site_id)
        .all()
    )
    results = []
    for port in ports:
        if free_only and port.cable_drop is not None:
            continue
        rack_item = port.switch.rack_item
        results.append(
            SwitchPortLocation(
                switch_port_id=port.id,
                port_number=port.port_number,
                switch_id=port.switch_id,
                switch_model=port.switch.model,
                rack_item_name=rack_item.name,
                rack_id=rack_item.rack_id,
                rack_number=rack_item.rack.rack_number,
                vlan_number=port.vlan.vlan_number if port.vlan else None,
                cable_drop_id=port.cable_drop.id if port.cable_drop else None,
            )
        )
    return results
