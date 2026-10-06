from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import ScheduleVersion, Assignment
from app.api.v1.schemas import ScheduleVersionResponse, AssignmentResponse

router = APIRouter()


@router.get("/schedule", response_model=ScheduleVersionResponse)
def get_active_schedule(db: Session = Depends(get_db)):
    latest = (
        db.query(ScheduleVersion)
        .order_by(ScheduleVersion.version_number.desc())
        .first()
    )
    if not latest:
        # Return empty response or create baseline version
        new_v = ScheduleVersion(version_number=1, trigger_reason="Initial System Baseline", created_by="SYSTEM")
        db.add(new_v)
        db.commit()
        db.refresh(new_v)
        latest = new_v
    return latest


@router.get("/schedules/{schedule_id}", response_model=ScheduleVersionResponse)
def get_schedule_by_id(schedule_id: str, db: Session = Depends(get_db)):
    sched = db.query(ScheduleVersion).filter(ScheduleVersion.id == schedule_id).first()
    if not sched:
        raise HTTPException(status_code=404, detail=f"Schedule version '{schedule_id}' not found.")
    return sched


@router.get("/assignments", response_model=List[AssignmentResponse])
def list_assignments(
    technician_id: Optional[str] = None,
    schedule_version_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Assignment)
    if technician_id:
        query = query.filter(Assignment.technician_id == technician_id)
    if schedule_version_id:
        query = query.filter(Assignment.schedule_version_id == schedule_version_id)
    return query.order_by(Assignment.start_time.asc()).all()


@router.get("/assignments/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: str, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail=f"Assignment '{assignment_id}' not found.")
    return assignment
