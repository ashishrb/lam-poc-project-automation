# Enhanced Autonomous PM – Setup Guide

This guide walks you through environment setup, installation, optional AI integrations, and how to run the application locally.

## 1) Prerequisites
- Python 3.9–3.11 (recommended)
- OS: macOS, Linux, or Windows
- Optional (advanced AI + background jobs):
  - Ollama (local LLMs for `gpt-oss:20b` and `nomic-embed-text:v1.5` embeddings)
  - NVIDIA CUDA (for GPU acceleration with Transformers/xLAM)
  - Redis + Celery (async/background processing, future phase)

## 2) Project Layout (key directories)
- `enhanced_autonomous_pm/` – main package
  - `core/` – AI orchestration, RAG, decision engine, model manager
  - `automation/` – lifecycle automation, comms engine, predictive, resource optimizer
  - `interfaces/` – Flask blueprints for pages and APIs
  - `data/` – vector store, operational DB, analytics warehouse (persisted)
  - `web/` – templates and static assets
- `flask_app.py` – Flask app entry with blueprint registration
- `autonomous_manager.py` – DB + core PM logic (seed data on first use)
- `enhanced_lam_integration.py` – legacy interface (now using core orchestrator when available)

## 3) Create Virtual Environment
macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```
Windows (PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Upgrade basics
```bash
pip install -U pip setuptools wheel
```

## 4) Install Dependencies
```bash
pip install -r requirements.txt
```
Notes:
- Torch/Transformers may be large. Install time varies by platform.
- If CUDA is available, Transformers uses GPU automatically.

## 5) Optional: Enable Ollama + Embeddings
Ollama enhances complex analysis and RAG embeddings.
```bash
# Install Ollama (see https://ollama.com)
ollama serve &
ollama pull gpt-oss:20b
ollama pull nomic-embed-text:v1.5
```
If Ollama is not available, the app falls back to xLAM-only mode. RAG uses a deterministic embedding fallback.

## 6) First Run and Databases
- `project_updates.db` is created by `flask_app.py:init_db()` on first run.
- `autonomous_projects.db` is created + seeded by `DatabaseManager` when first accessed.
- Vector store persists to `enhanced_autonomous_pm/data/vector_store/` (Chroma).

## 7) Run the Application
```bash
python flask_app.py
```
Open in browser:
- Manager dashboard: http://127.0.0.1:5000/manager
- Leadership dashboard: http://127.0.0.1:5000/dashboard
- Employee portal: http://127.0.0.1:5000/employee
- Executive view: http://127.0.0.1:5000/executive

## 8) Environment Variables (optional)
- `FLASK_ENV=development` – enable debug-style reloading
- `FLASK_RUN_PORT=5050` – change port (or edit `app.run`)

## 9) Optional: Celery + Redis (Phase 2)
Install services
```bash
brew install redis   # macOS (example)
# Or use Docker: docker run -p 6379:6379 redis:7
pip install celery redis
```
Example skeleton (not yet wired):
```bash
celery -A tasks.celery_app worker --loglevel=INFO
```
We can wire scheduled autonomous workflows upon request.

## 10) Troubleshooting
- Torch/Transformers slow to install: try CPU-only first; GPU is optional.
- Ollama not found: ensure `ollama serve` is running; otherwise app runs in fallback mode.
- Port conflicts: set `FLASK_RUN_PORT` or change `app.run(debug=True)`.
- Missing tables: app initializes them on first run; delete `autonomous_projects.db` to reseed.

