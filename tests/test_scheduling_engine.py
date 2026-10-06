import pytest
from app.db.seed import seed_database
from app.domain.models import ScheduleVersion, Assignment, ServiceRequest, RequestStatusEnum
from app.services.scheduling_engine import SchedulingEngine, get_travel_buffer_minutes


def test_travel_buffer_calculation():
    assert get_travel_buffer_minutes(1.5) == 15
    assert get_travel_buffer_minutes(5.0) == 30
    assert get_travel_buffer_minutes(15.0) == 45


def test_generate_schedule_proposal_initial(db_session):
    seed_database(db_session)

    proposal = SchedulingEngine.generate_schedule_proposal(
        db=db_session,
        created_by="TEST_DISPATCHER",
        trigger_reason="Unit Test Initial Generation",
    )

    assert proposal["schedule_version_id"] is not None
    assert proposal["version_number"] == 1
    assert len(proposal["assignments"]) > 0

    # Verify unassigned request handled safely (REQ-111 nuclear research lab has no eligible tech)
    unassigned_ids = [u["request_id"] for u in proposal["unassigned_requests"]]
    assert "req_111" in unassigned_ids


def test_generate_schedule_proposal_twice_preserves_versioning(db_session):
    seed_database(db_session)

    # 1. First Proposal Generation
    v1_proposal = SchedulingEngine.generate_schedule_proposal(
        db=db_session,
        created_by="TEST_DISPATCHER",
        trigger_reason="First Generation Run",
    )
    v1_id = v1_proposal["schedule_version_id"]
    v1_assignments_count = len(v1_proposal["assignments"])
    assert v1_proposal["version_number"] == 1

    # 2. Second Proposal Generation (Repeated Trigger)
    v2_proposal = SchedulingEngine.generate_schedule_proposal(
        db=db_session,
        created_by="TEST_DISPATCHER",
        trigger_reason="Second Generation Run",
    )
    v2_id = v2_proposal["schedule_version_id"]
    assert v2_proposal["version_number"] == 2

    # Verify Schedule Version 2 points to Version 1 as parent_version_id
    v2_db = db_session.query(ScheduleVersion).filter(ScheduleVersion.id == v2_id).first()
    assert v2_db is not None
    assert v2_db.parent_version_id == v1_id

    # Verify Version 1 historical assignments remain preserved in DB
    v1_db = db_session.query(ScheduleVersion).filter(ScheduleVersion.id == v1_id).first()
    assert len(v1_db.assignments) == v1_assignments_count
