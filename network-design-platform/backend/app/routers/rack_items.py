from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.rack import Rack
from app.models.rack_item import RackItem
from app.schemas.rack_item import RackItemCreate, RackItemMove, RackItemRead

router = APIRouter(prefix="/racks/{rack_id}/items", tags=["rack-items"])


def _get_rack_or_404(rack_id: int, db: Session) -> Rack:
    rack = db.get(Rack, rack_id)
    if rack is None:
        raise HTTPException(status_code=404, detail=f"Rack {rack_id} not found")
    return rack


def _check_overlap(db: Session, rack: Rack, start_u: int, size_u: int, exclude_item_id: int | None = None):
    """Two rack items may not occupy the same U slot. Used both on create
    and on the drag-to-place move, since a drop target the UI thought was
    free can be stale by the time the request lands."""
    end_u = start_u + size_u - 1
    if end_u > rack.total_u:
        raise HTTPException(
            status_code=409,
            detail=f"Item would occupy U{start_u}-U{end_u}, past the rack's {rack.total_u}U capacity",
        )
    for other in rack.items:
        if exclude_item_id is not None and other.id == exclude_item_id:
            continue
        if start_u <= other.end_u and other.start_u <= end_u:
            raise HTTPException(
                status_code=409,
                detail=f"U{start_u}-U{end_u} overlaps '{other.name}' at U{other.start_u}-U{other.end_u}",
            )


@router.get("", response_model=list[RackItemRead])
def list_rack_items(rack_id: int, db: Session = Depends(get_db)):
    rack = _get_rack_or_404(rack_id, db)
    return sorted(rack.items, key=lambda i: i.start_u)


@router.post("", response_model=RackItemRead, status_code=201)
def create_rack_item(rack_id: int, payload: RackItemCreate, db: Session = Depends(get_db)):
    rack = _get_rack_or_404(rack_id, db)
    _check_overlap(db, rack, payload.start_u, payload.size_u)
    item = RackItem(rack_id=rack_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _get_item_or_404(rack_id: int, item_id: int, db: Session) -> RackItem:
    item = db.get(RackItem, item_id)
    if item is None or item.rack_id != rack_id:
        raise HTTPException(status_code=404, detail=f"Rack item {item_id} not found in rack {rack_id}")
    return item


@router.patch("/{item_id}/move", response_model=RackItemRead)
def move_rack_item(rack_id: int, item_id: int, payload: RackItemMove, db: Session = Depends(get_db)):
    rack = _get_rack_or_404(rack_id, db)
    item = _get_item_or_404(rack_id, item_id, db)
    _check_overlap(db, rack, payload.start_u, item.size_u, exclude_item_id=item.id)
    item.start_u = payload.start_u
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_rack_item(rack_id: int, item_id: int, db: Session = Depends(get_db)):
    item = _get_item_or_404(rack_id, item_id, db)
    db.delete(item)
    db.commit()
