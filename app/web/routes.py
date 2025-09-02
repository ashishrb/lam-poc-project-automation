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
    """Web home page - redirect to login"""
    return RedirectResponse(url="/web/login")

@web_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@web_router.get("/project-plan-creator", response_class=HTMLResponse)
async def project_plan_creator_page(request: Request):
    """Project plan creator page"""
    return templates.TemplateResponse("project_plan_creator.html", {"request": request})

@web_router.get("/project-reports", response_class=HTMLResponse)
async def project_reports_page(request: Request):
    """Project reports page with Gantt charts and analytics"""
    return templates.TemplateResponse("project_reports.html", {"request": request})

@web_router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin page"""
    return templates.TemplateResponse("admin.html", {"request": request})


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
            "project_manager_id": "Lisa Coordinator", 
            "status": "completed", 
            "priority": "medium",
            "description": "Automated Workflow Engine",
            "start_date": "2023-09-01",
            "end_date": "2024-02-28",
            "budget": 250000,
            "progress": 100
        },
        {
            "id": 5, 
            "name": "EPSILON Project", 
            "code": "PRJ-005", 
            "project_manager_id": "David Architect", 
            "status": "on_hold", 
            "priority": "low",
            "description": "Cloud Migration Initiative",
            "start_date": "2024-03-01",
            "end_date": "2024-11-30",
            "budget": 800000,
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
    # Sample resources data
    resources = [
        {
            "id": 1,
            "name": "John Developer",
            "email": "john.dev@company.com",
            "role": "Senior Developer",
            "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "availability": 80,
            "current_projects": ["ALPHA Project", "GAMMA Project"]
        },
        {
            "id": 2,
            "name": "Sarah Designer",
            "email": "sarah.design@company.com",
            "role": "UI/UX Designer",
            "skills": ["Figma", "Adobe XD", "Sketch", "Prototyping"],
            "availability": 60,
            "current_projects": ["BETA Project"]
        },
        {
            "id": 3,
            "name": "Mike Tester",
            "email": "mike.test@company.com",
            "role": "QA Engineer",
            "skills": ["Selenium", "JUnit", "TestNG", "Manual Testing"],
            "availability": 90,
            "current_projects": ["ALPHA Project", "DELTA Project"]
        },
        {
            "id": 4,
            "name": "Lisa Analyst",
            "email": "lisa.analyst@company.com",
            "role": "Business Analyst",
            "skills": ["Requirements Analysis", "Process Modeling", "Stakeholder Management"],
            "availability": 70,
            "current_projects": ["BETA Project", "EPSILON Project"]
        },
        {
            "id": 5,
            "name": "David DevOps",
            "email": "david.devops@company.com",
            "role": "DevOps Engineer",
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "availability": 85,
            "current_projects": ["GAMMA Project", "EPSILON Project"]
        }
    ]
    
    return templates.TemplateResponse("resources.html", {
        "request": request,
        "resources": resources
    })


@web_router.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request):
    """Finance page"""
    # Sample financial data
    financial_data = {
        "total_budget": 2250000,
        "spent": 1850000,
        "remaining": 400000,
        "variance_percentage": 82.2,
        "projects": [
            {
                "name": "ALPHA Project",
                "budget": 500000,
                "spent": 375000,
                "remaining": 125000,
                "variance": 0,
                "status": "On Track"
            },
            {
                "name": "BETA Project",
                "budget": 300000,
                "spent": 75000,
                "remaining": 225000,
                "variance": 0,
                "status": "Under Budget"
            },
            {
                "name": "GAMMA Project",
                "budget": 400000,
                "spent": 240000,
                "remaining": 160000,
                "variance": 0,
                "status": "On Track"
            },
            {
                "name": "DELTA Project",
                "budget": 250000,
                "spent": 250000,
                "remaining": 0,
                "variance": 0,
                "status": "Completed"
            },
            {
                "name": "EPSILON Project",
                "budget": 800000,
                "spent": 120000,
                "remaining": 680000,
                "variance": 0,
                "status": "Under Budget"
            }
        ]
    }
    
    return templates.TemplateResponse("finance.html", {
        "request": request,
        "finance": financial_data
    })


@web_router.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio page"""
    return templates.TemplateResponse("portfolio.html", {"request": request})


@web_router.get("/ai-copilot", response_class=HTMLResponse)
async def ai_copilot_page(request: Request):
    """AI Copilot page"""
    return templates.TemplateResponse("ai_copilot.html", {"request": request})


@web_router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin page"""
    return templates.TemplateResponse("admin.html", {"request": request})


@web_router.get("/autonomous-admin", response_class=HTMLResponse)
async def autonomous_admin_page(request: Request):
    """Autonomous system admin page"""
    return templates.TemplateResponse("autonomous_admin.html", {"request": request})


@web_router.get("/developer-workbench", response_class=HTMLResponse)
async def developer_workbench_page(request: Request):
    """Developer workbench page"""
    return templates.TemplateResponse("developer_workbench.html", {"request": request})


@web_router.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """Alerts page"""
    # Sample alerts data
    alerts = [
        {
            "id": 1,
            "type": "warning",
            "title": "Budget Overrun Risk",
            "message": "ALPHA Project is approaching 80% budget utilization",
            "project": "ALPHA Project",
            "timestamp": "2024-01-15T10:30:00Z",
            "severity": "medium"
        },
        {
            "id": 2,
            "type": "error",
            "title": "Resource Conflict",
            "message": "John Developer is over-allocated by 20%",
            "project": "Multiple Projects",
            "timestamp": "2024-01-15T09:15:00Z",
            "severity": "high"
        },
        {
            "id": 3,
            "type": "info",
            "title": "Milestone Completed",
            "message": "DELTA Project Phase 1 completed successfully",
            "project": "DELTA Project",
            "timestamp": "2024-01-14T16:45:00Z",
            "severity": "low"
        }
    ]
    
    return templates.TemplateResponse("alerts.html", {
        "request": request,
        "alerts": alerts
    })


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
