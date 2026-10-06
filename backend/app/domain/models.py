from datetime import datetime, time
import enum
import uuid
from typing import Dict, List, Any, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Time,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class PriorityEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequestStatusEnum(str, enum.Enum):
    UNASSIGNED = "UNASSIGNED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AssignmentStatusEnum(str, enum.Enum):
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ApprovalDecisionEnum(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class AIProposalStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    skills = Column(JSON, nullable=False, default=list)  # e.g., ["HVAC", "ELECTRICAL"]
    skill_expertise = Column(JSON, nullable=False, default=dict)  # e.g., {"HVAC": 4, "ELECTRICAL": 5}
    region = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    availability_start = Column(String(10), nullable=False, default="08:00")  # "HH:MM"
    availability_end = Column(String(10), nullable=False, default="17:00")    # "HH:MM"
    max_daily_hours = Column(Float, nullable=False, default=8.0)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="technician")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    customer_name = Column(String(100), nullable=False)
    location_name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    required_skills = Column(JSON, nullable=False, default=list)  # e.g., ["HVAC"]
    min_expertise = Column(Integer, nullable=False, default=1)
    priority = Column(SQLEnum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM, index=True)
    estimated_duration_hours = Column(Float, nullable=False, default=2.0)
    preferred_start = Column(String(10), nullable=False, default="08:00")  # "HH:MM"
    preferred_end = Column(String(10), nullable=False, default="17:00")    # "HH:MM"
    status = Column(SQLEnum(RequestStatusEnum), nullable=False, default=RequestStatusEnum.UNASSIGNED, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="service_request")


class ScheduleVersion(Base):
    __tablename__ = "schedule_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    version_number = Column(Integer, nullable=False, index=True)
    parent_version_id = Column(String, ForeignKey("schedule_versions.id"), nullable=True)
    trigger_reason = Column(String(255), nullable=False, default="Initial Dispatch")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100), nullable=False, default="SYSTEM")

    assignments = relationship("Assignment", back_populates="schedule_version")
    parent_version = relationship("ScheduleVersion", remote_side=[id])


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String, primary_key=True, default=generate_uuid)
    service_request_id = Column(String, ForeignKey("service_requests.id"), nullable=False, index=True)
    technician_id = Column(String, ForeignKey("technicians.id"), nullable=False, index=True)
    schedule_version_id = Column(String, ForeignKey("schedule_versions.id"), nullable=False, index=True)
    start_time = Column(String(20), nullable=False)  # ISO string or "YYYY-MM-DD HH:MM"
    end_time = Column(String(20), nullable=False)    # ISO string or "YYYY-MM-DD HH:MM"
    score = Column(Float, nullable=False, default=0.0)
    score_breakdown = Column(JSON, nullable=False, default=dict)  # Stores breakdown metrics
    status = Column(SQLEnum(AssignmentStatusEnum), nullable=False, default=AssignmentStatusEnum.PROPOSED, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    service_request = relationship("ServiceRequest", back_populates="assignments")
    technician = relationship("Technician", back_populates="assignments")
    schedule_version = relationship("ScheduleVersion", back_populates="assignments")
    approvals = relationship("Approval", back_populates="assignment")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True, default=generate_uuid)
    assignment_id = Column(String, ForeignKey("assignments.id"), nullable=True, index=True)
    schedule_version_id = Column(String, ForeignKey("schedule_versions.id"), nullable=True, index=True)
    actor = Column(String(100), nullable=False)
    decision = Column(SQLEnum(ApprovalDecisionEnum), nullable=False)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    actor = Column(String(100), nullable=False, default="SYSTEM")
    metadata_json = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class AIProposalRecord(Base):
    __tablename__ = "ai_proposals"

    id = Column(String, primary_key=True, default=generate_uuid)
    base_schedule_version_id = Column(String, ForeignKey("schedule_versions.id"), nullable=True, index=True)
    status = Column(SQLEnum(AIProposalStatusEnum), nullable=False, default=AIProposalStatusEnum.DRAFT, index=True)
    proposal_json = Column(JSON, nullable=False, default=dict)
    validation_result_json = Column(JSON, nullable=False, default=dict)
    observability_json = Column(JSON, nullable=False, default=dict)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    recipient_type = Column(String(50), nullable=False, index=True)  # DISPATCHER or TECHNICIAN
    recipient_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="UNREAD", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
