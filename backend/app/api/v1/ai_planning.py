from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain.models import AIProposalRecord, Notification
from app.ai.agent import AIPlanningAgent
from app.ai.service import AIPipelinesService

router = APIRouter()


# Request Schemas
class AIProposeRequest(BaseModel):
    request_ids: Optional[List[str]] = None
    base_schedule_version_id: Optional[str] = None


class ProposalApproveRequest(BaseModel):
    actor: str = Field("DISPATCHER_JOHN", json_schema_extra={"example": "DISPATCHER_JOHN"})


class ProposalRejectRequest(BaseModel):
    reason: str = Field(..., json_schema_extra={"example": "Over-allocates North region technicians."})
    actor: str = Field("DISPATCHER_JOHN", json_schema_extra={"example": "DISPATCHER_JOHN"})


class AssignmentDeclineRequest(BaseModel):
    technician_id: str = Field(..., json_schema_extra={"example": "tech_ravi"})
    reason: str = Field(..., json_schema_extra={"example": "Emergency family illness"})


class AssignmentAcceptRequest(BaseModel):
    technician_id: str = Field(..., json_schema_extra={"example": "tech_ravi"})


class EmergencyRequestPayload(BaseModel):
    customer_name: str = Field(..., json_schema_extra={"example": "City Hospital ICU"})
    location_name: str = Field(..., json_schema_extra={"example": "Emergency Medical Wing"})
    region: str = Field(..., json_schema_extra={"example": "NORTH_ZONE"})
    required_skills: List[str] = Field(..., json_schema_extra={"example": ["ELECTRICAL"]})
    min_expertise: int = Field(4, json_schema_extra={"example": 4})
    estimated_duration_hours: float = Field(2.0, json_schema_extra={"example": 2.0})
    actor: str = Field("DISPATCHER_JOHN", json_schema_extra={"example": "DISPATCHER_JOHN"})


class TechnicianCancelPayload(BaseModel):
    reason: str = Field("Severe vehicle breakdown", json_schema_extra={"example": "Severe vehicle breakdown"})
    actor: str = Field("DISPATCHER_JOHN", json_schema_extra={"example": "DISPATCHER_JOHN"})


class ExplainDiffPayload(BaseModel):
    before_assignments: List[Dict[str, Any]]
    after_assignments: List[Dict[str, Any]]
    trigger_event: str = "Technician Cancellation"


# Router Endpoints
@router.post("/ai/planning/propose")
def propose_ai_plan(
    payload: AIProposeRequest,
    db: Session = Depends(get_db),
):
    try:
        result = AIPlanningAgent.generate_plan(
            db=db,
            request_ids=payload.request_ids,
            base_schedule_version_id=payload.base_schedule_version_id,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to generate AI plan proposal: {str(exc)}",
        )


@router.post("/ai/proposals/{proposal_id}/approve")
def approve_ai_proposal(
    proposal_id: str,
    payload: ProposalApproveRequest,
    db: Session = Depends(get_db),
):
    try:
        return AIPipelinesService.approve_proposal(
            db=db,
            proposal_id=proposal_id,
            actor=payload.actor,
        )
    except ValueError as val_err:
        err_msg = str(val_err)
        if "stale" in err_msg.lower():
            raise HTTPException(status_code=409, detail=err_msg)
        raise HTTPException(status_code=400, detail=err_msg)


@router.post("/ai/proposals/{proposal_id}/reject")
def reject_ai_proposal(
    proposal_id: str,
    payload: ProposalRejectRequest,
    db: Session = Depends(get_db),
):
    try:
        return AIPipelinesService.reject_proposal(
            db=db,
            proposal_id=proposal_id,
            reason=payload.reason,
            actor=payload.actor,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.post("/ai/assignments/{assignment_id}/accept")
def accept_assignment(
    assignment_id: str,
    payload: AssignmentAcceptRequest,
    db: Session = Depends(get_db),
):
    try:
        return AIPipelinesService.technician_accept_assignment(
            db=db,
            assignment_id=assignment_id,
            technician_id=payload.technician_id,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.post("/ai/assignments/{assignment_id}/decline")
def decline_assignment(
    assignment_id: str,
    payload: AssignmentDeclineRequest,
    db: Session = Depends(get_db),
):
    try:
        return AIPipelinesService.technician_decline_assignment(
            db=db,
            assignment_id=assignment_id,
            technician_id=payload.technician_id,
            reason=payload.reason,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.post("/ai/emergency")
def create_emergency_request(
    payload: EmergencyRequestPayload,
    db: Session = Depends(get_db),
):
    try:
        return AIPipelinesService.create_emergency_request_and_replan(
            db=db,
            customer_name=payload.customer_name,
            location_name=payload.location_name,
            region=payload.region,
            required_skills=payload.required_skills,
            min_expertise=payload.min_expertise,
            estimated_duration_hours=payload.estimated_duration_hours,
            actor=payload.actor,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/ai/technicians/{technician_id}/cancel")
def cancel_technician(
    technician_id: str,
    payload: TechnicianCancelPayload,
    db: Session = Depends(get_db),
):
    try:
        return AIPipelinesService.cancel_technician_and_replan(
            db=db,
            technician_id=technician_id,
            reason=payload.reason,
            actor=payload.actor,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.post("/ai/planning/explain_diff")
def explain_diff(payload: ExplainDiffPayload):
    return AIPipelinesService.generate_replanning_change_explanation(
        before_assignments=payload.before_assignments,
        after_assignments=payload.after_assignments,
        trigger_event=payload.trigger_event,
    )


@router.get("/notifications")
def list_notifications(db: Session = Depends(get_db)):
    return db.query(Notification).order_by(Notification.created_at.desc()).all()
