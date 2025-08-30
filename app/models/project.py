from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ProjectPhase(str, enum.Enum):
    INITIATION = "initiation"
    PLANNING = "planning"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    CLOSURE = "closure"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PLANNING)
    phase = Column(Enum(ProjectPhase), default=ProjectPhase.INITIATION)
    start_date = Column(Date)
    end_date = Column(Date)
    planned_end_date = Column(Date)
    project_manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    client_name = Column(String(100))
    tags = Column(Text)  # JSON tags
    health_score = Column(Float, default=0.0)  # 0-100
    risk_level = Column(String(20), default="low")  # low, medium, high
    
    # AI-First Mode Flags
    ai_autopublish = Column(Boolean, default=False)  # Auto-publish AI-generated tasks
    allow_dev_task_create = Column(Boolean, default=False)  # Allow developers to create tasks
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project_manager = relationship("User", back_populates="projects")
    tenant = relationship("Tenant", back_populates="projects")
    tasks = relationship("Task", back_populates="project")
    milestones = relationship("Milestone", back_populates="project")
    budgets = relationship("Budget", back_populates="project")
    risks = relationship("Risk", back_populates="project")
    issues = relationship("Issue", back_populates="project")
    changes = relationship("Change", back_populates="project")
    stakeholders = relationship("Stakeholder", back_populates="project")
    documents = relationship("Document", back_populates="project")
    ai_drafts = relationship("AIDraft", back_populates="project")


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    parent_task_id = Column(Integer, ForeignKey("tasks.id"))
    estimated_hours = Column(Float)
    actual_hours = Column(Float, default=0.0)
    start_date = Column(Date)
    due_date = Column(Date)
    completed_date = Column(Date)
    dependencies = Column(Text)  # JSON dependency IDs
    tags = Column(Text)  # JSON tags
    
    # AI-First Mode Fields
    confidence_score = Column(Float, default=0.0)  # AI confidence in this task
    reasoning = Column(JSON)  # AI reasoning for task creation/assignment
    source = Column(String(20), default="ai")  # 'ai' or 'human'
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_to = relationship("User", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id])
    subtasks = relationship("Task", back_populates="parent_task")
    work_items = relationship("WorkItem", back_populates="task")
    timesheets = relationship("Timesheet", back_populates="task")


class WorkItem(Base):
    __tablename__ = "work_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(String(50))  # story, bug, task, epic
    status = Column(String(50))  # backlog, sprint, done
    priority = Column(Integer, default=0)
    story_points = Column(Integer)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    sprint_id = Column(String(50))
    assignee_id = Column(Integer, ForeignKey("users.id"))
    reporter_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="work_items")
    assignee = relationship("User", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])


class Milestone(Base):
    __tablename__ = "milestones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    is_critical = Column(Boolean, default=False)
    status = Column(String(20), default="pending")  # pending, completed, delayed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="milestones")
