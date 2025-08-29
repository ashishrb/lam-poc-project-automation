from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BudgetBase(BaseModel):
    project_id: int
    version: str = "1.0"
    total_budget: float
    currency: str = "USD"
    fiscal_year: Optional[int] = None
    notes: Optional[str] = None


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    total_budget: Optional[float] = None
    currency: Optional[str] = None
    fiscal_year: Optional[int] = None
    notes: Optional[str] = None


class BudgetResponse(BudgetBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ActualBase(BaseModel):
    budget_id: int
    amount: float
    date: datetime
    category: str
    description: Optional[str] = None


class ActualCreate(ActualBase):
    pass


class ActualUpdate(BaseModel):
    amount: Optional[float] = None
    date: Optional[datetime] = None
    category: Optional[str] = None
    description: Optional[str] = None


class ActualResponse(ActualBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BudgetListResponse(BaseModel):
    budgets: List[BudgetResponse]
    total: int
    page: int
    size: int
