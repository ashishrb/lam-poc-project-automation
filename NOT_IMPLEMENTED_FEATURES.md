# NOT YET IMPLEMENTED FEATURES - LAM Project Portfolio Management System

## 1) Doc → Plan automation (AI-generated WBS/Gantt/CPM) - ✅ COMPLETE

### Document AI extraction
- Parse HLD/BRD/SRS to Epics → Features → Stories/Tasks + dependencies, estimates, risks
- [Owner] AI/Backend
- [Key Files] app/services/plan_builder.py, enhanced_autonomous_pm/core/knowledge_manager.py
- Acceptance: Upload doc → JSON plan (WBS+deps+durations+owners) persisted to DB

### Baseline & versioning - ✅ COMPLETE
- [Owner] PM/Backend
- [Key Files] app/models/project.py (baseline tables), app/services/baseline_service.py, alembic migration
- Acceptance: Create/compare baselines; changes produce variance records

### Gantt & CPM generation - ✅ COMPLETE
- [Owner] Frontend/Backend
- [Key Files] app/services/gantt_cpm_service.py, app/api/v1/endpoints/baseline_gantt.py
- Acceptance: Auto-draw Gantt from server data; CPM identifies critical path

### "Plan from Document" wizard (UI - new) - ✅ COMPLETE
- Steps: Upload → Extract preview → Adjust WBS → Confirm → Generate Plan
- [Owner] Frontend
- [Key Files] app/web/templates/plan_wizard.html
- Acceptance: One-click end-to-end plan creation visible on Projects page

---

## 2) Dynamic re-planning & scenario simulation - ✅ COMPLETE

### Constraint solver for re-planning
- Reschedule on delays/resource contention
- [Owner] Backend
- [Key Files] app/services/scheduler.py
- Acceptance: Change a task → proposed new dates/assignees with rationale

### EVM & variance (SV/CV, SPI/CPI)
- [Owner] PM/Backend
- [Key Files] app/services/metrics.py, reports
- Acceptance: Weekly EVM metrics auto-computed per project/portfolio

### What-If simulator
- Deadline, staffing, scope toggles; compare outcomes
- [Owner] Frontend/Backend
- [Key Files] app/services/scenario_sim.py, UI panel in projects.html
- Acceptance: Side-by-side scenario cards with finish dates/cost deltas

### Scenario drawer/panel (UI - new)
- Sliders (duration, heads, cost); "Apply" creates new baseline
- [Owner] Frontend
- Acceptance: Interactive scenario comparison with apply functionality

---

## 3) Autonomous task ops & status policy enforcement - ✅ COMPLETE

### Email/meeting/chat → Task extraction
- [Owner] AI/Backend
- [Key Files] enhanced_autonomous_pm/automation/communication_engine.py
- Acceptance: Paste transcript → tasks with owner/ETA/priority created

### Celery Beat for policies
- Status rollups, overdue nudges, weekly digests
- [Owner] Platform/Backend
- [Key Files] app/core/celery_app.py, app/tasks/status_update_tasks.py
- Acceptance: Beat/worker services in compose; jobs visible in logs

### Dependency inference & guardrails
- NLP to find missing/suspicious deps; prevent cycles
- [Owner] AI/Backend
- Acceptance: Warnings + auto-fix suggestions on save

### Inline "Convert to Task" buttons (UI - new)
- [Owner] Frontend
- Acceptance: Convert meeting notes/comments to tasks

### Policy status banner per project (UI - new)
- [Owner] Frontend
- Acceptance: Display status like "3 overdue updates; nudge sent"

---

## 4) Predictive, causal & prescriptive intelligence - 0% COMPLETE

### Risk scoring models
- Train on velocity, blockers, past slippage
- [Owner] Data/AI
- [Key Files] enhanced_autonomous_pm/automation/predictive_analytics.py
- Acceptance: Risk % per project/task with feature attributions

### Causal explanations
- [Owner] AI
- Acceptance: Human-readable "why" for each high risk

### Prescriptive playbooks
- Auto actions (split, reassign, escalate) with human-in-the-loop
- [Owner] Backend
- Acceptance: One-click "Apply mitigation" updates plan + notifies owners

### Risk card rail on dashboard (UI - new)
- [Owner] Frontend
- Acceptance: Risk visualization with "Apply suggested fix" buttons

---

## 5) Resource optimization & calendars - 0% COMPLETE

### Working calendars & holidays
- Integrate org/global holidays; per-resource calendars
- [Owner] Backend
- Acceptance: Scheduling respects non-working days

### Skill-based assignment
- Map tasks→required skills; choose best available resource
- [Owner] Backend/AI
- Acceptance: Suggested assignee with utilization impact preview

