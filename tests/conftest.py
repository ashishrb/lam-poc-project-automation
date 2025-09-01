"""
Pytest configuration and shared fixtures
"""

import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import app components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.models import *
from app.services.ai_copilot import AICopilotService
from app.services.rag_engine import RAGEngine
from app.services.ai_first_service import AIFirstService
from app.services.ai_guardrails import AIGuardrails


# Test database configuration
TEST_DATABASE_URL = settings.DATABASE_URL.replace("ppm", "ppm_test")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient, db_session: AsyncSession) -> TestClient:
    """Create an authenticated test client."""
    # TODO: Implement authentication token generation
    client.headers.update({"Authorization": "Bearer test-token"})
    return client


@pytest.fixture(scope="function") 
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Mock basic operations
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result
    
    return mock_session


@pytest.fixture(scope="function")
def ai_copilot_service() -> AICopilotService:
    """Create AI Copilot service instance."""
    return AICopilotService()


@pytest.fixture(scope="function")
def rag_engine() -> RAGEngine:
    """Create RAG engine instance."""
    return RAGEngine()


@pytest.fixture(scope="function")
def ai_first_service() -> AIFirstService:
    """Create AI First service instance."""
    return AIFirstService()


@pytest.fixture(scope="function")
def ai_guardrails() -> AIGuardrails:
    """Create AI Guardrails instance."""
    return AIGuardrails()


@pytest.fixture(scope="function")
def sample_project_data() -> dict:
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for automation",
        "start_date": "2025-01-01",
        "planned_end_date": "2025-06-30",
        "client_name": "Test Client",
        "health_score": 85.0,
        "risk_level": "medium"
    }


@pytest.fixture(scope="function")
def sample_task_data() -> dict:
    """Sample task data for testing."""
    return {
        "name": "Test Task",
        "description": "A test task for automation",
        "estimated_hours": 40.0,
        "start_date": "2025-01-01",
        "due_date": "2025-01-15",
        "priority": "medium",
        "status": "todo"
    }


@pytest.fixture(scope="function")
def sample_wbs_data() -> dict:
    """Sample WBS data for testing."""
    return {
        "tasks": [
            {
                "id": 1,
                "name": "Task 1",
                "description": "First test task",
                "estimated_hours": 40,
                "start_date": "2025-01-01",
                "due_date": "2025-01-15"
            },
            {
                "id": 2,
                "name": "Task 2", 
                "description": "Second test task",
                "estimated_hours": 30,
                "start_date": "2025-01-16",
                "due_date": "2025-01-30"
            }
        ],
        "dependencies": [
            {"from": 1, "to": 2}
        ]
    }


@pytest.fixture(scope="function")
def sample_constraints() -> dict:
    """Sample project constraints for testing."""
    return {
        "budget_limit": 100000,
        "start_date": "2025-01-01",
        "end_date": "2025-06-30",
        "team_size": 5,
        "hourly_rate": 100
    }


@pytest.fixture(scope="function")
def sample_allocation_data() -> dict:
    """Sample resource allocation data for testing."""
    return {
        "allocations": [
            {
                "resource_id": 1,
                "task_id": 1,
                "hours_per_day": 8.0
            },
            {
                "resource_id": 2,
                "task_id": 2,
                "hours_per_day": 6.0
            }
        ]
    }


@pytest.fixture(scope="function")
def mock_ollama_client() -> Mock:
    """Create a mock Ollama client."""
    mock_client = Mock()
    mock_client.generate.return_value = {
        "response": "Test AI response",
        "done": True
    }
    mock_client.chat.return_value = {
        "message": {"content": "Test AI chat response"},
        "done": True
    }
    return mock_client


@pytest.fixture(scope="function")
def mock_redis_client() -> Mock:
    """Create a mock Redis client."""
    mock_redis = Mock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    return mock_redis


@pytest.fixture(scope="function")
def mock_chroma_client() -> Mock:
    """Create a mock ChromaDB client."""
    mock_chroma = Mock()
    mock_collection = Mock()
    mock_collection.query.return_value = {
        "documents": [["Test document content"]],
        "metadatas": [[{"source": "test.txt"}]],
        "distances": [[0.1]]
    }
    mock_chroma.get_or_create_collection.return_value = mock_collection
    return mock_chroma


# Environment setup fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": TEST_DATABASE_URL,
        "REDIS_URL": "redis://localhost:6379/1",  # Use test database
        "JWT_SECRET": "test-secret-key-for-testing-only",
        "AI_FIRST_MODE": "true",
        "AI_GUARDRAILS_ENABLED": "true",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": "8000"
    }
    
    # Set environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield
    
    # Clean up environment variables
    for key in test_env.keys():
        os.environ.pop(key, None)


# Helper functions for tests
def create_test_user(db_session: AsyncSession, **kwargs):
    """Helper to create test user."""
    from app.models.user import User, Role, Tenant
    
    # Create default test data if not provided
    defaults = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "hashed_password",
        "is_active": True
    }
    defaults.update(kwargs)
    
    return User(**defaults)


def create_test_project(db_session: AsyncSession, **kwargs):
    """Helper to create test project."""
    from app.models.project import Project
    from datetime import date, timedelta
    
    defaults = {
        "name": "Test Project",
        "description": "Test project description",
        "status": "active",
        "phase": "execution",
        "start_date": date.today(),
        "planned_end_date": date.today() + timedelta(days=90),
        "health_score": 85.0,
        "risk_level": "medium"
    }
    defaults.update(kwargs)
    
    return Project(**defaults)


def create_test_task(db_session: AsyncSession, **kwargs):
    """Helper to create test task."""
    from app.models.project import Task
    from datetime import date, timedelta
    
    defaults = {
        "name": "Test Task",
        "description": "Test task description",
        "status": "todo",
        "priority": "medium",
        "estimated_hours": 40.0,
        "start_date": date.today(),
        "due_date": date.today() + timedelta(days=14)
    }
    defaults.update(kwargs)
    
    return Task(**defaults)


# Skip markers for optional dependencies
def pytest_configure(config):
    """Configure pytest with custom markers and skip conditions."""
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items based on configuration."""
    # Skip external service tests if services are not available
    skip_external = pytest.mark.skip(reason="External services not available")
    
    for item in items:
        if "external" in item.keywords:
            # Check if external services are available
            if not _check_external_services():
                item.add_marker(skip_external)


def _check_external_services() -> bool:
    """Check if external services are available."""
    # You can implement actual health checks here
    # For now, return True to run all tests
    return True


# Async test utilities
@pytest_asyncio.fixture
async def async_client():
    """Create an async test client."""
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Performance test fixtures
@pytest.fixture
def benchmark_config():
    """Configuration for performance benchmarks."""
    return {
        "rounds": 10,
        "iterations": 100,
        "timeout": 30.0
    }
