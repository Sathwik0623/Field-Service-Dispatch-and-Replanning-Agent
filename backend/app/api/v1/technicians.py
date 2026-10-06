from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import Technician, AuditLog
from app.api.v1.schemas import TechnicianCreate, TechnicianResponse

router = APIRouter()


@router.get("/technicians", response_model=List[TechnicianResponse])
def list_technicians(
    region: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Technician)
    if region:
        query = query.filter(Technician.region == region)
    if active_only:
        query = query.filter(Technician.is_active == True)
    return query.order_by(Technician.name.asc()).all()


@router.post("/technicians", response_model=TechnicianResponse, status_code=status.HTTP_201_CREATED)
def create_technician(
    payload: TechnicianCreate,
    db: Session = Depends(get_db),
):
    tech = Technician(**payload.model_dump())
    db.add(tech)
    db.flush()

    audit = AuditLog(
        event_type="TECHNICIAN_CREATED",
        entity_type="Technician",
        entity_id=tech.id,
        actor="ADMIN",
        metadata_json={"name": tech.name, "region": tech.region, "skills": tech.skills},
    )
    db.add(audit)
    db.commit()
    db.refresh(tech)
    return tech


@router.get("/technicians/{technician_id}", response_model=TechnicianResponse)
def get_technician(technician_id: str, db: Session = Depends(get_db)):
    tech = db.query(Technician).filter(Technician.id == technician_id).first()
    if not tech:
        raise HTTPException(status_code=404, detail=f"Technician '{technician_id}' not found.")
    return tech
