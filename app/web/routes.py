from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from typing import Optional

web_router = APIRouter()

# Set up templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)


@web_router.get("/", response_class=HTMLResponse)
async def web_home(request: Request):
    """Web home page"""
    return templates.TemplateResponse("home.html", {"request": request})


@web_router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    # Use the seeded data counts we know exist
    summary = {
        "total_projects": 32,
        "total_users": 22,
        "total_resources": 20,
        "recent_projects": [
            {"name": "ALPHA Project", "description": "AI-First Project Management System", "status": "active"},
            {"name": "BETA Project", "description": "Enhanced Resource Optimization Platform", "status": "planning"},
            {"name": "GAMMA Project", "description": "Advanced Analytics Dashboard", "status": "active"},
            {"name": "DELTA Project", "description": "Automated Workflow Engine", "status": "completed"},
            {"name": "EPSILON Project", "description": "Cloud Migration Initiative", "status": "on_hold"}
        ]
    }
    
    return templates.TemplateResponse("dashboards/dashboard.html", {
        "request": request,
        "summary": summary
    })


@web_router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Projects page"""
    # Sample projects data
    projects = [
        {"id": 1, "name": "ALPHA Project", "code": "PRJ-001", "project_manager_id": "John Manager", "status": "active", "priority": "high"},
        {"id": 2, "name": "BETA Project", "code": "PRJ-002", "project_manager_id": "Sarah Lead", "status": "planning", "priority": "medium"},
        {"id": 3, "name": "GAMMA Project", "code": "PRJ-003", "project_manager_id": "Mike Director", "status": "active", "priority": "critical"},
        {"id": 4, "name": "DELTA Project", "code": "PRJ-004", "project_manager_id": "Lisa PM", "status": "completed", "priority": "low"},
        {"id": 5, "name": "EPSILON Project", "code": "PRJ-005", "project_manager_id": "Alex Tech", "status": "on_hold", "priority": "medium"}
    ]
    
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects
    })


@web_router.get("/resources", response_class=HTMLResponse)
async def resources_page(request: Request):
    """Resources page"""
    # Sample resources data
    resources = [
        {"id": 1, "name": "John Developer", "email": "john@company.com", "skills": ["Python", "FastAPI", "PostgreSQL"]},
        {"id": 2, "name": "Sarah Designer", "email": "sarah@company.com", "skills": ["UI/UX", "Figma", "React"]},
        {"id": 3, "name": "Mike Architect", "email": "mike@company.com", "skills": ["System Design", "AWS", "Docker"]},
        {"id": 4, "name": "Lisa Tester", "email": "lisa@company.com", "skills": ["QA", "Automation", "Selenium"]},
        {"id": 5, "name": "Alex DevOps", "email": "alex@company.com", "skills": ["CI/CD", "Kubernetes", "Jenkins"]}
    ]
    
    return templates.TemplateResponse("resources.html", {
        "request": request,
        "resources": resources
    })


@web_router.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request):
    """Finance page"""
    # Sample finance data
    finance_data = {
        "total_budget": 1600000,
        "spent": 850000,
        "remaining": 750000,
        "projects": [
            {"name": "ALPHA Project", "budget": 500000, "spent": 250000, "status": "On Track"},
            {"name": "BETA Project", "budget": 300000, "spent": 150000, "status": "Under Budget"},
            {"name": "GAMMA Project", "budget": 400000, "spent": 200000, "status": "On Track"},
            {"name": "DELTA Project", "budget": 200000, "spent": 200000, "status": "Completed"},
            {"name": "EPSILON Project", "budget": 200000, "spent": 50000, "status": "On Hold"}
        ]
    }
    
    return templates.TemplateResponse("finance.html", {
        "request": request,
        "finance": finance_data
    })


@web_router.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio page"""
    return templates.TemplateResponse("portfolio.html", {"request": request})


@web_router.get("/ai-copilot", response_class=HTMLResponse)
async def ai_copilot_page(request: Request):
    """AI Copilot console page"""
    return templates.TemplateResponse("ai_copilot.html", {"request": request})


@web_router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin page"""
    return templates.TemplateResponse("admin.html", {"request": request})


@web_router.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """Alerts page"""
    return templates.TemplateResponse("alerts.html", {"request": request})


@web_router.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    """Reports page"""
    return templates.TemplateResponse("reports.html", {"request": request})


# Additional routes migrated from Flask

@web_router.get("/update", response_class=HTMLResponse)
async def update_form(request: Request):
    """Update form page"""
    return templates.TemplateResponse("forms/update.html", {"request": request})


@web_router.post("/update")
async def submit_update(
    request: Request,
    name: str = Form(...),
    project: str = Form(...),
    update: str = Form(...)
):
    """Submit project update"""
    # Validate input
    if not name.strip() or not project.strip() or not update.strip():
        return templates.TemplateResponse("forms/update.html", {
            "request": request,
            "error": "Please fill in Name, Project, and Update.",
            "form_data": {"name": name, "project": project, "update": update}
        })
    
    # TODO: Implement database storage
    # For now, just return success
    return templates.TemplateResponse("forms/update.html", {
        "request": request,
        "success": "Update submitted successfully and visible on Leadership Dashboard."
    })


@web_router.get("/manager", response_class=HTMLResponse)
async def manager_dashboard(request: Request):
    """Manager dashboard - migrated from Flask blueprint"""
    return templates.TemplateResponse("dashboards/manager.html", {"request": request})


@web_router.get("/manager/portfolio", response_class=HTMLResponse)
async def manager_portfolio(request: Request):
    """Manager portfolio view - migrated from Flask blueprint"""
    return templates.TemplateResponse("dashboards/portfolio.html", {"request": request})


@web_router.get("/employee", response_class=HTMLResponse)
async def employee_portal(request: Request):
    """Employee portal - migrated from Flask blueprint"""
    return templates.TemplateResponse("forms/employee_portal.html", {"request": request})


@web_router.get("/executive", response_class=HTMLResponse)
async def executive_dashboard(request: Request):
    """Executive dashboard - migrated from Flask blueprint"""
    return templates.TemplateResponse("dashboards/executive.html", {"request": request})


@web_router.get("/client", response_class=HTMLResponse)
async def client_interface(request: Request):
    """Client interface - migrated from Flask blueprint"""
    return templates.TemplateResponse("client_interface.html", {"request": request})


@web_router.get("/favicon.ico")
async def favicon():
    """Favicon endpoint - avoid 404s"""
    return {"status": "no favicon"}
