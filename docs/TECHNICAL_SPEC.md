# Enhanced Autonomous Project Management – Technical Specification

## 1. Overview
A Flask-based, RAG‑assisted autonomous project management platform. The system ingests operational signals (updates, performance), analyzes project health, makes strategic decisions, generates stakeholder communications, and renders executive‑grade dashboards with Plotly. AI orchestration coordinates xLAM (functions/tooling) with Ollama models for complex reasoning and embeddings.

Goals
- API‑first architecture with versioned routes (`/api/v1`)
- Unified data store (SQLite) with extensible schema
- Optional local LLM stack (Ollama) and vector DB (Chroma)
- Executable, demo‑ready POC with professional structure (blueprints, Docker)

Out of scope (POC)
- Authentication/authorization, multi‑tenant concerns
- Production‑grade observability and horizontal scaling

## 2. Architecture
Layers
- Web/UI: Flask app (`flask_app.py`) + Blueprints + Jinja templates + Plotly
- API: REST endpoints under `/api/v1` (JSON)
- Core AI: Orchestrator, Model Manager, Decision Engine, RAG Engine
- Automation: Autonomous project lifecycle controller
- Data: SQLite (`autonomous_projects.db`) + Chroma vector store (optional)

Key Modules
- `enhanced_autonomous_pm/core/ai_orchestrator.py`: Model routing (xLAM, `gpt-oss:20b`, `nomic-embed-text:v1.5`)
- `enhanced_autonomous_pm/core/model_manager.py`: Central xLAM model loading
- `enhanced_autonomous_pm/core/decision_engine.py`: Decision wrapper (legacy engine behind a stable API)
- `enhanced_autonomous_pm/core/rag_engine.py`: Chroma retrieval; stores vectors in `enhanced_autonomous_pm/data/vector_store`
- `autonomous_manager.py`: DB schema + `AutonomousProjectManager` + `FullyAutonomousManager`
- `enhanced_lam_integration.py`: Legacy interface; now prefers `core/ai_orchestrator` when present

UI & Blueprints
- `enhanced_autonomous_pm/interfaces/employee/blueprint.py` → `/employee`
- `enhanced_autonomous_pm/interfaces/manager/blueprint.py` → `/manager`
- `enhanced_autonomous_pm/interfaces/executive/blueprint.py` → `/executive`
- `enhanced_autonomous_pm/interfaces/client/blueprint.py` → `/client`
- `enhanced_autonomous_pm/interfaces/api/blueprint.py` → `/api/v1`
- Templates root: `enhanced_autonomous_pm/web/templates` (Plotly dashboards)

Runtime Flow (Manager view)
1. Browser requests `/manager`, loads Plotly dashboard
2. JS fetches analytics from `/api/v1/*`
3. API pulls from SQLite, runs analytics/autonomous logic
4. JSON responses render live charts (heatmap, burndown, radar, etc.)

## 3. Configuration
- Module: `enhanced_autonomous_pm/core/config.py`
- Env vars:
  - `DEBUG` (default `False`)
  - `PORT` (default `5000`)
  - `DATABASE_URL` (default `autonomous_projects.db`)
  - `API_VERSION` (default `v1`, not dynamically wired in POC)
- Flask uses `Config.DEBUG` and `Config.PORT`. DB unification uses `Config.DATABASE_URL`.

## 4. Data Model (SQLite)
Primary DB: `autonomous_projects.db`
Tables (key fields only):
- `projects(project_id PK, name, status, start_date, end_date, budget_allocated, budget_used, completion_percentage, risk_level, team_size, client_name, project_manager, created_at, last_updated)`
- `stakeholders(stakeholder_id PK, name, email, role, project_id FK, phone, department, notification_preferences, last_contacted)`
- `tasks(task_id PK, project_id FK, title, description, assigned_to, status, priority, estimated_hours, actual_hours, start_date, due_date, completion_date, dependencies)`
- `autonomous_actions(action_id PK, project_id FK, action_type, description, reasoning, executed_at, result, confidence_score, stakeholders_notified, follow_up_required)`
- `employee_performance(id PK, employee_id, employee_name, project_id, quarter, hours_worked, tasks_completed, quality_score, collaboration_score, innovation_score, performance_trend, skill_gaps, achievements, development_goals, last_review_date, next_review_date)`
- `employee_profiles(employee_id PK, name, email, department, role, manager_id, skills, hire_date, availability_percentage, last_updated)`
- `task_dependencies(task_id, depends_on_task_id, PK(task_id, depends_on_task_id))`
- `project_financials(id PK, project_id FK, entry_date, category, amount, description)`
- `communication_logs(id PK, stakeholder_id, project_id, channel, subject, message, sent_at, status)`
- `performance_history(id PK, employee_id, metric_name, metric_value, recorded_at)`
- `learning_development(id PK, employee_id, course_name, provider, start_date, completion_date, status, notes)`
- `updates(id PK, name, project, update, date)`  ← migrated from `project_updates.db`

