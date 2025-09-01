#!/usr/bin/env python3
"""
Baseline Service for Project Versioning and Change Tracking
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from app.models.project import (
    Project, Task, ProjectBaseline, BaselineTask, ProjectVariance,
    BaselineStatus, VarianceType, TaskStatus, TaskPriority
)
from app.models.user import User

logger = logging.getLogger(__name__)


class BaselineService:
    """Service for managing project baselines and versioning"""
    
    async def create_baseline(
        self,
        project_id: int,
        name: str,
        description: str,
        version: str,
        created_by_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new project baseline"""
        try:
            # Get current project state
            project_query = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get all tasks for the project
            tasks_query = select(Task).where(Task.project_id == project_id)
            tasks_result = await db.execute(tasks_query)
            tasks = tasks_result.scalars().all()
            
            # Create baseline data snapshot
            baseline_data = {
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status.value,
                    "phase": project.phase.value,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
                    "health_score": project.health_score,
                    "risk_level": project.risk_level,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None
                },
                "tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "status": task.status.value,
                        "priority": task.priority.value,
                        "estimated_hours": task.estimated_hours,
                        "actual_hours": task.actual_hours,
                        "start_date": task.start_date.isoformat() if task.start_date else None,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "dependencies": task.dependencies,
                        "assigned_to_id": task.assigned_to_id,
                        "parent_task_id": task.parent_task_id,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat() if task.updated_at else None
                    }
                    for task in tasks
                ],
                "metadata": {
                    "baseline_created_at": datetime.utcnow().isoformat(),
                    "total_tasks": len(tasks),
                    "total_estimated_hours": sum(task.estimated_hours or 0 for task in tasks),
                    "total_actual_hours": sum(task.actual_hours or 0 for task in tasks)
                }
            }
            
            # Create baseline record
            baseline = ProjectBaseline(
                project_id=project_id,
                name=name,
                description=description,
                version=version,
                status=BaselineStatus.DRAFT,
                baseline_data=baseline_data,
                created_by_id=created_by_id
            )
            
            db.add(baseline)
            await db.flush()  # Get the baseline ID
            
            # Create baseline tasks
            baseline_tasks = []
            for task in tasks:
                baseline_task = BaselineTask(
                    baseline_id=baseline.id,
                    task_id=task.id,
                    name=task.name,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    estimated_hours=task.estimated_hours,
                    start_date=task.start_date,
                    due_date=task.due_date,
                    dependencies=task.dependencies,
                    assigned_to_id=task.assigned_to_id
                )
                baseline_tasks.append(baseline_task)
            
            db.add_all(baseline_tasks)
            await db.commit()
            
            logger.info(f"Created baseline {baseline.id} for project {project_id}")
            
            return {
                "success": True,
                "baseline_id": baseline.id,
                "baseline": {
                    "id": baseline.id,
                    "name": baseline.name,
                    "version": baseline.version,
                    "status": baseline.status.value,
                    "created_at": baseline.created_at.isoformat(),
                    "total_tasks": len(baseline_tasks)
                }
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating baseline: {e}")
            raise
    
    async def approve_baseline(
        self,
        baseline_id: int,
        approved_by_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Approve a baseline"""
        try:
            baseline_query = select(ProjectBaseline).where(ProjectBaseline.id == baseline_id)
            baseline_result = await db.execute(baseline_query)
            baseline = baseline_result.scalar_one_or_none()
            
            if not baseline:
                raise ValueError(f"Baseline {baseline_id} not found")
            
            if baseline.status != BaselineStatus.DRAFT:
                raise ValueError(f"Baseline {baseline_id} is not in DRAFT status")
            
            # Update baseline status
            baseline.status = BaselineStatus.APPROVED
            baseline.approved_by_id = approved_by_id
            baseline.approved_at = datetime.utcnow()
            
            # Update project's current baseline
            project_update = update(Project).where(Project.id == baseline.project_id).values(
                current_baseline_id=baseline.id
            )
            await db.execute(project_update)
            
            await db.commit()
            
            logger.info(f"Approved baseline {baseline_id}")
            
            return {
                "success": True,
                "baseline_id": baseline.id,
                "status": baseline.status.value,
                "approved_at": baseline.approved_at.isoformat()
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error approving baseline: {e}")
            raise
    
    async def compare_baselines(
        self,
        baseline_id_1: int,
        baseline_id_2: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Compare two baselines and identify differences"""
        try:
            # Get both baselines
            baseline_query = select(ProjectBaseline).where(
                ProjectBaseline.id.in_([baseline_id_1, baseline_id_2])
            )
            baseline_result = await db.execute(baseline_query)
            baselines = baseline_result.scalars().all()
            
            if len(baselines) != 2:
                raise ValueError("One or both baselines not found")
            
            baseline_1, baseline_2 = baselines
            
            # Extract baseline data
            data_1 = baseline_1.baseline_data
            data_2 = baseline_2.baseline_data
            
            # Compare project-level changes
            project_changes = self._compare_project_data(data_1["project"], data_2["project"])
            
            # Compare tasks
            task_changes = self._compare_task_data(data_1["tasks"], data_2["tasks"])
            
            # Calculate summary metrics
            summary = {
                "project_changes": len(project_changes),
                "task_changes": len(task_changes),
                "tasks_added": len([c for c in task_changes if c["change_type"] == "added"]),
                "tasks_modified": len([c for c in task_changes if c["change_type"] == "modified"]),
                "tasks_removed": len([c for c in task_changes if c["change_type"] == "removed"]),
                "schedule_impact": self._calculate_schedule_impact(task_changes),
                "effort_impact": self._calculate_effort_impact(task_changes)
            }
            
            return {
                "success": True,
                "baseline_1": {
                    "id": baseline_1.id,
                    "name": baseline_1.name,
                    "version": baseline_1.version,
                    "created_at": baseline_1.created_at.isoformat()
                },
                "baseline_2": {
                    "id": baseline_2.id,
                    "name": baseline_2.name,
                    "version": baseline_2.version,
                    "created_at": baseline_2.created_at.isoformat()
                },
                "project_changes": project_changes,
                "task_changes": task_changes,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Error comparing baselines: {e}")
            raise
    
    async def calculate_variances(
        self,
        project_id: int,
        baseline_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate variances between baseline and current project state"""
        try:
            # Get baseline
            baseline_query = select(ProjectBaseline).where(ProjectBaseline.id == baseline_id)
            baseline_result = await db.execute(baseline_query)
            baseline = baseline_result.scalar_one_or_none()
            
            if not baseline:
                raise ValueError(f"Baseline {baseline_id} not found")
            
            # Get current project state
            project_query = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get current tasks
            tasks_query = select(Task).where(Task.project_id == project_id)
            tasks_result = await db.execute(tasks_query)
            current_tasks = tasks_result.scalars().all()
            
            # Get baseline tasks
            baseline_tasks_query = select(BaselineTask).where(BaselineTask.baseline_id == baseline_id)
            baseline_tasks_result = await db.execute(baseline_tasks_query)
            baseline_tasks = baseline_tasks_result.scalars().all()
            
            # Calculate variances
            variances = []
            
            # Project-level variances
            project_variances = self._calculate_project_variances(
                baseline.baseline_data["project"],
                project
            )
            variances.extend(project_variances)
            
            # Task-level variances
            task_variances = self._calculate_task_variances(
                baseline_tasks,
                current_tasks
            )
            variances.extend(task_variances)
            
            # Store variances in database
            variance_records = []
            for variance_data in variances:
                variance = ProjectVariance(
                    project_id=project_id,
                    baseline_id=baseline_id,
                    task_id=variance_data.get("task_id"),
                    variance_type=variance_data["variance_type"],
                    description=variance_data["description"],
                    baseline_value=variance_data["baseline_value"],
                    current_value=variance_data["current_value"],
                    variance_amount=variance_data["variance_amount"],
                    variance_percentage=variance_data["variance_percentage"],
                    impact_level=variance_data["impact_level"]
                )
                variance_records.append(variance)
            
            db.add_all(variance_records)
            await db.commit()
            
            return {
                "success": True,
                "baseline_id": baseline_id,
                "total_variances": len(variances),
                "variances": variances,
                "summary": {
                    "schedule_variances": len([v for v in variances if v["variance_type"] == VarianceType.SCHEDULE.value]),
                    "cost_variances": len([v for v in variances if v["variance_type"] == VarianceType.COST.value]),
                    "scope_variances": len([v for v in variances if v["variance_type"] == VarianceType.SCOPE.value]),
                    "high_impact": len([v for v in variances if v["impact_level"] in ["high", "critical"]])
                }
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error calculating variances: {e}")
            raise
    
    def _compare_project_data(self, project_1: Dict, project_2: Dict) -> List[Dict]:
        """Compare project-level data between two baselines"""
        changes = []
        
        # Compare key fields
        fields_to_compare = [
            "name", "description", "status", "phase", "start_date", 
            "end_date", "planned_end_date", "health_score", "risk_level"
        ]
        
        for field in fields_to_compare:
            value_1 = project_1.get(field)
            value_2 = project_2.get(field)
            
            if value_1 != value_2:
                changes.append({
                    "field": field,
                    "change_type": "modified",
                    "old_value": value_1,
                    "new_value": value_2
                })
        
        return changes
    
    def _compare_task_data(self, tasks_1: List[Dict], tasks_2: List[Dict]) -> List[Dict]:
        """Compare task data between two baselines"""
        changes = []
        
        # Create lookup dictionaries
        tasks_1_dict = {task["id"]: task for task in tasks_1}
        tasks_2_dict = {task["id"]: task for task in tasks_2}
        
        # Find added tasks
        for task_id, task_2 in tasks_2_dict.items():
            if task_id not in tasks_1_dict:
                changes.append({
                    "task_id": task_id,
                    "change_type": "added",
                    "task_name": task_2["name"],
                    "details": task_2
                })
        
        # Find removed tasks
        for task_id, task_1 in tasks_1_dict.items():
            if task_id not in tasks_2_dict:
                changes.append({
                    "task_id": task_id,
                    "change_type": "removed",
                    "task_name": task_1["name"],
                    "details": task_1
                })
        
        # Find modified tasks
        for task_id in tasks_1_dict:
            if task_id in tasks_2_dict:
                task_1 = tasks_1_dict[task_id]
                task_2 = tasks_2_dict[task_id]
                
                task_changes = []
                fields_to_compare = [
                    "name", "description", "status", "priority", "estimated_hours",
                    "start_date", "due_date", "dependencies", "assigned_to_id"
                ]
                
                for field in fields_to_compare:
                    value_1 = task_1.get(field)
                    value_2 = task_2.get(field)
                    
                    if value_1 != value_2:
                        task_changes.append({
                            "field": field,
                            "old_value": value_1,
                            "new_value": value_2
                        })
                
                if task_changes:
                    changes.append({
                        "task_id": task_id,
                        "change_type": "modified",
                        "task_name": task_1["name"],
                        "changes": task_changes
                    })
        
        return changes
    
    def _calculate_schedule_impact(self, task_changes: List[Dict]) -> Dict[str, Any]:
        """Calculate schedule impact of task changes"""
        total_days_impact = 0
        critical_path_impact = 0
        
        for change in task_changes:
            if change["change_type"] == "modified":
                for field_change in change.get("changes", []):
                    if field_change["field"] in ["start_date", "due_date"]:
                        # Simple impact calculation (could be more sophisticated)
                        total_days_impact += 1
        
        return {
            "total_days_impact": total_days_impact,
            "critical_path_impact": critical_path_impact,
            "impact_level": "low" if total_days_impact <= 3 else "medium" if total_days_impact <= 7 else "high"
        }
    
    def _calculate_effort_impact(self, task_changes: List[Dict]) -> Dict[str, Any]:
        """Calculate effort impact of task changes"""
        total_hours_impact = 0
        
        for change in task_changes:
            if change["change_type"] == "modified":
                for field_change in change.get("changes", []):
                    if field_change["field"] == "estimated_hours":
                        old_hours = field_change["old_value"] or 0
                        new_hours = field_change["new_value"] or 0
                        total_hours_impact += abs(new_hours - old_hours)
            elif change["change_type"] == "added":
                total_hours_impact += change["details"].get("estimated_hours", 0)
            elif change["change_type"] == "removed":
                total_hours_impact -= change["details"].get("estimated_hours", 0)
        
        return {
            "total_hours_impact": total_hours_impact,
            "impact_level": "low" if abs(total_hours_impact) <= 8 else "medium" if abs(total_hours_impact) <= 40 else "high"
        }
    
    def _calculate_project_variances(
        self,
        baseline_project: Dict,
        current_project: Project
    ) -> List[Dict]:
        """Calculate project-level variances"""
        variances = []
        
        # Schedule variance
        if baseline_project.get("planned_end_date") and current_project.planned_end_date:
            baseline_end = datetime.fromisoformat(baseline_project["planned_end_date"]).date()
            current_end = current_project.planned_end_date
            
            if baseline_end != current_end:
                days_diff = (current_end - baseline_end).days
                variance_percentage = (days_diff / 30) * 100  # Assuming 30-day baseline
                
                variances.append({
                    "variance_type": VarianceType.SCHEDULE.value,
                    "description": f"Project end date changed from {baseline_end} to {current_end}",
                    "baseline_value": baseline_end.isoformat(),
                    "current_value": current_end.isoformat(),
                    "variance_amount": days_diff,
                    "variance_percentage": variance_percentage,
                    "impact_level": "high" if abs(days_diff) > 7 else "medium" if abs(days_diff) > 3 else "low"
                })
        
        # Health score variance
        baseline_health = baseline_project.get("health_score", 0)
        current_health = current_project.health_score
        
        if baseline_health != current_health:
            health_diff = current_health - baseline_health
            variance_percentage = (health_diff / 100) * 100
            
            variances.append({
                "variance_type": VarianceType.QUALITY.value,
                "description": f"Project health score changed from {baseline_health} to {current_health}",
                "baseline_value": baseline_health,
                "current_value": current_health,
                "variance_amount": health_diff,
                "variance_percentage": variance_percentage,
                "impact_level": "high" if abs(health_diff) > 20 else "medium" if abs(health_diff) > 10 else "low"
            })
        
        return variances
    
    def _calculate_task_variances(
        self,
        baseline_tasks: List[BaselineTask],
        current_tasks: List[Task]
    ) -> List[Dict]:
        """Calculate task-level variances"""
        variances = []
        
        # Create lookup dictionaries
        baseline_tasks_dict = {bt.task_id: bt for bt in baseline_tasks}
        current_tasks_dict = {ct.id: ct for ct in current_tasks}
        
        # Compare each baseline task with current task
        for baseline_task in baseline_tasks:
            current_task = current_tasks_dict.get(baseline_task.task_id)
            
            if not current_task:
                # Task was removed
                variances.append({
                    "task_id": baseline_task.task_id,
                    "variance_type": VarianceType.SCOPE.value,
                    "description": f"Task '{baseline_task.name}' was removed",
                    "baseline_value": baseline_task.estimated_hours,
                    "current_value": 0,
                    "variance_amount": -(baseline_task.estimated_hours or 0),
                    "variance_percentage": -100,
                    "impact_level": "high"
                })
                continue
            
            # Check for effort variance
            if baseline_task.estimated_hours != current_task.estimated_hours:
                baseline_hours = baseline_task.estimated_hours or 0
                current_hours = current_task.estimated_hours or 0
                hours_diff = current_hours - baseline_hours
                
                if baseline_hours > 0:
                    variance_percentage = (hours_diff / baseline_hours) * 100
                else:
                    variance_percentage = 100 if current_hours > 0 else 0
                
                variances.append({
                    "task_id": baseline_task.task_id,
                    "variance_type": VarianceType.COST.value,
                    "description": f"Task '{baseline_task.name}' effort changed from {baseline_hours}h to {current_hours}h",
                    "baseline_value": baseline_hours,
                    "current_value": current_hours,
                    "variance_amount": hours_diff,
                    "variance_percentage": variance_percentage,
                    "impact_level": "high" if abs(hours_diff) > 8 else "medium" if abs(hours_diff) > 4 else "low"
                })
            
            # Check for schedule variance
            if baseline_task.due_date and current_task.due_date:
                if baseline_task.due_date != current_task.due_date:
                    days_diff = (current_task.due_date - baseline_task.due_date).days
                    variance_percentage = (days_diff / 7) * 100  # Assuming 1-week baseline
                    
                    variances.append({
                        "task_id": baseline_task.task_id,
                        "variance_type": VarianceType.SCHEDULE.value,
                        "description": f"Task '{baseline_task.name}' due date changed from {baseline_task.due_date} to {current_task.due_date}",
                        "baseline_value": baseline_task.due_date.isoformat(),
                        "current_value": current_task.due_date.isoformat(),
                        "variance_amount": days_diff,
                        "variance_percentage": variance_percentage,
                        "impact_level": "high" if abs(days_diff) > 3 else "medium" if abs(days_diff) > 1 else "low"
                    })
        
        # Check for new tasks
        for current_task in current_tasks:
            if current_task.id not in baseline_tasks_dict:
                variances.append({
                    "task_id": current_task.id,
                    "variance_type": VarianceType.SCOPE.value,
                    "description": f"New task '{current_task.name}' was added",
                    "baseline_value": 0,
                    "current_value": current_task.estimated_hours or 0,
                    "variance_amount": current_task.estimated_hours or 0,
                    "variance_percentage": 100,
                    "impact_level": "medium"
                })
        
        return variances
