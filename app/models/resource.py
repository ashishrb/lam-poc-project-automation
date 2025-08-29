from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ResourceType(str, enum.Enum):
    EMPLOYEE = "employee"
    CONTRACTOR = "contractor"
    VENDOR = "vendor"
    EQUIPMENT = "equipment"


class ResourceStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class EvaluationType(str, enum.Enum):
    PERFORMANCE = "performance"
    SKILL = "skill"
    PROJECT = "project"
    PEER = "peer"
    MANAGER = "manager"


class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    resource_type = Column(Enum(ResourceType), default=ResourceType.EMPLOYEE)
    status = Column(Enum(ResourceStatus), default=ResourceStatus.ACTIVE)
    department = Column(String(100))
    position = Column(String(100))
    hire_date = Column(Date)
    hourly_rate = Column(Float)
    capacity_hours_per_week = Column(Float, default=40.0)
    skills = Column(JSON)  # JSON array of skill IDs
    availability = Column(JSON)  # JSON availability schedule
    preferences = Column(JSON)  # JSON preferences
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    evaluations = relationship("Evaluation", back_populates="resource")
    timesheets = relationship("Timesheet", back_populates="resource")
    resource_skills = relationship("ResourceSkill", back_populates="resource")


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100))  # technical, soft, domain
    description = Column(Text)
    proficiency_levels = Column(JSON)  # JSON array of levels
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    resource_skills = relationship("ResourceSkill", back_populates="skill")


class ResourceSkill(Base):
    __tablename__ = "resource_skills"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    proficiency_level = Column(Integer, default=1)  # 1-5 scale
    years_experience = Column(Float)
    last_used = Column(Date)
    certification = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resource = relationship("Resource", back_populates="resource_skills")
    skill = relationship("Skill", back_populates="resource_skills")


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    evaluator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evaluation_type = Column(Enum(EvaluationType), nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)
    scores = Column(JSON)  # JSON scores by criteria
    comments = Column(Text)
    overall_rating = Column(Float)  # 1-5 scale
    strengths = Column(Text)
    areas_for_improvement = Column(Text)
    goals = Column(Text)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resource = relationship("Resource", back_populates="evaluations")
    evaluator = relationship("User", back_populates="evaluations")
    tenant = relationship("Tenant")


class Timesheet(Base):
    __tablename__ = "timesheets"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    date = Column(Date, nullable=False)
    hours_worked = Column(Float, nullable=False)
    description = Column(Text)
    billable = Column(Boolean, default=True)
    approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resource = relationship("Resource", back_populates="timesheets")
    user = relationship("User", back_populates="timesheets")
    task = relationship("Task", back_populates="timesheets")
    project = relationship("Project")
    approver = relationship("User", foreign_keys=[approved_by])
    tenant = relationship("Tenant")
