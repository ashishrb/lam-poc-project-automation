import pytest
from fastapi.testclient import TestClient
from app.core.config import settings
from app.services.ai_copilot import AICopilotService
from app.services.rag_engine import RAGEngine


def test_config_loading():
    """Test that configuration loads correctly"""
    assert settings.APP_NAME == "Project Portfolio Management System"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.DATABASE_URL is not None
    assert settings.OLLAMA_BASE_URL == "http://localhost:11434"


def test_ai_copilot_initialization():
    """Test AI Copilot service initialization"""
    copilot = AICopilotService()
    assert copilot is not None
    assert len(copilot.tools_registry) > 0
    
    # Check that required tools exist
    tool_names = [tool["name"] for tool in copilot.tools_registry.values()]
    assert "search_docs" in tool_names
    assert "generate_wbs" in tool_names
    assert "forecast_budget" in tool_names


def test_rag_engine_initialization():
    """Test RAG engine initialization"""
    rag = RAGEngine()
    assert rag is not None
    assert rag.collection_name == "project_documents"


def test_tools_registry_structure():
    """Test that tools registry has correct structure"""
    copilot = AICopilotService()
    
    for tool_name, tool in copilot.tools_registry.items():
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool
        assert "returns" in tool
        
        # Check that tool name matches key
        assert tool["name"] == tool_name


def test_environment_variables():
    """Test that required environment variables are set"""
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL", 
        "CHROMA_HOST",
        "CHROMA_PORT",
        "OLLAMA_BASE_URL",
        "JWT_SECRET"
    ]
    
    for var in required_vars:
        assert hasattr(settings, var), f"Missing environment variable: {var}"


def test_ai_model_configuration():
    """Test AI model configuration"""
    assert settings.OLLAMA_REASONER_MODEL == "gpt-oss:20b"
    assert settings.OLLAMA_EMBED_MODEL == "nomic-embed-text:v1.5"
    assert settings.XLAM_MODEL_ID == "Salesforce/Llama-xLAM-2-8b-fc-r"


def test_rag_configuration():
    """Test RAG configuration"""
    assert settings.CHUNK_SIZE == 1000
    assert settings.CHUNK_OVERLAP == 200
    assert settings.MAX_RETRIEVAL_RESULTS == 10


def test_security_configuration():
    """Test security configuration"""
    assert settings.JWT_ALGORITHM == "HS256"
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30


def test_pagination_configuration():
    """Test pagination configuration"""
    assert settings.DEFAULT_PAGE_SIZE == 20
    assert settings.MAX_PAGE_SIZE == 100


if __name__ == "__main__":
    pytest.main([__file__])
