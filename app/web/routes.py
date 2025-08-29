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
    return templates.TemplateResponse("dashboards/dashboard.html", {"request": request})


@web_router.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    """Projects page"""
    return templates.TemplateResponse("projects.html", {"request": request})


@web_router.get("/resources", response_class=HTMLResponse)
async def resources_page(request: Request):
    """Resources page"""
    return templates.TemplateResponse("resources.html", {"request": request})


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
