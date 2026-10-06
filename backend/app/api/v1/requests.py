from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import ServiceRequest, Technician, Assignment, AuditLog, RequestStatusEnum
from app.api.v1.schemas import ServiceRequestCreate, ServiceRequestResponse
from app.services.assignment_engine import AssignmentEngine

router = APIRouter()


@router.get("/requests", response_model=List[ServiceRequestResponse])
def list_service_requests(
    status: Optional[RequestStatusEnum] = None,
    region: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ServiceRequest)
    if status:
        query = query.filter(ServiceRequest.status == status)
    if region:
        query = query.filter(ServiceRequest.region == region)
    return query.order_by(ServiceRequest.created_at.desc()).all()


@router.post("/requests", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_service_request(
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
):
    req = ServiceRequest(**payload.model_dump())
    db.add(req)
    db.flush()

    audit = AuditLog(
        event_type="REQUEST_CREATED",
        entity_type="ServiceRequest",
        entity_id=req.id,
        actor="DISPATCHER",
        metadata_json={
            "customer_name": req.customer_name,
            "priority": req.priority.value,
            "region": req.region,
        },
    )
    db.add(audit)
    db.commit()
    db.refresh(req)
    return req


@router.get("/requests/{request_id}", response_model=ServiceRequestResponse)
def get_service_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail=f"Service request '{request_id}' not found.")
    return req


@router.post("/requests/{request_id}/evaluate")
def evaluate_candidates_for_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail=f"Service request '{request_id}' not found.")

    technicians = db.query(Technician).all()
    existing_assignments = db.query(Assignment).all()

    eval_result = AssignmentEngine.evaluate_candidates(
        request=req,
        technicians=technicians,
        existing_assignments=existing_assignments,
    )
    return eval_result.model_dump()
