from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.domain.models import (
    ServiceRequest,
    Technician,
    ScheduleVersion,
    Assignment,
    AIProposalRecord,
    AIProposalStatusEnum,
    RequestStatusEnum,
    AuditLog,
)
from app.services.assignment_engine import AssignmentEngine
from app.ai.prompts import SYSTEM_PROMPT, build_llm_context_prompt
from app.ai.provider import OpenAIProvider, MockAIProvider
from app.ai.validator import AIProposalValidator
from app.ai.schemas import AIPlanningProposal, AIValidationResult, AIObservabilityMetadata


class AIPlanningAgent:
    """
    AI Planning Agent orchestrating structured LLM proposal generation,
    authoritative backend validation, and observability metric tracking.
    """

    @staticmethod
    def generate_plan(
        db: Session,
        request_ids: Optional[List[str]] = None,
        base_schedule_version_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1. Fetch pending requests
        query = db.query(ServiceRequest)
        if request_ids:
            query = query.filter(ServiceRequest.id.in_(request_ids))
        else:
            query = query.filter(ServiceRequest.status.in_([RequestStatusEnum.UNASSIGNED, RequestStatusEnum.SCHEDULED]))

        requests = query.all()
        technicians = db.query(Technician).filter(Technician.is_active == True).all()

        # 2. Get active schedule version if not provided
        if not base_schedule_version_id:
            latest_version = (
                db.query(ScheduleVersion)
                .order_by(ScheduleVersion.version_number.desc())
                .first()
            )
            base_schedule_version_id = latest_version.id if latest_version else None

        # 3. Compute deterministic evaluations for context
        deterministic_evaluations: Dict[str, Any] = {}
        existing_assignments = db.query(Assignment).all()

        for req in requests:
            eval_res = AssignmentEngine.evaluate_candidates(
                request=req,
                technicians=technicians,
                existing_assignments=existing_assignments,
            )
            deterministic_evaluations[req.id] = eval_res.model_dump()

        # 4. Serialize data for LLM prompt
        requests_json = [
            {
                "id": r.id,
                "customer_name": r.customer_name,
                "region": r.region,
                "required_skills": r.required_skills,
                "min_expertise": r.min_expertise,
                "priority": r.priority.value,
                "estimated_duration_hours": r.estimated_duration_hours,
                "preferred_start": r.preferred_start,
                "preferred_end": r.preferred_end,
            }
            for r in requests
        ]

        techs_json = [
            {
                "id": t.id,
                "name": t.name,
                "region": t.region,
                "skills": t.skills,
                "skill_expertise": t.skill_expertise,
                "availability_start": t.availability_start,
                "availability_end": t.availability_end,
                "max_daily_hours": t.max_daily_hours,
            }
            for t in technicians
        ]

        user_context = build_llm_context_prompt(
            requests=requests_json,
            technicians=techs_json,
            deterministic_evaluations=deterministic_evaluations,
            current_schedule_version=base_schedule_version_id or "1",
        )

        # 5. Invoke Provider (OpenAI or Mock)
        provider = OpenAIProvider()
        proposal, observability = provider.generate_proposal(
            system_prompt=SYSTEM_PROMPT,
            user_context=user_context,
            requests=requests_json,
            technicians=techs_json,
            deterministic_evaluations=deterministic_evaluations,
        )

        proposal.base_schedule_version_id = base_schedule_version_id

        # 6. Authoritative Deterministic Validation
        validation_result = AIProposalValidator.validate_proposal(
            db=db,
            proposed_assignments=proposal.assignments,
            existing_assignments=existing_assignments,
        )
        validation_result.proposal_id = proposal.proposal_id

        # Update Observability counts
        observability.validated_count = len(validation_result.validated_assignments)
        observability.rejected_count = len(validation_result.invalid_assignments)

        # 7. Persist AI Proposal Record in Database
        record = AIProposalRecord(
            id=proposal.proposal_id,
            base_schedule_version_id=base_schedule_version_id,
            status=AIProposalStatusEnum.VALIDATED if validation_result.all_valid else AIProposalStatusEnum.DRAFT,
            proposal_json=proposal.model_dump(),
            validation_result_json=validation_result.model_dump(),
            observability_json=observability.model_dump(),
        )
        db.add(record)

        # 8. Record Audit Log Event
        audit = AuditLog(
            event_type="AI_PROPOSAL_CREATED",
            entity_type="AIProposalRecord",
            entity_id=proposal.proposal_id,
            actor="AI_PLANNING_AGENT",
            metadata_json={
                "provider": observability.provider,
                "model_name": observability.model_name,
                "proposed_count": observability.proposed_count,
                "validated_count": observability.validated_count,
                "rejected_count": observability.rejected_count,
                "is_mock": observability.is_mock,
            },
        )
        db.add(audit)
        db.commit()

        return {
            "proposal": proposal.model_dump(),
            "validation": validation_result.model_dump(),
            "observability": observability.model_dump(),
        }
