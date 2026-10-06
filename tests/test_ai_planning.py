import pytest
from app.db.seed import seed_database
from app.domain.models import (
    AIProposalRecord,
    ScheduleVersion,
    Assignment,
    AssignmentStatusEnum,
    ServiceRequest,
    RequestStatusEnum,
    Technician,
    AuditLog,
)
from app.ai.agent import AIPlanningAgent
from app.ai.provider import MockAIProvider
from app.ai.validator import AIProposalValidator
from app.ai.schemas import AIProposedAssignment
from app.ai.service import AIPipelinesService


def test_mock_ai_provider_proposal(db_session):
    seed_database(db_session)
    provider = MockAIProvider()

    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    assert len(proposal.assignments) == 1
    assert proposal.assignments[0].service_request_id == "req_101"
    assert obs.is_mock is True


def test_ai_agent_generate_plan(db_session):
    seed_database(db_session)

    result = AIPlanningAgent.generate_plan(db=db_session)
    assert "proposal" in result
    assert "validation" in result
    assert "observability" in result

    proposal = result["proposal"]
    validation = result["validation"]
    obs = result["observability"]

    assert proposal["proposal_id"] is not None
    assert len(validation["validated_assignments"]) > 0
    assert len(validation["invalid_assignments"]) > 0
    assert obs["proposed_count"] == len(validation["validated_assignments"]) + len(validation["invalid_assignments"])

    # Verify AI Proposal Record saved in DB
    record = db_session.query(AIProposalRecord).filter(AIProposalRecord.id == proposal["proposal_id"]).first()
    assert record is not None


def test_ai_validator_rejects_invalid_skill_or_missing_tech(db_session):
    seed_database(db_session)

    # 1. Invalid skill proposal (assigning tech_vikram [Plumbing] to req_101 [HVAC requiring 3])
    bad_skill_prop = AIProposedAssignment(
        service_request_id="req_101",
        technician_id="tech_vikram",  # Vikram only has Plumbing level 5, HVAC level 2 (req_101 requires 3)
        proposed_start="09:00",
        proposed_end="11:00",
        rationale="Test invalid skill assignment",
    )

    val_res = AIProposalValidator.validate_proposal(db_session, [bad_skill_prop])
    assert val_res.all_valid is False
    assert len(val_res.invalid_assignments) == 1
    assert "Insufficient expertise" in val_res.invalid_assignments[0].rejection_reasons[0]

    # 2. Non-existent technician proposal
    missing_tech_prop = AIProposedAssignment(
        service_request_id="req_101",
        technician_id="non_existent_tech",
        proposed_start="09:00",
        proposed_end="11:00",
        rationale="Test non existent tech",
    )
    val_res2 = AIProposalValidator.validate_proposal(db_session, [missing_tech_prop])
    assert val_res2.all_valid is False
    assert "does not exist in backend database" in val_res2.invalid_assignments[0].rejection_reasons[0]


def test_dispatcher_approval_and_rejection(db_session):
    seed_database(db_session)

    # Generate plan
    plan = AIPlanningAgent.generate_plan(db_session)
    prop_id = plan["proposal"]["proposal_id"]

    # Approve proposal
    appr_res = AIPipelinesService.approve_proposal(db_session, proposal_id=prop_id, actor="DISPATCHER_UNIT_TEST")
    assert appr_res["status"] == "APPROVED"
    assert appr_res["confirmed_count"] > 0

    # Verify audit log recorded DISPATCHER_APPROVED
    audit = db_session.query(AuditLog).filter(AuditLog.event_type == "DISPATCHER_APPROVED").first()
    assert audit is not None


