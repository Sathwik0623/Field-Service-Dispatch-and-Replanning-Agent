from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.domain.models import PriorityEnum, RequestStatusEnum, AssignmentStatusEnum


# --- Technician Schemas ---
class TechnicianCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Ravi Kumar"})
    skills: List[str] = Field(..., json_schema_extra={"example": ["HVAC", "ELECTRICAL"]})
    skill_expertise: Dict[str, int] = Field(..., json_schema_extra={"example": {"HVAC": 4, "ELECTRICAL": 5}})
    region: str = Field(..., json_schema_extra={"example": "NORTH_ZONE"})
    latitude: float = Field(..., json_schema_extra={"example": 12.9716})
    longitude: float = Field(..., json_schema_extra={"example": 77.5946})
    availability_start: str = Field("08:00", json_schema_extra={"example": "08:00"})
    availability_end: str = Field("17:00", json_schema_extra={"example": "17:00"})
    max_daily_hours: float = Field(8.0, json_schema_extra={"example": 8.0})
    is_active: bool = True


class TechnicianResponse(TechnicianCreate):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Service Request Schemas ---
class ServiceRequestCreate(BaseModel):
    customer_name: str = Field(..., json_schema_extra={"example": "Acme Corp HQ"})
    location_name: str = Field(..., json_schema_extra={"example": "MG Road Office Park"})
    region: str = Field(..., json_schema_extra={"example": "NORTH_ZONE"})
    latitude: float = Field(..., json_schema_extra={"example": 12.9720})
    longitude: float = Field(..., json_schema_extra={"example": 77.5950})
    required_skills: List[str] = Field(..., json_schema_extra={"example": ["HVAC"]})
    min_expertise: int = Field(1, json_schema_extra={"example": 3})
    priority: PriorityEnum = Field(PriorityEnum.MEDIUM)
    estimated_duration_hours: float = Field(2.0, json_schema_extra={"example": 2.0})
    preferred_start: str = Field("09:00", json_schema_extra={"example": "09:00"})
    preferred_end: str = Field("17:00", json_schema_extra={"example": "17:00"})


class ServiceRequestResponse(ServiceRequestCreate):
    id: str
    status: RequestStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Assignment & Schedule Schemas ---
class AssignmentResponse(BaseModel):
    id: str
    service_request_id: str
    technician_id: str
    schedule_version_id: str
    start_time: str
    end_time: str
    score: float
    score_breakdown: Dict[str, Any]
    status: AssignmentStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlanningProposeRequest(BaseModel):
    request_ids: Optional[List[str]] = None
    created_by: str = "DISPATCHER"
    trigger_reason: str = "Manual Proposal Request"


class PlanningProposeResponse(BaseModel):
    schedule_version_id: str
    version_number: int
    assignments: List[Dict[str, Any]]
    unassigned_requests: List[Dict[str, Any]]
    warnings: List[str]


class ScheduleVersionResponse(BaseModel):
    id: str
    version_number: int
    parent_version_id: Optional[str]
    trigger_reason: str
    created_by: str
    created_at: datetime
    assignments: List[AssignmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    actor: str
    metadata_json: Dict[str, Any]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
