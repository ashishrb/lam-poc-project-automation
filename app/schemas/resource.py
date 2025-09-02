from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceBase(BaseModel):
    name: str
    email: str
    role: str
    department: Optional[str] = None
    skills: List[int] = []
    hourly_rate: Optional[float] = None
    availability: Optional[str] = "available"
    capacity_hours: Optional[float] = 40.0


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    skills: Optional[List[int]] = None
    hourly_rate: Optional[float] = None
    availability: Optional[str] = None
    capacity_hours: Optional[float] = None


class ResourceResponse(ResourceBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceListResponse(BaseModel):
    resources: List[ResourceResponse]
    total: int
    page: int
    size: int


class SkillMatch(BaseModel):
    skill_name: str
    proficiency_level: float
    years_experience: int
    match_score: float


class ResourceAssignment(BaseModel):
    task_id: int
    task_name: str
    resource_id: int
    resource_name: str
    skill_match: float
    confidence_score: float
    reasoning: str
    assignment_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssignmentRequest(BaseModel):
    tasks: List[Dict[str, Any]]
    project_id: Optional[int] = None
    constraints: Optional[Dict[str, Any]] = None


class AssignmentResponse(BaseModel):
    assignments: List[ResourceAssignment]
    summary: Dict[str, Any]
    success: bool
    message: str


class ResourceSkillInfo(BaseModel):
    skill_name: str
    skill_category: Optional[str] = None
    proficiency_level: float
    years_experience: int
    last_used: Optional[datetime] = None


class ResourceSkillsResponse(BaseModel):
    resource: Dict[str, Any]
    skills: List[ResourceSkillInfo]
    total_skills: int
