from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class AlertBase(BaseModel):
    title: str
    description: Optional[str] = None
    alert_type: str
    severity: str = "warning"
    status: str = "active"
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    assignee_id: Optional[int] = None


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None
    resolution_notes: Optional[str] = None


class AlertResponse(AlertBase):
    id: int
    rule_id: Optional[int] = None
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    alert_type: str
    severity: str = "warning"
    conditions: dict
    entity_types: Optional[List[str]] = None
    is_active: bool = True


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    alert_type: Optional[str] = None
    severity: Optional[str] = None
    conditions: Optional[dict] = None
    entity_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    created_by: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    size: int


class AlertRuleListResponse(BaseModel):
    rules: List[AlertRuleResponse]
    total: int
    page: int
    size: int
