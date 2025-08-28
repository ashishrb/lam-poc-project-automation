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

## 15. Known Issues and Risks (Current State)

Critical
- Import system fragility and circular imports
  - Legacy module `enhanced_lam_integration.py` sometimes imports from `enhanced_autonomous_pm.core` while also being a dependency of modules that import it.
  - Try/except around imports obscures real failures and can leave features half‑initialized.
  - Some directories originally lacked `__init__.py` (now added) but legacy paths may still be referenced.
- Database architecture inconsistencies
  - Two databases historically used (`project_updates.db`, `autonomous_projects.db`). Migration to a unified DB has been implemented, but legacy code snippets may still reference `DB_NAME`.
  - Mixed connection patterns (context managers vs. shared handles).
- Configuration sprawl
  - Hardware‑specific assumptions (GPU/AMD) documented and sometimes implied in code.
  - Settings scattered across files; inconsistent use of env vars.

Structural
- Legacy code coexistence
  - `enhanced_lam_integration.py` contains both legacy and active logic; unclear precedence.
  - Diagnostic/performance code lives next to core feature code.
- Optional dependency handling
  - `ollama`, `chromadb` treated inconsistently; many try/except blocks.
- Blueprint registration
  - Blueprints import with fallbacks; registration path assumes availability and may not fail fast with context.

Design
- Data model complexity
  - `project_models.py` large dataclass hierarchies; potential field‑ordering pitfalls.
- API inconsistencies
  - Mixed HTML/JSON responses; no uniform response envelope in legacy endpoints.
  - Versioning introduced (`/api/v1`) but not enforced across all older routes.
- Template organization
  - Old root templates have been removed, but ensure no straggling references remain.

## 16. Remediation Plan (Prioritized)

P0 – Stability and Clarity
- Enforce unified DB usage
  - Keep `project_updates.db` only as a migration source; block reads from it in code paths.
  - Ensure every DB access uses `Config.DATABASE_URL` and context managers.
- Standardize API response envelope
  - All `/api/v1/*` return `{ success, data?, error? }` consistently.
  - Register global error handler for JSON on `/api/*` (done) and audit endpoints for consistency.
- Consolidate imports
  - Replace broad try/except import guards with capability flags set by a single module (e.g., `core/capabilities.py`).
  - Clearly document orchestrator precedence: core orchestrator first; legacy fallback only.

P1 – Maintainability
- Configuration hierarchy
  - Single source in `core/config.py`; remove hardware assumptions from code paths (document in docs only).
  - Introduce `.env` overrides for local dev; avoid setting envs inside code.
- Optional dependency strategy
  - Define REQUIRED vs OPTIONAL in docs; gate features via capability flags and surface health in `/api/v1/health`.
- Blueprint robustness
  - Fail fast on blueprint import errors and return a friendly startup error; log missing modules.

P2 – Quality and Ops
- Health checks
  - Add `/api/v1/health` with sub‑checks: DB RW, Ollama reachable, Chroma available, model cache warm.
- Logging
  - Replace prints with `logging` configured by env: `LOG_LEVEL`.
- Tests (incremental)
  - Add smoke tests for `/api/v1/*` and a workflow invocation; keep under a minute.

## 17. Standards and Conventions

- API envelope
  - Success: `{ "success": true, "data": <payload> }`
  - Error: `{ "success": false, "error": "message" }`
- Error boundaries
  - Exceptions in `/api/*` are converted to JSON errors (global handler). Views render `error.html`.
- Dependencies
  - REQUIRED: `flask`, `requests`, `pandas`, `numpy`, `scikit-learn`, `transformers`, `torch`, `beautifulsoup4`, `lxml`
  - OPTIONAL: `ollama`, `chromadb`, `celery`, `redis`, `plotly` (UI via CDN)
  - Optional features must degrade gracefully and advertise availability via health endpoint.
- Imports
  - Avoid circular imports; prefer injecting services (or late imports) at function boundaries.
- Database
  - Use SQLite with context managers; schema changes through idempotent `CREATE TABLE IF NOT EXISTS`.
  - All modules must reference the unified DB via `Config.DATABASE_URL`.

## 18. Open Questions
- Authentication scope for POC vs. pilot deployments?
- Do we need API keys or IP allowlists for the `/api/v1/*` in demos?
- Required cadence and content for autonomous reports (daily/weekly)?

