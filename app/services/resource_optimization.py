#!/usr/bin/env python3
"""
Resource Optimization Service
Handles working calendars, holidays, skill-based assignment, and resource optimization
"""

import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.project import Project, Task
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class CalendarType(Enum):
    """Calendar types for different regions/organizations"""
    STANDARD = "standard"
    US_FEDERAL = "us_federal"
    EUROPEAN = "european"
    ASIA_PACIFIC = "asia_pacific"
    CUSTOM = "custom"

class SkillLevel(Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class AssignmentStrategy(Enum):
    """Resource assignment strategies"""
    BEST_FIT = "best_fit"
    LOAD_BALANCE = "load_balance"
    SKILL_OPTIMIZATION = "skill_optimization"
    COST_OPTIMIZATION = "cost_optimization"
    AVAILABILITY_FIRST = "availability_first"

@dataclass
class WorkingHours:
    """Working hours configuration"""
    start_time: str = "09:00"
    end_time: str = "17:00"
    days_per_week: int = 5
    hours_per_day: float = 8.0
    timezone: str = "UTC"

@dataclass
class Holiday:
    """Holiday definition"""
    name: str
    date: date
    is_recurring: bool = True
    description: Optional[str] = None

@dataclass
class Skill:
    """Skill definition"""
    name: str
    level: SkillLevel
    years_experience: float = 0.0
    certifications: List[str] = None
    last_updated: datetime = None

@dataclass
class ResourceAvailability:
    """Resource availability information"""
    user_id: int
    start_date: date
    end_date: date
    available_hours: float
    assigned_hours: float
    utilization_rate: float
    conflicts: List[str] = None

@dataclass
class AssignmentRecommendation:
    """Resource assignment recommendation"""
    user_id: int
    user_name: str
    task_id: int
    task_name: str
    skill_match_score: float
    availability_score: float
    cost_score: float
    overall_score: float
    reasoning: str
    estimated_hours: float
    start_date: date
    end_date: date

@dataclass
class ResourceHeatmapData:
    """Resource heatmap data point"""
    user_id: int
    user_name: str
    date: date
    utilization_percentage: float
    assigned_hours: float
    available_hours: float
    project_count: int
    task_count: int
    status: str  # available, busy, overloaded, unavailable

class ResourceOptimizationService:
    """Service for resource optimization and calendar management"""
    
    def __init__(self):
        # Standard working calendars
        self.calendars = {
            CalendarType.STANDARD: {
                "working_hours": WorkingHours(),
                "holidays": [
                    Holiday("New Year's Day", date(2024, 1, 1)),
                    Holiday("Christmas Day", date(2024, 12, 25)),
                    Holiday("Independence Day", date(2024, 7, 4)),
                    Holiday("Thanksgiving", date(2024, 11, 28)),
                    Holiday("Memorial Day", date(2024, 5, 27)),
                    Holiday("Labor Day", date(2024, 9, 2)),
                ]
            },
            CalendarType.US_FEDERAL: {
                "working_hours": WorkingHours(start_time="08:00", end_time="17:00"),
                "holidays": [
                    Holiday("New Year's Day", date(2024, 1, 1)),
                    Holiday("Martin Luther King Jr. Day", date(2024, 1, 15)),
                    Holiday("Presidents' Day", date(2024, 2, 19)),
                    Holiday("Memorial Day", date(2024, 5, 27)),
                    Holiday("Independence Day", date(2024, 7, 4)),
                    Holiday("Labor Day", date(2024, 9, 2)),
                    Holiday("Columbus Day", date(2024, 10, 14)),
                    Holiday("Veterans Day", date(2024, 11, 11)),
                    Holiday("Thanksgiving", date(2024, 11, 28)),
                    Holiday("Christmas Day", date(2024, 12, 25)),
                ]
            },
            CalendarType.EUROPEAN: {
                "working_hours": WorkingHours(start_time="08:30", end_time="17:30"),
                "holidays": [
                    Holiday("New Year's Day", date(2024, 1, 1)),
                    Holiday("Easter Monday", date(2024, 4, 1)),
                    Holiday("May Day", date(2024, 5, 1)),
                    Holiday("Christmas Day", date(2024, 12, 25)),
                    Holiday("Boxing Day", date(2024, 12, 26)),
                ]
            }
        }
        
        # Skill weights for assignment scoring
        self.skill_weights = {
            "skill_match": 0.4,
            "availability": 0.3,
            "cost": 0.2,
            "experience": 0.1
        }
        
        # Working days (Monday = 0, Sunday = 6)
        self.working_days = [0, 1, 2, 3, 4]  # Monday to Friday
        
    async def get_working_calendar(self, calendar_type: CalendarType = CalendarType.STANDARD) -> Dict[str, Any]:
        """Get working calendar configuration"""
        try:
            calendar = self.calendars.get(calendar_type, self.calendars[CalendarType.STANDARD])
            return {
                "success": True,
                "calendar_type": calendar_type.value,
                "working_hours": calendar["working_hours"],
                "holidays": [holiday.__dict__ for holiday in calendar["holidays"]],
                "working_days": self.working_days
            }
        except Exception as e:
            logger.error(f"Error getting working calendar: {e}")
            return {"success": False, "error": str(e)}
    
    async def is_working_day(self, check_date: date, calendar_type: CalendarType = CalendarType.STANDARD) -> bool:
        """Check if a date is a working day"""
        try:
            # Check if it's a weekend
            if check_date.weekday() in [5, 6]:  # Saturday or Sunday
                return False
            
            # Check if it's a holiday
            calendar = self.calendars.get(calendar_type, self.calendars[CalendarType.STANDARD])
            for holiday in calendar["holidays"]:
                if holiday.date == check_date:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking working day: {e}")
            return False
    
    async def calculate_working_hours(self, start_date: date, end_date: date, 
                                    calendar_type: CalendarType = CalendarType.STANDARD) -> float:
        """Calculate total working hours between two dates"""
        try:
            total_hours = 0.0
            current_date = start_date
            
            calendar = self.calendars.get(calendar_type, self.calendars[CalendarType.STANDARD])
            working_hours = calendar["working_hours"]
            
            while current_date <= end_date:
                if await self.is_working_day(current_date, calendar_type):
                    total_hours += working_hours.hours_per_day
                current_date += timedelta(days=1)
            
            return total_hours
        except Exception as e:
            logger.error(f"Error calculating working hours: {e}")
            return 0.0
    
    async def get_resource_availability(self, user_id: int, start_date: date, end_date: date,
                                      db: AsyncSession) -> Dict[str, Any]:
        """Get resource availability for a specific period"""
        try:
            # Get user information
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                return {"success": False, "error": "User not found"}
            
            # Get assigned tasks for the period
            tasks_query = select(Task).where(
                and_(
                    Task.assignee_id == user_id,
                    or_(
                        and_(Task.start_date <= end_date, Task.end_date >= start_date),
                        and_(Task.start_date >= start_date, Task.start_date <= end_date)
                    )
                )
            )
            tasks_result = await db.execute(tasks_query)
            assigned_tasks = tasks_result.scalars().all()
            
            # Calculate availability
            total_available_hours = await self.calculate_working_hours(start_date, end_date)
            total_assigned_hours = sum(task.estimated_hours or 0 for task in assigned_tasks)
            
            utilization_rate = (total_assigned_hours / total_available_hours * 100) if total_available_hours > 0 else 0
            
            # Check for conflicts
            conflicts = []
            if utilization_rate > 100:
                conflicts.append("Over-allocated")
            if utilization_rate > 80:
                conflicts.append("High utilization")
            
            availability = ResourceAvailability(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                available_hours=total_available_hours,
                assigned_hours=total_assigned_hours,
                utilization_rate=utilization_rate,
                conflicts=conflicts
            )
            
            return {
                "success": True,
                "availability": availability,
                "assigned_tasks": [{"id": task.id, "name": task.name, "hours": task.estimated_hours} 
                                 for task in assigned_tasks]
            }
        except Exception as e:
            logger.error(f"Error getting resource availability: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_skill_based_recommendations(self, task_id: int, db: AsyncSession,
                                           strategy: AssignmentStrategy = AssignmentStrategy.BEST_FIT) -> Dict[str, Any]:
        """Get skill-based assignment recommendations for a task"""
        try:
            # Get task information
            task_query = select(Task).where(Task.id == task_id)
            task_result = await db.execute(task_query)
            task = task_result.scalar_one_or_none()
            
            if not task:
                return {"success": False, "error": "Task not found"}
            
            # Get all available users
            users_query = select(User).where(User.is_active == True)
            users_result = await db.execute(users_query)
            users = users_result.scalars().all()
            
            recommendations = []
            
            for user in users:
                # Calculate skill match score (simplified - in real implementation, this would use actual skill data)
                skill_match_score = await self._calculate_skill_match(user, task)
                
                # Calculate availability score
                availability_score = await self._calculate_availability_score(user, task, db)
                
                # Calculate cost score (lower cost = higher score)
                cost_score = await self._calculate_cost_score(user, task)
                
                # Calculate experience score
                experience_score = await self._calculate_experience_score(user, task)
                
                # Calculate overall score based on strategy
                overall_score = await self._calculate_overall_score(
                    skill_match_score, availability_score, cost_score, experience_score, strategy
                )
                
                # Generate reasoning
                reasoning = await self._generate_assignment_reasoning(
                    skill_match_score, availability_score, cost_score, experience_score, strategy
                )
                
                recommendation = AssignmentRecommendation(
                    user_id=user.id,
                    user_name=f"{user.first_name} {user.last_name}",
                    task_id=task.id,
                    task_name=task.name,
                    skill_match_score=skill_match_score,
                    availability_score=availability_score,
                    cost_score=cost_score,
                    overall_score=overall_score,
                    reasoning=reasoning,
                    estimated_hours=task.estimated_hours or 0,
                    start_date=task.start_date,
                    end_date=task.end_date
                )
                
                recommendations.append(recommendation)
            
            # Sort by overall score (descending)
            recommendations.sort(key=lambda x: x.overall_score, reverse=True)
            
            return {
                "success": True,
                "recommendations": recommendations[:10],  # Top 10 recommendations
                "task": {"id": task.id, "name": task.name, "estimated_hours": task.estimated_hours}
            }
        except Exception as e:
            logger.error(f"Error getting skill-based recommendations: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_resource_heatmap(self, start_date: date, end_date: date, 
                                      db: AsyncSession) -> Dict[str, Any]:
        """Generate resource heatmap data"""
        try:
            # Get all active users
            users_query = select(User).where(User.is_active == True)
            users_result = await db.execute(users_query)
            users = users_result.scalars().all()
            
            heatmap_data = []
            current_date = start_date
            
            while current_date <= end_date:
                for user in users:
                    # Get user's tasks for this date
                    tasks_query = select(Task).where(
                        and_(
                            Task.assignee_id == user.id,
                            Task.start_date <= current_date,
                            Task.end_date >= current_date
                        )
                    )
                    tasks_result = await db.execute(tasks_query)
                    user_tasks = tasks_result.scalars().all()
                    
                    # Calculate utilization
                    assigned_hours = sum(task.estimated_hours or 0 for task in user_tasks)
                    available_hours = 8.0 if await self.is_working_day(current_date) else 0.0
                    utilization_percentage = (assigned_hours / available_hours * 100) if available_hours > 0 else 0
                    
                    # Determine status
                    if utilization_percentage == 0:
                        status = "unavailable" if not await self.is_working_day(current_date) else "available"
                    elif utilization_percentage <= 50:
                        status = "available"
                    elif utilization_percentage <= 80:
                        status = "busy"
                    else:
                        status = "overloaded"
                    
                    heatmap_point = ResourceHeatmapData(
                        user_id=user.id,
                        user_name=f"{user.first_name} {user.last_name}",
                        date=current_date,
                        utilization_percentage=utilization_percentage,
                        assigned_hours=assigned_hours,
                        available_hours=available_hours,
                        project_count=len(set(task.project_id for task in user_tasks)),
                        task_count=len(user_tasks),
                        status=status
                    )
                    
                    heatmap_data.append(heatmap_point)
                
                current_date += timedelta(days=1)
            
            return {
                "success": True,
                "heatmap_data": heatmap_data,
                "date_range": {"start": start_date, "end": end_date},
                "total_users": len(users)
            }
        except Exception as e:
            logger.error(f"Error generating resource heatmap: {e}")
            return {"success": False, "error": str(e)}
    
    async def optimize_resource_allocation(self, project_id: int, db: AsyncSession,
                                        strategy: AssignmentStrategy = AssignmentStrategy.BEST_FIT) -> Dict[str, Any]:
        """Optimize resource allocation for a project"""
        try:
            # Get project tasks
            tasks_query = select(Task).where(Task.project_id == project_id)
            tasks_result = await db.execute(tasks_query)
            tasks = tasks_result.scalars().all()
            
            # Get available users
            users_query = select(User).where(User.is_active == True)
            users_result = await db.execute(users_query)
            users = users_result.scalars().all()
            
            optimization_results = []
            
            for task in tasks:
                if not task.assignee_id:  # Only optimize unassigned tasks
                    task_recommendations = await self.get_skill_based_recommendations(task.id, strategy, db)
                    
                    if task_recommendations["success"] and task_recommendations["recommendations"]:
                        best_recommendation = task_recommendations["recommendations"][0]
                        optimization_results.append({
                            "task_id": task.id,
                            "task_name": task.name,
                            "recommended_user": {
                                "id": best_recommendation.user_id,
                                "name": best_recommendation.user_name,
                                "score": best_recommendation.overall_score,
                                "reasoning": best_recommendation.reasoning
                            }
                        })
            
            return {
                "success": True,
                "optimization_results": optimization_results,
                "strategy": strategy.value,
                "total_tasks": len(tasks),
                "optimized_tasks": len(optimization_results)
            }
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")
            return {"success": False, "error": str(e)}
    
    # Private helper methods
    async def _calculate_skill_match(self, user: User, task: Task) -> float:
        """Calculate skill match score between user and task"""
        # Simplified implementation - in real system, this would use actual skill data
        # For now, return a random score between 0.3 and 1.0
        import random
        return random.uniform(0.3, 1.0)
    
    async def _calculate_availability_score(self, user: User, task: Task, db: AsyncSession) -> float:
        """Calculate availability score for user on task"""
        try:
            availability = await self.get_resource_availability(
                user.id, task.start_date, task.end_date, db
            )
            
            if availability["success"]:
                utilization_rate = availability["availability"].utilization_rate
                if utilization_rate <= 50:
                    return 1.0
                elif utilization_rate <= 80:
                    return 0.7
                elif utilization_rate <= 100:
                    return 0.3
                else:
                    return 0.0
            return 0.5  # Default score if availability check fails
        except Exception:
            return 0.5
    
    async def _calculate_cost_score(self, user: User, task: Task) -> float:
        """Calculate cost score (lower cost = higher score)"""
        # Simplified implementation - in real system, this would use actual cost data
        # For now, return a random score between 0.5 and 1.0
        import random
        return random.uniform(0.5, 1.0)
    
    async def _calculate_experience_score(self, user: User, task: Task) -> float:
        """Calculate experience score based on user's experience with similar tasks"""
        # Simplified implementation - in real system, this would analyze historical data
        # For now, return a random score between 0.4 and 1.0
        import random
        return random.uniform(0.4, 1.0)
    
    async def _calculate_overall_score(self, skill_match: float, availability: float, 
                                     cost: float, experience: float, 
                                     strategy: AssignmentStrategy) -> float:
        """Calculate overall score based on strategy"""
        if strategy == AssignmentStrategy.SKILL_OPTIMIZATION:
            weights = {"skill_match": 0.5, "availability": 0.2, "cost": 0.2, "experience": 0.1}
        elif strategy == AssignmentStrategy.LOAD_BALANCE:
            weights = {"skill_match": 0.3, "availability": 0.4, "cost": 0.2, "experience": 0.1}
        elif strategy == AssignmentStrategy.COST_OPTIMIZATION:
            weights = {"skill_match": 0.3, "availability": 0.2, "cost": 0.4, "experience": 0.1}
        elif strategy == AssignmentStrategy.AVAILABILITY_FIRST:
            weights = {"skill_match": 0.2, "availability": 0.5, "cost": 0.2, "experience": 0.1}
        else:  # BEST_FIT
            weights = self.skill_weights
        
        overall_score = (
            skill_match * weights["skill_match"] +
            availability * weights["availability"] +
            cost * weights["cost"] +
            experience * weights["experience"]
        )
        
        return round(overall_score, 3)
    
    async def _generate_assignment_reasoning(self, skill_match: float, availability: float,
                                           cost: float, experience: float, 
                                           strategy: AssignmentStrategy) -> str:
        """Generate human-readable reasoning for assignment recommendation"""
        reasons = []
        
        if skill_match > 0.8:
            reasons.append("Excellent skill match")
        elif skill_match > 0.6:
            reasons.append("Good skill match")
        
        if availability > 0.8:
            reasons.append("High availability")
        elif availability < 0.3:
            reasons.append("Limited availability")
        
        if cost > 0.8:
            reasons.append("Cost-effective")
        
        if experience > 0.8:
            reasons.append("Experienced with similar tasks")
        
        if strategy == AssignmentStrategy.SKILL_OPTIMIZATION:
            reasons.append("Optimized for skill requirements")
        elif strategy == AssignmentStrategy.LOAD_BALANCE:
            reasons.append("Balanced workload distribution")
        
        return "; ".join(reasons) if reasons else "Good overall fit"
