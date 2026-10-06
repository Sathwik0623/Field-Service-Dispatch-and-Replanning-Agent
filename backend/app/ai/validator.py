from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.domain.models import ServiceRequest, Technician, Assignment, AssignmentStatusEnum
from app.services.assignment_engine import AssignmentEngine
from app.ai.schemas import AIProposedAssignment, ValidatedAssignment, AIValidationResult


class AIProposalValidator:
    """
    Authoritative deterministic validator for AI-proposed assignments.
    Ensures LLM proposals NEVER bypass backend hard constraints or commit invalid assignments.
    """

    @staticmethod
    def validate_proposal(
        db: Session,
        proposed_assignments: List[AIProposedAssignment],
        existing_assignments: List[Any] = None,
    ) -> AIValidationResult:
        """
        Validates every proposed assignment in an AI proposal against deterministic backend hard constraints.
        """
        if existing_assignments is None:
            existing_assignments = (
                db.query(Assignment)
                .filter(Assignment.status == AssignmentStatusEnum.CONFIRMED)
                .all()
            )

        validated_list: List[ValidatedAssignment] = []
        invalid_list: List[ValidatedAssignment] = []

        active_assignments = list(existing_assignments)

        for prop in proposed_assignments:
            req_id = prop.service_request_id
            tech_id = prop.technician_id

            # Fetch DB entities
            req = db.query(ServiceRequest).filter(ServiceRequest.id == req_id).first()
            tech = db.query(Technician).filter(Technician.id == tech_id).first()

            reasons: List[str] = []

            # 1. Existence check
            if not req:
                reasons.append(f"Service Request '{req_id}' does not exist in backend database.")
            if not tech:
                reasons.append(f"Technician '{tech_id}' does not exist in backend database.")

            if reasons or not req or not tech:
                invalid_item = ValidatedAssignment(
                    service_request_id=req_id,
                    technician_id=tech_id,
                    proposed_start=prop.proposed_start,
                    proposed_end=prop.proposed_end,
                    rationale=prop.rationale,
                    confidence=prop.confidence,
                    is_valid=False,
                    rejection_reasons=reasons,
                )
                invalid_list.append(invalid_item)
                continue

            # 2. Run AssignmentEngine hard constraint evaluation on this single technician
            eval_res = AssignmentEngine.evaluate_candidates(
                request=req,
                technicians=[tech],
                existing_assignments=active_assignments,
            )

            if eval_res.eligible_candidates:
                cand = eval_res.eligible_candidates[0]
                valid_item = ValidatedAssignment(
                    service_request_id=req_id,
                    technician_id=tech_id,
                    proposed_start=prop.proposed_start,
                    proposed_end=prop.proposed_end,
                    rationale=prop.rationale,
                    confidence=prop.confidence,
                    is_valid=True,
                    score=cand.score,
                    score_breakdown=cand.score_breakdown.model_dump(),
                )
                validated_list.append(valid_item)

                # Temporarily attach to active_assignments in memory to check subsequent overlap
                temp_a = Assignment(
                    service_request_id=req_id,
                    technician_id=tech_id,
                    schedule_version_id="temp_validation",
                    start_time=prop.proposed_start,
                    end_time=prop.proposed_end,
                )
                setattr(temp_a, "duration_hours", req.estimated_duration_hours)
                setattr(temp_a, "latitude", req.latitude)
                setattr(temp_a, "longitude", req.longitude)
                active_assignments.append(temp_a)
            else:
                top_reasons = []
                if eval_res.ineligible_candidates:
                    top_reasons = eval_res.ineligible_candidates[0].reasons

                invalid_item = ValidatedAssignment(
                    service_request_id=req_id,
                    technician_id=tech_id,
                    proposed_start=prop.proposed_start,
                    proposed_end=prop.proposed_end,
                    rationale=prop.rationale,
                    confidence=prop.confidence,
                    is_valid=False,
                    rejection_reasons=top_reasons if top_reasons else ["Deterministic validation failed"],
                )
                invalid_list.append(invalid_item)

        all_valid = len(invalid_list) == 0

        summary = (
            f"AI Proposal Validation Passed ({len(validated_list)} valid assignments)."
            if all_valid
            else f"AI Proposal Validation Flagged {len(invalid_list)} Invalid Assignment(s)."
        )

        return AIValidationResult(
            proposal_id="",
            all_valid=all_valid,
            validated_assignments=validated_list,
            invalid_assignments=invalid_list,
            validation_summary=summary,
        )
