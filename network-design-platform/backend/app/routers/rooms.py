from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room import Room
from app.models.site import Site
from app.schemas.room import RoomCreate, RoomRead

router = APIRouter(prefix="/sites/{site_id}/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
def list_rooms(site_id: int, db: Session = Depends(get_db)):
    return db.query(Room).filter(Room.site_id == site_id).all()


@router.post("", response_model=RoomRead, status_code=201)
def create_room(site_id: int, payload: RoomCreate, db: Session = Depends(get_db)):
    if db.get(Site, site_id) is None:
        raise HTTPException(status_code=404, detail=f"Site {site_id} not found")
    room = Room(site_id=site_id, **payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room
