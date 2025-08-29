from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.api import api_router
from app.web.routes import web_router
from app.core.middleware import AuthMiddleware, AuditMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Project Portfolio Management System...")
    
    # Try to initialize database, but continue if it fails
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database initialized")
        app.state.demo_mode = False
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("🔄 Running in demo mode without database")
        app.state.demo_mode = True
    
    print("✅ System ready")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Project Portfolio Management System",
    description="AI-powered project and portfolio management platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(AuditMiddleware)
app.add_middleware(AuthMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include web routes
app.include_router(web_router, prefix="/web")

# Health check endpoint
@app.get("/health")
async def health_check():
    demo_mode = getattr(app.state, "demo_mode", False)
    return {
        "status": "healthy", 
        "service": "Project Portfolio Management System",
        "demo_mode": demo_mode,
        "database": "connected" if not demo_mode else "disconnected"
    }

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Project Portfolio Management System</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-md-12 text-center">
                    <h1 class="display-4">🚀 Project Portfolio Management System</h1>
                    <p class="lead">AI-powered project and portfolio management platform</p>
                    <div class="mt-4">
                        <a href="/web" class="btn btn-primary btn-lg me-3">Web Interface</a>
                        <a href="/api/docs" class="btn btn-outline-primary btn-lg">API Documentation</a>
                    </div>
                    <div class="mt-4">
                        <h5>Quick Links:</h5>
                        <a href="/web/dashboard" class="btn btn-outline-secondary me-2">Dashboard</a>
                        <a href="/web/projects" class="btn btn-outline-secondary me-2">Projects</a>
                        <a href="/web/resources" class="btn btn-outline-secondary me-2">Resources</a>
                        <a href="/web/finance" class="btn btn-outline-secondary me-2">Finance</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )
