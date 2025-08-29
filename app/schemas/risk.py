from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RiskBase(BaseModel):
    title: str
    description: Optional[str] = None
    probability: str = "medium"
    impact: str = "medium"
    status: str = "open"
    mitigation_strategy: Optional[str] = None
    contingency_plan: Optional[str] = None


class RiskCreate(RiskBase):
    project_id: int


class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    probability: Optional[str] = None
    impact: Optional[str] = None
    status: Optional[str] = None
    mitigation_strategy: Optional[str] = None
    contingency_plan: Optional[str] = None


class RiskResponse(RiskBase):
    id: int
    project_id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IssueBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    status: str = "open"
    resolution: Optional[str] = None


class IssueCreate(IssueBase):
    project_id: int


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None


class IssueResponse(IssueBase):
    id: int
    project_id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskListResponse(BaseModel):
    risks: List[RiskResponse]
    total: int
    page: int
    size: int


class IssueListResponse(BaseModel):
    issues: List[IssueResponse]
    total: int
    page: int
    size: int
