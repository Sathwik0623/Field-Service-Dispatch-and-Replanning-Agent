import pytest
from app.db.seed import seed_database


def test_api_list_and_create_requests(client, db_session):
    seed_database(db_session)

    # 1. List requests
    response = client.get("/api/v1/requests")
    assert response.status_code == 200
    requests_list = response.json()
    assert len(requests_list) >= 11

    # 2. Create new request
    new_req_payload = {
        "customer_name": "API Test Customer",
        "location_name": "Test Office Park",
        "region": "NORTH_ZONE",
        "latitude": 12.9715,
        "longitude": 77.5945,
        "required_skills": ["HVAC"],
        "min_expertise": 2,
        "priority": "HIGH",
        "estimated_duration_hours": 1.5,
        "preferred_start": "10:00",
        "preferred_end": "12:00",
    }
    create_res = client.post("/api/v1/requests", json=new_req_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["customer_name"] == "API Test Customer"
    assert created_data["id"] is not None


def test_api_evaluate_candidates_for_request(client, db_session):
    seed_database(db_session)

    response = client.post("/api/v1/requests/req_101/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "req_101"
    assert "eligible_candidates" in data
    assert "ineligible_candidates" in data
    assert len(data["eligible_candidates"]) > 0


def test_api_list_technicians(client, db_session):
    seed_database(db_session)

    response = client.get("/api/v1/technicians")
    assert response.status_code == 200
    techs = response.json()
    assert len(techs) == 7


def test_api_planning_propose_and_get_schedule(client, db_session):
    seed_database(db_session)

    propose_res = client.post(
        "/api/v1/planning/propose",
        json={"created_by": "API_TESTER", "trigger_reason": "API Verification Run"},
    )
    assert propose_res.status_code == 200
    proposal = propose_res.json()
    assert proposal["schedule_version_id"] is not None

    sched_res = client.get("/api/v1/schedule")
    assert sched_res.status_code == 200
    sched = sched_res.json()
    assert sched["id"] == proposal["schedule_version_id"]


def test_api_audit_logs(client, db_session):
    seed_database(db_session)

    res = client.get("/api/v1/audit")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)


def test_api_not_found_returns_404(client, db_session):
    res = client.get("/api/v1/requests/non_existent_id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
