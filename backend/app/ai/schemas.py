from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class AIProposedAssignment(BaseModel):
    service_request_id: str = Field(..., description="ID of the service request")
    technician_id: str = Field(..., description="ID of the assigned technician")
    proposed_start: str = Field(..., description="Start time in HH:MM format")
    proposed_end: str = Field(..., description="End time in HH:MM format")
    rationale: str = Field(..., description="Natural language reasoning for choosing this candidate")
    confidence: float = Field(0.9, description="Confidence score between 0.0 and 1.0")
    relevant_factors: List[str] = Field(default_factory=list, description="Key operational factors considered")


class RiskFactor(BaseModel):
    category: str = Field(..., json_schema_extra={"example": "Capacity Risk"})
    description: str = Field(..., json_schema_extra={"example": "REQ-111 cannot be fulfilled due to missing nuclear certification."})
    severity: str = Field("HIGH", json_schema_extra={"example": "HIGH"})
    affected_requests: List[str] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    context: str
    target_entity: str


class TradeoffAnalysis(BaseModel):
    factor: str
    decision_taken: str
    tradeoff_explanation: str


class AIPlanningProposal(BaseModel):
    proposal_id: str
    base_schedule_version_id: Optional[str] = None
    assignments: List[AIProposedAssignment] = Field(default_factory=list)
    unassigned_requests: List[str] = Field(default_factory=list)
    risks: List[RiskFactor] = Field(default_factory=list)
    clarification_questions: List[ClarificationQuestion] = Field(default_factory=list)
    tradeoffs: List[TradeoffAnalysis] = Field(default_factory=list)
    reasoning_summary: str = ""
    is_mock: bool = False
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ValidatedAssignment(BaseModel):
    service_request_id: str
    technician_id: str
    proposed_start: str
    proposed_end: str
    rationale: str
    confidence: float
    is_valid: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    score: float = 0.0
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)


class AIValidationResult(BaseModel):
    proposal_id: str
    all_valid: bool
    validated_assignments: List[ValidatedAssignment] = Field(default_factory=list)
    invalid_assignments: List[ValidatedAssignment] = Field(default_factory=list)
    validation_summary: str = ""


class AIObservabilityMetadata(BaseModel):
    provider: str
    model_name: str
    latency_ms: float
    proposed_count: int
    validated_count: int
    rejected_count: int
    is_mock: bool = False
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
