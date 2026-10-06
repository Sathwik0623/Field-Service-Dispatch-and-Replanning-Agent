import pytest
from app.domain.models import Technician, ServiceRequest, PriorityEnum, Assignment, AssignmentStatusEnum
from app.services.assignment_engine import AssignmentEngine, calculate_haversine_distance


def test_haversine_distance_calculation():
    # Distance between Bangalore MG Road (12.9720, 77.5950) and Commercial St (12.9810, 77.6080)
    dist = calculate_haversine_distance(12.9720, 77.5950, 12.9810, 77.6080)
    assert 1.0 <= dist <= 2.0


def test_valid_technician_passes_hard_constraints():
    tech = Technician(
        id="tech_1",
        name="Valid Tech",
        skills=["HVAC"],
        skill_expertise={"HVAC": 4},
        region="NORTH_ZONE",
        latitude=12.9716,
        longitude=77.5946,
        availability_start="08:00",
        availability_end="17:00",
        max_daily_hours=8.0,
        is_active=True,
    )
    req = ServiceRequest(
        id="req_1",
        customer_name="Test Corp",
        location_name="Site 1",
        region="NORTH_ZONE",
        latitude=12.9720,
        longitude=77.5950,
        required_skills=["HVAC"],
        min_expertise=3,
        estimated_duration_hours=2.0,
        preferred_start="09:00",
        preferred_end="12:00",
    )

    result = AssignmentEngine.evaluate_candidates(req, [tech])
    assert len(result.eligible_candidates) == 1
    assert result.eligible_candidates[0].technician_id == "tech_1"
    assert result.eligible_candidates[0].score > 0
    assert result.eligible_candidates[0].score_breakdown.total > 0


def test_missing_skill_fails_eligibility():
    tech = Technician(
        id="tech_2",
        name="Plumber Tech",
        skills=["PLUMBING"],
        skill_expertise={"PLUMBING": 5},
        region="NORTH_ZONE",
        latitude=12.9716,
        longitude=77.5946,
        availability_start="08:00",
        availability_end="17:00",
        is_active=True,
    )
    req = ServiceRequest(
        id="req_2",
        customer_name="HVAC Repair",
        location_name="Site 2",
        region="NORTH_ZONE",
        latitude=12.9720,
        longitude=77.5950,
        required_skills=["HVAC"],
        min_expertise=1,
    )

    result = AssignmentEngine.evaluate_candidates(req, [tech])
    assert len(result.eligible_candidates) == 0
    assert len(result.ineligible_candidates) == 1
    assert "Missing required skill(s): HVAC" in result.ineligible_candidates[0].reasons[0]


def test_insufficient_expertise_fails_eligibility():
    tech = Technician(
        id="tech_3",
        name="Junior Tech",
        skills=["HVAC"],
        skill_expertise={"HVAC": 2},
        region="NORTH_ZONE",
        latitude=12.9716,
        longitude=77.5946,
        is_active=True,
    )
    req = ServiceRequest(
        id="req_3",
        customer_name="Expert HVAC Required",
        location_name="Site 3",
        region="NORTH_ZONE",
        latitude=12.9720,
        longitude=77.5950,
        required_skills=["HVAC"],
        min_expertise=5,
    )

    result = AssignmentEngine.evaluate_candidates(req, [tech])
    assert len(result.eligible_candidates) == 0
    assert "Insufficient expertise for HVAC" in result.ineligible_candidates[0].reasons[0]


def test_inactive_technician_fails_eligibility():
    tech = Technician(
        id="tech_4",
        name="Inactive Tech",
        skills=["HVAC"],
        skill_expertise={"HVAC": 4},
        region="NORTH_ZONE",
        is_active=False,
    )
    req = ServiceRequest(
        id="req_4",
        customer_name="Site 4",
        region="NORTH_ZONE",
        required_skills=["HVAC"],
    )

    result = AssignmentEngine.evaluate_candidates(req, [tech])
    assert len(result.eligible_candidates) == 0
    assert "INACTIVE" in result.ineligible_candidates[0].reasons[0]


def test_wrong_region_fails_eligibility():
    tech = Technician(
        id="tech_5",
        name="South Tech",
        skills=["HVAC"],
        skill_expertise={"HVAC": 4},
        region="SOUTH_ZONE",
        is_active=True,
    )
    req = ServiceRequest(
        id="req_5",
        customer_name="North Site",
        region="NORTH_ZONE",
        required_skills=["HVAC"],
    )

    result = AssignmentEngine.evaluate_candidates(req, [tech])
    assert len(result.eligible_candidates) == 0
    assert "Region mismatch" in result.ineligible_candidates[0].reasons[0]


def test_distance_soft_factor_does_not_override_hard_constraint():
    # Tech A is 0.1km away but lacks skill
    tech_a = Technician(
        id="tech_near_noskill",
        name="Near Tech No Skill",
        skills=["PLUMBING"],
        region="NORTH_ZONE",
        latitude=12.9720,
        longitude=77.5950,
        is_active=True,
    )
    # Tech B is 5km away with valid skill
    tech_b = Technician(
        id="tech_far_skilled",
        name="Far Tech Skilled",
        skills=["HVAC"],
        skill_expertise={"HVAC": 4},
        region="NORTH_ZONE",
        latitude=12.9300,
        longitude=77.5950,
        is_active=True,
    )

    req = ServiceRequest(
        id="req_dist_test",
        customer_name="Site Dist Test",
        region="NORTH_ZONE",
        latitude=12.9721,
        longitude=77.5951,
        required_skills=["HVAC"],
    )

    result = AssignmentEngine.evaluate_candidates(req, [tech_a, tech_b])
    assert len(result.eligible_candidates) == 1
    assert result.eligible_candidates[0].technician_id == "tech_far_skilled"
    assert len(result.ineligible_candidates) == 1
    assert result.ineligible_candidates[0].technician_id == "tech_near_noskill"


def test_no_eligible_technician_handled_safely():
    req = ServiceRequest(
        id="req_impossible",
        customer_name="Impossible Job",
        region="NORTH_ZONE",
        required_skills=["QUANTUM_COMPUTING"],
    )
    result = AssignmentEngine.evaluate_candidates(req, [])
    assert len(result.eligible_candidates) == 0
    assert len(result.ineligible_candidates) == 0
