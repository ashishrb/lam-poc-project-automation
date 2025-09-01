#!/usr/bin/env python3
"""
Pydantic schemas for resource optimization
"""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class CalendarType(str, Enum):
    """Calendar types for different regions/organizations"""
    STANDARD = "standard"
    US_FEDERAL = "us_federal"
    EUROPEAN = "european"
    ASIA_PACIFIC = "asia_pacific"
    CUSTOM = "custom"

class SkillLevel(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class AssignmentStrategy(str, Enum):
    """Resource assignment strategies"""
    BEST_FIT = "best_fit"
    LOAD_BALANCE = "load_balance"
    SKILL_OPTIMIZATION = "skill_optimization"
    COST_OPTIMIZATION = "cost_optimization"
    AVAILABILITY_FIRST = "availability_first"

# Working Hours Schema
class WorkingHoursSchema(BaseModel):
    start_time: str = Field(default="09:00", description="Start time in HH:MM format")
    end_time: str = Field(default="17:00", description="End time in HH:MM format")
    days_per_week: int = Field(default=5, description="Number of working days per week")
    hours_per_day: float = Field(default=8.0, description="Hours per working day")
    timezone: str = Field(default="UTC", description="Timezone for working hours")

# Holiday Schema
class HolidaySchema(BaseModel):
    name: str = Field(..., description="Holiday name")
    holiday_date: date = Field(..., description="Holiday date")
    is_recurring: bool = Field(default=True, description="Whether holiday recurs annually")
    description: Optional[str] = Field(None, description="Holiday description")

# Calendar Schema
class CalendarSchema(BaseModel):
    calendar_type: str = Field(..., description="Calendar type")
    working_hours: WorkingHoursSchema = Field(..., description="Working hours configuration")
    holidays: List[HolidaySchema] = Field(..., description="List of holidays")
    working_days: List[int] = Field(..., description="Working days (0=Monday, 6=Sunday)")

# Calendar Response
class CalendarResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    calendar: Optional[CalendarSchema] = Field(None, description="Calendar configuration")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Working Day Check
class WorkingDayCheckRequest(BaseModel):
    check_date: date = Field(..., description="Date to check")
    calendar_type: CalendarType = Field(default=CalendarType.STANDARD, description="Calendar type to use")

class WorkingDayCheckResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    is_working_day: bool = Field(..., description="Whether the date is a working day")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Working Hours Calculation
class WorkingHoursRequest(BaseModel):
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    calendar_type: CalendarType = Field(default=CalendarType.STANDARD, description="Calendar type to use")

class WorkingHoursResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    total_hours: float = Field(..., description="Total working hours")
    working_days: int = Field(..., description="Number of working days")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Resource Availability
class ResourceAvailabilityRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")

class AssignedTaskInfo(BaseModel):
    id: int = Field(..., description="Task ID")
    name: str = Field(..., description="Task name")
    hours: Optional[float] = Field(None, description="Estimated hours")

class ResourceAvailabilityData(BaseModel):
    user_id: int = Field(..., description="User ID")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    available_hours: float = Field(..., description="Available hours")
    assigned_hours: float = Field(..., description="Assigned hours")
    utilization_rate: float = Field(..., description="Utilization percentage")
    conflicts: List[str] = Field(default=[], description="Conflicts or issues")

class ResourceAvailabilityResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    availability: Optional[ResourceAvailabilityData] = Field(None, description="Availability data")
    assigned_tasks: List[AssignedTaskInfo] = Field(default=[], description="Assigned tasks")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Skill-based Recommendations
class SkillBasedRecommendationRequest(BaseModel):
    task_id: int = Field(..., description="Task ID")
    strategy: AssignmentStrategy = Field(default=AssignmentStrategy.BEST_FIT, description="Assignment strategy")

class AssignmentRecommendationData(BaseModel):
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    task_id: int = Field(..., description="Task ID")
    task_name: str = Field(..., description="Task name")
    skill_match_score: float = Field(..., description="Skill match score (0-1)")
    availability_score: float = Field(..., description="Availability score (0-1)")
    cost_score: float = Field(..., description="Cost score (0-1)")
    overall_score: float = Field(..., description="Overall recommendation score")
    reasoning: str = Field(..., description="Reasoning for recommendation")
    estimated_hours: float = Field(..., description="Estimated hours")
    start_date: date = Field(..., description="Task start date")
    end_date: date = Field(..., description="Task end date")

class SkillBasedRecommendationResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    recommendations: List[AssignmentRecommendationData] = Field(default=[], description="Recommendations")
    task: Optional[Dict[str, Any]] = Field(None, description="Task information")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Resource Heatmap
class ResourceHeatmapRequest(BaseModel):
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")

class ResourceHeatmapDataPoint(BaseModel):
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    heatmap_date: date = Field(..., description="Date")
    utilization_percentage: float = Field(..., description="Utilization percentage")
    assigned_hours: float = Field(..., description="Assigned hours")
    available_hours: float = Field(..., description="Available hours")
    project_count: int = Field(..., description="Number of projects")
    task_count: int = Field(..., description="Number of tasks")
    status: str = Field(..., description="Status: available, busy, overloaded, unavailable")

class ResourceHeatmapResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    heatmap_data: List[ResourceHeatmapDataPoint] = Field(default=[], description="Heatmap data points")
    date_range: Dict[str, date] = Field(..., description="Date range")
    total_users: int = Field(..., description="Total number of users")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Resource Optimization
class ResourceOptimizationRequest(BaseModel):
    project_id: int = Field(..., description="Project ID")
    strategy: AssignmentStrategy = Field(default=AssignmentStrategy.BEST_FIT, description="Optimization strategy")

class OptimizationResult(BaseModel):
    task_id: int = Field(..., description="Task ID")
    task_name: str = Field(..., description="Task name")
    recommended_user: Dict[str, Any] = Field(..., description="Recommended user information")

class ResourceOptimizationResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    optimization_results: List[OptimizationResult] = Field(default=[], description="Optimization results")
    strategy: str = Field(..., description="Strategy used")
    total_tasks: int = Field(..., description="Total tasks in project")
    optimized_tasks: int = Field(..., description="Number of tasks optimized")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Skill Management
class SkillInfo(BaseModel):
    name: str = Field(..., description="Skill name")
    level: SkillLevel = Field(..., description="Skill level")
    years_experience: float = Field(default=0.0, description="Years of experience")
    certifications: List[str] = Field(default=[], description="Certifications")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

class UserSkillProfile(BaseModel):
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    skills: List[SkillInfo] = Field(default=[], description="User skills")
    total_skills: int = Field(..., description="Total number of skills")
    average_level: str = Field(..., description="Average skill level")

class SkillProfileResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    skill_profile: Optional[UserSkillProfile] = Field(None, description="Skill profile")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Assignment Assistant
class AssignmentAssistantRequest(BaseModel):
    task_id: int = Field(..., description="Task ID")
    preferred_users: Optional[List[int]] = Field(None, description="Preferred user IDs")
    exclude_users: Optional[List[int]] = Field(None, description="User IDs to exclude")
    strategy: AssignmentStrategy = Field(default=AssignmentStrategy.BEST_FIT, description="Assignment strategy")

class AssignmentAssistantResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    recommendations: List[AssignmentRecommendationData] = Field(default=[], description="Recommendations")
    task_info: Optional[Dict[str, Any]] = Field(None, description="Task information")
    filters_applied: Dict[str, Any] = Field(default={}, description="Filters applied")
    error: Optional[str] = Field(None, description="Error message if operation failed")