def test_duplicate_approval_rejection_prevention(db_session):
    seed_database(db_session)

    plan = AIPlanningAgent.generate_plan(db_session)
    prop_id = plan["proposal"]["proposal_id"]

    AIPipelinesService.approve_proposal(db_session, proposal_id=prop_id, actor="DISPATCHER_TEST")

    # Second approval attempt must raise ValueError
    with pytest.raises(ValueError, match="cannot be approved"):
        AIPipelinesService.approve_proposal(db_session, proposal_id=prop_id, actor="DISPATCHER_TEST")

    # Rejection attempt on approved proposal must also raise ValueError
    with pytest.raises(ValueError, match="cannot be rejected"):
        AIPipelinesService.reject_proposal(db_session, proposal_id=prop_id, reason="Changed mind", actor="DISPATCHER_TEST")


def test_rejection_requires_reason(db_session):
    seed_database(db_session)

    plan = AIPlanningAgent.generate_plan(db_session)
    prop_id = plan["proposal"]["proposal_id"]

    with pytest.raises(ValueError, match="Rejection reason is required"):
        AIPipelinesService.reject_proposal(db_session, proposal_id=prop_id, reason="", actor="DISPATCHER_TEST")


def test_technician_accept_and_decline_workflow(db_session):
    seed_database(db_session)

    # Approve plan to create confirmed assignment
    plan = AIPlanningAgent.generate_plan(db_session)
    prop_id = plan["proposal"]["proposal_id"]
    appr_res = AIPipelinesService.approve_proposal(db_session, proposal_id=prop_id, actor="DISPATCHER_TEST")

    # Fetch created assignment
    assignment = (
        db_session.query(Assignment)
        .filter(Assignment.schedule_version_id == appr_res["schedule_version_id"])
        .first()
    )
    assert assignment is not None

    # 1. Accept assignment
    accept_res = AIPipelinesService.technician_accept_assignment(
        db_session, assignment_id=assignment.id, technician_id=assignment.technician_id
    )
    assert accept_res["status"] == "CONFIRMED"

    # 2. Decline assignment
    decline_res = AIPipelinesService.technician_decline_assignment(
        db_session,
        assignment_id=assignment.id,
        technician_id=assignment.technician_id,
        reason="Vehicle breakdown",
    )
    assert decline_res["status"] == "DECLINED"
    assert decline_res["reason"] == "Vehicle breakdown"
    assert "replan_proposal" in decline_res


def test_emergency_request_and_technician_cancellation(db_session):
    seed_database(db_session)

    # 1. Emergency request creation
    emerg_res = AIPipelinesService.create_emergency_request_and_replan(
        db=db_session,
        customer_name="Emergency Metro Hospital",
        location_name="ICU Substation",
        region="NORTH_ZONE",
        required_skills=["ELECTRICAL"],
        min_expertise=4,
    )
    assert emerg_res["priority"] == "CRITICAL"
    assert "replan_proposal" in emerg_res

    # 2. Technician cancellation
    cancel_res = AIPipelinesService.cancel_technician_and_replan(
        db=db_session,
        technician_id="tech_ravi",
        reason="Sickness emergency",
    )
    assert cancel_res["status"] == "INACTIVE"
    assert "replan_proposal" in cancel_res


def test_change_explanation_generator():
    before = [
        {"service_request_id": "req_101", "technician_id": "tech_ravi", "start_time": "09:00", "end_time": "11:00"},
        {"service_request_id": "req_102", "technician_id": "tech_arun", "start_time": "11:15", "end_time": "13:00"},
    ]
    after = [
        {"service_request_id": "req_101", "technician_id": "tech_priya", "start_time": "09:00", "end_time": "11:00"},
        {"service_request_id": "req_102", "technician_id": "tech_arun", "start_time": "11:15", "end_time": "13:00"},
    ]

    diff = AIPipelinesService.generate_replanning_change_explanation(
        before_assignments=before,
        after_assignments=after,
        trigger_event="Technician Sickness",
    )
    assert len(diff["changed_assignments"]) == 1
    assert diff["changed_assignments"][0]["service_request_id"] == "req_101"
    assert diff["changed_assignments"][0]["before_technician_id"] == "tech_ravi"
    assert diff["changed_assignments"][0]["after_technician_id"] == "tech_priya"
    assert "req_102" in diff["unchanged_request_ids"]


