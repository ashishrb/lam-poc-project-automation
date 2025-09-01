#!/usr/bin/env python3
"""
Baseline and Gantt Pydantic Schemas
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, date


class BaselineCreate(BaseModel):
    """Schema for creating a new baseline"""
    project_id: int = Field(..., description="Project ID")
    name: str = Field(..., description="Baseline name")
    description: Optional[str] = Field(None, description="Baseline description")
    version: str = Field(..., description="Baseline version (e.g., '1.0', '2.1')")
    created_by_id: int = Field(..., description="User ID who created the baseline")


class BaselineApprove(BaseModel):
    """Schema for approving a baseline"""
    approved_by_id: int = Field(..., description="User ID who approved the baseline")


class BaselineCompare(BaseModel):
    """Schema for comparing baselines"""
    baseline_id_1: int = Field(..., description="First baseline ID")
    baseline_id_2: int = Field(..., description="Second baseline ID")


class BaselineInfo(BaseModel):
    """Schema for baseline information"""
    id: int
    name: str
    version: str
    status: str
    created_at: str
    total_tasks: int


class BaselineResponse(BaseModel):
    """Schema for baseline response"""
    success: bool
    baseline_id: Optional[int] = None
    baseline: Optional[BaselineInfo] = None
    status: Optional[str] = None
    approved_at: Optional[str] = None
    message: Optional[str] = None


class BaselineListResponse(BaseModel):
    """Schema for baseline list response"""
    success: bool
    baselines: List[BaselineInfo] = []
    total: int = 0
    project_id: Optional[int] = None
    message: Optional[str] = None


class VarianceInfo(BaseModel):
    """Schema for variance information"""
    variance_type: str
    description: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    variance_amount: float
    variance_percentage: float
    impact_level: str
    task_id: Optional[int] = None


class VarianceResponse(BaseModel):
    """Schema for variance response"""
    success: bool
    baseline_id: int
    total_variances: int
    variances: List[VarianceInfo] = []
    summary: Dict[str, Any] = {}


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
