from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.reference_data import ReferenceItem, ReferenceList
from app.schemas.reference_data import ReferenceItemCreate, ReferenceListCreate, ReferenceListRead

router = APIRouter(prefix="/reference-lists", tags=["reference-data"])


@router.get("", response_model=list[ReferenceListRead])
def list_reference_lists(db: Session = Depends(get_db)):
    return db.query(ReferenceList).all()


@router.get("/{key}", response_model=ReferenceListRead)
def get_reference_list(key: str, db: Session = Depends(get_db)):
    ref_list = db.query(ReferenceList).filter(ReferenceList.key == key).first()
    if ref_list is None:
        raise HTTPException(status_code=404, detail=f"Reference list '{key}' not found")
    return ref_list


@router.post("", response_model=ReferenceListRead, status_code=201)
def create_reference_list(payload: ReferenceListCreate, db: Session = Depends(get_db)):
    if db.query(ReferenceList).filter(ReferenceList.key == payload.key).first():
        raise HTTPException(status_code=409, detail=f"Reference list '{payload.key}' already exists")
    ref_list = ReferenceList(**payload.model_dump())
    db.add(ref_list)
    db.commit()
    db.refresh(ref_list)
    return ref_list


@router.post("/{key}/items", response_model=ReferenceListRead, status_code=201)
def add_reference_item(key: str, payload: ReferenceItemCreate, db: Session = Depends(get_db)):
    ref_list = db.query(ReferenceList).filter(ReferenceList.key == key).first()
    if ref_list is None:
        raise HTTPException(status_code=404, detail=f"Reference list '{key}' not found")
    ref_list.items.append(ReferenceItem(**payload.model_dump()))
    db.commit()
    db.refresh(ref_list)
    return ref_list
