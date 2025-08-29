from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StakeholderBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    influence: str = "medium"
    interest: str = "medium"
    project_id: Optional[int] = None
    organization: Optional[str] = None
    notes: Optional[str] = None


class StakeholderCreate(StakeholderBase):
    pass


class StakeholderUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    influence: Optional[str] = None
    interest: Optional[str] = None
    organization: Optional[str] = None
    notes: Optional[str] = None


class StakeholderResponse(StakeholderBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StakeholderListResponse(BaseModel):
    stakeholders: List[StakeholderResponse]
    total: int
    page: int
    size: int
