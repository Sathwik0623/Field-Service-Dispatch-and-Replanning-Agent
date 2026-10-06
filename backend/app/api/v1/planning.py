from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.v1.schemas import PlanningProposeRequest, PlanningProposeResponse
from app.services.scheduling_engine import SchedulingEngine

router = APIRouter()


@router.post("/planning/propose", response_model=PlanningProposeResponse)
def propose_schedule(
    payload: PlanningProposeRequest,
    db: Session = Depends(get_db),
):
    try:
        result = SchedulingEngine.generate_schedule_proposal(
            db=db,
            request_ids=payload.request_ids,
            created_by=payload.created_by,
            trigger_reason=payload.trigger_reason,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to generate schedule proposal: {str(exc)}",
        )