Migration
- On startup, `flask_app.py` creates `updates` in autonomous DB and migrates rows from `project_updates.db` (kept on disk for safety).

## 5. API Specification (JSON, `/api/v1`)
General
- Status: `200` success; failures return `{ "success": false, "error": "..." }`

Endpoints
- GET `/projects/health`
  - Response: `{ success, projects: [ { project_id, name, budget_health, schedule_health, team_health, overall_risk } ] }`
- GET `/projects/resource-utilization`
  - Response: `{ success, utilization: { "Backend": 0.92, ... } }`
- GET `/projects/budget-burndown`
  - Response: `{ success, series: [ { date, spent, allocated } ], project }`
- GET `/projects/timeline`
  - Response: `{ success, expected, actual, project }`
- GET `/projects/team-performance`
  - Response: `{ success, averages: { quality, collaboration, innovation } }`
- GET `/analytics/predictions`
  - Response: `{ success, prediction }` (0–1 success probability)
- GET|POST `/projects/autonomous-analysis`
  - Params: `project_id` optional
  - Response: `{ success, data, workflow_results }`
- POST `/employee/submit-data`
  - Request: form or JSON; fields include `employee_id`, `name`, `project_id`, `tasks_completed`, `quality_score`, etc.
  - Response: `{ success, employee_id }`
- POST `/communications/generate`
  - Response: `{ success, generated: [ { recipient, subject, message, role } ], count }`

## 6. Frontend Visualization (Plotly)
Manager dashboard (`web/templates/dashboards/manager.html`):
- Project health heatmap (budget/schedule/team)
- Resource utilization bar chart
- Budget burn‑down (allocated vs spent)
- Timeline adherence gauge
- Team performance radar (quality, collaboration, innovation)
- Predictive trend line (probability over horizon)

## 7. AI Orchestration & RAG
Routing
- `ai_orchestrator.py` routes by query complexity:
  - Simple/tooling → xLAM (Transformers)
  - Strategic/complex → `gpt-oss:20b` (Ollama) when available
  - Embeddings → `nomic-embed-text:v1.5` (Ollama)
Fallbacks
- If Ollama unavailable, orchestrator falls back to xLAM; RAG falls back to deterministic embeddings
RAG Engine
- `rag_engine.py` indexes projects, employee performance, updates, and sample policies into Chroma (if available). Store under `enhanced_autonomous_pm/data/vector_store/`.
- Retrieval augments queries and summaries; used by `FullyAutonomousManager` and Communication Engine.

## 8. Error Handling
- Global Flask error handler in `flask_app.py`:
  - For `/api/*` paths → JSON `{ success: false, error }`
  - For page requests → renders `error.html`
- Modules generally return `{ success: bool, error?: str, data?: any }` to keep handlers simple.

## 9. Security & Environments (POC)
- No auth configured; deploy behind trusted network for demos
- Debug/port controlled via env; default `DEBUG=False`
- Secrets/config should be added via env if/when introduced

## 10. Deployment
Local
- `python flask_app.py`
Docker
- `docker build -t autonomous-pm:poc .`
- `docker run --rm -p 5000:5000 -e PORT=5000 -e DEBUG=False autonomous-pm:poc`
Optional (LLM stack)
- Ollama: `ollama serve`, then `ollama pull gpt-oss:20b` and `ollama pull nomic-embed-text:v1.5`

## 11. Dependencies
Required
- flask, requests, pandas, numpy, scikit‑learn, transformers, torch (CPU ok), beautifulsoup4, lxml
Optional
- ollama, chromadb, dash/plotly (Plotly via CDN in UI), celery/redis (future)

## 12. Non‑Functional Characteristics (POC targets)
- Performance: in‑memory processing with SQLite; adequate for single‑node demos
- Reliability: graceful degradation when optional deps are missing
- Observability: console logging; add structured logging for production later
- Scalability: single‑process Flask; scale out with WSGI server and proper DB later

## 13. Testing Strategy (POC)
- Manual validation of `/api/v1` endpoints
- Smoke tests for app import/compile
- Future: pytest API tests, orchestrator unit tests, UI cypress tests (optional)

## 14. Roadmap
Phase 2
- Celery + Redis tasks for scheduled autonomous workflows and async updates
- Full policy‑based decisions + audit surfacing in UI
- Docker Compose for app + redis + optional Ollama container
Phase 3
- Authentication/authorization, RBAC
- Persistent vector DB service and document ingestion UI
- Advanced predictive models and what‑if scenario explorer

