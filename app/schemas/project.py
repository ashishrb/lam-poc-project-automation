from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.common import PaginationParams


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "planning"
    priority: str = "medium"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    manager_id: int


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    manager_id: Optional[int] = None


class ProjectResponse(ProjectBase):
    id: int
    tenant_id: int
    health_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    estimated_hours: Optional[float] = None
    assigned_to: Optional[int] = None


class TaskCreate(TaskBase):
    project_id: int


class TaskUpdate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "task"
    status: str = "todo"
    priority: str = "medium"


class WorkItemCreate(WorkItemBase):
    project_id: int


class WorkItemUpdate(WorkItemBase):
    pass


class WorkItemResponse(WorkItemBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MilestoneBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    status: str = "pending"


class MilestoneCreate(MilestoneBase):
    project_id: int


class MilestoneUpdate(MilestoneBase):
    pass


class MilestoneResponse(MilestoneBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
