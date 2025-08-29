from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class StakeholderRole(str, enum.Enum):
    SPONSOR = "sponsor"
    PROJECT_MANAGER = "project_manager"
    TEAM_MEMBER = "team_member"
    CLIENT = "client"
    VENDOR = "vendor"
    STAKEHOLDER = "stakeholder"
    APPROVER = "approver"


class InfluenceLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InterestLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationPreference(str, enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    MEETING = "meeting"
    REPORT = "report"
    DASHBOARD = "dashboard"


class Stakeholder(Base):
    __tablename__ = "stakeholders"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    organization = Column(String(100))
    role = Column(Enum(StakeholderRole), nullable=False)
    influence_level = Column(Enum(InfluenceLevel), default=InfluenceLevel.MEDIUM)
    interest_level = Column(Enum(InterestLevel), default=InterestLevel.MEDIUM)
    communication_preferences = Column(Text)  # JSON array of preferences
    contact_frequency = Column(String(50))  # daily, weekly, monthly, as-needed
    last_contact = Column(DateTime(timezone=True))
    next_contact = Column(DateTime(timezone=True))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="stakeholders")
    tenant = relationship("Tenant")
