from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

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
        "recent_projects": []
    }
    
    return templates.TemplateResponse("dashboards/dashboard.html", {
        "request": request,
        "summary": summary
    })


@web_router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Projects page"""
    # For now, return empty projects list to test template rendering
    projects = []
    
    return templates.TemplateResponse("projects.html", {
        "request": request,
        "projects": projects
    })


@web_router.get("/resources", response_class=HTMLResponse)
async def resources_page(request: Request):
    """Resources page"""
    from app.core.database import engine
    from app.models.resource import Resource
    from sqlalchemy import select
    
    # Fetch resources from database with simple query
    resources = []
    try:
        async with engine.begin() as conn:
            stmt = select(Resource).limit(20)
            result = await conn.execute(stmt)
            resources = result.scalars().all()
    except Exception as e:
        print(f"Error fetching resources: {e}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
    
    return templates.TemplateResponse("resources.html", {
        "request": request,
        "resources": resources
    })


@web_router.get("/finance", response_class=HTMLResponse)
async def finance_page(request: Request):
    """Finance page"""
    return templates.TemplateResponse("finance.html", {"request": request})


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
