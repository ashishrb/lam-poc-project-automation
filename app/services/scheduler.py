#!/usr/bin/env python3
"""
Scheduler Service for Dynamic Re-planning
Handles constraint solving, resource allocation, and schedule optimization
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.project import Project, Task
from app.models.user import User
from app.models.project import TaskStatus, TaskPriority, ProjectStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConstraintType(str, Enum):
    """Types of scheduling constraints"""
    RESOURCE_AVAILABILITY = "resource_availability"
    DEPENDENCY = "dependency"
    DEADLINE = "deadline"
    WORKING_HOURS = "working_hours"
    SKILL_REQUIREMENT = "skill_requirement"
    BUDGET = "budget"


class RescheduleReason(str, Enum):
    """Reasons for rescheduling"""
    DELAY = "delay"
    RESOURCE_CONFLICT = "resource_conflict"
    DEPENDENCY_CHANGE = "dependency_change"
    SCOPE_CHANGE = "scope_change"
    PRIORITY_CHANGE = "priority_change"
    RESOURCE_UNAVAILABLE = "resource_unavailable"


@dataclass
class SchedulingConstraint:
    """Represents a scheduling constraint"""
    constraint_type: ConstraintType
    task_id: int
    description: str
    severity: str  # low, medium, high, critical
    current_value: Any
    required_value: Any
    is_violated: bool = False


@dataclass
class RescheduleProposal:
    """Proposal for rescheduling a task"""
    task_id: int
    current_start_date: date
    current_end_date: date
    proposed_start_date: date
    proposed_end_date: date
    current_assignee_id: Optional[int]
    proposed_assignee_id: Optional[int]
    reason: RescheduleReason
    impact_level: str  # low, medium, high, critical
    rationale: str
    affected_tasks: List[int] = None
    estimated_delay: int = 0  # days


class SchedulerService:
    """Service for dynamic re-planning and constraint solving"""
    
    def __init__(self):
        self.constraint_weights = {
            ConstraintType.DEADLINE: 1.0,
            ConstraintType.DEPENDENCY: 0.9,
            ConstraintType.RESOURCE_AVAILABILITY: 0.8,
            ConstraintType.SKILL_REQUIREMENT: 0.7,
            ConstraintType.WORKING_HOURS: 0.6,
            ConstraintType.BUDGET: 0.5
        }
    
    async def analyze_project_constraints(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze all constraints for a project"""
        try:
            # Get project and tasks
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            tasks = await self._get_project_tasks(project_id, db)
            
            # Analyze different constraint types
            constraints = []
            
            # Dependency constraints
            dep_constraints = await self._analyze_dependency_constraints(tasks)
            constraints.extend(dep_constraints)
            
            # Resource availability constraints
            resource_constraints = await self._analyze_resource_constraints(tasks, db)
            constraints.extend(resource_constraints)
            
            # Deadline constraints
            deadline_constraints = await self._analyze_deadline_constraints(tasks, project)
            constraints.extend(deadline_constraints)
            
            # Working hours constraints
            hours_constraints = await self._analyze_working_hours_constraints(tasks)
            constraints.extend(hours_constraints)
            
            # Calculate constraint score
            constraint_score = self._calculate_constraint_score(constraints)
            
            return {
                "success": True,
                "project_id": project_id,
                "total_constraints": len(constraints),
                "violated_constraints": len([c for c in constraints if c.is_violated]),
                "constraint_score": constraint_score,
                "constraints": [
                    {
                        "type": c.constraint_type.value,
                        "task_id": c.task_id,
                        "description": c.description,
                        "severity": c.severity,
                        "is_violated": c.is_violated,
                        "current_value": c.current_value,
                        "required_value": c.required_value
                    }
                    for c in constraints
                ],
                "summary": {
                    "critical_violations": len([c for c in constraints if c.is_violated and c.severity == "critical"]),
                    "high_violations": len([c for c in constraints if c.is_violated and c.severity == "high"]),
                    "medium_violations": len([c for c in constraints if c.is_violated and c.severity == "medium"]),
                    "low_violations": len([c for c in constraints if c.is_violated and c.severity == "low"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing project constraints: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_reschedule_proposals(
        self, 
        project_id: int, 
        task_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Generate reschedule proposals for a project or specific task"""
        try:
            # Get project and tasks
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            tasks = await self._get_project_tasks(project_id, db)
            
            if task_id:
                # Reschedule specific task
                target_task = next((t for t in tasks if t.id == task_id), None)
                if not target_task:
                    raise ValueError(f"Task {task_id} not found")
                proposals = await self._generate_task_reschedule_proposals(target_task, tasks, db)
            else:
                # Reschedule entire project
                proposals = await self._generate_project_reschedule_proposals(tasks, db)
            
            return {
                "success": True,
                "project_id": project_id,
                "task_id": task_id,
                "proposals": [
                    {
                        "task_id": p.task_id,
                        "current_start_date": p.current_start_date.isoformat(),
                        "current_end_date": p.current_end_date.isoformat(),
                        "proposed_start_date": p.proposed_start_date.isoformat(),
                        "proposed_end_date": p.proposed_end_date.isoformat(),
                        "current_assignee_id": p.current_assignee_id,
                        "proposed_assignee_id": p.proposed_assignee_id,
                        "reason": p.reason.value,
                        "impact_level": p.impact_level,
                        "rationale": p.rationale,
                        "affected_tasks": p.affected_tasks or [],
                        "estimated_delay": p.estimated_delay
                    }
                    for p in proposals
                ],
                "summary": {
                    "total_proposals": len(proposals),
                    "high_impact": len([p for p in proposals if p.impact_level == "high"]),
                    "medium_impact": len([p for p in proposals if p.impact_level == "medium"]),
                    "low_impact": len([p for p in proposals if p.impact_level == "low"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating reschedule proposals: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def apply_reschedule_proposal(
        self, 
        project_id: int, 
        proposal_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply a reschedule proposal"""
        try:
            task_id = proposal_data["task_id"]
            
            # Get the task
            task = await self._get_task(task_id, db)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Validate proposal
            validation_result = await self._validate_proposal(proposal_data, db)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid proposal: {validation_result['error']}"
                }
            
            # Apply changes
            updates = {}
            
            # Update dates
            if "proposed_start_date" in proposal_data:
                task.start_date = datetime.fromisoformat(proposal_data["proposed_start_date"]).date()
                updates["start_date"] = task.start_date.isoformat()
            
            if "proposed_end_date" in proposal_data:
                task.due_date = datetime.fromisoformat(proposal_data["proposed_end_date"]).date()
                updates["due_date"] = task.due_date.isoformat()
            
            # Update assignee
            if "proposed_assignee_id" in proposal_data:
                task.assigned_to_id = proposal_data["proposed_assignee_id"]
                updates["assigned_to_id"] = task.assigned_to_id
            
            # Commit changes
            await db.commit()
            
            # Log the change
            await self._log_reschedule_change(task_id, proposal_data, updates, db)
            
            return {
                "success": True,
                "task_id": task_id,
                "updates": updates,
                "message": "Reschedule proposal applied successfully"
            }
            
        except Exception as e:
            logger.error(f"Error applying reschedule proposal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def optimize_resource_allocation(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Optimize resource allocation for a project"""
        try:
            # Get project and tasks
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            tasks = await self._get_project_tasks(project_id, db)
            available_resources = await self._get_available_resources(db)
            
            # Analyze current allocation
            current_allocation = await self._analyze_current_allocation(tasks)
            
            # Generate optimization suggestions
            optimizations = await self._generate_optimization_suggestions(
                tasks, available_resources, current_allocation
            )
            
            return {
                "success": True,
                "project_id": project_id,
                "current_allocation": current_allocation,
                "optimizations": optimizations,
                "summary": {
                    "total_suggestions": len(optimizations),
                    "resource_utilization_improvement": self._calculate_utilization_improvement(optimizations),
                    "estimated_cost_savings": self._calculate_cost_savings(optimizations)
                }
            }
            
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _get_project(self, project_id: int, db: AsyncSession) -> Optional[Project]:
        """Get project by ID"""
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()
    
    async def _get_project_tasks(self, project_id: int, db: AsyncSession) -> List[Task]:
        """Get all tasks for a project"""
        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.start_date)
        )
        return result.scalars().all()
    
    async def _get_task(self, task_id: int, db: AsyncSession) -> Optional[Task]:
        """Get task by ID"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    async def _get_available_resources(self, db: AsyncSession) -> List[User]:
        """Get available resources/users"""
        result = await db.execute(select(User).where(User.is_active == True))
        return result.scalars().all()
    
    async def _analyze_dependency_constraints(self, tasks: List[Task]) -> List[SchedulingConstraint]:
        """Analyze dependency constraints"""
        constraints = []
        
        for task in tasks:
            if not task.dependencies:
                continue
            
            try:
                deps = json.loads(task.dependencies)
                if isinstance(deps, list):
                    dep_ids = deps
                elif isinstance(deps, dict) and "dependencies" in deps:
                    dep_ids = deps["dependencies"]
                else:
                    continue
                
                for dep_id in dep_ids:
                    dep_task = next((t for t in tasks if t.id == dep_id), None)
                    if not dep_task:
                        continue
                    
                    # Check if dependency is completed before this task starts
                    if dep_task.due_date and task.start_date:
                        if dep_task.due_date > task.start_date:
                            constraints.append(SchedulingConstraint(
                                constraint_type=ConstraintType.DEPENDENCY,
                                task_id=task.id,
                                description=f"Task {task.id} starts before dependency {dep_id} completes",
                                severity="high",
                                current_value=f"Start: {task.start_date}, Dep End: {dep_task.due_date}",
                                required_value="Dependency must complete before task starts",
                                is_violated=True
                            ))
            
            except (json.JSONDecodeError, TypeError):
                continue
        
        return constraints
    
    async def _analyze_resource_constraints(self, tasks: List[Task], db: AsyncSession) -> List[SchedulingConstraint]:
        """Analyze resource availability constraints"""
        constraints = []
        
        # Group tasks by assignee and date
        resource_schedule = {}
        
        for task in tasks:
            if not task.assigned_to_id or not task.start_date or not task.due_date:
                continue
            
            assignee_id = task.assigned_to_id
            if assignee_id not in resource_schedule:
                resource_schedule[assignee_id] = {}
            
            # Check for overlapping tasks
            current_date = task.start_date
            while current_date <= task.due_date:
                if current_date in resource_schedule[assignee_id]:
                    # Resource conflict found
                    conflicting_task = resource_schedule[assignee_id][current_date]
                    constraints.append(SchedulingConstraint(
                        constraint_type=ConstraintType.RESOURCE_AVAILABILITY,
                        task_id=task.id,
                        description=f"Resource {assignee_id} assigned to multiple tasks on {current_date}",
                        severity="medium",
                        current_value=f"Conflicts with task {conflicting_task.id}",
                        required_value="One task per resource per day",
                        is_violated=True
                    ))
                else:
                    resource_schedule[assignee_id][current_date] = task
                
                current_date += timedelta(days=1)
        
        return constraints
    
    async def _analyze_deadline_constraints(self, tasks: List[Task], project: Project) -> List[SchedulingConstraint]:
        """Analyze deadline constraints"""
        constraints = []
        
        for task in tasks:
            if not task.due_date or not project.planned_end_date:
                continue
            
            # Check if task exceeds project deadline
            if task.due_date > project.planned_end_date:
                constraints.append(SchedulingConstraint(
                    constraint_type=ConstraintType.DEADLINE,
                    task_id=task.id,
                    description=f"Task {task.id} exceeds project deadline",
                    severity="critical",
                    current_value=f"Due: {task.due_date}, Project End: {project.planned_end_date}",
                    required_value="Task must complete before project deadline",
                    is_violated=True
                ))
            
            # Check for overdue tasks
            if task.due_date < date.today() and task.status != TaskStatus.DONE:
                constraints.append(SchedulingConstraint(
                    constraint_type=ConstraintType.DEADLINE,
                    task_id=task.id,
                    description=f"Task {task.id} is overdue",
                    severity="high",
                    current_value=f"Due: {task.due_date}, Today: {date.today()}",
                    required_value="Task should be completed by due date",
                    is_violated=True
                ))
        
        return constraints
    
    async def _analyze_working_hours_constraints(self, tasks: List[Task]) -> List[SchedulingConstraint]:
        """Analyze working hours constraints"""
        constraints = []
        
        for task in tasks:
            if not task.estimated_hours or not task.start_date or not task.due_date:
                continue
            
            # Calculate working days
            working_days = (task.due_date - task.start_date).days + 1
            if working_days <= 0:
                continue
            
            # Assume 8 hours per day
            available_hours = working_days * 8
            
            if task.estimated_hours > available_hours:
                constraints.append(SchedulingConstraint(
                    constraint_type=ConstraintType.WORKING_HOURS,
                    task_id=task.id,
                    description=f"Task {task.id} requires more hours than available working days",
                    severity="medium",
                    current_value=f"Estimated: {task.estimated_hours}h, Available: {available_hours}h",
                    required_value="Task hours must fit within working days",
                    is_violated=True
                ))
        
        return constraints
    
    def _calculate_constraint_score(self, constraints: List[SchedulingConstraint]) -> float:
        """Calculate overall constraint violation score"""
        if not constraints:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for constraint in constraints:
            if constraint.is_violated:
                weight = self.constraint_weights[constraint.constraint_type]
                severity_multiplier = {
                    "low": 0.25,
                    "medium": 0.5,
                    "high": 0.75,
                    "critical": 1.0
                }.get(constraint.severity, 0.5)
                
                total_score += weight * severity_multiplier
            
            total_weight += self.constraint_weights[constraint.constraint_type]
        
        return (total_score / total_weight) * 100 if total_weight > 0 else 0.0
    
    async def _generate_task_reschedule_proposals(
        self, 
        task: Task, 
        all_tasks: List[Task], 
        db: AsyncSession
    ) -> List[RescheduleProposal]:
        """Generate reschedule proposals for a specific task"""
        proposals = []
        
        # Proposal 1: Extend timeline if overdue
        if task.due_date and task.due_date < date.today() and task.status != TaskStatus.DONE:
            new_end_date = date.today() + timedelta(days=7)  # Add 1 week
            proposals.append(RescheduleProposal(
                task_id=task.id,
                current_start_date=task.start_date or date.today(),
                current_end_date=task.due_date,
                proposed_start_date=task.start_date or date.today(),
                proposed_end_date=new_end_date,
                current_assignee_id=task.assigned_to_id,
                proposed_assignee_id=task.assigned_to_id,
                reason=RescheduleReason.DELAY,
                impact_level="medium",
                rationale="Extend timeline to accommodate overdue task",
                estimated_delay=(new_end_date - task.due_date).days
            ))
        
        # Proposal 2: Reassign to available resource
        if task.assigned_to_id:
            # Find alternative resources
            available_resources = await self._get_available_resources(db)
            alternative_resources = [r for r in available_resources if r.id != task.assigned_to_id]
            
            if alternative_resources:
                new_assignee = alternative_resources[0]  # Simple selection
                proposals.append(RescheduleProposal(
                    task_id=task.id,
                    current_start_date=task.start_date or date.today(),
                    current_end_date=task.due_date or (task.start_date + timedelta(days=1)) if task.start_date else date.today(),
                    proposed_start_date=task.start_date or date.today(),
                    proposed_end_date=task.due_date or (task.start_date + timedelta(days=1)) if task.start_date else date.today(),
                    current_assignee_id=task.assigned_to_id,
                    proposed_assignee_id=new_assignee.id,
                    reason=RescheduleReason.RESOURCE_CONFLICT,
                    impact_level="low",
                    rationale=f"Reassign to available resource {new_assignee.name}",
                    estimated_delay=0
                ))
        
        return proposals
    
    async def _generate_project_reschedule_proposals(
        self, 
        tasks: List[Task], 
        db: AsyncSession
    ) -> List[RescheduleProposal]:
        """Generate reschedule proposals for entire project"""
        proposals = []
        
        # Generate proposals for each task
        for task in tasks:
            task_proposals = await self._generate_task_reschedule_proposals(task, tasks, db)
            proposals.extend(task_proposals)
        
        return proposals
    
    async def _validate_proposal(self, proposal_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Validate a reschedule proposal"""
        try:
            task_id = proposal_data["task_id"]
            task = await self._get_task(task_id, db)
            
            if not task:
                return {"valid": False, "error": "Task not found"}
            
            # Check if proposed dates are valid
            if "proposed_start_date" in proposal_data and "proposed_end_date" in proposal_data:
                start_date = datetime.fromisoformat(proposal_data["proposed_start_date"]).date()
                end_date = datetime.fromisoformat(proposal_data["proposed_end_date"]).date()
                
                if start_date > end_date:
                    return {"valid": False, "error": "Start date cannot be after end date"}
                
                if start_date < date.today():
                    return {"valid": False, "error": "Start date cannot be in the past"}
            
            # Check if proposed assignee exists
            if "proposed_assignee_id" in proposal_data:
                assignee_id = proposal_data["proposed_assignee_id"]
                if assignee_id:
                    result = await db.execute(select(User).where(User.id == assignee_id))
                    if not result.scalar_one_or_none():
                        return {"valid": False, "error": "Proposed assignee not found"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _log_reschedule_change(
        self, 
        task_id: int, 
        proposal_data: Dict[str, Any], 
        updates: Dict[str, Any], 
        db: AsyncSession
    ):
        """Log reschedule changes for audit"""
        # This would typically log to an audit table
        logger.info(f"Task {task_id} rescheduled: {updates}")
    
    async def _analyze_current_allocation(self, tasks: List[Task]) -> Dict[str, Any]:
        """Analyze current resource allocation"""
        allocation = {}
        
        for task in tasks:
            if task.assigned_to_id:
                assignee_id = task.assigned_to_id
                if assignee_id not in allocation:
                    allocation[assignee_id] = {
                        "total_tasks": 0,
                        "total_hours": 0,
                        "overlapping_tasks": 0
                    }
                
                allocation[assignee_id]["total_tasks"] += 1
                allocation[assignee_id]["total_hours"] += task.estimated_hours or 0
        
        return allocation
    
    async def _generate_optimization_suggestions(
        self, 
        tasks: List[Task], 
        available_resources: List[User], 
        current_allocation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate resource optimization suggestions"""
        suggestions = []
        
        # Find underutilized resources
        for resource in available_resources:
            if resource.id not in current_allocation:
                suggestions.append({
                    "type": "reassign_to_underutilized",
                    "resource_id": resource.id,
                    "resource_name": resource.name,
                    "description": f"Reassign tasks to underutilized resource {resource.name}",
                    "impact": "medium",
                    "estimated_improvement": "20% better resource utilization"
                })
        
        # Find overutilized resources
        for resource_id, allocation in current_allocation.items():
            if allocation["total_hours"] > 160:  # More than 4 weeks of work
                suggestions.append({
                    "type": "reduce_overload",
                    "resource_id": resource_id,
                    "description": f"Reduce workload for resource {resource_id}",
                    "impact": "high",
                    "estimated_improvement": "Prevent burnout and improve quality"
                })
        
        return suggestions
    
    def _calculate_utilization_improvement(self, optimizations: List[Dict[str, Any]]) -> float:
        """Calculate estimated utilization improvement"""
        return len(optimizations) * 5.0  # Simple estimation
    
    def _calculate_cost_savings(self, optimizations: List[Dict[str, Any]]) -> float:
        """Calculate estimated cost savings"""
        return len(optimizations) * 1000.0  # Simple estimation
