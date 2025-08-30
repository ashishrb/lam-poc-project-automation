"""
Tests for AI-First PPM System
Tests AI-first flows, guardrails, and background tasks
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.ai_guardrails import AIGuardrails, ValidationResult, GuardrailViolation
from app.services.ai_first_service import AIFirstService
from app.models.ai_draft import AIDraft, DraftType, DraftStatus
from app.models.status_update_policy import StatusUpdatePolicy, UpdateFrequency


class TestAIGuardrails:
    """Test AI Guardrails functionality"""
    
    @pytest.fixture
    def guardrails(self):
        return AIGuardrails()
    
    @pytest.fixture
    def sample_wbs_data(self):
        return {
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "description": "Description 1",
                    "estimated_hours": 40,
                    "start_date": "2025-01-01",
                    "due_date": "2025-01-15"
                },
                {
                    "id": 2,
                    "name": "Task 2",
                    "description": "Description 2",
                    "estimated_hours": 60,
                    "start_date": "2025-01-16",
                    "due_date": "2025-02-15"
                }
            ],
            "dependencies": [
                {"from": 1, "to": 2, "type": "finish_to_start"}
            ]
        }
    
    @pytest.fixture
    def sample_constraints(self):
        return {
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "budget_limit": 100000
        }
    
    @pytest.mark.asyncio
    async def test_validate_wbs_output_valid(self, guardrails, sample_wbs_data, sample_constraints):
        """Test validation of valid WBS output"""
        result = await guardrails.validate_wbs_output(sample_wbs_data, sample_constraints)
        
        assert result.is_valid is True
        assert len(result.violations) == 0
        assert result.confidence_score == 1.0
        assert len(result.repair_suggestions) == 0
    
    @pytest.mark.asyncio
    async def test_validate_wbs_output_missing_required_fields(self, guardrails, sample_constraints):
        """Test validation of WBS with missing required fields"""
        invalid_wbs = {
            "tasks": [
                {
                    "id": 1,
                    "name": "",  # Missing name
                    "description": "",  # Missing description
                    "estimated_hours": 40
                }
            ]
        }
        
        result = await guardrails.validate_wbs_output(invalid_wbs, sample_constraints)
        
        assert result.is_valid is False
        assert len(result.violations) > 0
        assert any(v.rule_name == "required_field" for v in result.violations)
        assert result.confidence_score < 1.0
    
    @pytest.mark.asyncio
    async def test_validate_wbs_output_invalid_dates(self, guardrails, sample_constraints):
        """Test validation of WBS with invalid dates"""
        invalid_wbs = {
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "description": "Description 1",
                    "estimated_hours": 40,
                    "start_date": "2025-01-15",
                    "due_date": "2025-01-01"  # Due date before start date
                }
            ]
        }
        
        result = await guardrails.validate_wbs_output(invalid_wbs, sample_constraints)
        
        assert result.is_valid is False
        assert any(v.rule_name == "date_logic" for v in result.violations)
    
    @pytest.mark.asyncio
    async def test_validate_wbs_output_invalid_dependencies(self, guardrails, sample_constraints):
        """Test validation of WBS with invalid dependencies"""
        invalid_wbs = {
            "tasks": [
                {
                    "id": 1,
                    "name": "Task 1",
                    "description": "Description 1",
                    "estimated_hours": 40
                }
            ],
            "dependencies": [
                {"from": 1, "to": 999}  # Invalid task ID
            ]
        }
        
        result = await guardrails.validate_wbs_output(invalid_wbs, sample_constraints)
        
        assert result.is_valid is False
        assert any(v.rule_name == "dependency_reference" for v in result.violations)
    
    @pytest.mark.asyncio
    async def test_validate_wbs_output_project_constraints(self, guardrails, sample_wbs_data):
        """Test validation against project constraints"""
        invalid_constraints = {
            "start_date": "2025-06-30",
            "end_date": "2025-01-01"  # End before start
        }
        
        result = await guardrails.validate_wbs_output(sample_wbs_data, invalid_constraints)
        
        assert result.is_valid is False
        assert any(v.rule_name == "project_duration" for v in result.violations)
    
    @pytest.mark.asyncio
    async def test_repair_wbs_output(self, guardrails, sample_constraints):
        """Test WBS output repair functionality"""
        invalid_wbs = {
            "tasks": [
                {
                    "id": 1,
                    "name": "",  # Missing name
                    "description": "",  # Missing description
                    "estimated_hours": 40,
                    "start_date": "2025-01-01",
                    "due_date": "2025-01-01"  # Same as start
                }
            ]
        }
        
        # First validate to get violations
        validation_result = await guardrails.validate_wbs_output(invalid_wbs, sample_constraints)
        
        # Then repair
        repaired_wbs = await guardrails.repair_wbs_output(invalid_wbs, validation_result.violations)
        
        # Check that repairs were made
        assert repaired_wbs["tasks"][0]["name"] == "Unnamed Task"
        assert repaired_wbs["tasks"][0]["description"] == "No description provided"
        assert repaired_wbs["tasks"][0]["due_date"] != "2025-01-01"  # Should be fixed


class TestAIFirstService:
    """Test AI-First Service functionality"""
    
    @pytest.fixture
    def ai_service(self):
        return AIFirstService()
    
    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock()
    
    @pytest.mark.asyncio
    async def test_auto_plan_project_success(self, ai_service, mock_db_session):
        """Test successful project auto-planning"""
        with patch.object(ai_service, '_generate_wbs_with_ai') as mock_generate:
            mock_generate.return_value = {
                "wbs": {
                    "tasks": [
                        {
                            "id": 1,
                            "name": "Task 1",
                            "description": "Description 1",
                            "estimated_hours": 40
                        }
                    ]
                },
                "prompt_tokens": 1000,
                "completion_tokens": 500
            }
            
            result = await ai_service.auto_plan_project(
                project_id=1,
                document_content="Sample document",
                constraints={"budget": 100000},
                db=mock_db_session
            )
            
            assert result["success"] is True
            assert "wbs" in result
            assert "draft_id" in result
            assert result["validation"]["is_valid"] is True
    
    @pytest.mark.asyncio
    async def test_auto_plan_project_validation_failure(self, ai_service, mock_db_session):
        """Test project auto-planning with validation failure"""
        with patch.object(ai_service, '_generate_wbs_with_ai') as mock_generate:
            mock_generate.return_value = {
                "wbs": {
                    "tasks": [
                        {
                            "id": 1,
                            "name": "",  # Invalid: missing name
                            "description": "Description 1",
                            "estimated_hours": 40
                        }
                    ]
                },
                "prompt_tokens": 1000,
                "completion_tokens": 500
            }
            
            result = await ai_service.auto_plan_project(
                project_id=1,
                constraints={},
                db=mock_db_session
            )
            
            assert result["success"] is True
            assert result["validation"]["is_valid"] is False
            assert len(result["validation"]["violations"]) > 0
    
    @pytest.mark.asyncio
    async def test_auto_allocate_resources_success(self, ai_service, mock_db_session):
        """Test successful resource allocation"""
        with patch.object(ai_service, '_generate_allocation_with_ai') as mock_generate:
            mock_generate.return_value = {
                "allocation": {
                    "allocations": [
                        {
                            "resource_id": 1,
                            "task_id": 1,
                            "hours_per_day": 8.0
                        }
                    ]
                },
                "prompt_tokens": 800,
                "completion_tokens": 400
            }
            
            result = await ai_service.auto_allocate_resources(
                project_id=1,
                task_ids=[1, 2],
                resource_constraints={"max_hours_per_day": 8},
                db=mock_db_session
            )
            
            assert result["success"] is True
            assert "allocation" in result
            assert "draft_id" in result
    
    @pytest.mark.asyncio
    async def test_generate_status_update_draft(self, ai_service, mock_db_session):
        """Test status update draft generation"""
        with patch.object(ai_service, '_generate_status_update_with_ai') as mock_generate:
            mock_generate.return_value = {
                "draft": "Sample status update draft",
                "confidence": 0.85,
                "prompt_tokens": 400,
                "completion_tokens": 200
            }
            
            result = await ai_service.generate_status_update_draft(
                user_id=1,
                project_id=1,
                policy_id=1,
                db=mock_db_session
            )
            
            assert result["success"] is True
            assert "draft" in result
            assert result["confidence"] == 0.85


class TestAIDraftModel:
    """Test AI Draft model functionality"""
    
    def test_ai_draft_creation(self):
        """Test AI draft creation"""
        draft = AIDraft(
            project_id=1,
            draft_type=DraftType.WBS,
            payload={"tasks": []},
            rationale={"confidence": 0.8}
        )
        
        assert draft.project_id == 1
        assert draft.draft_type == DraftType.WBS
        assert draft.status == DraftStatus.DRAFT
        assert draft.created_by_ai is True
    
    def test_ai_draft_ready_for_review(self):
        """Test AI draft ready for review property"""
        draft = AIDraft(
            project_id=1,
            draft_type=DraftType.WBS,
            payload={"tasks": []},
            rationale={"confidence": 0.8}
        )
        
        assert draft.is_ready_for_review is True
        
        # Add validation errors
        draft.validation_errors = ["Error 1"]
        assert draft.is_ready_for_review is False
    
    def test_ai_draft_confidence_score(self):
        """Test AI draft confidence score property"""
        draft = AIDraft(
            project_id=1,
            draft_type=DraftType.WBS,
            payload={"tasks": []},
            rationale={"confidence": 0.85}
        )
        
        assert draft.confidence_score == 0.85
    
    def test_ai_draft_can_be_published(self):
        """Test AI draft can be published property"""
        draft = AIDraft(
            project_id=1,
            draft_type=DraftType.WBS,
            payload={"tasks": []},
            rationale={"confidence": 0.8}
        )
        
        # Draft should not be publishable initially
        assert draft.can_be_published is False
        
        # Approve the draft
        draft.status = DraftStatus.APPROVED
        assert draft.can_be_published is True
        
        # Add validation errors
        draft.validation_errors = ["Error 1"]
        assert draft.can_be_published is False


class TestStatusUpdatePolicy:
    """Test Status Update Policy functionality"""
    
    def test_policy_creation(self):
        """Test status update policy creation"""
        policy = StatusUpdatePolicy(
            project_id=1,
            name="Weekly Updates",
            description="Weekly team updates",
            frequency=UpdateFrequency.WEEKLY,
            created_by_user_id=1
        )
        
        assert policy.project_id == 1
        assert policy.frequency == UpdateFrequency.WEEKLY
        assert policy.is_active is True
    
    def test_policy_weekday_numbers(self):
        """Test policy weekday number generation"""
        # Weekly policy
        weekly_policy = StatusUpdatePolicy(
            project_id=1,
            name="Weekly",
            frequency=UpdateFrequency.WEEKLY,
            created_by_user_id=1
        )
        assert weekly_policy.get_weekday_numbers() == [0]  # Monday
        
        # Bi-weekly policy
        biweekly_policy = StatusUpdatePolicy(
            project_id=1,
            name="Bi-weekly",
            frequency=UpdateFrequency.BIWEEKLY,
            created_by_user_id=1
        )
        assert biweekly_policy.get_weekday_numbers() == [0, 3]  # Monday and Thursday
        
        # Custom policy
        custom_policy = StatusUpdatePolicy(
            project_id=1,
            name="Custom",
            frequency=UpdateFrequency.CUSTOM,
            custom_days=[1, 3, 5],  # Tuesday, Thursday, Saturday
            created_by_user_id=1
        )
        assert custom_policy.get_weekday_numbers() == [1, 3, 5]


class TestIntegration:
    """Integration tests for AI-first functionality"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_auto_planning(self):
        """Test end-to-end auto-planning flow"""
        # This would test the complete flow from document upload to AI plan generation
        # For now, we'll test the components individually
        guardrails = AIGuardrails()
        
        # Test with valid data
        wbs_data = {
            "tasks": [
                {
                    "id": 1,
                    "name": "Valid Task",
                    "description": "Valid description",
                    "estimated_hours": 40
                }
            ]
        }
        
        constraints = {
            "start_date": "2025-01-01",
            "end_date": "2025-06-30"
        }
        
        result = await guardrails.validate_wbs_output(wbs_data, constraints)
        assert result.is_valid is True
    
    @pytest.mark.asyncio
    async def test_ai_guardrails_repair_flow(self):
        """Test AI guardrails repair flow"""
        guardrails = AIGuardrails()
        
        # Create invalid WBS
        invalid_wbs = {
            "tasks": [
                {
                    "id": 1,
                    "name": "",  # Missing name
                    "description": "",  # Missing description
                    "estimated_hours": 40
                }
            ]
        }
        
        # Validate to get violations
        validation_result = await guardrails.validate_wbs_output(invalid_wbs, {})
        assert validation_result.is_valid is False
        
        # Repair the WBS
        repaired_wbs = await guardrails.repair_wbs_output(invalid_wbs, validation_result.violations)
        
        # Validate repaired WBS
        repair_validation = await guardrails.validate_wbs_output(repaired_wbs, {})
        assert repair_validation.is_valid is True


# Test configuration
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