def test_openai_provider_missing_or_placeholder_key(monkeypatch):
    from app.core.config import settings
    from app.ai.provider import OpenAIProvider

    monkeypatch.setattr(settings, "OPENAI_API_KEY", ' "your_openai_api_key_here" ')
    provider = OpenAIProvider()

    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    assert obs.is_mock is True


def test_openai_provider_successful_200_response(monkeypatch):
    import json
    from app.core.config import settings
    from app.ai.provider import OpenAIProvider
    import httpx

    monkeypatch.setattr(settings, "OPENAI_API_KEY", ' "sk-valid-test-key" ')
    monkeypatch.setattr(settings, "LLM_MODEL", "gpt-4o-mini")

    captured_headers = {}

    def mock_post(url, headers=None, json=None, timeout=None, **kwargs):
        nonlocal captured_headers
        captured_headers = headers or {}
        mock_response_json = {
            "choices": [
                {
                    "message": {
                        "content": json_mod.dumps({
                            "assignments": [
                                {
                                    "service_request_id": "req_101",
                                    "technician_id": "tech_ravi",
                                    "proposed_start": "09:00",
                                    "proposed_end": "11:00",
                                    "rationale": "Top score tech",
                                    "confidence": 0.95,
                                    "relevant_factors": ["Proximity"],
                                }
                            ],
                            "unassigned_requests": [],
                            "risks": [],
                            "clarification_questions": [],
                            "tradeoffs": [],
                            "reasoning_summary": "Optimal dispatch",
                        })
                    }
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        }

        class MockResponse:
            status_code = 200
            text = json_mod.dumps(mock_response_json)
            def json(self):
                return mock_response_json

        return MockResponse()

    import json as json_mod
    monkeypatch.setattr(httpx, "post", mock_post)

    provider = OpenAIProvider()
    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is False
    assert obs.is_mock is False
    assert obs.provider == "openai"
    assert obs.model_name == "gpt-4o-mini"
    assert captured_headers.get("Authorization") == "Bearer sk-valid-test-key"


def test_openai_provider_non_200_response(monkeypatch, capsys):
    from app.core.config import settings
    from app.ai.provider import OpenAIProvider
    import httpx

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-valid-test-key")

    def mock_post(url, headers=None, json=None, timeout=None, **kwargs):
        class MockResponse:
            status_code = 401
            text = '{"error": {"message": "Incorrect API key provided"}}'
        return MockResponse()

    monkeypatch.setattr(httpx, "post", mock_post)

    provider = OpenAIProvider()
    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    captured = capsys.readouterr()
    assert "[AI Provider Error] OpenAI HTTP status 401" in captured.out
    assert "Incorrect API key provided" in captured.out


def test_openai_provider_malformed_200_response(monkeypatch, capsys):
    from app.core.config import settings
    from app.ai.provider import OpenAIProvider
    import httpx

    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-valid-test-key")

    def mock_post(url, headers=None, json=None, timeout=None, **kwargs):
        class MockResponse:
            status_code = 200
            text = '{malformed json'
            def json(self):
                raise ValueError("JSON decode error")
        return MockResponse()

    monkeypatch.setattr(httpx, "post", mock_post)

    provider = OpenAIProvider()
    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    captured = capsys.readouterr()
    assert "[AI Provider Error] Falling back to Mock Provider" in captured.out


def test_gemini_provider_missing_or_placeholder_key(monkeypatch):
    from app.core.config import settings
    from app.ai.provider import GeminiProvider

    monkeypatch.setattr(settings, "GEMINI_API_KEY", ' "your_gemini_api_key_here" ')
    provider = GeminiProvider()

    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    assert obs.is_mock is True


def test_gemini_provider_successful_response(monkeypatch):
    import json
    import google.genai
    from app.core.config import settings
    from app.ai.provider import GeminiProvider

    monkeypatch.setattr(settings, "GEMINI_API_KEY", ' "AIzaSy-valid-gemini-key" ')
    monkeypatch.setattr(settings, "LLM_MODEL", "gemini-2.5-flash")

    class MockUsage:
        prompt_token_count = 120
        candidates_token_count = 60

    class MockGeminiResponse:
        text = json.dumps({
            "assignments": [
                {
                    "service_request_id": "req_101",
                    "technician_id": "tech_ravi",
                    "proposed_start": "09:00",
                    "proposed_end": "11:00",
                    "rationale": "Top score tech",
                    "confidence": 0.95,
                    "relevant_factors": ["Proximity"],
                }
            ],
            "unassigned_requests": [],
            "risks": [],
            "clarification_questions": [],
            "tradeoffs": [],
            "reasoning_summary": "Gemini dispatch proposal",
        })
        usage_metadata = MockUsage()

    class MockModels:
        def generate_content(self, model, contents, config):
            assert model == "gemini-2.5-flash"
            assert config.response_mime_type == "application/json"
            return MockGeminiResponse()

    class MockGenAIClient:
        def __init__(self, api_key):
            assert api_key == "AIzaSy-valid-gemini-key"
            self.models = MockModels()

    monkeypatch.setattr(google.genai, "Client", MockGenAIClient)

    provider = GeminiProvider()
    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is False
    assert obs.is_mock is False
    assert obs.provider == "gemini"
    assert obs.model_name == "gemini-2.5-flash"
    assert obs.prompt_tokens == 120
    assert obs.completion_tokens == 60


def test_gemini_provider_api_failure(monkeypatch, capsys):
    import google.genai
    from app.core.config import settings
    from app.ai.provider import GeminiProvider

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIzaSy-valid-gemini-key")

    class MockGenAIClient:
        def __init__(self, api_key):
            raise Exception("API quota exceeded or invalid key")

    monkeypatch.setattr(google.genai, "Client", MockGenAIClient)

    provider = GeminiProvider()
    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    captured = capsys.readouterr()
    assert "[AI Provider Error] Gemini API error: API quota exceeded" in captured.out


def test_gemini_provider_malformed_json_response(monkeypatch, capsys):
    import google.genai
    from app.core.config import settings
    from app.ai.provider import GeminiProvider

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "AIzaSy-valid-gemini-key")

    class MockGeminiResponse:
        text = "{bad json string"
        usage_metadata = None

    class MockModels:
        def generate_content(self, model, contents, config):
            return MockGeminiResponse()

    class MockGenAIClient:
        def __init__(self, api_key):
            self.models = MockModels()

    monkeypatch.setattr(google.genai, "Client", MockGenAIClient)

    provider = GeminiProvider()
    reqs = [{"id": "req_101", "customer_name": "Acme", "region": "NORTH_ZONE", "required_skills": ["HVAC"], "min_expertise": 3}]
    techs = [{"id": "tech_ravi", "name": "Ravi", "region": "NORTH_ZONE", "skills": ["HVAC"], "skill_expertise": {"HVAC": 4}}]
    evals = {"req_101": {"eligible_candidates": [{"technician_id": "tech_ravi", "technician_name": "Ravi", "score": 90.0, "distance_km": 1.2}]}}

    proposal, obs = provider.generate_proposal("sys", "usr", reqs, techs, evals)
    assert proposal.is_mock is True
    captured = capsys.readouterr()
    assert "[AI Provider Error] Gemini API error" in captured.out


def test_ai_agent_provider_selection_gemini(db_session, monkeypatch):
    from app.core.config import settings
    from app.db.seed import seed_database

    seed_database(db_session)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    result = AIPlanningAgent.generate_plan(db=db_session)
    assert "proposal" in result
    assert "observability" in result
    assert result["observability"]["is_mock"] is True
