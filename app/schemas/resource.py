from pydantic import BaseModel
from typing import Optional, List
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
