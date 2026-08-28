from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rack_item import RackItem
from app.models.switch import Switch, SwitchPort
from app.models.vlan import Vlan
from app.schemas.switch import SwitchCreate, SwitchPortRead, SwitchPortUpdate, SwitchRead
from app.services.cli_export import DEFAULT_INTERFACE_PREFIX, SwitchPortConfig, export_switch_config

router = APIRouter(tags=["switches"])


@router.post("/racks/{rack_id}/items/{item_id}/switch", response_model=SwitchRead, status_code=201)
def create_switch(rack_id: int, item_id: int, payload: SwitchCreate, db: Session = Depends(get_db)):
    item = db.get(RackItem, item_id)
    if item is None or item.rack_id != rack_id:
        raise HTTPException(status_code=404, detail=f"Rack item {item_id} not found in rack {rack_id}")
    if item.switch is not None:
        raise HTTPException(status_code=409, detail=f"Rack item {item_id} already has a switch")
    if payload.port_count < 1:
        raise HTTPException(status_code=422, detail="port_count must be >= 1")

    switch = Switch(
        rack_item_id=item_id,
        model=payload.model,
        management_ip=payload.management_ip,
        port_count=payload.port_count,
    )
    db.add(switch)
    db.flush()
    for n in range(1, payload.port_count + 1):
        db.add(SwitchPort(switch_id=switch.id, port_number=n))
    db.commit()
    db.refresh(switch)
    return switch


@router.get("/switches/{switch_id}", response_model=SwitchRead)
def get_switch(switch_id: int, db: Session = Depends(get_db)):
    switch = db.get(Switch, switch_id)
    if switch is None:
        raise HTTPException(status_code=404, detail=f"Switch {switch_id} not found")
    return switch


@router.patch("/switches/{switch_id}/ports/{port_id}", response_model=SwitchPortRead)
def update_switch_port(switch_id: int, port_id: int, payload: SwitchPortUpdate, db: Session = Depends(get_db)):
    port = db.get(SwitchPort, port_id)
    if port is None or port.switch_id != switch_id:
        raise HTTPException(status_code=404, detail=f"Port {port_id} not found on switch {switch_id}")

    updates = payload.model_dump(exclude_unset=True)
    if "vlan_id" in updates and updates["vlan_id"] is not None:
        vlan = db.get(Vlan, updates["vlan_id"])
        if vlan is None:
            raise HTTPException(status_code=404, detail=f"VLAN {updates['vlan_id']} not found")
        switch = db.get(Switch, switch_id)
        if vlan.site_id != switch.rack_item.rack.site_id:
            raise HTTPException(status_code=422, detail="VLAN belongs to a different site")

    for field, value in updates.items():
        setattr(port, field, value)
    db.commit()
    db.refresh(port)
    return port


@router.get("/switches/{switch_id}/export")
def export_switch(switch_id: int, interface_prefix: str = DEFAULT_INTERFACE_PREFIX, db: Session = Depends(get_db)):
    """Generates the switch's port config from its live SwitchPort rows --
    Cisco IOS interface-config text for IOS-capable models, a structured
    port list (Meraki API shape) for MS-series -- instead of the old
    workbook's hand-typed CLI cells that could drift from the actual
    config the moment someone edited a cell but not the string."""
    switch = db.get(Switch, switch_id)
    if switch is None:
        raise HTTPException(status_code=404, detail=f"Switch {switch_id} not found")

    port_configs = [
        SwitchPortConfig(
            port_number=p.port_number,
            mode=p.mode.value,
            vlan_number=p.vlan.vlan_number if p.vlan else None,
            description=p.description,
        )
        for p in switch.ports
    ]
    content, content_type = export_switch_config(switch.model, port_configs, interface_prefix)
    return PlainTextResponse(content, media_type=content_type)
