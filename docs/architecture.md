# Field Service Dispatch and Replanning Agent - System Architecture

## 1. System Overview

The **Field Service Dispatch and Replanning Agent** is an AI-assisted field-service management platform designed to automate, optimize, and replan complex technician schedules under real-world operational constraints.

The system adheres strictly to the architectural core principle:

> **LLM proposes → Deterministic backend validates → Human dispatcher reviews/modifies → Technician accepts/declines → Confirmed/Replanned**

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Web Dispatcher UI (React / TS)                    │
│   (Dashboard, Request Creator, AI Planner, Replanning View, Timeline)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API
┌───────────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Modular Monolith)                   │
├────────────────────────────────────────────────────────────────────────┤
│  [API Routers] ──> [AI Planning Agent] ──> [AI Proposal Validator]     │
│       │                    │                       │                   │
│       ▼                    ▼                       ▼                   │
│  [Assignment Engine] ──> [Provider]      [Hard Constraint Filter]      │
│       │                                            │                   │
│       ▼                                            ▼                   │
│  [Scheduling Engine] ───────────────>  [Travel Buffer & Versioning]    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ ORM Sessions
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL / SQLite Database                      │
│   (Technicians, ServiceRequests, ScheduleVersions, Assignments,        │
│    AIProposals, Notifications, AuditLogs)                              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Layer (Phase 1, Phase 2 & Phase 3 Complete)

- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Vanilla CSS with dark mode, glassmorphism, responsive grid system, and Inter typography.
- **Views**:
  - **Dashboard**: High-level operational readiness, system infrastructure status, active technician roster counts, ticket priority metrics, dispatch proposal trigger, and audit activity feed.
  - **AI Dispatch Planner**: Comprehensive AI proposal generator displaying proposed assignments, deterministic validation status badges (`VALIDATED` vs `INVALID`), AI trade-off explanations, risk assessments, missing-information questions, approval/rejection triggers, and inline assignment modification forms.
  - **Replanning & Emergency Workspace**: Emergency ticket creation (CRITICAL priority insertion), simulated technician cancellation trigger (reassigning future jobs while preserving completed jobs), side-by-side diff explanation of schedule changes, and replan approval actions.
  - **Service Requests**: Detailed table of service tickets with status badges, priority badges, skill tags, time windows, request creation modal, and an interactive candidate evaluation modal.
  - **Technician Roster**: Roster management with region filtering, skill & expertise ratings, shift availability hours, max daily workload, and technician registration form.
  - **Schedule Timeline & Versioning**: Visual day grid displaying color-coded assignment blocks per technician, schedule version selector, and ranking rationale breakdowns.

---

## 3. Backend Architecture & AI Layer (Phase 3 Complete)

- **Framework**: Python 3.10 + FastAPI + Pydantic v2
- **Structure**:
  - `app/ai/agent.py`: `AIPlanningAgent` orchestrating context creation, provider invocation, validation, and audit recording.
  - `app/ai/provider.py`: `AIProviderInterface` with `OpenAIProvider` (`gpt-4o-mini`) and `MockAIProvider` (zero-dependency fallback).
  - `app/ai/validator.py`: `AIProposalValidator` re-evaluating every AI proposed assignment against all backend hard constraints.
  - `app/ai/service.py`: `AIPipelinesService` handling dispatcher approval, rejection, manual overrides, technician notifications, accept/decline, emergency tickets, and schedule diff generation.
  - `app/ai/schemas.py`: Pydantic structured output models for proposals, risks, trade-offs, questions, and validation results.
  - `app/services/assignment_engine.py`: Hard constraint evaluation & candidate ranking engine.
  - `app/services/scheduling_engine.py`: Schedule generation & versioning engine.

---

## 4. Deterministic Validation Boundary & Rules

Hard constraints are evaluated **BEFORE** LLM proposals and **RE-VALIDATED** after LLM proposals:

1. **Active Status**: Technician must be `is_active == True`.
2. **Required Skill**: Technician must possess all required skills specified in the request.
3. **Skill Expertise Level**: Technician's skill rating must meet or exceed `min_expertise`.
4. **Region Match**: Technician region must match the request location region.
5. **Shift Availability**: Preferred request time window must fall within technician's shift (`availability_start` to `availability_end`).
6. **Workload Limit**: Technician's current assigned hours + estimated job duration must not exceed `max_daily_hours`.
7. **Schedule Overlap & Travel Buffer**: Job window must not conflict with existing confirmed assignments + travel buffer.

If ANY proposed assignment fails validation, it is marked `INVALID` with exact violation details. The LLM cannot bypass these rules.

---

## 5. Human-in-the-Loop & Replanning Workflow

1. **AI Proposes**: LLM generates `DRAFT` plan with trade-offs, risks, and proposed assignments.
2. **Backend Validates**: Validator tags assignments as `VALID` or `INVALID`.
3. **Dispatcher Reviews**: Dispatcher views plan, risks, questions, and trade-off rationales. Dispatcher can Approve, Reject (with reason), or Modify (re-validates modified assignment).
4. **Technician Notification & Response**: Mock notification sent to technician. Technician accepts or declines (declines require a reason and trigger replanning).
5. **Emergency / Cancellation Replanning**: Creating an emergency ticket or marking a technician inactive triggers AI replanning. Completed assignments remain locked while future assignments are dynamically re-routed to available technicians.
