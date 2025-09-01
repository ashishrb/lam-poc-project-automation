#!/usr/bin/env python3
"""
Tests for Resource Optimization Service
"""

import pytest
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.resource_optimization import (
    ResourceOptimizationService, CalendarType, AssignmentStrategy,
    WorkingHours, Holiday, ResourceAvailability, AssignmentRecommendation,
    ResourceHeatmapData
)
from app.models.project import Project, Task
from app.models.user import User

@pytest.fixture
def resource_service():
    return ResourceOptimizationService()

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.first_name = "John"
    user.last_name = "Doe"
    user.is_active = True
    return user

@pytest.fixture
def mock_task():
    task = MagicMock(spec=Task)
    task.id = 1
    task.name = "Test Task"
    task.estimated_hours = 40.0
    task.start_date = date(2024, 1, 1)
    task.end_date = date(2024, 1, 31)
    task.project_id = 1
    task.assignee_id = None
    return task

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

class TestResourceOptimizationService:
    
    def test_init(self, resource_service):
        """Test service initialization"""
        assert resource_service is not None
        assert len(resource_service.calendars) == 3  # STANDARD, US_FEDERAL, EUROPEAN
        assert resource_service.skill_weights["skill_match"] == 0.4
        assert resource_service.working_days == [0, 1, 2, 3, 4]
    
    @pytest.mark.asyncio
    async def test_get_working_calendar_standard(self, resource_service):
        """Test getting standard working calendar"""
        result = await resource_service.get_working_calendar(CalendarType.STANDARD)
        
        assert result["success"] is True
        assert result["calendar_type"] == "standard"
        assert result["working_hours"].start_time == "09:00"
        assert result["working_hours"].end_time == "17:00"
        assert len(result["holidays"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_working_calendar_us_federal(self, resource_service):
        """Test getting US federal working calendar"""
        result = await resource_service.get_working_calendar(CalendarType.US_FEDERAL)
        
        assert result["success"] is True
        assert result["calendar_type"] == "us_federal"
        assert result["working_hours"].start_time == "08:00"
        assert result["working_hours"].end_time == "17:00"
        assert len(result["holidays"]) > 0
    
    @pytest.mark.asyncio
    async def test_is_working_day_weekday(self, resource_service):
        """Test checking if a weekday is a working day"""
        # Monday, January 1, 2024 (New Year's Day - holiday)
        holiday_date = date(2024, 1, 1)
        is_working = await resource_service.is_working_day(holiday_date)
        assert is_working is False
        
        # Tuesday, January 2, 2024 (regular weekday)
        weekday_date = date(2024, 1, 2)
        is_working = await resource_service.is_working_day(weekday_date)
        assert is_working is True
    
    @pytest.mark.asyncio
    async def test_is_working_day_weekend(self, resource_service):
        """Test checking if a weekend is a working day"""
        # Saturday, January 6, 2024
        saturday_date = date(2024, 1, 6)
        is_working = await resource_service.is_working_day(saturday_date)
        assert is_working is False
        
        # Sunday, January 7, 2024
        sunday_date = date(2024, 1, 7)
        is_working = await resource_service.is_working_day(sunday_date)
        assert is_working is False
    
    @pytest.mark.asyncio
    async def test_calculate_working_hours(self, resource_service):
        """Test calculating working hours between dates"""
        start_date = date(2024, 1, 1)  # Monday (New Year's Day - holiday)
        end_date = date(2024, 1, 5)    # Friday
        
        # Should be 4 working days (Tue-Fri) * 8 hours = 32 hours
        total_hours = await resource_service.calculate_working_hours(start_date, end_date)
        assert total_hours == 32.0
    
    @pytest.mark.asyncio
    async def test_get_resource_availability_success(self, resource_service, mock_user, mock_db):
        """Test getting resource availability successfully"""
        # Mock database queries
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        result = await resource_service.get_resource_availability(
            1, date(2024, 1, 1), date(2024, 1, 31), mock_db
        )
        
        assert result["success"] is True
        assert result["availability"].user_id == 1
        assert result["availability"].utilization_rate == 0.0
        assert result["assigned_tasks"] == []
    
    @pytest.mark.asyncio
    async def test_get_resource_availability_user_not_found(self, resource_service, mock_db):
        """Test getting resource availability when user not found"""
        # Mock database query returning None
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await resource_service.get_resource_availability(
            999, date(2024, 1, 1), date(2024, 1, 31), mock_db
        )
        
        assert result["success"] is False
        assert result["error"] == "User not found"
    
    @pytest.mark.asyncio
    async def test_get_skill_based_recommendations_success(self, resource_service, mock_task, mock_user, mock_db):
        """Test getting skill-based recommendations successfully"""
        # Mock database queries
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]
        
        result = await resource_service.get_skill_based_recommendations(
            1, AssignmentStrategy.BEST_FIT, mock_db
        )
        
        assert result["success"] is True
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0].user_id == 1
        assert result["recommendations"][0].task_id == 1
        assert result["task"]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_get_skill_based_recommendations_task_not_found(self, resource_service, mock_db):
        """Test getting skill-based recommendations when task not found"""
        # Mock database query returning None
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await resource_service.get_skill_based_recommendations(
            999, AssignmentStrategy.BEST_FIT, mock_db
        )
        
        assert result["success"] is False
        assert result["error"] == "Task not found"
    
    @pytest.mark.asyncio
    async def test_generate_resource_heatmap_success(self, resource_service, mock_user, mock_db):
        """Test generating resource heatmap successfully"""
        # Mock database queries
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        result = await resource_service.generate_resource_heatmap(
            date(2024, 1, 1), date(2024, 1, 7), mock_db
        )
        
        assert result["success"] is True
        assert result["total_users"] == 1
        assert len(result["heatmap_data"]) > 0
        assert result["date_range"]["start"] == date(2024, 1, 1)
        assert result["date_range"]["end"] == date(2024, 1, 7)
    
    @pytest.mark.asyncio
    async def test_optimize_resource_allocation_success(self, resource_service, mock_task, mock_user, mock_db):
        """Test optimizing resource allocation successfully"""
        # Mock database queries
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_task]
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]
        
        # Mock skill-based recommendations
        recommendation = AssignmentRecommendation(
            user_id=1,
            user_name="John Doe",
            task_id=1,
            task_name="Test Task",
            skill_match_score=0.8,
            availability_score=0.9,
            cost_score=0.7,
            overall_score=0.8,
            reasoning="Good fit",
            estimated_hours=40.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        # Mock the get_skill_based_recommendations method
        resource_service.get_skill_based_recommendations = AsyncMock(return_value={
            "success": True,
            "recommendations": [recommendation]
        })
        
        result = await resource_service.optimize_resource_allocation(
            1, AssignmentStrategy.BEST_FIT, mock_db
        )
        
        assert result["success"] is True
        assert result["strategy"] == "best_fit"
        assert result["total_tasks"] == 1
        assert result["optimized_tasks"] == 1
    
    @pytest.mark.asyncio
    async def test_calculate_overall_score_best_fit(self, resource_service):
        """Test calculating overall score with best fit strategy"""
        score = await resource_service._calculate_overall_score(
            0.8, 0.9, 0.7, 0.8, AssignmentStrategy.BEST_FIT
        )
        
        # Expected: 0.8*0.4 + 0.9*0.3 + 0.7*0.2 + 0.8*0.1 = 0.32 + 0.27 + 0.14 + 0.08 = 0.81
        assert score == 0.81
    
    @pytest.mark.asyncio
    async def test_calculate_overall_score_skill_optimization(self, resource_service):
        """Test calculating overall score with skill optimization strategy"""
        score = await resource_service._calculate_overall_score(
            0.8, 0.9, 0.7, 0.8, AssignmentStrategy.SKILL_OPTIMIZATION
        )
        
        # Expected: 0.8*0.5 + 0.9*0.2 + 0.7*0.2 + 0.8*0.1 = 0.4 + 0.18 + 0.14 + 0.08 = 0.8
        assert score == 0.8
    
    @pytest.mark.asyncio
    async def test_generate_assignment_reasoning(self, resource_service):
        """Test generating assignment reasoning"""
        reasoning = await resource_service._generate_assignment_reasoning(
            0.8, 0.9, 0.7, 0.8, AssignmentStrategy.SKILL_OPTIMIZATION
        )
        
        assert "Excellent skill match" in reasoning
        assert "High availability" in reasoning
        assert "Optimized for skill requirements" in reasoning
    
    @pytest.mark.asyncio
    async def test_calculate_skill_match(self, resource_service, mock_user, mock_task):
        """Test calculating skill match score"""
        score = await resource_service._calculate_skill_match(mock_user, mock_task)
        
        # Should return a value between 0.3 and 1.0
        assert 0.3 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_availability_score(self, resource_service, mock_user, mock_task, mock_db):
        """Test calculating availability score"""
        # Mock get_resource_availability
        resource_service.get_resource_availability = AsyncMock(return_value={
            "success": True,
            "availability": ResourceAvailability(
                user_id=1,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                available_hours=160.0,
                assigned_hours=80.0,
                utilization_rate=50.0,
                conflicts=[]
            )
        })
        
        score = await resource_service._calculate_availability_score(mock_user, mock_task, mock_db)
        
        # 50% utilization should return 1.0
        assert score == 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_cost_score(self, resource_service, mock_user, mock_task):
        """Test calculating cost score"""
        score = await resource_service._calculate_cost_score(mock_user, mock_task)
        
        # Should return a value between 0.5 and 1.0
        assert 0.5 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_calculate_experience_score(self, resource_service, mock_user, mock_task):
        """Test calculating experience score"""
        score = await resource_service._calculate_experience_score(mock_user, mock_task)
        
        # Should return a value between 0.4 and 1.0
        assert 0.4 <= score <= 1.0

class TestEnums:
    """Test enum values"""
    
    def test_calendar_type_values(self):
        """Test CalendarType enum values"""
        assert CalendarType.STANDARD == "standard"
        assert CalendarType.US_FEDERAL == "us_federal"
        assert CalendarType.EUROPEAN == "european"
        assert CalendarType.ASIA_PACIFIC == "asia_pacific"
        assert CalendarType.CUSTOM == "custom"
    
    def test_skill_level_values(self):
        """Test SkillLevel enum values"""
        assert SkillLevel.BEGINNER == "beginner"
        assert SkillLevel.INTERMEDIATE == "intermediate"
        assert SkillLevel.ADVANCED == "advanced"
        assert SkillLevel.EXPERT == "expert"
    
    def test_assignment_strategy_values(self):
        """Test AssignmentStrategy enum values"""
        assert AssignmentStrategy.BEST_FIT == "best_fit"
        assert AssignmentStrategy.LOAD_BALANCE == "load_balance"
        assert AssignmentStrategy.SKILL_OPTIMIZATION == "skill_optimization"
        assert AssignmentStrategy.COST_OPTIMIZATION == "cost_optimization"
        assert AssignmentStrategy.AVAILABILITY_FIRST == "availability_first"

class TestDataclasses:
    """Test dataclass structures"""
    
    def test_working_hours(self):
        """Test WorkingHours dataclass"""
        wh = WorkingHours()
        assert wh.start_time == "09:00"
        assert wh.end_time == "17:00"
        assert wh.days_per_week == 5
        assert wh.hours_per_day == 8.0
        assert wh.timezone == "UTC"
    
    def test_holiday(self):
        """Test Holiday dataclass"""
        holiday = Holiday("Test Holiday", date(2024, 1, 1))
        assert holiday.name == "Test Holiday"
        assert holiday.date == date(2024, 1, 1)
        assert holiday.is_recurring is True
        assert holiday.description is None
    
    def test_resource_availability(self):
        """Test ResourceAvailability dataclass"""
        availability = ResourceAvailability(
            user_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            available_hours=160.0,
            assigned_hours=80.0,
            utilization_rate=50.0,
            conflicts=["High utilization"]
        )
        
        assert availability.user_id == 1
        assert availability.utilization_rate == 50.0
        assert "High utilization" in availability.conflicts
    
    def test_assignment_recommendation(self):
        """Test AssignmentRecommendation dataclass"""
        recommendation = AssignmentRecommendation(
            user_id=1,
            user_name="John Doe",
            task_id=1,
            task_name="Test Task",
            skill_match_score=0.8,
            availability_score=0.9,
            cost_score=0.7,
            overall_score=0.8,
            reasoning="Good fit",
            estimated_hours=40.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
        
        assert recommendation.user_id == 1
        assert recommendation.user_name == "John Doe"
        assert recommendation.overall_score == 0.8
        assert recommendation.reasoning == "Good fit"
    
    def test_resource_heatmap_data(self):
        """Test ResourceHeatmapData dataclass"""
        heatmap_data = ResourceHeatmapData(
            user_id=1,
            user_name="John Doe",
            date=date(2024, 1, 1),
            utilization_percentage=75.0,
            assigned_hours=6.0,
            available_hours=8.0,
            project_count=2,
            task_count=3,
            status="busy"
        )
        
        assert heatmap_data.user_id == 1
        assert heatmap_data.utilization_percentage == 75.0
        assert heatmap_data.status == "busy"
        assert heatmap_data.project_count == 2
