# Enhanced Autonomous PM – Application Usage & Process Guide

This guide explains how to use the application, dashboards, APIs, and core autonomous processes.

## 1) Start the App
```bash
python flask_app.py
```
Navigate to:
- Manager Dashboard: http://127.0.0.1:5000/manager
- Leadership Dashboard: http://127.0.0.1:5000/dashboard
- Employee Portal: http://127.0.0.1:5000/employee
- Executive Command: http://127.0.0.1:5000/executive

## 2) Blueprints & Navigation
- `employee` blueprint (`/employee`): Self-service data entry
- `manager` blueprint (`/manager`): Visual analytics & controls
- `executive` blueprint (`/executive`): Strategic overview
- `client` blueprint (`/client`): External stakeholder access (placeholder)
- `api` blueprint (`/api`): REST endpoints used by dashboards

## 3) Manager Dashboard Visuals (Plotly)
- Project Health Heatmap: overall budget/schedule/team health across projects
- Resource Utilization Bar: capacity usage per function
- Budget Burn-down: allocated vs. spent over time
- Timeline Adherence Gauge: expected vs. actual completion
- Team Performance Radar: quality/collaboration/innovation averages
- Predictive Trend Line: success probability trend

Data is fetched in real-time from `/api/*` endpoints and rendered via Plotly.

## 4) Key API Endpoints
- `GET /api/projects/health` – health per project (budget/schedule/team)
- `GET /api/projects/resource-utilization` – utilization snapshot
- `GET /api/projects/budget-burndown` – time series: allocated vs spent
- `GET /api/projects/timeline` – expected vs actual progress
- `GET /api/projects/team-performance` – team averages (quality, collaboration, innovation)
- `GET /api/analytics/predictions` – success probability (heuristic/predictive)
- `GET|POST /api/projects/autonomous-analysis` – runs autonomous lifecycle workflow
- `POST /api/employee/submit-data` – record portal submissions
- `POST /api/communications/generate` – intelligent communications (RAG-assisted)

Example usage (curl):
```bash
curl -X GET http://127.0.0.1:5000/api/projects/health
curl -X POST http://127.0.0.1:5000/api/employee/submit-data \
  -H 'Content-Type: application/json' \
  -d '{"employee_id":"EMP999","name":"Ada","project_id":"PROJ001","tasks_completed":5}'
```

## 5) Autonomous Workflows
- Execution: `GET|POST /api/projects/autonomous-analysis`
- Under the hood:
  - `AutonomousProjectManager` orchestrates: project health → strategic decisions → team analysis → stakeholder comms → development actions
  - `FullyAutonomousManager` augments with RAG context from `core/rag_engine.py`
  - Results are summarized and returned with an audit-friendly narrative

## 6) Orchestrator Architecture
- Central coordination: `core/ai_orchestrator.py` (xLAM, gpt-oss:20b via Ollama, nomic-embed embeddings)
- Model loading: `core/model_manager.py` (xLAM via Hugging Face Transformers)
- Knowledge retrieval: `core/rag_engine.py` (Chroma persistence under `enhanced_autonomous_pm/data/vector_store`)
- Decision logic: `core/decision_engine.py` (wrapper over legacy logic)
- `enhanced_lam_integration.py` prefers the core orchestrator when available

## 7) Data Flow & Storage
- Operational DB: `autonomous_projects.db` (seeded with sample projects/stakeholders/tasks/performance)
- Updates DB: `project_updates.db` (portal updates)
- Vector Store: `enhanced_autonomous_pm/data/vector_store/` (Chroma)

## 8) Employee Portal Process
1. Navigate to `/employee`
2. Submit daily tracking, self-assessment, skills, and suggestions
3. Data is saved to `employee_profiles` + performance snapshots; major updates appear in Leadership Dashboard

## 9) Adding Content to RAG
Use `core/knowledge_manager.py` to add documents programmatically:
```python
from enhanced_autonomous_pm.core.knowledge_manager import KnowledgeManager
km = KnowledgeManager()
km.add_documents([
  {"id":"policy:security","text":"Least privilege & MFA.","metadata":{"type":"policy"}}
])
```
RAG is consulted by `FullyAutonomousManager` to enrich summaries and by the Communication Engine for guidance.

## 10) Extending the System
- Add endpoints to `interfaces/api/blueprint.py`
- Add visuals by updating Plotly sections in `web/templates/dashboards/manager.html`
- Extend orchestrator to include new models in `core/ai_orchestrator.py`
- Add background jobs (Celery) to schedule autonomous workflows

## 11) Troubleshooting
- Visuals not loading: check browser console for `/api/*` errors
- No projects listed: delete `autonomous_projects.db` to reseed sample data
- Ollama not used: ensure `ollama serve` and models pulled
- RAG storage errors: ensure `enhanced_autonomous_pm/data/vector_store/` is writable

