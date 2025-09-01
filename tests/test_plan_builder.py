#!/usr/bin/env python3
"""
Tests for Document Plan Builder functionality
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.services.plan_builder import PlanBuilderService
from app.services.ai_guardrails import AIGuardrails


class TestPlanBuilderService:
    """Test cases for PlanBuilderService"""
    
    @pytest.fixture
    def plan_builder(self):
        return PlanBuilderService()
    
    @pytest.fixture
    def sample_hld_content(self):
        return """
        High-Level Design Document
        
        System Architecture:
        1. Frontend Layer
           - React.js application
           - User interface components
           - State management with Redux
        
        2. Backend Layer
           - RESTful API with FastAPI
           - Database layer with PostgreSQL
           - Authentication and authorization
        
        3. Data Layer
           - PostgreSQL database
           - Redis for caching
           - File storage system
        
        Technical Requirements:
        - Scalable microservices architecture
        - Containerized deployment with Docker
        - CI/CD pipeline with GitHub Actions
        - Monitoring and logging with Prometheus/Grafana
        """
    
    @pytest.fixture
    def sample_brd_content(self):
        return """
        Business Requirements Document
        
        Business Objectives:
        1. Improve project management efficiency
        2. Reduce manual planning time by 50%
        3. Enhance stakeholder communication
        4. Increase project success rate
        
        Functional Requirements:
        - Automated project planning from documents
        - Real-time project tracking and reporting
        - Resource allocation optimization
        - Risk assessment and mitigation
        
        User Stories:
        - As a Project Manager, I want to upload documents and generate project plans
        - As a Team Lead, I want to track task progress and resource utilization
        - As a Stakeholder, I want to receive automated status reports
        """
    
    @pytest.fixture
    def sample_srs_content(self):
        return """
        Software Requirements Specification
        
        System Overview:
        The system shall provide automated project management capabilities including
        document processing, plan generation, and project tracking.
        
        Functional Requirements:
        FR1. Document Processing
             - Accept HLD, BRD, and SRS documents
             - Extract structured project information
             - Generate work breakdown structures
        
        FR2. Plan Generation
             - Create epics, features, and tasks
             - Estimate effort and duration
             - Identify dependencies and critical path
        
        FR3. Project Tracking
             - Monitor task progress
             - Track resource utilization
             - Generate status reports
        
        Non-Functional Requirements:
        NFR1. Performance: System shall process documents within 30 seconds
        NFR2. Scalability: Support up to 100 concurrent users
        NFR3. Reliability: 99.9% uptime
        """
    
    def test_detect_document_type_hld(self, plan_builder, sample_hld_content):
        """Test HLD document type detection"""
        metadata = {"file_name": "system_design_hld.txt"}
        doc_type = plan_builder._detect_document_type(sample_hld_content, metadata)
        assert doc_type == "hld"
    
    def test_detect_document_type_brd(self, plan_builder, sample_brd_content):
        """Test BRD document type detection"""
        metadata = {"file_name": "business_requirements.txt"}
        doc_type = plan_builder._detect_document_type(sample_brd_content, metadata)
        assert doc_type == "brd"
    
    def test_detect_document_type_srs(self, plan_builder, sample_srs_content):
        """Test SRS document type detection"""
        metadata = {"file_name": "software_spec.txt"}
        doc_type = plan_builder._detect_document_type(sample_srs_content, metadata)
        assert doc_type == "srs"
    
    def test_detect_document_type_by_filename(self, plan_builder):
        """Test document type detection by filename"""
        content = "Some random content"
        metadata = {"file_name": "project_hld_v2.txt"}
        doc_type = plan_builder._detect_document_type(content, metadata)
        assert doc_type == "hld"
    
    def test_detect_document_type_default(self, plan_builder):
        """Test default document type detection"""
        content = "Some random content without clear patterns"
        metadata = {"file_name": "random.txt"}
        doc_type = plan_builder._detect_document_type(content, metadata)
        assert doc_type == "srs"  # Default fallback
    
    @pytest.mark.asyncio
    async def test_parse_extraction_response_valid(self, plan_builder):
        """Test parsing valid AI response"""
        response = """
        Here's the extracted plan:
        
        ```json
        {
            "epics": [
                {
                    "id": "epic_1",
                    "name": "Frontend Development",
                    "description": "User interface components",
                    "priority": "high"
                }
            ],
            "features": [
                {
                    "id": "feature_1",
                    "epic_id": "epic_1",
                    "name": "User Authentication",
                    "description": "Login and registration",
                    "complexity": "medium"
                }
            ],
            "tasks": [
                {
                    "id": "task_1",
                    "feature_id": "feature_1",
                    "name": "Implement Login Form",
                    "description": "Create login UI",
                    "type": "development",
                    "estimated_hours": 8
                }
            ],
            "summary": "Frontend development plan"
        }
        ```
        """
        
        result = plan_builder._parse_extraction_response(response)
        
        assert "epics" in result
        assert "features" in result
        assert "tasks" in result
        assert "summary" in result
        assert len(result["epics"]) == 1
        assert len(result["features"]) == 1
        assert len(result["tasks"]) == 1
        assert result["epics"][0]["name"] == "Frontend Development"
    
    @pytest.mark.asyncio
    async def test_parse_extraction_response_invalid(self, plan_builder):
        """Test parsing invalid AI response"""
        response = "Invalid response without JSON"
        result = plan_builder._parse_extraction_response(response)
        
        assert "epics" in result
        assert "features" in result
        assert "tasks" in result
        assert "summary" in result
        assert result["summary"] == "Failed to parse AI response"
        assert len(result["epics"]) == 0
        assert len(result["features"]) == 0
        assert len(result["tasks"]) == 0
    
    @pytest.mark.asyncio
    async def test_parse_dependency_response(self, plan_builder):
        """Test parsing dependency analysis response"""
        response = """
        ```json
        {
            "dependencies": [
                {
                    "from_id": "task_1",
                    "to_id": "task_2",
                    "type": "finish_to_start",
                    "lag": 0,
                    "description": "Task 2 depends on Task 1 completion"
                }
            ],
            "critical_path": ["task_1", "task_2"],
            "dependency_graph": {
                "task_1": ["task_2"],
                "task_2": []
            }
        }
        ```
        """
        
        result = plan_builder._parse_dependency_response(response)
        
        assert "dependencies" in result
        assert "critical_path" in result
        assert "dependency_graph" in result
        assert len(result["dependencies"]) == 1
        assert result["dependencies"][0]["from_id"] == "task_1"
    
    @pytest.mark.asyncio
    async def test_parse_risk_response(self, plan_builder):
        """Test parsing risk assessment response"""
        response = """
        ```json
        {
            "risks": [
                {
                    "id": "risk_1",
                    "name": "Technical Risk",
                    "description": "Complex integration requirements",
                    "probability": "medium",
                    "impact": "high",
                    "severity": "high",
                    "affected_tasks": ["task_1"],
                    "mitigation_strategy": "Early prototyping"
                }
            ],
            "risk_summary": {
                "high_risks": 1,
                "medium_risks": 0,
                "low_risks": 0,
                "total_risks": 1
            }
        }
        ```
        """
        
        result = plan_builder._parse_risk_response(response)
        
        assert "risks" in result
        assert "risk_summary" in result
        assert len(result["risks"]) == 1
        assert result["risks"][0]["name"] == "Technical Risk"
    
    @pytest.mark.asyncio
    async def test_parse_effort_response(self, plan_builder):
        """Test parsing effort estimation response"""
        response = """
        ```json
        {
            "task_efforts": [
                {
                    "task_id": "task_1",
                    "estimated_hours": 8,
                    "confidence": "high",
                    "assumptions": ["Experienced developer"],
                    "complexity_factors": ["UI complexity"]
                }
            ],
            "total_effort": 8,
            "effort_distribution": {
                "development": 8,
                "testing": 0,
                "deployment": 0,
                "documentation": 0
            }
        }
        ```
        """
        
        result = plan_builder._parse_effort_response(response)
        
        assert "task_efforts" in result
        assert "total_effort" in result
        assert "effort_distribution" in result
        assert len(result["task_efforts"]) == 1
        assert result["task_efforts"][0]["estimated_hours"] == 8


class TestPlanBuilderAPI:
    """Test cases for Plan Builder API endpoints"""
    
    @pytest.fixture
    def client(self):
        from main import app
        return TestClient(app)
    
    def test_get_document_types(self, client):
        """Test getting supported document types"""
        response = client.get("/api/v1/plan-builder/document-types")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "supported_types" in data
        assert "hld" in data["supported_types"]
        assert "brd" in data["supported_types"]
        assert "srs" in data["supported_types"]
        assert "file_extensions" in data
    
    @pytest.mark.asyncio
    async def test_extract_from_text_success(self, client):
        """Test successful plan extraction from text"""
        with patch('app.services.plan_builder.PlanBuilderService.extract_plan_from_document') as mock_extract:
            mock_extract.return_value = {
                "success": True,
                "document_type": "srs",
                "extraction": {
                    "epics": [{"id": "epic_1", "name": "Test Epic"}],
                    "features": [{"id": "feature_1", "name": "Test Feature"}],
                    "tasks": [{"id": "task_1", "name": "Test Task"}],
                    "summary": "Test summary"
                },
                "dependencies": {"dependencies": []},
                "risks": {"risks": []},
                "efforts": {"task_efforts": []},
                "validation": {"is_valid": True, "violations": []},
                "metadata": {"extraction_date": "2024-01-01T00:00:00"}
            }
            
            response = client.post(
                "/api/v1/plan-builder/extract-from-text",
                data={
                    "document_content": "Test document content",
                    "document_name": "test.txt"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["document_type"] == "srs"
    
    @pytest.mark.asyncio
    async def test_extract_from_text_failure(self, client):
        """Test plan extraction failure"""
        with patch('app.services.plan_builder.PlanBuilderService.extract_plan_from_document') as mock_extract:
            mock_extract.return_value = {
                "success": False,
                "error": "AI model unavailable",
                "document_type": "unknown"
            }
            
            response = client.post(
                "/api/v1/plan-builder/extract-from-text",
                data={
                    "document_content": "Test document content",
                    "document_name": "test.txt"
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Plan extraction failed" in data["detail"]
    
    def test_validate_plan_success(self, client):
        """Test plan validation success"""
        with patch('app.services.ai_guardrails.AIGuardrails.validate_extracted_plan') as mock_validate:
            mock_validate.return_value = AsyncMock(
                is_valid=True,
                violations=[],
                repair_suggestions=[],
                confidence_score=0.9
            )
            
            plan_data = {
                "extraction": {"epics": [], "features": [], "tasks": []},
                "dependencies": {"dependencies": []},
                "risks": {"risks": []},
                "efforts": {"task_efforts": []}
            }
            
            response = client.post(
                "/api/v1/plan-builder/validate-plan",
                json=plan_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["validation"]["is_valid"] is True
            assert data["validation"]["confidence_score"] == 0.9
    
    def test_repair_plan_success(self, client):
        """Test plan repair success"""
        with patch('app.services.ai_guardrails.AIGuardrails.repair_extracted_plan') as mock_repair:
            mock_repair.return_value = {
                "extraction": {"epics": [], "features": [], "tasks": []},
                "dependencies": {"dependencies": []},
                "risks": {"risks": []},
                "efforts": {"task_efforts": []}
            }
            
            plan_data = {"extraction": {"epics": [], "features": [], "tasks": []}}
            violations = [
                {
                    "rule_name": "required_field",
                    "severity": "error",
                    "message": "Missing required field",
                    "field_path": "epics[0].name",
                    "current_value": None,
                    "expected_value": "non_empty_value"
                }
            ]
            
            response = client.post(
                "/api/v1/plan-builder/repair-plan",
                json={"plan_data": plan_data, "violations": violations}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "repaired_plan" in data


class TestPlanBuilderIntegration:
    """Integration tests for Plan Builder functionality"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_plan_extraction(self):
        """Test end-to-end plan extraction workflow"""
        plan_builder = PlanBuilderService()
        
        # Sample document content
        document_content = """
        Software Requirements Specification
        
        System Overview:
        The system shall provide automated project management capabilities.
        
        Functional Requirements:
        FR1. Document Processing
             - Accept HLD, BRD, and SRS documents
             - Extract structured project information
        
        FR2. Plan Generation
             - Create epics, features, and tasks
             - Estimate effort and duration
        
        Non-Functional Requirements:
        NFR1. Performance: System shall process documents within 30 seconds
        NFR2. Scalability: Support up to 100 concurrent users
        """
        
        document_metadata = {
            "file_name": "test_srs.txt",
            "file_size": len(document_content),
            "file_type": "txt",
            "source": "test",
            "upload_date": "2024-01-01T00:00:00"
        }
        
        # Mock AI model calls
        with patch.object(plan_builder, '_call_ai_model') as mock_ai:
            # Mock responses for different AI calls
            mock_ai.side_effect = [
                # Extraction response
                json.dumps({
                    "epics": [{"id": "epic_1", "name": "Document Processing", "priority": "high"}],
                    "features": [{"id": "feature_1", "epic_id": "epic_1", "name": "File Upload", "complexity": "medium"}],
                    "tasks": [{"id": "task_1", "feature_id": "feature_1", "name": "Implement Upload", "type": "development", "estimated_hours": 8}],
                    "summary": "Document processing system"
                }),
                # Dependency analysis response
                json.dumps({
                    "dependencies": [{"from_id": "task_1", "to_id": "task_2", "type": "finish_to_start"}],
                    "critical_path": ["task_1", "task_2"],
                    "dependency_graph": {"task_1": ["task_2"]}
                }),
                # Risk assessment response
                json.dumps({
                    "risks": [{"id": "risk_1", "name": "Technical Risk", "description": "Complex integration", "severity": "medium"}],
                    "risk_summary": {"high_risks": 0, "medium_risks": 1, "low_risks": 0, "total_risks": 1}
                }),
                # Effort estimation response
                json.dumps({
                    "task_efforts": [{"task_id": "task_1", "estimated_hours": 8, "confidence": "high"}],
                    "total_effort": 8,
                    "effort_distribution": {"development": 8, "testing": 0, "deployment": 0, "documentation": 0}
                })
            ]
            
            # Mock guardrails validation
            with patch.object(plan_builder.guardrails, 'validate_extracted_plan') as mock_validate:
                mock_validate.return_value = AsyncMock(
                    is_valid=True,
                    violations=[],
                    repair_suggestions=[],
                    confidence_score=0.9
                )
                
                # Execute plan extraction
                result = await plan_builder.extract_plan_from_document(
                    document_content=document_content,
                    document_metadata=document_metadata
                )
                
                # Verify results
                assert result["success"] is True
                assert result["document_type"] == "srs"
                assert "extraction" in result
                assert "dependencies" in result
                assert "risks" in result
                assert "efforts" in result
                assert "validation" in result
                assert "metadata" in result
                
                # Verify extraction content
                extraction = result["extraction"]
                assert len(extraction["epics"]) == 1
                assert len(extraction["features"]) == 1
                assert len(extraction["tasks"]) == 1
                assert extraction["epics"][0]["name"] == "Document Processing"
                assert extraction["features"][0]["name"] == "File Upload"
                assert extraction["tasks"][0]["name"] == "Implement Upload"
                
                # Verify AI was called 4 times (extraction, dependencies, risks, efforts)
                assert mock_ai.call_count == 4
