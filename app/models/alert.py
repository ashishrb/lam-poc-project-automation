from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class AlertType(str, enum.Enum):
    BUDGET_VARIANCE = "budget_variance"
    SCHEDULE_SLIP = "schedule_slip"
    RESOURCE_OVERALLOCATION = "resource_overallocation"
    QUALITY_ISSUE = "quality_issue"
    RISK_TRIGGER = "risk_trigger"
    MILESTONE_MISSED = "milestone_missed"
    VENDOR_DELAY = "vendor_delay"
    SYSTEM_ISSUE = "system_issue"
    CUSTOM = "custom"


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING)
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"))
    entity_type = Column(String(50))  # project, task, resource, budget, etc.
    entity_id = Column(Integer)  # ID of the related entity
    assignee_id = Column(Integer, ForeignKey("users.id"))
    acknowledged_by = Column(Integer, ForeignKey("users.id"))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime(timezone=True))
    resolution_notes = Column(Text)
    metadata = Column(JSON)  # JSON metadata about the alert
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    rule = relationship("AlertRule")
    assignee = relationship("User", foreign_keys=[assignee_id])
    acknowledger = relationship("User", foreign_keys=[acknowledged_by])
    resolver = relationship("User", foreign_keys=[resolved_by])
    tenant = relationship("Tenant")


class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING)
    conditions = Column(JSON, nullable=False)  # JSON conditions for triggering
    entity_types = Column(JSON)  # JSON array of entity types to monitor
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")
    tenant = relationship("Tenant")
    alerts = relationship("Alert", back_populates="rule")