### Resource heatmap (UI - new)
- Week view; over/under allocation markers; assign from panel
- [Owner] Frontend
- Acceptance: Visual resource allocation

### Assignment assistant modal (UI - new)
- Skill matches & availability
- [Owner] Frontend
- Acceptance: Modal for resource assignment with skill matching

---

## 6) Approvals, governance & audit - 0% COMPLETE

### Approval engine
- Budget change, CRs, scope; SLAs & escalations
- [Owner] Backend
- [Key Files] app/services/approvals.py, models/audit.py
- Acceptance: Configurable workflows; full audit trail

### RBAC & JWT refresh
- Roles: Exec, PM, Manager, Dev, Finance; token rotation
- [Owner] Platform
- [Key Files] app/core/security.py, api/v1/auth.py
- Acceptance: Role-scoped routes; audit logs for all writes

### PII redaction & encryption at rest
- [Owner] Platform/Sec
- Acceptance: Secrets KMS; PII masked in logs/exports

### Approvals inbox (UI - new)
- Filters, bulk approve/deny, SLA timers, audit preview
- [Owner] Frontend
- Acceptance: Centralized approval management interface

### Audit timeline tab on Project (UI - new)
- Diffs & actors
- [Owner] Frontend
- Acceptance: Project audit history visualization

---

## 7) Integrations & bi-directional sync - 0% COMPLETE

