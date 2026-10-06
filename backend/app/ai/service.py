from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.domain.models import (
    AIProposalRecord,
    AIProposalStatusEnum,
    ScheduleVersion,
    Assignment,
    AssignmentStatusEnum,
    ServiceRequest,
    RequestStatusEnum,
    Technician,
    Approval,
    ApprovalDecisionEnum,
    AuditLog,
    Notification,
    PriorityEnum,
)
from app.services.scheduling_engine import SchedulingEngine
from app.ai.agent import AIPlanningAgent
from app.ai.schemas import AIProposedAssignment
from app.ai.validator import AIProposalValidator


def send_mock_notification(
    db: Session,
    recipient_type: str,
    recipient_id: str,
    title: str,
    message: str,
) -> Notification:
    """Creates a mock notification record."""
    notif = Notification(
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        title=title,
        message=message,
        status="UNREAD",
    )
    db.add(notif)
    return notif


class AIPipelinesService:
    """
    Service layer handling human-in-the-loop approvals, technician workflows,
    emergency replanning, change explanations, and notification dispatches.
    """

    @staticmethod
    def approve_proposal(
        db: Session,
        proposal_id: str,
        actor: str = "DISPATCHER_JOHN",
    ) -> Dict[str, Any]:
        """
        Dispatcher approves a validated AI proposal, persisting confirmed assignments to a new ScheduleVersion.
        """
        record = db.query(AIProposalRecord).filter(AIProposalRecord.id == proposal_id).first()
        if not record:
            raise ValueError(f"AI Proposal '{proposal_id}' not found.")

        if record.status in [AIProposalStatusEnum.APPROVED, AIProposalStatusEnum.REJECTED, AIProposalStatusEnum.SUPERSEDED]:
            raise ValueError(f"Proposal '{proposal_id}' cannot be approved because its current status is {record.status.value}.")

        proposal_data = record.proposal_json
        validation_data = record.validation_result_json

        # Validate proposal is not stale
        valid_assignments = validation_data.get("validated_assignments", [])
        if not valid_assignments:
            raise ValueError("Cannot approve a proposal with zero valid assignments.")

        # Re-run validation to ensure no stale conflicts
        re_props = [
            AIProposedAssignment(
                service_request_id=item["service_request_id"],
                technician_id=item["technician_id"],
                proposed_start=item["proposed_start"],
                proposed_end=item["proposed_end"],
                rationale=item.get("rationale", ""),
                confidence=item.get("confidence", 0.9),
            )
            for item in valid_assignments
        ]
        re_val = AIProposalValidator.validate_proposal(db, re_props)
        if not re_val.all_valid:
            record.status = AIProposalStatusEnum.SUPERSEDED
            db.commit()
            raise ValueError(
                "Proposal is stale because underlying schedule or technician availability changed. Please generate a new plan."
            )

        # 1. Create new ScheduleVersion
        latest_v = db.query(ScheduleVersion).order_by(ScheduleVersion.version_number.desc()).first()
        new_v_num = (latest_v.version_number + 1) if latest_v else 1

        new_version = ScheduleVersion(
            version_number=new_v_num,
            parent_version_id=record.base_schedule_version_id,
            trigger_reason=f"Approved AI Proposal {proposal_id}",
            created_by=actor,
        )
        db.add(new_version)
        db.flush()

        confirmed_assignments: List[Assignment] = []
        for item in valid_assignments:
            req_id = item["service_request_id"]
            tech_id = item["technician_id"]

            assignment = Assignment(
                service_request_id=req_id,
                technician_id=tech_id,
                schedule_version_id=new_version.id,
                start_time=item["proposed_start"],
                end_time=item["proposed_end"],
                score=item.get("score", 0.0),
                score_breakdown=item.get("score_breakdown", {}),
                status=AssignmentStatusEnum.CONFIRMED,
            )
            db.add(assignment)
            confirmed_assignments.append(assignment)

            # Update request status
            req = db.query(ServiceRequest).filter(ServiceRequest.id == req_id).first()
            if req:
                req.status = RequestStatusEnum.SCHEDULED

            # Send mock notification to technician
            send_mock_notification(
                db,
                recipient_type="TECHNICIAN",
                recipient_id=tech_id,
                title="New Dispatch Assignment",
                message=f"You have been assigned to Service Request {req_id} from {item['proposed_start']} to {item['proposed_end']}.",
            )

        # Update proposal record status
        record.status = AIProposalStatusEnum.APPROVED

        # Audit & Approval records
        appr = Approval(
            schedule_version_id=new_version.id,
            actor=actor,
            decision=ApprovalDecisionEnum.APPROVED,
            reason=f"Dispatcher approved AI Proposal {proposal_id}",
        )
        db.add(appr)

        audit = AuditLog(
            event_type="DISPATCHER_APPROVED",
            entity_type="AIProposalRecord",
            entity_id=proposal_id,
            actor=actor,
            metadata_json={"new_version_number": new_v_num, "assignments_count": len(confirmed_assignments)},
        )
        db.add(audit)
        db.commit()

        return {
            "schedule_version_id": new_version.id,
            "version_number": new_v_num,
            "status": "APPROVED",
            "confirmed_count": len(confirmed_assignments),
        }

    @staticmethod
    def reject_proposal(
        db: Session,
        proposal_id: str,
        reason: str,
        actor: str = "DISPATCHER_JOHN",
    ) -> Dict[str, Any]:
        """Dispatcher rejects an AI proposal with explicit reason."""
        if not reason:
            raise ValueError("Rejection reason is required.")

        record = db.query(AIProposalRecord).filter(AIProposalRecord.id == proposal_id).first()
        if not record:
            raise ValueError(f"AI Proposal '{proposal_id}' not found.")

        if record.status in [AIProposalStatusEnum.APPROVED, AIProposalStatusEnum.REJECTED, AIProposalStatusEnum.SUPERSEDED]:
            raise ValueError(f"Proposal '{proposal_id}' cannot be rejected because its current status is {record.status.value}.")

        record.status = AIProposalStatusEnum.REJECTED
        record.rejection_reason = reason

        appr = Approval(
            schedule_version_id=record.base_schedule_version_id,
            actor=actor,
            decision=ApprovalDecisionEnum.REJECTED,
            reason=reason,
        )
        db.add(appr)

        audit = AuditLog(
            event_type="DISPATCHER_REJECTED",
            entity_type="AIProposalRecord",
            entity_id=proposal_id,
            actor=actor,
            metadata_json={"reason": reason},
        )
        db.add(audit)
        db.commit()

        return {"proposal_id": proposal_id, "status": "REJECTED", "reason": reason}

    @staticmethod
    def technician_accept_assignment(
        db: Session,
        assignment_id: str,
        technician_id: str,
    ) -> Dict[str, Any]:
        """Technician accepts an assigned job."""
        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise ValueError(f"Assignment '{assignment_id}' not found.")

        assignment.status = AssignmentStatusEnum.CONFIRMED

        audit = AuditLog(
            event_type="TECHNICIAN_ACCEPTED",
            entity_type="Assignment",
            entity_id=assignment_id,
            actor=technician_id,
            metadata_json={"service_request_id": assignment.service_request_id},
        )
        db.add(audit)
        send_mock_notification(
            db,
            recipient_type="DISPATCHER",
            recipient_id="DISPATCHER_CENTER",
            title="Assignment Accepted",
            message=f"Technician {technician_id} accepted assignment {assignment_id} for request {assignment.service_request_id}.",
        )
        db.commit()

        return {"assignment_id": assignment_id, "status": "CONFIRMED"}

    @staticmethod
    def technician_decline_assignment(
        db: Session,
        assignment_id: str,
        technician_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Technician declines an assigned job, triggering replanning availability."""
        if not reason:
            raise ValueError("Decline reason is required.")

        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not assignment:
            raise ValueError(f"Assignment '{assignment_id}' not found.")

        assignment.status = AssignmentStatusEnum.DECLINED

        # Mark service request unassigned so it can be replanned
        req = db.query(ServiceRequest).filter(ServiceRequest.id == assignment.service_request_id).first()
        if req:
            req.status = RequestStatusEnum.UNASSIGNED

        audit = AuditLog(
            event_type="TECHNICIAN_DECLINED",
            entity_type="Assignment",
            entity_id=assignment_id,
            actor=technician_id,
            metadata_json={"reason": reason, "service_request_id": assignment.service_request_id},
        )
        db.add(audit)

        send_mock_notification(
            db,
            recipient_type="DISPATCHER",
            recipient_id="DISPATCHER_CENTER",
            title="Assignment Declined - Replanning Needed",
            message=f"Technician {technician_id} declined assignment for request {assignment.service_request_id}. Reason: {reason}",
        )
        db.commit()

        # Trigger AI Replanning Proposal
        replan_proposal = AIPlanningAgent.generate_plan(db, request_ids=[req.id] if req else None)

        return {
            "assignment_id": assignment_id,
            "status": "DECLINED",
            "reason": reason,
            "replan_proposal": replan_proposal,
        }

    @staticmethod
    def create_emergency_request_and_replan(
        db: Session,
        customer_name: str,
        location_name: str,
        region: str,
        required_skills: List[str],
        min_expertise: int = 4,
        estimated_duration_hours: float = 2.0,
        actor: str = "DISPATCHER",
    ) -> Dict[str, Any]:
        """Creates an emergency CRITICAL priority request and generates a replanning proposal."""
        req = ServiceRequest(
            customer_name=customer_name,
            location_name=location_name,
            region=region,
            latitude=12.9716,
            longitude=77.5946,
            required_skills=required_skills,
            min_expertise=min_expertise,
            priority=PriorityEnum.CRITICAL,
            estimated_duration_hours=estimated_duration_hours,
            preferred_start="09:00",
            preferred_end="17:00",
            status=RequestStatusEnum.UNASSIGNED,
        )
        db.add(req)
        db.flush()

        audit = AuditLog(
            event_type="EMERGENCY_REQUEST_CREATED",
            entity_type="ServiceRequest",
            entity_id=req.id,
            actor=actor,
            metadata_json={"customer": customer_name, "skills": required_skills, "priority": "CRITICAL"},
        )
        db.add(audit)
        db.commit()

        # Generate Replanning Proposal
        replan = AIPlanningAgent.generate_plan(db)

        return {
            "emergency_request_id": req.id,
            "priority": "CRITICAL",
            "replan_proposal": replan,
        }

    @staticmethod
    def cancel_technician_and_replan(
        db: Session,
        technician_id: str,
        reason: str = "Technician emergency illness",
        actor: str = "DISPATCHER",
    ) -> Dict[str, Any]:
        """Simulates technician cancellation, marks active future assignments unassigned, and generates replan."""
        tech = db.query(Technician).filter(Technician.id == technician_id).first()
        if not tech:
            raise ValueError(f"Technician '{technician_id}' not found.")

        tech.is_active = False

        # Find affected active assignments for this technician
        affected_assignments = (
            db.query(Assignment)
            .filter(
                Assignment.technician_id == technician_id,
                Assignment.status.in_([AssignmentStatusEnum.CONFIRMED, AssignmentStatusEnum.PROPOSED]),
            )
            .all()
        )

        affected_req_ids = []
        for a in affected_assignments:
            a.status = AssignmentStatusEnum.CANCELLED
            sr = db.query(ServiceRequest).filter(ServiceRequest.id == a.service_request_id).first()
            if sr and sr.status != RequestStatusEnum.COMPLETED:
                sr.status = RequestStatusEnum.UNASSIGNED
                affected_req_ids.append(sr.id)

        audit = AuditLog(
            event_type="TECHNICIAN_CANCELLED",
            entity_type="Technician",
            entity_id=technician_id,
            actor=actor,
            metadata_json={"reason": reason, "affected_requests": affected_req_ids},
        )
        db.add(audit)
        db.commit()

        # Generate Replanning Proposal for affected requests
        replan = AIPlanningAgent.generate_plan(db)

        return {
            "technician_id": technician_id,
            "status": "INACTIVE",
            "affected_request_ids": affected_req_ids,
            "replan_proposal": replan,
        }

    @staticmethod
    def generate_replanning_change_explanation(
        before_assignments: List[Dict[str, Any]],
        after_assignments: List[Dict[str, Any]],
        trigger_event: str,
    ) -> Dict[str, Any]:
        """Generates factual change diff explanation between old schedule version and new proposed version."""
        before_map = {a["service_request_id"]: a for a in before_assignments}
        after_map = {a["service_request_id"]: a for a in after_assignments}

        changes = []
        unchanged = []

        all_req_ids = set(before_map.keys()).union(set(after_map.keys()))

        for req_id in all_req_ids:
            b_item = before_map.get(req_id)
            a_item = after_map.get(req_id)

            if b_item and a_item:
                if b_item["technician_id"] != a_item["technician_id"] or b_item["start_time"] != a_item["start_time"]:
                    changes.append({
                        "service_request_id": req_id,
                        "before_technician_id": b_item["technician_id"],
                        "after_technician_id": a_item["technician_id"],
                        "before_window": f"{b_item['start_time']}-{b_item['end_time']}",
                        "after_window": f"{a_item['start_time']}-{a_item['end_time']}",
                        "reason": f"Reassigned due to {trigger_event}",
                    })
                else:
                    unchanged.append(req_id)
            elif not b_item and a_item:
                changes.append({
                    "service_request_id": req_id,
                    "before_technician_id": "None (Unassigned)",
                    "after_technician_id": a_item["technician_id"],
                    "before_window": "N/A",
                    "after_window": f"{a_item['start_time']}-{a_item['end_time']}",
                    "reason": f"Newly assigned in replan after {trigger_event}",
                })

        return {
            "trigger_event": trigger_event,
            "changed_assignments": changes,
            "unchanged_request_ids": list(unchanged),
            "summary": f"{len(changes)} assignment(s) changed and {len(unchanged)} assignment(s) remained unchanged after {trigger_event}.",
        }
