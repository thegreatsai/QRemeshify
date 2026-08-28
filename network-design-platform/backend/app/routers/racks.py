from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rack import Rack
from app.models.site import Site
from app.schemas.rack import RackCreate, RackRead

router = APIRouter(prefix="/sites/{site_id}/racks", tags=["racks"])


@router.get("", response_model=list[RackRead])
def list_racks(site_id: int, db: Session = Depends(get_db)):
    return db.query(Rack).filter(Rack.site_id == site_id).all()


@router.post("", response_model=RackRead, status_code=201)
def create_rack(site_id: int, payload: RackCreate, db: Session = Depends(get_db)):
    if db.get(Site, site_id) is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    rack = Rack(site_id=site_id, **payload.model_dump())
    db.add(rack)
    db.commit()
    db.refresh(rack)
    return rack
