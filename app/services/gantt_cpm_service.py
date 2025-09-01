#!/usr/bin/env python3
"""
Gantt Chart and Critical Path Method (CPM) Service
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.project import Project, Task, TaskStatus, TaskPriority
from app.models.user import User

logger = logging.getLogger(__name__)


class GanttCPMService:
    """Service for Gantt chart generation and Critical Path Method calculations"""
    
    async def generate_gantt_data(
        self,
        project_id: int,
        db: AsyncSession,
        include_completed: bool = True,
        include_dependencies: bool = True
    ) -> Dict[str, Any]:
        """Generate Gantt chart data for a project"""
        try:
            # Get project
            project_query = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Get tasks
            tasks_query = select(Task).where(Task.project_id == project_id)
            if not include_completed:
                tasks_query = tasks_query.where(Task.status != TaskStatus.DONE)
            
            tasks_result = await db.execute(tasks_query)
            tasks = tasks_result.scalars().all()
            
            # Convert tasks to Gantt format
            gantt_tasks = []
            for task in tasks:
                gantt_task = {
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "status": task.status.value,
                    "priority": task.priority.value,
                    "start_date": task.start_date.isoformat() if task.start_date else None,
                    "end_date": task.due_date.isoformat() if task.due_date else None,
                    "duration": self._calculate_duration(task.start_date, task.due_date),
                    "progress": self._calculate_progress(task),
                    "assigned_to": task.assigned_to_id,
                    "parent_task_id": task.parent_task_id,
                    "estimated_hours": task.estimated_hours,
                    "actual_hours": task.actual_hours,
                    "dependencies": self._parse_dependencies(task.dependencies) if task.dependencies else [],
                    "is_critical": False,  # Will be set by CPM calculation
                    "early_start": None,  # Will be set by CPM calculation
                    "early_finish": None,  # Will be set by CPM calculation
                    "late_start": None,  # Will be set by CPM calculation
                    "late_finish": None,  # Will be set by CPM calculation
                    "slack": None  # Will be set by CPM calculation
                }
                gantt_tasks.append(gantt_task)
            
            # Calculate CPM if dependencies are included
            if include_dependencies and gantt_tasks:
                cpm_data = self._calculate_critical_path(gantt_tasks)
                gantt_tasks = cpm_data["tasks"]
                critical_path = cpm_data["critical_path"]
                project_duration = cpm_data["project_duration"]
            else:
                critical_path = []
                project_duration = self._calculate_project_duration(gantt_tasks)
            
            # Calculate project metrics
            metrics = self._calculate_project_metrics(gantt_tasks)
            
            return {
                "success": True,
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
                    "status": project.status.value,
                    "health_score": project.health_score
                },
                "tasks": gantt_tasks,
                "critical_path": critical_path,
                "project_duration": project_duration,
                "metrics": metrics,
                "dependencies": self._extract_dependencies(gantt_tasks) if include_dependencies else []
            }
            
        except Exception as e:
            logger.error(f"Error generating Gantt data: {e}")
            raise
    
    async def calculate_critical_path(
        self,
        project_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate critical path for a project"""
        try:
            # Get tasks with dependencies
            tasks_query = select(Task).where(
                and_(
                    Task.project_id == project_id,
                    Task.dependencies.isnot(None)
                )
            )
            tasks_result = await db.execute(tasks_query)
            tasks = tasks_result.scalars().all()
            
            if not tasks:
                return {
                    "success": True,
                    "critical_path": [],
                    "project_duration": 0,
                    "message": "No tasks with dependencies found"
                }
            
            # Convert to Gantt format
            gantt_tasks = []
            for task in tasks:
                gantt_task = {
                    "id": task.id,
                    "name": task.name,
                    "start_date": task.start_date.isoformat() if task.start_date else None,
                    "end_date": task.due_date.isoformat() if task.due_date else None,
                    "duration": self._calculate_duration(task.start_date, task.due_date),
                    "dependencies": self._parse_dependencies(task.dependencies)
                }
                gantt_tasks.append(gantt_task)
            
            # Calculate critical path
            cpm_data = self._calculate_critical_path(gantt_tasks)
            
            return {
                "success": True,
                "critical_path": cpm_data["critical_path"],
                "project_duration": cpm_data["project_duration"],
                "tasks": cpm_data["tasks"],
                "summary": {
                    "total_tasks": len(gantt_tasks),
                    "critical_tasks": len(cpm_data["critical_path"]),
                    "total_duration": cpm_data["project_duration"],
                    "critical_path_duration": cpm_data["project_duration"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating critical path: {e}")
            raise
    
    def _calculate_duration(self, start_date: Optional[date], end_date: Optional[date]) -> int:
        """Calculate duration in days between two dates"""
        if not start_date or not end_date:
            return 0
        
        return (end_date - start_date).days + 1  # Inclusive
    
    def _calculate_progress(self, task: Task) -> float:
        """Calculate task progress percentage"""
        if task.status == TaskStatus.DONE:
            return 100.0
        elif task.status == TaskStatus.IN_PROGRESS:
            # Estimate progress based on actual hours vs estimated hours
            if task.estimated_hours and task.actual_hours:
                progress = min((task.actual_hours / task.estimated_hours) * 100, 100)
                return max(progress, 10)  # Minimum 10% for in-progress tasks
            else:
                return 50.0  # Default 50% for in-progress tasks
        elif task.status == TaskStatus.REVIEW:
            return 90.0
        elif task.status == TaskStatus.BLOCKED:
            return 0.0
        else:
            return 0.0
    
    def _parse_dependencies(self, dependencies_str: str) -> List[int]:
        """Parse dependencies JSON string to list of task IDs"""
        try:
            if not dependencies_str:
                return []
            
            dependencies = json.loads(dependencies_str)
            if isinstance(dependencies, list):
                return dependencies
            elif isinstance(dependencies, dict) and "dependencies" in dependencies:
                return dependencies["dependencies"]
            else:
                return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _extract_dependencies(self, tasks: List[Dict]) -> List[Dict]:
        """Extract all dependencies from tasks"""
        dependencies = []
        for task in tasks:
            for dep_id in task.get("dependencies", []):
                dependencies.append({
                    "from": dep_id,
                    "to": task["id"],
                    "type": "finish_to_start"  # Default dependency type
                })
        return dependencies
    
    def _calculate_project_duration(self, tasks: List[Dict]) -> int:
        """Calculate total project duration"""
        if not tasks:
            return 0
        
        # Find earliest start and latest end dates
        start_dates = [task["start_date"] for task in tasks if task["start_date"]]
        end_dates = [task["end_date"] for task in tasks if task["end_date"]]
        
        if not start_dates or not end_dates:
            return 0
        
        earliest_start = min(start_dates)
        latest_end = max(end_dates)
        
        return self._calculate_duration(
            datetime.fromisoformat(earliest_start).date(),
            datetime.fromisoformat(latest_end).date()
        )
    
    def _calculate_project_metrics(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Calculate project metrics for Gantt chart"""
        if not tasks:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "in_progress_tasks": 0,
                "overdue_tasks": 0,
                "total_estimated_hours": 0,
                "total_actual_hours": 0,
                "progress_percentage": 0
            }
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t["status"] == "done"])
        in_progress_tasks = len([t for t in tasks if t["status"] == "in_progress"])
        
        # Calculate overdue tasks
        today = date.today()
        overdue_tasks = 0
        for task in tasks:
            if task["end_date"] and task["status"] != "done":
                try:
                    end_date = datetime.fromisoformat(task["end_date"]).date()
                    if end_date < today:
                        overdue_tasks += 1
                except (ValueError, TypeError):
                    # Skip invalid dates
                    continue
        
        # Calculate hours
        total_estimated_hours = sum(task.get("estimated_hours", 0) or 0 for task in tasks)
        total_actual_hours = sum(task.get("actual_hours", 0) or 0 for task in tasks)
        
        # Calculate progress percentage
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": overdue_tasks,
            "total_estimated_hours": total_estimated_hours,
            "total_actual_hours": total_actual_hours,
            "progress_percentage": progress_percentage
        }
    
    def _calculate_critical_path(self, tasks: List[Dict]) -> Dict[str, Any]:
        """Calculate critical path using CPM algorithm"""
        if not tasks:
            return {
                "tasks": [],
                "critical_path": [],
                "project_duration": 0
            }
        
        # Create task lookup
        task_dict = {task["id"]: task for task in tasks}
        
        # Forward pass: Calculate early start and early finish
        for task in tasks:
            if not task["dependencies"]:
                # No dependencies, can start immediately
                task["early_start"] = 0
                task["duration"] = task["duration"] or 1
                task["early_finish"] = task["early_start"] + task["duration"]
            else:
                # Has dependencies, find latest early finish of predecessors
                max_early_finish = 0
                for dep_id in task["dependencies"]:
                    if dep_id in task_dict:
                        dep_task = task_dict[dep_id]
                        if dep_task["early_finish"] is not None:
                            max_early_finish = max(max_early_finish, dep_task["early_finish"])
                
                task["early_start"] = max_early_finish
                task["duration"] = task["duration"] or 1
                task["early_finish"] = task["early_start"] + task["duration"]
        
        # Find project duration (latest early finish)
        project_duration = max(task["early_finish"] for task in tasks)
        
        # Backward pass: Calculate late start and late finish
        for task in reversed(tasks):
            # Find tasks that depend on this task
            dependents = [t for t in tasks if task["id"] in t.get("dependencies", [])]
            
            if not dependents:
                # No dependents, can finish at project end
                task["late_finish"] = project_duration
                task["late_start"] = task["late_finish"] - task["duration"]
            else:
                # Has dependents, find earliest late start of successors
                min_late_start = project_duration
                for dep_task in dependents:
                    if dep_task["late_start"] is not None:
                        min_late_start = min(min_late_start, dep_task["late_start"])
                
                task["late_finish"] = min_late_start
                task["late_start"] = task["late_finish"] - task["duration"]
            
            # Calculate slack
            task["slack"] = task["late_start"] - task["early_start"]
            
            # Mark as critical if slack is 0
            task["is_critical"] = task["slack"] == 0
        
        # Identify critical path
        critical_path = []
        current_task = None
        
        # Find starting task (no dependencies)
        for task in tasks:
            if not task["dependencies"]:
                current_task = task
                break
        
        # Follow critical path
        while current_task:
            critical_path.append(current_task["id"])
            
            # Find next critical task
            next_critical_task = None
            for task in tasks:
                if current_task["id"] in task.get("dependencies", []) and task["is_critical"]:
                    next_critical_task = task
                    break
            
            current_task = next_critical_task
        
        return {
            "tasks": tasks,
            "critical_path": critical_path,
            "project_duration": project_duration
        }
    
    async def generate_gantt_export(
        self,
        project_id: int,
        format_type: str,  # "json", "csv", "pdf"
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate Gantt chart export in various formats"""
        try:
            # Get Gantt data
            gantt_data = await self.generate_gantt_data(project_id, db)
            
            if format_type == "json":
                return {
                    "success": True,
                    "format": "json",
                    "data": gantt_data
                }
            elif format_type == "csv":
                csv_data = self._convert_to_csv(gantt_data)
                return {
                    "success": True,
                    "format": "csv",
                    "data": csv_data
                }
            elif format_type == "pdf":
                # PDF generation would require additional libraries
                return {
                    "success": False,
                    "error": "PDF export not yet implemented"
                }
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format_type}"
                }
            
        except Exception as e:
            logger.error(f"Error generating Gantt export: {e}")
            raise
    
    def _convert_to_csv(self, gantt_data: Dict[str, Any]) -> str:
        """Convert Gantt data to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "Task ID", "Task Name", "Status", "Priority", "Start Date", "End Date",
            "Duration (days)", "Progress (%)", "Estimated Hours", "Actual Hours",
            "Is Critical", "Slack (days)", "Assigned To"
        ])
        
        # Write task data
        for task in gantt_data["tasks"]:
            writer.writerow([
                task["id"],
                task["name"],
                task["status"],
                task["priority"],
                task["start_date"] or "",
                task["end_date"] or "",
                task["duration"] or 0,
                task["progress"] or 0,
                task["estimated_hours"] or 0,
                task["actual_hours"] or 0,
                "Yes" if task["is_critical"] else "No",
                task["slack"] or 0,
                task["assigned_to"] or ""
            ])
        
        return output.getvalue()
