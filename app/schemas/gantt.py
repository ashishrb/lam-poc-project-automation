#!/usr/bin/env python3
"""
Gantt Chart Pydantic Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date


class GanttTask(BaseModel):
    """Schema for Gantt task"""
    id: int
    name: str
    description: Optional[str] = None
    status: str
    priority: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: int
    progress: float
    assigned_to: Optional[int] = None
    parent_task_id: Optional[int] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: List[int] = []
    is_critical: bool = False
    early_start: Optional[int] = None
    early_finish: Optional[int] = None
    late_start: Optional[int] = None
    late_finish: Optional[int] = None
    slack: Optional[int] = None


class GanttProject(BaseModel):
    """Schema for Gantt project"""
    id: int
    name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    status: str
    health_score: float


class GanttMetrics(BaseModel):
    """Schema for Gantt metrics"""
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    total_estimated_hours: float
    total_actual_hours: float
    progress_percentage: float


class GanttDependency(BaseModel):
    """Schema for Gantt dependency"""
    from_task: int
    to_task: int
    type: str = "finish_to_start"


class GanttDataResponse(BaseModel):
    """Schema for Gantt data response"""
    success: bool
    project: GanttProject
    tasks: List[GanttTask] = []
    critical_path: List[int] = []
    project_duration: int
    metrics: GanttMetrics
    dependencies: List[GanttDependency] = []


class CriticalPathSummary(BaseModel):
    """Schema for critical path summary"""
    total_tasks: int
    critical_tasks: int
    total_duration: int
    critical_path_duration: int


class CriticalPathResponse(BaseModel):
    """Schema for critical path response"""
    success: bool
    critical_path: List[int] = []
    project_duration: int
    tasks: List[GanttTask] = []
    summary: CriticalPathSummary
    message: Optional[str] = None


class GanttExportResponse(BaseModel):
    """Schema for Gantt export response"""
    success: bool
    format: str
    data: Any
    error: Optional[str] = None
