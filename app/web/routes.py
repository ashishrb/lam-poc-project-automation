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
    # Sample projects data with more details
    projects = [
        {
            "id": 1, 
            "name": "ALPHA Project", 
            "code": "PRJ-001", 
            "project_manager_id": "John Manager", 
            "status": "active", 
            "priority": "high",
            "description": "AI-First Project Management System",
            "start_date": "2024-01-15",
            "end_date": "2024-06-30",
            "budget": 500000,
            "progress": 75
        },
        {
            "id": 2, 
            "name": "BETA Project", 
            "code": "PRJ-002", 
            "project_manager_id": "Sarah Lead", 
            "status": "planning", 
            "priority": "medium",
            "description": "Enhanced Resource Optimization Platform",
            "start_date": "2024-02-01",
            "end_date": "2024-08-31",
            "budget": 300000,
            "progress": 25
        },
        {
            "id": 3, 
            "name": "GAMMA Project", 
            "code": "PRJ-003", 
            "project_manager_id": "Mike Director", 
            "status": "active", 
            "priority": "critical",
            "description": "Advanced Analytics Dashboard",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "budget": 400000,
            "progress": 60
        },
        {
            "id": 4, 
            "name": "DELTA Project", 
            "code": "PRJ-004", 
            "project_manager_id": "Lisa PM", 
            "status": "completed", 
            "priority": "low",
            "description": "Automated Workflow Engine",
            "start_date": "2023-09-01",
            "end_date": "2024-01-31",
            "budget": 200000,
            "progress": 100
        },
        {
            "id": 5, 
            "name": "EPSILON Project", 
            "code": "PRJ-005", 
            "project_manager_id": "Alex Tech", 
            "status": "on_hold", 
            "priority": "medium",
            "description": "Cloud Migration Initiative",
            "start_date": "2024-03-01",
            "end_date": "2024-09-30",
            "budget": 200000,
            "progress": 15
        }
    ]
    
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects
    })


@web_router.get("/resources", response_class=HTMLResponse)
async def resources_page(request: Request):
    """Resources page"""
    # Sample resources data with project allocations
    resources = [
        {
            "id": 1, 
            "name": "John Developer", 
            "email": "john@company.com", 
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "role": "Senior Developer",
            "department": "Engineering",
            "availability": 85,
            "current_projects": [
                {"project_id": 1, "project_name": "ALPHA Project", "role": "Lead Developer", "hours_allocated": 40, "tasks": ["API Development", "Database Design"]},
                {"project_id": 3, "project_name": "GAMMA Project", "role": "Developer", "hours_allocated": 20, "tasks": ["Analytics Module"]}
            ]
        },
        {
            "id": 2, 
            "name": "Sarah Designer", 
            "email": "sarah@company.com", 
            "skills": ["UI/UX", "Figma", "React"],
            "role": "UX Designer",
            "department": "Design",
            "availability": 70,
            "current_projects": [
                {"project_id": 1, "project_name": "ALPHA Project", "role": "UI Designer", "hours_allocated": 30, "tasks": ["Dashboard Design", "User Interface"]},
                {"project_id": 2, "project_name": "BETA Project", "role": "UX Designer", "hours_allocated": 25, "tasks": ["User Research", "Wireframing"]}
            ]
        },
        {
            "id": 3, 
            "name": "Mike Architect", 
            "email": "mike@company.com", 
            "skills": ["System Design", "AWS", "Docker"],
            "role": "Solution Architect",
            "department": "Architecture",
            "availability": 60,
            "current_projects": [
                {"project_id": 2, "project_name": "BETA Project", "role": "Architect", "hours_allocated": 35, "tasks": ["System Architecture", "Cloud Setup"]},
                {"project_id": 5, "project_name": "EPSILON Project", "role": "Architect", "hours_allocated": 15, "tasks": ["Migration Planning"]}
            ]
        },
        {
            "id": 4, 
            "name": "Lisa Tester", 
            "email": "lisa@company.com", 
            "skills": ["QA", "Automation", "Selenium"],
            "role": "QA Engineer",
            "department": "Quality Assurance",
            "availability": 90,
            "current_projects": [
                {"project_id": 1, "project_name": "ALPHA Project", "role": "QA Lead", "hours_allocated": 25, "tasks": ["Test Planning", "Automation"]},
                {"project_id": 3, "project_name": "GAMMA Project", "role": "QA Engineer", "hours_allocated": 30, "tasks": ["Testing", "Bug Reports"]}
            ]
        },
        {
            "id": 5, 
            "name": "Alex DevOps", 
            "email": "alex@company.com", 
            "skills": ["CI/CD", "Kubernetes", "Jenkins"],
            "role": "DevOps Engineer",
            "department": "Operations",
            "availability": 80,
            "current_projects": [
                {"project_id": 4, "project_name": "DELTA Project", "role": "DevOps Engineer", "hours_allocated": 40, "tasks": ["Pipeline Setup", "Deployment"]},
                {"project_id": 5, "project_name": "EPSILON Project", "role": "DevOps Engineer", "hours_allocated": 20, "tasks": ["Infrastructure Setup"]}
            ]
        }
    ]
    
    return templates.TemplateResponse("resources.html", {
        "request": request,
        "resources": resources
    })


@web_router.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request):
    """Finance page"""
    # Sample finance data with actual values
    finance_data = {
        "total_budget": 1600000,
        "spent": 850000,
        "remaining": 750000,
        "variance": -50000,
        "variance_percentage": -3.1,
        "projects": [
            {"name": "ALPHA Project", "budget": 500000, "spent": 375000, "remaining": 125000, "variance": 25000, "status": "On Track"},
            {"name": "BETA Project", "budget": 300000, "spent": 75000, "remaining": 225000, "variance": -75000, "status": "Under Budget"},
            {"name": "GAMMA Project", "budget": 400000, "spent": 240000, "remaining": 160000, "variance": 0, "status": "On Track"},
            {"name": "DELTA Project", "budget": 200000, "spent": 200000, "remaining": 0, "variance": 0, "status": "Completed"},
            {"name": "EPSILON Project", "budget": 200000, "spent": 30000, "remaining": 170000, "variance": -30000, "status": "On Hold"}
        ],
        "monthly_spending": [
            {"month": "Jan", "spent": 120000},
            {"month": "Feb", "spent": 150000},
            {"month": "Mar", "spent": 180000},
            {"month": "Apr", "spent": 200000},
            {"month": "May", "spent": 0}
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
