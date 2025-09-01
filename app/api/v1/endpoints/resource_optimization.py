#!/usr/bin/env python3
"""
Resource Optimization API endpoints
"""

from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.resource_optimization import ResourceOptimizationService, CalendarType, AssignmentStrategy
from app.schemas.resource_optimization import (
    CalendarResponse, WorkingDayCheckRequest, WorkingDayCheckResponse,
    WorkingHoursRequest, WorkingHoursResponse, ResourceAvailabilityRequest,
    ResourceAvailabilityResponse, SkillBasedRecommendationRequest,
    SkillBasedRecommendationResponse, ResourceHeatmapRequest,
    ResourceHeatmapResponse, ResourceOptimizationRequest,
    ResourceOptimizationResponse, AssignmentAssistantRequest,
    AssignmentAssistantResponse
)

router = APIRouter()
resource_service = ResourceOptimizationService()

@router.get("/calendar/{calendar_type}", response_model=CalendarResponse)
async def get_working_calendar(
    calendar_type: CalendarType = CalendarType.STANDARD
):
    """Get working calendar configuration"""
    result = await resource_service.get_working_calendar(calendar_type)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return CalendarResponse(**result)

@router.post("/calendar/check-working-day", response_model=WorkingDayCheckResponse)
async def check_working_day(request: WorkingDayCheckRequest):
    """Check if a date is a working day"""
    is_working = await resource_service.is_working_day(request.date, request.calendar_type)
    return WorkingDayCheckResponse(
        success=True,
        is_working_day=is_working
    )

@router.post("/calendar/calculate-hours", response_model=WorkingHoursResponse)
async def calculate_working_hours(request: WorkingHoursRequest):
    """Calculate working hours between two dates"""
    total_hours = await resource_service.calculate_working_hours(
        request.start_date, request.end_date, request.calendar_type
    )
    
    # Calculate working days
    working_days = 0
    current_date = request.start_date
    while current_date <= request.end_date:
        if await resource_service.is_working_day(current_date, request.calendar_type):
            working_days += 1
        current_date = current_date.replace(day=current_date.day + 1)
    
    return WorkingHoursResponse(
        success=True,
        total_hours=total_hours,
        working_days=working_days
    )

@router.post("/resources/availability", response_model=ResourceAvailabilityResponse)
async def get_resource_availability(
    request: ResourceAvailabilityRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get resource availability for a specific period"""
    result = await resource_service.get_resource_availability(
        request.user_id, request.start_date, request.end_date, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return ResourceAvailabilityResponse(**result)

@router.post("/resources/skill-recommendations", response_model=SkillBasedRecommendationResponse)
async def get_skill_based_recommendations(
    request: SkillBasedRecommendationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get skill-based assignment recommendations for a task"""
    result = await resource_service.get_skill_based_recommendations(
        request.task_id, request.strategy, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return SkillBasedRecommendationResponse(**result)

@router.post("/resources/heatmap", response_model=ResourceHeatmapResponse)
async def generate_resource_heatmap(
    request: ResourceHeatmapRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate resource heatmap data"""
    result = await resource_service.generate_resource_heatmap(
        request.start_date, request.end_date, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return ResourceHeatmapResponse(**result)

@router.post("/resources/optimize", response_model=ResourceOptimizationResponse)
async def optimize_resource_allocation(
    request: ResourceOptimizationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Optimize resource allocation for a project"""
    result = await resource_service.optimize_resource_allocation(
        request.project_id, request.strategy, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return ResourceOptimizationResponse(**result)

@router.post("/resources/assignment-assistant", response_model=AssignmentAssistantResponse)
async def get_assignment_assistant(
    request: AssignmentAssistantRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get assignment assistant recommendations with filters"""
    # Get basic recommendations
    result = await resource_service.get_skill_based_recommendations(
        request.task_id, request.strategy, db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Apply filters
    recommendations = result["recommendations"]
    filtered_recommendations = []
    
    for rec in recommendations:
        # Apply preferred users filter
        if request.preferred_users and rec.user_id not in request.preferred_users:
            continue
        
        # Apply exclude users filter
        if request.exclude_users and rec.user_id in request.exclude_users:
            continue
        
        filtered_recommendations.append(rec)
    
    # Update recommendations to top 5 filtered results
    filtered_recommendations = filtered_recommendations[:5]
    
    return AssignmentAssistantResponse(
        success=True,
        recommendations=filtered_recommendations,
        task_info=result.get("task"),
        filters_applied={
            "preferred_users": request.preferred_users,
            "exclude_users": request.exclude_users,
            "strategy": request.strategy.value
        }
    )

@router.get("/resources/{user_id}/availability")
async def get_user_availability(
    user_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """Get user availability for a specific period"""
    result = await resource_service.get_resource_availability(
        user_id, start_date, end_date, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/tasks/{task_id}/recommendations")
async def get_task_recommendations(
    task_id: int,
    strategy: AssignmentStrategy = Query(default=AssignmentStrategy.BEST_FIT, description="Assignment strategy"),
    limit: int = Query(default=10, description="Number of recommendations to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get assignment recommendations for a specific task"""
    result = await resource_service.get_skill_based_recommendations(
        task_id, strategy, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Limit recommendations
    result["recommendations"] = result["recommendations"][:limit]
    return result

@router.get("/projects/{project_id}/optimization")
async def get_project_optimization(
    project_id: int,
    strategy: AssignmentStrategy = Query(default=AssignmentStrategy.BEST_FIT, description="Optimization strategy"),
    db: AsyncSession = Depends(get_db)
):
    """Get resource optimization recommendations for a project"""
    result = await resource_service.optimize_resource_allocation(
        project_id, strategy, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/heatmap")
async def get_resource_heatmap(
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    db: AsyncSession = Depends(get_db)
):
    """Get resource heatmap data"""
    result = await resource_service.generate_resource_heatmap(
        start_date, end_date, db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
