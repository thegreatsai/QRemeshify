from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.site import Site
from app.models.switch import SwitchPort
from app.models.vlan import Vlan
from app.schemas.vlan import VlanCreate, VlanRead, VlanUpdate

router = APIRouter(tags=["vlans"])


@router.get("/sites/{site_id}/vlans", response_model=list[VlanRead])
def list_vlans(site_id: int, db: Session = Depends(get_db)):
    return db.query(Vlan).filter(Vlan.site_id == site_id).order_by(Vlan.vlan_number).all()


@router.post("/sites/{site_id}/vlans", response_model=VlanRead, status_code=201)
def create_vlan(site_id: int, payload: VlanCreate, db: Session = Depends(get_db)):
    if db.get(Site, site_id) is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    if db.query(Vlan).filter_by(site_id=site_id, vlan_number=payload.vlan_number).first():
        raise HTTPException(
            status_code=409, detail=f"VLAN {payload.vlan_number} already exists at this site"
        )
    vlan = Vlan(site_id=site_id, **payload.model_dump())
    db.add(vlan)
    db.commit()
    db.refresh(vlan)
    return vlan


def _get_vlan_or_404(vlan_id: int, db: Session) -> Vlan:
    vlan = db.get(Vlan, vlan_id)
    if vlan is None:
        raise HTTPException(status_code=404, detail=f"VLAN {vlan_id} not found")
    return vlan


@router.patch("/vlans/{vlan_id}", response_model=VlanRead)
def update_vlan(vlan_id: int, payload: VlanUpdate, db: Session = Depends(get_db)):
    vlan = _get_vlan_or_404(vlan_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(vlan, field, value)
    db.commit()
    db.refresh(vlan)
    return vlan


@router.delete("/vlans/{vlan_id}", status_code=204)
def delete_vlan(vlan_id: int, db: Session = Depends(get_db)):
    vlan = _get_vlan_or_404(vlan_id, db)
    in_use = db.query(SwitchPort).filter(SwitchPort.vlan_id == vlan_id).count()
    if in_use:
        raise HTTPException(
            status_code=409,
            detail=f"VLAN {vlan.vlan_number} is assigned to {in_use} switch port(s); reassign them first",
        )
    db.delete(vlan)
    db.commit()
