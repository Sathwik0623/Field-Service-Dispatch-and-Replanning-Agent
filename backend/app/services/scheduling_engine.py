from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.domain.models import (
    Technician,
    ServiceRequest,
    ScheduleVersion,
    Assignment,
    AssignmentStatusEnum,
    RequestStatusEnum,
    AuditLog,
)
from app.services.assignment_engine import AssignmentEngine, parse_time_to_minutes


def minutes_to_time_str(minutes: int) -> str:
    """Helper to convert minutes from midnight to HH:MM string."""
    hours = (minutes // 60) % 24
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def get_travel_buffer_minutes(distance_km: float) -> int:
    """Deterministic travel buffer based on distance."""
    if distance_km <= 2.0:
        return 15
    elif distance_km <= 10.0:
        return 30
    else:
        return 45


class SchedulingEngine:
    """
    Standalone scheduling service that converts service requests into valid non-overlapping schedule assignments.
    """

    @staticmethod
    def generate_schedule_proposal(
        db: Session,
        request_ids: Optional[List[str]] = None,
        created_by: str = "DISPATCHER",
        trigger_reason: str = "Automated Dispatch Generation",
    ) -> Dict[str, Any]:
        """
        Generates a new ScheduleVersion with proposed assignments for pending service requests.
        """
        # 1. Fetch latest ScheduleVersion to derive version_number
        latest_version = (
            db.query(ScheduleVersion)
            .order_by(ScheduleVersion.version_number.desc())
            .first()
        )
        new_version_num = (latest_version.version_number + 1) if latest_version else 1
        parent_version_id = latest_version.id if latest_version else None

        # 2. Create new ScheduleVersion
        new_schedule_version = ScheduleVersion(
            version_number=new_version_num,
            parent_version_id=parent_version_id,
            trigger_reason=trigger_reason,
            created_by=created_by,
        )
        db.add(new_schedule_version)
        db.flush()

        # 3. Fetch Service Requests to schedule
        query = db.query(ServiceRequest)
        if request_ids:
            query = query.filter(ServiceRequest.id.in_(request_ids))
        else:
            # Evaluate unassigned or recently created pending requests
            query = query.filter(ServiceRequest.status.in_([RequestStatusEnum.UNASSIGNED, RequestStatusEnum.SCHEDULED]))

        # Sort requests by priority (CRITICAL > HIGH > MEDIUM > LOW) and creation date
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_requests = query.all()
        all_requests.sort(
            key=lambda r: (priority_order.get(r.priority.value, 4), r.created_at)
        )

        # 4. Fetch Active Technicians and Locked Confirmed Assignments
        technicians = db.query(Technician).filter(Technician.is_active == True).all()
        
        # Confirmed assignments are locked commitments from DB history
        confirmed_assignments = (
            db.query(Assignment)
            .filter(Assignment.status == AssignmentStatusEnum.CONFIRMED)
            .all()
        )

        proposed_assignments: List[Assignment] = []
        unassigned_requests: List[Dict[str, Any]] = []
        warnings: List[str] = []

        # Track active assignment state in memory for this schedule proposal generation run
        active_assignments = list(confirmed_assignments)

        for req in all_requests:
            eval_result = AssignmentEngine.evaluate_candidates(
                request=req,
                technicians=technicians,
                existing_assignments=active_assignments,
            )

            if not eval_result.eligible_candidates:
                top_reasons = []
                for in_cand in eval_result.ineligible_candidates[:2]:
                    top_reasons.extend(in_cand.reasons)
                
                unassigned_requests.append(
                    {
                        "request_id": req.id,
                        "customer_name": req.customer_name,
                        "priority": req.priority.value,
                        "reason": f"No eligible technician found. Rejection notes: {'; '.join(top_reasons[:2]) if top_reasons else 'Constraint mismatches'}",
                    }
                )
                warnings.append(f"Request {req.id} ({req.customer_name}) could not be scheduled.")
                continue

            # Select top ranked candidate
            top_candidate = eval_result.eligible_candidates[0]

            # Calculate start/end times considering preferred window & travel buffer from prior assignment
            preferred_start_min = parse_time_to_minutes(req.preferred_start)
            duration_mins = int(req.estimated_duration_hours * 60)

            # Check top candidate's previous assignments in active_assignments to apply travel buffer
            tech_prev_assignments = [
                a for a in active_assignments if getattr(a, "technician_id", "") == top_candidate.technician_id
            ]

            earliest_start_min = preferred_start_min
            if tech_prev_assignments:
                # Find end time of last assignment for this tech
                last_end_min = max(
                    parse_time_to_minutes(str(getattr(a, "end_time", "08:00"))[-5:])
                    for a in tech_prev_assignments
                )
                buffer_mins = get_travel_buffer_minutes(top_candidate.distance_km)
                earliest_start_min = max(preferred_start_min, last_end_min + buffer_mins)

            req_end_min = earliest_start_min + duration_mins

            start_time_str = minutes_to_time_str(earliest_start_min)
            end_time_str = minutes_to_time_str(req_end_min)

            # Create assignment entity
            new_assignment = Assignment(
                service_request_id=req.id,
                technician_id=top_candidate.technician_id,
                schedule_version_id=new_schedule_version.id,
                start_time=start_time_str,
                end_time=end_time_str,
                score=top_candidate.score,
                score_breakdown=top_candidate.score_breakdown.model_dump(),
                status=AssignmentStatusEnum.PROPOSED,
            )

            # Attach helper properties for in-memory tracking
            setattr(new_assignment, "duration_hours", req.estimated_duration_hours)
            setattr(new_assignment, "latitude", req.latitude)
            setattr(new_assignment, "longitude", req.longitude)
            setattr(new_assignment, "service_request", req)

            db.add(new_assignment)
            proposed_assignments.append(new_assignment)
            active_assignments.append(new_assignment)

            # Update request status to SCHEDULED
            req.status = RequestStatusEnum.SCHEDULED

        # 5. Create Audit Log
        audit = AuditLog(
            event_type="SCHEDULE_CREATED",
            entity_type="ScheduleVersion",
            entity_id=new_schedule_version.id,
            actor=created_by,
            metadata_json={
                "version_number": new_version_num,
                "proposed_count": len(proposed_assignments),
                "unassigned_count": len(unassigned_requests),
            },
        )
        db.add(audit)
        db.commit()

        return {
            "schedule_version_id": new_schedule_version.id,
            "version_number": new_version_num,
            "assignments": [
                {
                    "id": a.id,
                    "service_request_id": a.service_request_id,
                    "technician_id": a.technician_id,
                    "start_time": a.start_time,
                    "end_time": a.end_time,
                    "score": a.score,
                    "score_breakdown": a.score_breakdown,
                    "status": a.status.value if hasattr(a.status, 'value') else str(a.status),
                }
                for a in proposed_assignments
            ],
            "unassigned_requests": unassigned_requests,
            "warnings": warnings,
        }
