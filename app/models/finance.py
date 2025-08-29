from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class BudgetType(str, enum.Enum):
    LABOR = "labor"
    MATERIALS = "materials"
    EQUIPMENT = "equipment"
    TRAVEL = "travel"
    SOFTWARE = "software"
    OTHER = "other"


class BudgetStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    budget_type = Column(Enum(BudgetType), nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    fiscal_year = Column(Integer)
    status = Column(Enum(BudgetStatus), default=BudgetStatus.DRAFT)
    baseline_date = Column(Date)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="budgets")
    created_by_user = relationship("User")
    tenant = relationship("Tenant")
    versions = relationship("BudgetVersion", back_populates="budget")
    actuals = relationship("Actual", back_populates="budget")
    forecasts = relationship("Forecast", back_populates="budget")
    approvals = relationship("Approval", back_populates="budget")


class BudgetVersion(Base):
    __tablename__ = "budget_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    name = Column(String(200))
    description = Column(Text)
    total_amount = Column(Float, nullable=False)
    line_items = Column(JSON)  # JSON array of budget line items
    change_reason = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="versions")
    created_by_user = relationship("User")


class Actual(Base):
    __tablename__ = "actuals"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    category = Column(String(100))
    invoice_number = Column(String(100))
    vendor_name = Column(String(100))
    approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="actuals")
    approver = relationship("User", foreign_keys=[approved_by])
    tenant = relationship("Tenant")


class Forecast(Base):
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    confidence_level = Column(Float)  # 0-1 scale
    assumptions = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    budget = relationship("Budget", back_populates="forecasts")
    created_by_user = relationship("User")
    tenant = relationship("Tenant")


class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    amount = Column(Float)
    comments = Column(Text)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    
    # Relationships
    budget = relationship("Budget", back_populates="approvals")
    approver = relationship("User")
    tenant = relationship("Tenant")
