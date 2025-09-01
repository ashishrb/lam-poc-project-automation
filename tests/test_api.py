"""
API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


class TestHealthEndpoints:
    """Test health check and basic endpoints."""
    
    @pytest.mark.api
    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "database" in data
    
    @pytest.mark.api
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint redirect."""
        response = client.get("/")
        
        # Should redirect to docs or return basic info
        assert response.status_code in [200, 302, 307]


class TestWebRoutes:
    """Test web interface routes."""
    
    @pytest.mark.api
    def test_web_home(self, client: TestClient):
        """Test web home page."""
        response = client.get("/web/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_web_projects(self, client: TestClient):
        """Test web projects page."""
        response = client.get("/web/projects")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_web_dashboards(self, client: TestClient):
        """Test dashboard pages."""
        dashboard_routes = [
            "/web/manager",
            "/web/executive", 
            "/web/employee"
        ]
        
        for route in dashboard_routes:
            response = client.get(route)
            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_web_error_handling(self, client: TestClient):
        """Test web error handling."""
        response = client.get("/web/nonexistent-page")
        
        # Should return 404 or redirect
        assert response.status_code in [404, 302, 307]


class TestAPIv1Endpoints:
    """Test API v1 endpoints."""
    
    @pytest.mark.api
    def test_api_health(self, client: TestClient):
        """Test API health endpoint."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.api
    def test_projects_endpoint(self, client: TestClient):
        """Test projects API endpoint."""
        # Test GET projects (may require auth)
        response = client.get("/api/v1/projects/")
        
        # Should return 200 (if no auth required) or 401/403 (if auth required)
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            # If successful, should return JSON
            data = response.json()
            assert isinstance(data, (list, dict))
    
    @pytest.mark.api
    def test_tasks_endpoint(self, client: TestClient):
        """Test tasks API endpoint."""
        response = client.get("/api/v1/tasks/")
        
        # Should return 200 (if no auth required) or 401/403 (if auth required)
        assert response.status_code in [200, 401, 403]
    
    @pytest.mark.api
    def test_resources_endpoint(self, client: TestClient):
        """Test resources API endpoint."""
        response = client.get("/api/v1/resources/")
        
        # Should return 200 (if no auth required) or 401/403 (if auth required)
        assert response.status_code in [200, 401, 403]


class TestAIFirstEndpoints:
    """Test AI-First API endpoints."""
    
    @pytest.mark.api
    @pytest.mark.ai
    def test_ai_autoplan_endpoint(self, client: TestClient):
        """Test AI autoplan endpoint."""
        payload = {
            "project_id": 1,
            "document_content": "Sample project requirements document",
            "constraints": {
                "budget": 100000,
                "timeline": "6 months"
            }
        }
        
        response = client.post("/api/v1/ai-first/autoplan", json=payload)
        
        # Should return 200 (success) or 401/403 (auth required) or 422 (validation error)
        assert response.status_code in [200, 401, 403, 422]
        
        if response.status_code == 422:
            # Validation error is expected without proper setup
            data = response.json()
            assert "detail" in data
    
    @pytest.mark.api
    @pytest.mark.ai
    def test_ai_allocate_endpoint(self, client: TestClient):
        """Test AI resource allocation endpoint."""
        payload = {
            "project_id": 1,
            "task_ids": [1, 2, 3],
            "resource_constraints": {
                "max_hours_per_day": 8
            }
        }
        
        response = client.post("/api/v1/ai-first/allocate", json=payload)
        
        # Should return appropriate status code
        assert response.status_code in [200, 401, 403, 422]
    
    @pytest.mark.api
    @pytest.mark.ai
    def test_ai_status_update_endpoint(self, client: TestClient):
        """Test AI status update generation endpoint."""
        payload = {
            "user_id": 1,
            "project_id": 1,
            "policy_id": 1
        }
        
        response = client.post("/api/v1/ai-first/status-update", json=payload)
        
        # Should return appropriate status code
        assert response.status_code in [200, 401, 403, 422]


class TestDocumentEndpoints:
    """Test document management endpoints."""
    
    @pytest.mark.api
    def test_documents_list(self, client: TestClient):
        """Test documents list endpoint."""
        response = client.get("/api/v1/documents/")
        
        assert response.status_code in [200, 401, 403]
    
    @pytest.mark.api
    def test_document_upload_endpoint_exists(self, client: TestClient):
        """Test that document upload endpoint exists."""
        # Test with empty data to check endpoint existence
        response = client.post("/api/v1/documents/upload")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.api
    @pytest.mark.auth
    def test_auth_login_endpoint_exists(self, client: TestClient):
        """Test that auth login endpoint exists."""
        response = client.post("/api/v1/auth/login")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    @pytest.mark.api
    @pytest.mark.auth
    def test_auth_token_endpoint_exists(self, client: TestClient):
        """Test that auth token endpoint exists."""
        response = client.post("/api/v1/auth/token")
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


class TestErrorHandling:
    """Test API error handling."""
    
    @pytest.mark.api
    def test_404_error_handling(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/api/v1/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.api
    def test_method_not_allowed(self, client: TestClient):
        """Test method not allowed error."""
        # Try POST on a GET-only endpoint
        response = client.post("/api/v1/health")
        
        assert response.status_code == 405
    
    @pytest.mark.api
    def test_invalid_json_handling(self, client: TestClient):
        """Test invalid JSON handling."""
        response = client.post(
            "/api/v1/projects/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]


class TestAPIValidation:
    """Test API request validation."""
    
    @pytest.mark.api
    def test_project_creation_validation(self, client: TestClient):
        """Test project creation with invalid data."""
        invalid_payloads = [
            {},  # Empty payload
            {"name": ""},  # Empty name
            {"name": "Test", "start_date": "invalid-date"},  # Invalid date
        ]
        
        for payload in invalid_payloads:
            response = client.post("/api/v1/projects/", json=payload)
            
            # Should return validation error
            assert response.status_code in [400, 422]
    
    @pytest.mark.api
    def test_task_creation_validation(self, client: TestClient):
        """Test task creation with invalid data."""
        invalid_payloads = [
            {},  # Empty payload
            {"name": "", "project_id": 1},  # Empty name
            {"name": "Test", "estimated_hours": -10},  # Negative hours
        ]
        
        for payload in invalid_payloads:
            response = client.post("/api/v1/tasks/", json=payload)
            
            # Should return validation error
            assert response.status_code in [400, 422]


class TestAPIPerformance:
    """Test API performance."""
    
    @pytest.mark.api
    @pytest.mark.performance
    def test_health_endpoint_performance(self, client: TestClient):
        """Test health endpoint response time."""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    @pytest.mark.api
    @pytest.mark.performance
    def test_multiple_requests_performance(self, client: TestClient):
        """Test multiple requests performance."""
        import time
        
        start_time = time.time()
        
        # Make multiple requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
        
        end_time = time.time()
        
        # All requests should complete within reasonable time
        assert (end_time - start_time) < 5.0


class TestCORS:
    """Test CORS configuration."""
    
    @pytest.mark.api
    def test_cors_headers(self, client: TestClient):
        """Test CORS headers are present."""
        response = client.options("/api/v1/health")
        
        # Check for CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers or response.status_code == 405
    
    @pytest.mark.api
    def test_preflight_request(self, client: TestClient):
        """Test preflight request handling."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = client.options("/api/v1/projects/", headers=headers)
        
        # Should handle preflight request
        assert response.status_code in [200, 204, 405]


class TestContentTypes:
    """Test content type handling."""
    
    @pytest.mark.api
    def test_json_content_type(self, client: TestClient):
        """Test JSON content type handling."""
        response = client.get("/api/v1/health")
        
        if response.status_code == 200:
            assert "application/json" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_html_content_type(self, client: TestClient):
        """Test HTML content type for web routes."""
        response = client.get("/web/")
        
        if response.status_code == 200:
            assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.api
    def test_unsupported_content_type(self, client: TestClient):
        """Test unsupported content type handling."""
        response = client.post(
            "/api/v1/projects/",
            data="test data",
            headers={"Content-Type": "text/plain"}
        )
        
        # Should return 415 (Unsupported Media Type) or 422 (Validation Error)
        assert response.status_code in [415, 422]
