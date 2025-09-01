#!/usr/bin/env python3
"""
Tests for Baseline and Gantt Services
"""

import pytest
import json
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.baseline_service import BaselineService
from app.services.gantt_cpm_service import GanttCPMService
from app.models.project import (
    Project, Task, ProjectBaseline, BaselineTask, ProjectVariance,
    BaselineStatus, VarianceType, TaskStatus, TaskPriority, ProjectStatus, ProjectPhase
)


class TestBaselineService:
    """Test cases for BaselineService"""
    
    @pytest.fixture
    def baseline_service(self):
        return BaselineService()
    
    def test_compare_project_data(self, baseline_service):
        """Test project data comparison"""
        project_1 = {
            "name": "Project A",
            "description": "Original description",
            "status": "planning",
            "health_score": 85.0
        }
        
        project_2 = {
            "name": "Project A Updated",
            "description": "Updated description",
            "status": "active",
            "health_score": 90.0
        }
        
        changes = baseline_service._compare_project_data(project_1, project_2)
        
        assert len(changes) == 4
        assert any(c["field"] == "name" and c["old_value"] == "Project A" for c in changes)
        assert any(c["field"] == "status" and c["new_value"] == "active" for c in changes)
    
    def test_compare_task_data(self, baseline_service):
        """Test task data comparison"""
        tasks_1 = [
            {"id": 1, "name": "Task 1", "estimated_hours": 8.0},
            {"id": 2, "name": "Task 2", "estimated_hours": 12.0}
        ]
        
        tasks_2 = [
            {"id": 1, "name": "Task 1 Updated", "estimated_hours": 10.0},
            {"id": 3, "name": "Task 3", "estimated_hours": 6.0}
        ]
        
        changes = baseline_service._compare_task_data(tasks_1, tasks_2)
        
        assert len(changes) == 3  # 1 modified, 1 added, 1 removed
        assert any(c["change_type"] == "modified" for c in changes)
        assert any(c["change_type"] == "added" for c in changes)
        assert any(c["change_type"] == "removed" for c in changes)


class TestGanttCPMService:
    """Test cases for GanttCPMService"""
    
    @pytest.fixture
    def gantt_service(self):
        return GanttCPMService()
    
    def test_calculate_duration(self, gantt_service):
        """Test duration calculation"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        
        duration = gantt_service._calculate_duration(start_date, end_date)
        assert duration == 5  # Inclusive
        
        # Test with None dates
        duration_none = gantt_service._calculate_duration(None, end_date)
        assert duration_none == 0
    
    def test_calculate_progress(self, gantt_service):
        """Test progress calculation"""
        # Test done task
        done_task = Task(status=TaskStatus.DONE)
        progress = gantt_service._calculate_progress(done_task)
        assert progress == 100.0
        
        # Test in-progress task with hours
        in_progress_task = Task(
            status=TaskStatus.IN_PROGRESS,
            estimated_hours=10.0,
            actual_hours=5.0
        )
        progress = gantt_service._calculate_progress(in_progress_task)
        assert progress == 50.0
        
        # Test in-progress task without hours
        in_progress_task_no_hours = Task(status=TaskStatus.IN_PROGRESS)
        progress = gantt_service._calculate_progress(in_progress_task_no_hours)
        assert progress == 50.0
        
        # Test review task
        review_task = Task(status=TaskStatus.REVIEW)
        progress = gantt_service._calculate_progress(review_task)
        assert progress == 90.0
        
        # Test blocked task
        blocked_task = Task(status=TaskStatus.BLOCKED)
        progress = gantt_service._calculate_progress(blocked_task)
        assert progress == 0.0
    
    def test_parse_dependencies(self, gantt_service):
        """Test dependency parsing"""
        # Test list format
        deps_list = json.dumps([1, 2, 3])
        result = gantt_service._parse_dependencies(deps_list)
        assert result == [1, 2, 3]
        
        # Test dict format
        deps_dict = json.dumps({"dependencies": [4, 5, 6]})
        result = gantt_service._parse_dependencies(deps_dict)
        assert result == [4, 5, 6]
        
        # Test empty string
        result = gantt_service._parse_dependencies("")
        assert result == []
        
        # Test invalid JSON
        result = gantt_service._parse_dependencies("invalid json")
        assert result == []
    
    def test_calculate_critical_path_algorithm(self, gantt_service):
        """Test CPM algorithm"""
        tasks = [
            {
                "id": 1,
                "name": "Task 1",
                "duration": 3,
                "dependencies": []
            },
            {
                "id": 2,
                "name": "Task 2",
                "duration": 2,
                "dependencies": [1]
            },
            {
                "id": 3,
                "name": "Task 3",
                "duration": 4,
                "dependencies": [1]
            }
        ]
        
        result = gantt_service._calculate_critical_path(tasks)
        
        assert result["project_duration"] == 7  # Task 1 (3) + Task 3 (4)
        assert len(result["critical_path"]) > 0
        assert all(task["is_critical"] == (task["slack"] == 0) for task in result["tasks"])
    
    def test_calculate_project_metrics(self, gantt_service):
        """Test project metrics calculation"""
        from datetime import date
        
        today = date.today()
        future_date = (today + timedelta(days=30)).isoformat()  # 30 days in future
        past_date = (today - timedelta(days=30)).isoformat()    # 30 days in past
        
        tasks = [
            {
                "id": 1,
                "name": "Task 1",
                "status": "done",
                "estimated_hours": 8.0,
                "actual_hours": 8.0,
                "end_date": past_date  # Past date, but completed
            },
            {
                "id": 2,
                "name": "Task 2",
                "status": "in_progress",
                "estimated_hours": 12.0,
                "actual_hours": 6.0,
                "end_date": future_date  # Future date
            },
            {
                "id": 3,
                "name": "Task 3",
                "status": "todo",
                "estimated_hours": 6.0,
                "actual_hours": 0.0,
                "end_date": past_date  # Past date, not completed
            }
        ]
        
        metrics = gantt_service._calculate_project_metrics(tasks)
        
        assert metrics["total_tasks"] == 3
        assert metrics["completed_tasks"] == 1
        assert metrics["in_progress_tasks"] == 1
        assert metrics["overdue_tasks"] == 1  # Only Task 3 should be overdue
        assert metrics["total_estimated_hours"] == 26.0
        assert metrics["total_actual_hours"] == 14.0
        assert metrics["progress_percentage"] == pytest.approx(33.33, rel=1e-2)
