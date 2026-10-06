# AGENT USAGE & AI ASSISTANCE LOG

## Overview

This project was developed with assistance from Google DeepMind's **Antigravity AI Agentic Assistant**. 

The core development philosophy maintained throughout this collaboration is:
> **AI proposes & accelerates implementation → Deterministic backend code & tests validate correctness → Human engineer reviews & approves.**

---

## 1. Tools & Runtimes Used

- **AI Assistant**: Antigravity (Powered by Gemini 3.6 Flash)
- **Primary Tools Invoked**:
  - `run_command` (powershell environment inspection, virtualenv setup, alembic migrations, pytest executions, vite builds)
  - `write_to_file` & `replace_file_content` (modular file creation and incremental edits)
  - `list_dir` & `view_file` (workspace inspection)

---

## 2. Representative Prompts

- **Phase 1 Foundation Prompt**:
  > *"Establish a clean, production-oriented project foundation for the Field Service Dispatch and Replanning Agent. Create a modular monolith structure with FastAPI backend, SQLAlchemy database session, Alembic migrations, React + TypeScript frontend, pytest test framework, environment configuration, health endpoint, architecture docs, and README."*

- **Phase 2 Deterministic Core Prompt**:
  > *"Implement Phase 2 of the Field Service Dispatch and Replanning Agent project. Build the domain models, Alembic migration, seed data, deterministic assignment engine with 7 hard constraints and 5-factor scoring model, scheduling engine with travel buffers and versioning, REST API endpoints, functional React UI, and automated Pytest test cases."*

- **Phase 3 AI Planning Agent & Human-in-the-Loop Prompt**:
  > *"Implement Phase 3 of the Field Service Dispatch and Replanning Agent project: AI Planning Agent, structured AI proposals, deterministic validator, trade-off explanations, risk/unassigned request analysis, missing-information questions, dispatcher approval/rejection/modification workflow, technician accept/decline workflow, emergency ticket insertion, technician cancellation replanning, mock notifications, AI observability, Pytest test suite, and React UI."*

- **Phase 4 Hardening & Audit Prompt**:
  > *"Perform end-to-end technical audit and hardening of the Field Service Dispatch and Replanning Agent before submission. Verify deterministic validation boundary, prompt injection isolation, double-approval prevention, mandatory rejection reasons, stale proposal detection, full Pytest suite (31 tests), and Vite frontend build."*

- **Phase 5 Deployment Readiness Prompt**:
  > *"Prepare deployment and production configuration. Create backend Dockerfile, docker-compose.yml for PostgreSQL orchestration, configure dynamic PORT binding in FastAPI, add CORS_ORIGINS validator in Pydantic settings, update README deployment documentation, and verify deployment readiness."*

---

## 3. Work Delegated to AI in Phase 4 & Phase 5

1. **Hardening & Edge Case Fixes**:
   - Added proposal state guards in `AIPipelinesService` (`approve_proposal` and `reject_proposal`) to prevent duplicate approvals/rejections and race conditions.
   - Enforced mandatory rejection reason string validation.
   - Added Rule 7 for untrusted context isolation in `SYSTEM_PROMPT` (`prompts.py`).
   - Fixed unused TypeScript imports across React components.
2. **Production Containerization & Configuration**:
   - Built `backend/Dockerfile` with Python 3.10 slim runtime and `psycopg2-binary` system libraries.
   - Created `docker-compose.yml` orchestrating PostgreSQL 15 and FastAPI containerized services.
   - Configured `CORS_ORIGINS` validator in `config.py` supporting JSON array strings or comma-separated origin lists.
   - Added dynamic `PORT` binding in `app/main.py`.
3. **Comprehensive Verification**:
   - Expanded backend Pytest suite to 31 passing unit/integration tests.
   - Verified Vite production build (`dist/`) output.

---

## 4. AI Mistakes & Rejected Suggestions (Log)

- **Issue 1**: Proposal re-approval race condition allowed duplicate schedule version creation.
  - *Detail*: `approve_proposal` did not check if `record.status` was already `APPROVED`.
  - *Correction*: Added state validation check enforcing proposals must be in `DRAFT` or `VALIDATED` state before approval or rejection.
- **Issue 2**: String parsing error for `CORS_ORIGINS` when passed as comma-separated string in environment variables.
  - *Detail*: Pydantic `List[str]` default failed when string `"http://localhost:5173,http://localhost:3000"` was provided in `.env`.
  - *Correction*: Added `@field_validator("CORS_ORIGINS", mode="before")` in `config.py`.

---

## 5. Verification Process

1. **Automated Backend Test Suite**:
   - Command: `$env:PYTHONPATH="backend"; .\backend\.venv\Scripts\pytest.exe tests`
   - Result: **31 passed** in 0.94s.
2. **Automated Frontend Production Build**:
   - Command: `npm run build` in `frontend/`
   - Result: `tsc -b` and `vite build` completed cleanly, generating `dist/` bundle.
3. **Alembic Migration Verification**:
   - Command: `alembic -c backend/alembic.ini current`
   - Result: `654c737578d9 (head)`.

---

## 6. Phase Status

| Phase | Scope | Status |
|-------|-------|--------|
| **Phase 1** | Monolith Foundation | **COMPLETED & APPROVED** |
| **Phase 2** | Deterministic Core & Rules Engine | **COMPLETED & APPROVED** |
| **Phase 3** | AI Planning Agent & Human-in-the-Loop Workflow | **COMPLETED & VERIFIED** |
| **Phase 4** | E2E Hardening & Verification | **COMPLETED & VERIFIED** |
| **Phase 5** | Deployment & Production Readiness | **COMPLETED & VERIFIED** |
