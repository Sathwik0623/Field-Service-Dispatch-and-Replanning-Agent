# Field Service Dispatch and Replanning Agent

> **Phase 1, Phase 2 & Phase 3 Complete**: Fully functional AI-assisted field service dispatch platform with deterministic validation, AI planning proposals, human-in-the-loop review, dispatcher overrides, technician accept/decline workflows, emergency replanning, mock notifications, schedule versioning, and AI observability.

---

## Project Overview

The **Field Service Dispatch and Replanning Agent** is an AI-assisted field-service management platform. It matches service requests to technicians, enforces deterministic hard constraints (skills, availability, shift boundaries, region, workload limits), ranks eligible technicians using operational metrics, generates AI dispatches, allows human-in-the-loop dispatcher approvals/modifications, handles emergency replanning, and maintains complete audit logging and schedule version histories.

### Core Architectural Principle

$$\text{LLM proposes} \longrightarrow \text{Deterministic backend validates} \longrightarrow \text{Human dispatcher reviews/modifies} \longrightarrow \text{Technician accepts/declines} \longrightarrow \text{Confirmed/Replanned}$$

- **Deterministic Backend**: Authoritative source of truth enforcing strict hard constraints, eligibility, travel buffers, workload limits, double-booking prevention, and persistence.
- **AI/LLM Agent**: Advisory planning layer that proposes feasible dispatches, explains trade-offs in natural language, identifies risks, and asks clarification questions.
- **Human Dispatcher & Technician**: Final approval and acceptance authority. The LLM NEVER directly confirms an assignment.

---

## Repository Structure

```
Field Service Dispatch and Replanning Agent/
├── backend/                  # FastAPI Modular Monolith Backend
│   ├── app/
│   │   ├── ai/               # Phase 3 AI Module
│   │   │   ├── agent.py      # AIPlanningAgent orchestrator
│   │   │   ├── provider.py   # OpenAIProvider & MockAIProvider
│   │   │   ├── prompts.py    # System prompt & structured context builder
│   │   │   ├── schemas.py    # Pydantic structured output models
│   │   │   ├── service.py    # AIPipelinesService (approval, replanning, diffs)
│   │   │   └── validator.py  # AIProposalValidator (backend hard constraint checker)
│   │   ├── api/              # REST API Routers
│   │   │   └── v1/           # requests, technicians, planning, ai_planning, schedules, audit, health
│   │   ├── core/             # Pydantic settings & config
│   │   ├── db/               # SQLAlchemy session management & seed data
│   │   ├── domain/           # SQLAlchemy models & enums (incl. AIProposalRecord, Notification)
│   │   └── services/         # Deterministic dispatch & scheduling engines
│   ├── alembic/              # Alembic database migrations
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React + TypeScript + Vite Web Application
│   ├── src/
│   │   ├── components/       # Header, Navigation, AIPlannerView, ReplanningView, DashboardView, etc.
│   │   ├── config.ts         # Environment API URL configuration
│   │   └── types.ts          # TypeScript interfaces
│   └── package.json          # Node dependencies & scripts
├── tests/                    # Backend Pytest Test Suite (31 tests)
│   ├── test_ai_planning.py   # AI planning, validation, mock provider, approval, replanning tests
│   ├── test_assignment_engine.py
│   ├── test_scheduling_engine.py
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_db.py
│   └── test_health.py
├── docs/
│   └── architecture.md       # Detailed system architecture document
├── .env.example              # Environment variables template
├── README.md                 # Project documentation
└── AGENT_USAGE.md            # AI coding assistant log & verification rules
```

---

## Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Lucide React, Glassmorphism & Dark Theme CSS
- **Backend**: Python 3.10, FastAPI, Pydantic v2, Pydantic Settings
- **AI Integration**: Structured Output JSON, OpenAI API (`gpt-4o-mini` default), Zero-dependency Mock Provider fallback
- **Database & ORM**: SQLite / PostgreSQL (SQLAlchemy 2.0 ORM, Alembic Migrations)
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## AI Architecture & Provider Configuration

The AI planning agent utilizes a structured proposal pipeline:

1. **Context Building**: The backend builds structured JSON context containing active service requests, technician workloads/skills, and deterministic candidate rankings.
2. **Provider Execution**: Invokes configured provider (`OPENAI` or `MOCK`).
   - If `OPENAI_API_KEY` is provided in `.env`, connects to OpenAI API.
   - If key is absent/unavailable, seamlessly falls back to `MockAIProvider` (explicitly tagged as `mock-development-planner`).
3. **Deterministic Validation**: `AIProposalValidator` checks every proposed assignment against all backend hard constraints (skills, expertise, shift, region, travel buffer, workload, double-booking).
4. **Human Review**: Dispatcher approves, rejects with reason, or manually modifies assignments before persistence.

---

## Quick Start & Local Development

### 1. Backend Setup & Run

1. Activate virtual environment and install dependencies:
   ```powershell
   # Activate environment (Windows PowerShell)
   .\backend\.venv\Scripts\Activate.ps1

   # Install dependencies
   pip install -r backend/requirements.txt
   ```

2. Run Database Migrations & Seed Data:
   ```powershell
   $env:PYTHONPATH="backend"
   .\backend\.venv\Scripts\alembic.exe upgrade head
   python -m app.db.seed
   ```

3. Launch FastAPI Development Server:
   ```powershell
   python -m app.main
   ```
   API runs at `http://localhost:8000`. Swagger API docs: `http://localhost:8000/docs`.

### 2. Frontend Setup & Run

1. Install Node dependencies & launch dev server:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Frontend runs at `http://localhost:5173`.

### 3. Verification Commands

- **Backend Pytest Suite (31 tests)**:
  ```powershell
  $env:PYTHONPATH="backend"
  .\backend\.venv\Scripts\pytest.exe tests
  ```
- **Frontend Production Build**:
  ```powershell
  cd frontend
  npm run build
  ```

---

## Deployment & Production Setup (Render)

### 1. Deployment Architecture

- **Frontend Static Site**: React + TypeScript + Vite static site (`frontend/dist`), deployed on Render Static Site with `VITE_API_BASE_URL` set to the backend API URL.
- **Backend Web Service**: FastAPI modular monolith deployed as a Docker Web Service on Render (`backend/Dockerfile`), listening on `0.0.0.0:${PORT}` with health check endpoint `/health`.
- **Database**: Render Managed PostgreSQL Database (`postgresql://<user>:<password>@<host>:5432/<database>`).
- **Blueprint Spec**: `render.yaml` infrastructure-as-code specification provided at project root for automated 1-click Blueprint deployment on Render.
- **AI Integration**: Backend-only integration via `OPENAI_API_KEY` with automatic fallback to zero-dependency `MockAIProvider` when unconfigured.

### 2. Docker Compose Deployment (Local Production Verification)

To spin up the local containerized stack (PostgreSQL database + FastAPI backend service):

```powershell
docker-compose up --build -d
```

Database migrations run via:
```powershell
docker-compose exec backend alembic -c backend/alembic.ini upgrade head
```

Optional demo seed data creation:
```powershell
docker-compose exec backend python -m app.db.seed
```

### 3. Production Environment Variables (Render)

Configure the following environment variables in Render Dashboard or `.env`:

```env
APP_ENV=production
DEBUG=False
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>
CORS_ORIGINS=["https://your-frontend-site.onrender.com","http://localhost:5173"]
VITE_API_BASE_URL=https://your-backend-service.onrender.com
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key_here
```

---

## License & Notes

Developed as part of the Aggroso Full Stack Development Intern Assessment.
