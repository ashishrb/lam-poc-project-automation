from fastapi import APIRouter
from .endpoints import (
    auth,
    projects,
    resources,
    finance,
    risks,
    vendors,
    documents,
    alerts,
    stakeholders,
    reports,
    ai_copilot,
    ai_first,
    plan_builder,
    resource_assignment,
    autonomous_system,
    developer_workbench
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(resources.router, prefix="/resources", tags=["Resources"])
api_router.include_router(finance.router, prefix="/finance", tags=["Finance"])
api_router.include_router(risks.router, prefix="/risks", tags=["Risks & Issues"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["Vendors"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(stakeholders.router, prefix="/stakeholders", tags=["Stakeholders"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(ai_copilot.router, prefix="/ai", tags=["AI Copilot"])
api_router.include_router(ai_first.router, prefix="/ai-first", tags=["AI-First Operations"])
api_router.include_router(plan_builder.router, prefix="/plan-builder", tags=["Document Plan Builder"])
api_router.include_router(resource_assignment.router, prefix="/resource-assignment", tags=["Resource Assignment"])
api_router.include_router(autonomous_system.router, prefix="/autonomous-system", tags=["Autonomous System"])
api_router.include_router(developer_workbench.router, prefix="/developer-workbench", tags=["Developer Workbench"])
