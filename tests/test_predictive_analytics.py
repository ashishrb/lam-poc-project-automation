#!/usr/bin/env python3
"""
Tests for Predictive Analytics Service
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.predictive_analytics import (
    PredictiveAnalyticsService, 
    RiskLevel, 
    MitigationAction,
    RiskFactor,
    RiskAssessment,
    PrescriptiveAction
)
from app.models.project import Project, Task, TaskStatus, TaskPriority, ProjectStatus
from app.models.user import User


class TestPredictiveAnalyticsService:
    """Test cases for PredictiveAnalyticsService"""
    
    @pytest.fixture
    def predictive_service(self):
        """Create PredictiveAnalyticsService instance"""
        return PredictiveAnalyticsService()
    
    @pytest.fixture
    def mock_project(self):
        """Create mock project"""
        return Project(
            id=1,
            name="Test Project",
            description="Test project description",
            status=ProjectStatus.ACTIVE,
            planned_start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=30),
            actual_start_date=date.today(),
            budget=Decimal("10000.00")
        )
    
    @pytest.fixture
    def mock_tasks(self):
        """Create mock tasks"""
        return [
            Task(
                id=1,
                project_id=1,
                title="Task 1",
                description="Test task 1",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                start_date=date.today(),
                due_date=date.today() + timedelta(days=7),
                estimated_hours=40,
                actual_hours=20,
                assigned_to_id=1
            ),
            Task(
                id=2,
                project_id=1,
                title="Task 2",
                description="Test task 2",
                status=TaskStatus.DONE,
                priority=TaskPriority.MEDIUM,
                start_date=date.today() - timedelta(days=7),
                due_date=date.today() - timedelta(days=1),
                estimated_hours=20,
                actual_hours=25,
                assigned_to_id=1
            ),
            Task(
                id=3,
                project_id=1,
                title="Task 3",
                description="Test task 3",
                status=TaskStatus.TODO,
                priority=TaskPriority.LOW,
                start_date=date.today() + timedelta(days=7),
                due_date=date.today() + timedelta(days=14),
                estimated_hours=30,
                actual_hours=0,
                assigned_to_id=None
            )
        ]
    
    @pytest.fixture
    def mock_evm_metrics(self):
        """Create mock EVM metrics"""
        return {
            "schedule_variance": 500,
            "cost_variance": 2000,
            "schedule_performance_index": 0.8,
            "cost_performance_index": 0.9,
            "actual_cost": 5000,
            "planned_value": 6000,
            "earned_value": 4800
        }
    
    @pytest.mark.asyncio
    async def test_calculate_project_risk_score_success(self, predictive_service, mock_project, mock_tasks, mock_evm_metrics):
        """Test successful project risk score calculation"""
        with patch.object(predictive_service, '_get_project', return_value=mock_project), \
             patch.object(predictive_service, '_get_project_tasks', return_value=mock_tasks), \
             patch.object(predictive_service.evm_service, 'calculate_project_evm', return_value={"success": True, "metrics": mock_evm_metrics}):
            
            result = await predictive_service.calculate_project_risk_score(1, AsyncMock())
            
            assert result["success"] is True
            assert "risk_score" in result
            assert "risk_level" in result
            assert "risk_factors" in result
            assert "causal_explanation" in result
            assert "mitigation_actions" in result
            assert "confidence" in result
            assert "last_updated" in result
            assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_calculate_project_risk_score_project_not_found(self, predictive_service):
        """Test project risk score calculation when project not found"""
        with patch.object(predictive_service, '_get_project', return_value=None):
            result = await predictive_service.calculate_project_risk_score(999, AsyncMock())
            
            assert result["success"] is False
            assert "Project 999 not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_calculate_project_risk_score_evm_failure(self, predictive_service, mock_project, mock_tasks):
        """Test project risk score calculation when EVM calculation fails"""
        with patch.object(predictive_service, '_get_project', return_value=mock_project), \
             patch.object(predictive_service, '_get_project_tasks', return_value=mock_tasks), \
             patch.object(predictive_service.evm_service, 'calculate_project_evm', return_value={"success": False, "error": "EVM error"}):
            
            result = await predictive_service.calculate_project_risk_score(1, AsyncMock())
            
            assert result["success"] is False
            assert "Failed to calculate EVM metrics" in result["error"]
    
    @pytest.mark.asyncio
    async def test_calculate_task_risk_score_success(self, predictive_service, mock_project):
        """Test successful task risk score calculation"""
        mock_task = Task(
            id=1,
            project_id=1,
            title="Test Task",
            description="Test task description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            start_date=date.today(),
            due_date=date.today() - timedelta(days=1),  # Overdue
            estimated_hours=40,
            actual_hours=50,  # Over estimated
            assigned_to_id=1,
            dependencies='[2, 3]'
        )
        
        with patch.object(predictive_service, '_get_task', return_value=mock_task), \
             patch.object(predictive_service, '_get_project', return_value=mock_project):
            
            result = await predictive_service.calculate_task_risk_score(1, AsyncMock())
            
            assert result["success"] is True
            assert "risk_score" in result
            assert "risk_level" in result
            assert "risk_factors" in result
            assert "causal_explanation" in result
            assert "mitigation_actions" in result
            assert "confidence" in result
            assert "last_updated" in result
    
    @pytest.mark.asyncio
    async def test_calculate_task_risk_score_task_not_found(self, predictive_service):
        """Test task risk score calculation when task not found"""
        with patch.object(predictive_service, '_get_task', return_value=None):
            result = await predictive_service.calculate_task_risk_score(999, AsyncMock())
            
            assert result["success"] is False
            assert "Task 999 not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_prescriptive_playbook_success(self, predictive_service, mock_project, mock_tasks, mock_evm_metrics):
        """Test successful prescriptive playbook generation"""
        with patch.object(predictive_service, 'calculate_project_risk_score', return_value={
            "success": True,
            "project_id": 1,
            "risk_score": 75.0,
            "risk_level": "high",
            "risk_factors": [
                {
                    "factor_name": "schedule_variance",
                    "factor_value": 0.8,
                    "weight": 0.25,
                    "contribution": 0.2,
                    "description": "High schedule variance"
                }
            ]
        }):
            
            result = await predictive_service.generate_prescriptive_playbook(1, None, AsyncMock())
            
            assert result["success"] is True
            assert "project_id" in result
            assert "risk_level" in result
            assert "playbook" in result
            assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_generate_prescriptive_playbook_risk_level_filter(self, predictive_service):
        """Test prescriptive playbook generation with risk level filter"""
        with patch.object(predictive_service, 'calculate_project_risk_score', return_value={
            "success": True,
            "project_id": 1,
            "risk_score": 25.0,
            "risk_level": "low",
            "risk_factors": []
        }):
            
            result = await predictive_service.generate_prescriptive_playbook(1, RiskLevel.HIGH, AsyncMock())
            
            assert result["success"] is True
            assert "message" in result
            assert "Project risk level (low) doesn't match requested level (high)" in result["message"]
            assert result["playbook"] == []
    
    @pytest.mark.asyncio
    async def test_apply_mitigation_action_success(self, predictive_service):
        """Test successful mitigation action application"""
        action_params = {"task_id": 1, "new_assignee_id": 2}
        
        with patch.object(predictive_service, '_validate_action_parameters', return_value={"valid": True}), \
             patch.object(predictive_service, '_apply_reassign_resource_action', return_value={
                 "success": True,
                 "action": "reassign_resource",
                 "message": "Task 1 reassigned to 2"
             }), \
             patch.object(predictive_service, '_log_mitigation_action'):
            
            result = await predictive_service.apply_mitigation_action(
                1, MitigationAction.REASSIGN_RESOURCE, action_params, AsyncMock()
            )
            
            assert result["success"] is True
            assert result["action"] == "reassign_resource"
            assert "Task 1 reassigned to 2" in result["message"]
    
    @pytest.mark.asyncio
    async def test_apply_mitigation_action_invalid_params(self, predictive_service):
        """Test mitigation action application with invalid parameters"""
        action_params = {"task_id": 1}  # Missing new_assignee_id
        
        with patch.object(predictive_service, '_validate_action_parameters', return_value={
            "valid": False, 
            "error": "Missing task_id or new_assignee_id"
        }):
            
            result = await predictive_service.apply_mitigation_action(
                1, MitigationAction.REASSIGN_RESOURCE, action_params, AsyncMock()
            )
            
            assert result["success"] is False
            assert "Invalid action parameters" in result["error"]
    
    @pytest.mark.asyncio
    async def test_predict_project_outcomes_success(self, predictive_service, mock_project, mock_evm_metrics):
        """Test successful project outcome prediction"""
        with patch.object(predictive_service, '_get_project', return_value=mock_project), \
             patch.object(predictive_service.evm_service, 'calculate_project_evm', return_value={
                 "success": True, 
                 "metrics": mock_evm_metrics
             }):
            
            result = await predictive_service.predict_project_outcomes(1, AsyncMock())
            
            assert result["success"] is True
            assert "project_id" in result
            assert "predictions" in result
            assert "confidence_intervals" in result
            assert "trends" in result
            assert "risk_factors" in result
    
    @pytest.mark.asyncio
    async def test_predict_project_outcomes_project_not_found(self, predictive_service):
        """Test project outcome prediction when project not found"""
        with patch.object(predictive_service, '_get_project', return_value=None):
            result = await predictive_service.predict_project_outcomes(999, AsyncMock())
            
            assert result["success"] is False
            assert "Project 999 not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_calculate_risk_factors(self, predictive_service, mock_project, mock_tasks, mock_evm_metrics):
        """Test risk factor calculation"""
        risk_factors = await predictive_service._calculate_risk_factors(mock_project, mock_tasks, mock_evm_metrics)
        
        assert len(risk_factors) == 7  # 7 risk factors
        assert all(isinstance(factor, RiskFactor) for factor in risk_factors)
        
        # Check specific factors
        factor_names = [f.factor_name for f in risk_factors]
        assert "schedule_variance" in factor_names
        assert "cost_variance" in factor_names
        assert "resource_utilization" in factor_names
        assert "task_completion_rate" in factor_names
        assert "dependency_complexity" in factor_names
        assert "scope_volatility" in factor_names
        assert "stakeholder_satisfaction" in factor_names
    
    def test_determine_risk_level(self, predictive_service):
        """Test risk level determination"""
        assert predictive_service._determine_risk_level(10) == RiskLevel.LOW
        assert predictive_service._determine_risk_level(30) == RiskLevel.MEDIUM
        assert predictive_service._determine_risk_level(60) == RiskLevel.HIGH
        assert predictive_service._determine_risk_level(85) == RiskLevel.HIGH
        assert predictive_service._determine_risk_level(95) == RiskLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_generate_causal_explanation(self, predictive_service):
        """Test causal explanation generation"""
        risk_factors = [
            RiskFactor(
                factor_name="schedule_variance",
                factor_value=0.8,
                weight=0.25,
                contribution=0.2,
                description="High schedule variance"
            ),
            RiskFactor(
                factor_name="cost_variance",
                factor_value=0.6,
                weight=0.20,
                contribution=0.12,
                description="Moderate cost variance"
            )
        ]
        
        explanation = await predictive_service._generate_causal_explanation(risk_factors, RiskLevel.HIGH)
        
        assert "high risk level" in explanation.lower()
        assert "schedule variance" in explanation.lower()
        assert "cost variance" in explanation.lower()
    
    @pytest.mark.asyncio
    async def test_calculate_task_risk_factors(self, predictive_service, mock_project):
        """Test task risk factor calculation"""
        mock_task = Task(
            id=1,
            project_id=1,
            title="Test Task",
            description="Test task description",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            start_date=date.today(),
            due_date=date.today() - timedelta(days=1),  # Overdue
            estimated_hours=40,
            actual_hours=50,  # Over estimated
            assigned_to_id=1,
            dependencies='[2, 3]'
        )
        
        risk_factors = await predictive_service._calculate_task_risk_factors(mock_task, mock_project, AsyncMock())
        
        assert len(risk_factors) >= 3  # At least overdue, priority, and dependencies
        assert all(isinstance(factor, RiskFactor) for factor in risk_factors)
        
        # Check for overdue factor
        overdue_factors = [f for f in risk_factors if f.factor_name == "overdue"]
        assert len(overdue_factors) == 1
        assert overdue_factors[0].factor_value > 0
    
    @pytest.mark.asyncio
    async def test_validate_action_parameters(self, predictive_service):
        """Test action parameter validation"""
        # Valid parameters
        valid_params = {"task_id": 1, "new_assignee_id": 2}
        result = await predictive_service._validate_action_parameters(MitigationAction.REASSIGN_RESOURCE, valid_params)
        assert result["valid"] is True
        
        # Invalid parameters
        invalid_params = {"task_id": 1}  # Missing new_assignee_id
        result = await predictive_service._validate_action_parameters(MitigationAction.REASSIGN_RESOURCE, invalid_params)
        assert result["valid"] is False
        assert "Missing task_id or new_assignee_id" in result["error"]
    
    @pytest.mark.asyncio
    async def test_calculate_confidence(self, predictive_service):
        """Test confidence calculation"""
        risk_factors = [
            RiskFactor(
                factor_name="test",
                factor_value=0.5,
                weight=0.3,
                contribution=0.15,
                description="Test factor"
            )
        ]
        
        confidence = await predictive_service._calculate_confidence(risk_factors)
        assert 0 <= confidence <= 1
    
    @pytest.mark.asyncio
    async def test_predict_outcomes(self, predictive_service, mock_project, mock_evm_metrics):
        """Test outcome prediction"""
        predictions = await predictive_service._predict_outcomes(mock_project, mock_evm_metrics)
        
        assert "completion_date" in predictions
        assert "final_cost" in predictions
        assert "completion_probability" in predictions
        assert "quality_score" in predictions
        assert "stakeholder_satisfaction" in predictions
        assert "completion_date_ci" in predictions
        assert "final_cost_ci" in predictions
        assert "schedule_trend" in predictions
        assert "cost_trend" in predictions
        assert "quality_trend" in predictions
        assert "risk_factors" in predictions


class TestRiskLevel:
    """Test cases for RiskLevel enum"""
    
    def test_risk_level_values(self):
        """Test RiskLevel enum values"""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.MEDIUM == "medium"
        assert RiskLevel.HIGH == "high"
        assert RiskLevel.CRITICAL == "critical"


class TestMitigationAction:
    """Test cases for MitigationAction enum"""
    
    def test_mitigation_action_values(self):
        """Test MitigationAction enum values"""
        assert MitigationAction.SPLIT_TASK == "split_task"
        assert MitigationAction.REASSIGN_RESOURCE == "reassign_resource"
        assert MitigationAction.ESCALATE == "escalate"
        assert MitigationAction.ADD_RESOURCE == "add_resource"
        assert MitigationAction.REDUCE_SCOPE == "reduce_scope"
        assert MitigationAction.EXTEND_TIMELINE == "extend_timeline"
        assert MitigationAction.INCREASE_BUDGET == "increase_budget"
