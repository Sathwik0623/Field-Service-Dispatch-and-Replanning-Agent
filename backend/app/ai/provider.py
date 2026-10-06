import time
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

from app.core.config import settings
from app.ai.schemas import (
    AIPlanningProposal,
    AIProposedAssignment,
    RiskFactor,
    ClarificationQuestion,
    TradeoffAnalysis,
    AIObservabilityMetadata,
)


class BaseAIProvider(ABC):
    """Abstract base class for LLM planning providers."""

    @abstractmethod
    def generate_proposal(
        self,
        system_prompt: str,
        user_context: str,
        requests: List[Dict[str, Any]],
        technicians: List[Dict[str, Any]],
        deterministic_evaluations: Dict[str, Any],
    ) -> Tuple[AIPlanningProposal, AIObservabilityMetadata]:
        pass


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI Provider integration using structured outputs.
    Falls back gracefully if API call fails.
    """

    def generate_proposal(
        self,
        system_prompt: str,
        user_context: str,
        requests: List[Dict[str, Any]],
        technicians: List[Dict[str, Any]],
        deterministic_evaluations: Dict[str, Any],
    ) -> Tuple[AIPlanningProposal, AIObservabilityMetadata]:
        start_time = time.time()
        # If no real API key is set, delegate to MockAIProvider safely
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your_"):
            mock_p = MockAIProvider()
            return mock_p.generate_proposal(
                system_prompt, user_context, requests, technicians, deterministic_evaluations
            )

        try:
            import httpx

            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            }

            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0,
            )

            latency_ms = round((time.time() - start_time) * 1000, 2)

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                
                proposal = AIPlanningProposal(
                    proposal_id=str(uuid.uuid4()),
                    assignments=[AIProposedAssignment(**a) for a in parsed.get("assignments", [])],
                    unassigned_requests=parsed.get("unassigned_requests", []),
                    risks=[RiskFactor(**r) for r in parsed.get("risks", [])],
                    clarification_questions=[ClarificationQuestion(**q) for q in parsed.get("clarification_questions", [])],
                    tradeoffs=[TradeoffAnalysis(**t) for t in parsed.get("tradeoffs", [])],
                    reasoning_summary=parsed.get("reasoning_summary", "LLM schedule optimization generated successfully."),
                    is_mock=False,
                )

                usage = data.get("usage", {})
                obs = AIObservabilityMetadata(
                    provider="openai",
                    model_name=settings.LLM_MODEL,
                    latency_ms=latency_ms,
                    proposed_count=len(proposal.assignments),
                    validated_count=0,
                    rejected_count=0,
                    is_mock=False,
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                )
                return proposal, obs

        except Exception as exc:
            print(f"[AI Provider Error] Falling back to Mock Provider: {str(exc)}")

        # Fallback to Mock Provider if HTTP or parsing fails
        mock_p = MockAIProvider()
        return mock_p.generate_proposal(
            system_prompt, user_context, requests, technicians, deterministic_evaluations
        )


class MockAIProvider(BaseAIProvider):
    """
    Deterministic Mock AI Provider for zero-dependency local development and testing.
    Clearly tags outputs with is_mock=True.
    """

    def generate_proposal(
        self,
        system_prompt: str,
        user_context: str,
        requests: List[Dict[str, Any]],
        technicians: List[Dict[str, Any]],
        deterministic_evaluations: Dict[str, Any],
    ) -> Tuple[AIPlanningProposal, AIObservabilityMetadata]:
        start_time = time.time()
        proposal_id = f"prop_ai_mock_{str(uuid.uuid4())[:8]}"

        proposed_assignments: List[AIProposedAssignment] = []
        unassigned_requests: List[str] = []
        risks: List[RiskFactor] = []
        clarifications: List[ClarificationQuestion] = []
        tradeoffs: List[TradeoffAnalysis] = []

        # Track end time in minutes for technicians to avoid proposing overlapping time slots
        tech_time_slots: Dict[str, int] = {}

        for req in requests:
            req_id = req.get("id")
            eval_res = deterministic_evaluations.get(req_id, {})
            eligible = eval_res.get("eligible_candidates", [])

            chosen_cand = None
            chosen_start_str = ""
            chosen_end_str = ""

            for cand in eligible:
                t_id = cand.get("technician_id")
                dur = req.get("estimated_duration_hours", 2.0)
                dur_mins = int(dur * 60)

                pref_start = req.get("preferred_start", "08:00")
                start_mins = int(pref_start.split(":")[0]) * 60 + int(pref_start.split(":")[1])

                if t_id in tech_time_slots:
                    start_mins = max(start_mins, tech_time_slots[t_id] + 15)

                end_mins = start_mins + dur_mins

                tech_obj = next((t for t in technicians if t.get("id") == t_id), {})
                shift_end_str = tech_obj.get("availability_end", "17:00")
                shift_end_mins = int(shift_end_str.split(":")[0]) * 60 + int(shift_end_str.split(":")[1])

                if end_mins <= shift_end_mins:
                    chosen_cand = cand
                    chosen_start_str = f"{(start_mins // 60):02d}:{(start_mins % 60):02d}"
                    chosen_end_str = f"{(end_mins // 60):02d}:{(end_mins % 60):02d}"
                    tech_time_slots[t_id] = end_mins
                    break

            if chosen_cand:
                tech_id = chosen_cand.get("technician_id")
                tech_name = chosen_cand.get("technician_name")
                score = chosen_cand.get("score")
                dist = chosen_cand.get("distance_km")

                proposed_assignments.append(
                    AIProposedAssignment(
                        service_request_id=req_id,
                        technician_id=tech_id,
                        proposed_start=chosen_start_str,
                        proposed_end=chosen_end_str,
                        rationale=f"Selected {tech_name} ({tech_id}) with top deterministic ranking score of {score}/100. Tech is {dist}km away in region {req.get('region')}.",
                        confidence=0.92,
                        relevant_factors=["Skill Expertise", "Geographical Proximity", "Workload Capacity"],
                    )
                )

                if score < 70.0:
                    tradeoffs.append(
                        TradeoffAnalysis(
                            factor="Expertise/Proximity Balance",
                            decision_taken=f"Assigned {tech_name} to {req_id}",
                            tradeoff_explanation=f"Accepted lower composite score ({score}) to maintain regional shift coverage.",
                        )
                    )
            else:
                unassigned_requests.append(req_id)
                ineligible = eval_res.get("ineligible_candidates", [])
                reasons = []
                for in_c in ineligible[:2]:
                    reasons.extend(in_c.get("reasons", []))

                risks.append(
                    RiskFactor(
                        category="Unassigned Ticket Risk",
                        description=f"Request {req_id} ({req.get('customer_name')}) could not be assigned. Reasons: {'; '.join(reasons[:2]) if reasons else 'No active candidates in region'}",
                        severity="HIGH" if req.get("priority") in ["HIGH", "CRITICAL"] else "MEDIUM",
                        affected_requests=[req_id],
                    )
                )

                clarifications.append(
                    ClarificationQuestion(
                        id=f"q_{req_id}",
                        question=f"Can request {req_id} be rescheduled to an adjacent region or alternative time window?",
                        context=f"Request requires {req.get('required_skills')} Level {req.get('min_expertise')} in {req.get('region')}.",
                        target_entity=req_id,
                    )
                )

        latency_ms = round((time.time() - start_time) * 1000, 2)

        proposal = AIPlanningProposal(
            proposal_id=proposal_id,
            assignments=proposed_assignments,
            unassigned_requests=unassigned_requests,
            risks=risks,
            clarification_questions=clarifications,
            tradeoffs=tradeoffs,
            reasoning_summary=f"AI Dispatch Plan generated via Mock AI Provider (Development). Proposed {len(proposed_assignments)} valid candidate assignments with {len(unassigned_requests)} unassigned ticket risks.",
            is_mock=True,
        )

        obs = AIObservabilityMetadata(
            provider="mock-ai-provider-development",
            model_name="mock-gpt-4o-dev",
            latency_ms=latency_ms,
            proposed_count=len(proposed_assignments),
            validated_count=0,
            rejected_count=0,
            is_mock=True,
            prompt_tokens=150,
            completion_tokens=220,
        )

        return proposal, obs