### Jira/Azure Boards connectors
- Sync issues, assignees, status; resolve conflicts
- [Owner] Integrations
- [Key Files] app/services/integrations/*
- Acceptance: Two-way sync passes round-trip tests

### MS Project import/export
- [Owner] Integrations
- [Key Files] app/services/integrations/msp.py
- Acceptance: Upload MPP/XML → plan; export back to MSP

### Slack/Teams bot
- Create tasks, approvals, nudge owners via chat
- [Owner] Integrations
- [Key Files] app/services/integrations/chat.py
- Acceptance: Chat-based task management

---

## 8) Reporting & executive briefs - 0% COMPLETE

### Weekly exec brief (auto)
- KPIs, risks, asks, budget variance; PDF/HTML email
- [Owner] Backend/Reports
- [Key Files] app/services/exec_brief.py, reports/templates/*
- Acceptance: Scheduled mailout with attachments and links

### Portfolio dashboards
- Cross-project KPIs; drill-downs
- [Owner] Backend/Reports
- Acceptance: Filters by BU/PM/health; 2-click to root cause

### Cards/charts for EVM, schedule variance, risk trend (UI - upgrade)
- [Owner] Frontend
- Acceptance: Visual metrics and trends

### Export buttons (CSV, XLSX, PDF) on all grids (UI - upgrade)
- [Owner] Frontend
- Acceptance: Data export functionality

---

## 9) Alerts & notifications (predictive & escalations) - 0% COMPLETE

### Threshold + predictive alerts
- Combine rules with model risk; dedupe & severity ranks
- [Owner] Backend
- Acceptance: Rich alerts (who/what/impact/next best action)

### Escalation paths
- Pager trees, quiet hours, reroute on no-ack
- [Owner] Backend
- Acceptance: Simulated incidents exercise escalation successfully

### Alert Center with filters (UI - upgrade)
- Severity, entity, time; bulk actions
- [Owner] Frontend
- Acceptance: Centralized alert management

---

## 10) Observability, performance & scalability - 0% COMPLETE

### Structured logging & tracing
- OpenTelemetry traces/metrics; JSON logs; req IDs
- [Owner] Platform
- [Key Files] app/core/logging.py
- Acceptance: Traces visible in APM; error budgets defined

### Prometheus/Grafana
- API p95, Celery queues, DB pool, cache hit ratio
- [Owner] Platform
- [Key Files] docker-compose.yml, monitoring configs
- Acceptance: Comprehensive monitoring dashboard

### Caching & indexing plan
- Hot endpoints cached; DB indices for heavy queries
- [Owner] Platform
- [Key Files] app/core/cache.py
- Acceptance: Performance optimization

---

## 12) API hardening & productization - 0% COMPLETE

### Rate limiting & idempotency
- Prevent duplicate POSTs; burst control
- [Owner] Platform
- [Key Files] app/core/middleware.py
- Acceptance: API protection and reliability

### OpenAPI hygiene
- Tags, examples, error models; 100% operation coverage
- [Owner] Platform
- Acceptance: Complete API documentation

### Pagination, sorting, filtering on all list endpoints
- [Owner] Platform
- Acceptance: Scalable API responses

---

## 13) CI/CD, container & runtime hardening - 0% COMPLETE

### CI (GitHub Actions)
- Lint (ruff), type (mypy), tests (pytest), coverage gate, SBOM/Trivy
- [Owner] DevOps
- [Key Files] .github/workflows/ci.yml
- Acceptance: Automated quality gates

### Docker multi-stage, non-root, HEALTHCHECK, minimal image
- [Owner] DevOps
- [Key Files] Dockerfile, docker-compose.prod.yml
- Acceptance: Production-ready containers

### CSP/CORS/HTTPS on Nginx; HSTS; sec headers
- [Owner] DevOps
- [Key Files] nginx.conf
- Acceptance: Security-hardened web server

---

## 🎨 UI-Specific To-Dos (comprehensive) - 0% COMPLETE

### Consolidate UI under app/web/
- Remove legacy /templates & /web/static; unify CSS/JS
- [Owner] Frontend
- Acceptance: Unified UI structure

### Global components
- Skeleton loaders, error toasts, confirmation modals, date/time pickers, multi-select with chips
- [Owner] Frontend
- [Key Files] app/web/templates/components/
- Acceptance: Reusable UI components

### Gantt component (Projects)
- Zoom, drag-to-reschedule, critical-path highlight, dependency lines, baseline overlay
- [Owner] Frontend
- [Key Files] app/web/templates/components/gantt.html
- Acceptance: Interactive Gantt chart

### Scenario panel (Projects)
- Sliders (duration, heads, cost); "Apply" creates new baseline
- [Owner] Frontend
- [Key Files] app/web/templates/components/scenario.html
- Acceptance: Interactive scenario planning

### Resource heatmap (Resources)
- Week view; over/under allocation markers; assign from panel
- [Owner] Frontend
- [Key Files] app/web/templates/components/heatmap.html
- Acceptance: Visual resource allocation

### Approvals inbox (Navbar)
- Filters, bulk approve/deny, SLA timers, audit preview
- [Owner] Frontend
- Acceptance: Centralized approval interface

### Alert Center (Alerts)
- Severity chips, entity filters (project/task), ack/assign actions
- [Owner] Frontend
- Acceptance: Alert management interface

### Executive brief (Reports)
- One-click weekly report preview; export to PDF; schedule
- [Owner] Frontend
- Acceptance: Executive reporting interface

### Accessibility
- Color contrast AA, focus rings, skip links, ARIA labels, keyboard nav, form error summaries
- [Owner] Frontend
- Acceptance: WCAG 2.1 AA compliance

### Help & documentation sidebar
- Contextual help per page; link to USAGE.md / tooltips with examples
- [Owner] Frontend
- Acceptance: In-app help system

### Grid UX
- Column chooser, pinning, resizable columns, server-side pagination, quick filters, export buttons
- [Owner] Frontend
- Acceptance: Advanced data grid functionality

### Dark mode & density toggle (nice-to-have)
- [Owner] Frontend
- Acceptance: User preference customization

---

## 📦 File/Service adds (quick map)

### New Services to Create:
- app/services/plan_builder.py — Doc→Plan pipeline
- app/services/scheduler.py — re-planner/CPM/EVM
- app/services/scenario_sim.py — what-if engine
- app/services/approvals.py — approval workflows
- app/services/metrics.py — EVM/variance calculators
- app/services/integrations/ — Jira/Azure/MSP/Slack
- enhanced_autonomous_pm/automation/predictive_analytics.py — train/infer glue

### New UI Components:
- app/web/templates/components/ — Gantt, heatmap, modals, toasts

### Infrastructure Updates:
- docker-compose.yml — add celery-worker, celery-beat, Prometheus/Grafana

---

## 🔐 HLD anchors used

### Partial Implementations (need completion):
- AI Copilot/RAG partial
- Reporting Email/Scheduling partial  
- Alerts Rule/Escalation/Notify partial
- DB integration in progress
- Security/RBAC/HTTPS/PII partial
- UI Accessibility & Help/Docs partial
- Perf/Scalability/Monitoring partial

---

## 📊 Implementation Summary

**TOTAL FEATURES TO IMPLEMENT: 13 major areas + UI components**
**CURRENT STATUS: 3/13 areas complete (23%)**
**NEXT PRIORITY: Phase 1 - Core Features (Document automation, Dynamic re-planning, Resource optimization, Approvals)**

**Estimated effort remaining:**
- Phase 1 (Core Features): 4-6 weeks
- Phase 2 (Advanced Features): 6-8 weeks  
- Phase 3 (Polish & Scale): 4-6 weeks
- UI Components: 2-3 weeks
- **Total: 16-23 weeks**
