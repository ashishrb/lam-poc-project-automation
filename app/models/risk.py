from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskStatus(str, enum.Enum):
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATED = "mitigated"
    CLOSED = "closed"
    OCCURRED = "occurred"


class IssueStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ChangeStatus(str, enum.Enum):
    REQUESTED = "requested"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"


class Risk(Base):
    __tablename__ = "risks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    probability = Column(Float)  # 0-1 scale
    impact = Column(Float)  # 0-1 scale
    exposure = Column(Float)  # probability * impact
    status = Column(Enum(RiskStatus), default=RiskStatus.IDENTIFIED)
    category = Column(String(100))  # technical, business, external
    owner_id = Column(Integer, ForeignKey("users.id"))
    mitigation_strategy = Column(Text)
    contingency_plan = Column(Text)
    trigger_conditions = Column(Text)
    due_date = Column(Date)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="risks")
    owner = relationship("User")
    tenant = relationship("Tenant")


class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    due_date = Column(Date)
    resolution = Column(Text)
    resolution_date = Column(DateTime(timezone=True))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="issues")
    reporter = relationship("User", foreign_keys=[reported_by])
    assignee = relationship("User", foreign_keys=[assigned_to])
    tenant = relationship("Tenant")


class Change(Base):
    __tablename__ = "changes"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    change_type = Column(String(100))  # scope, schedule, budget, quality
    status = Column(Enum(ChangeStatus), default=ChangeStatus.REQUESTED)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approval_date = Column(DateTime(timezone=True))
    impact_assessment = Column(Text)
    implementation_plan = Column(Text)
    rollback_plan = Column(Text)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="changes")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    tenant = relationship("Tenant")
