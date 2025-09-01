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
    
    # Baseline & Versioning
    current_baseline_id = Column(Integer, ForeignKey("project_baselines.id"))
    
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
    baselines = relationship("ProjectBaseline", back_populates="project", foreign_keys="ProjectBaseline.project_id")
    current_baseline = relationship("ProjectBaseline", foreign_keys=[current_baseline_id])


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
    
    # Baseline & Versioning
    baseline_task_id = Column(Integer, ForeignKey("baseline_tasks.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_to = relationship("User", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id])
    subtasks = relationship("Task", back_populates="parent_task")
    work_items = relationship("WorkItem", back_populates="task")
    timesheets = relationship("Timesheet", back_populates="task")
    baseline_task = relationship("BaselineTask", back_populates="current_task", foreign_keys=[baseline_task_id])
    baseline_tasks = relationship("BaselineTask", back_populates="task", foreign_keys="BaselineTask.task_id")


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


class BaselineStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    ARCHIVED = "archived"


class VarianceType(str, enum.Enum):
    SCHEDULE = "schedule"
    COST = "cost"
    SCOPE = "scope"
    RESOURCE = "resource"
    QUALITY = "quality"


class ProjectBaseline(Base):
    """Project baseline for versioning and change tracking"""
    __tablename__ = "project_baselines"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    version = Column(String(20), nullable=False)  # e.g., "1.0", "2.1"
    status = Column(Enum(BaselineStatus), default=BaselineStatus.DRAFT)
    
    # Baseline data (snapshot of project state)
    baseline_data = Column(JSON, nullable=False)  # Complete project snapshot
    
    # Metadata
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("Project", back_populates="baselines", foreign_keys=[project_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    baseline_tasks = relationship("BaselineTask", back_populates="baseline")
    variances = relationship("ProjectVariance", back_populates="baseline")


class BaselineTask(Base):
    """Task baseline for versioning and change tracking"""
    __tablename__ = "baseline_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    baseline_id = Column(Integer, ForeignKey("project_baselines.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # Baseline task data (snapshot of task state)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), nullable=False)
    priority = Column(Enum(TaskPriority), nullable=False)
    estimated_hours = Column(Float)
    start_date = Column(Date)
    due_date = Column(Date)
    dependencies = Column(Text)  # JSON dependency IDs
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    baseline = relationship("ProjectBaseline", back_populates="baseline_tasks")
    task = relationship("Task", back_populates="baseline_tasks", foreign_keys=[task_id])
    current_task = relationship("Task", back_populates="baseline_task", foreign_keys="Task.baseline_task_id")
    assigned_to = relationship("User")


class ProjectVariance(Base):
    """Track variances between baseline and current state"""
    __tablename__ = "project_variances"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    baseline_id = Column(Integer, ForeignKey("project_baselines.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    
    variance_type = Column(Enum(VarianceType), nullable=False)
    description = Column(Text, nullable=False)
    
    # Variance metrics
    baseline_value = Column(Float)
    current_value = Column(Float)
    variance_amount = Column(Float)  # current - baseline
    variance_percentage = Column(Float)
    
    # Impact assessment
    impact_level = Column(String(20), default="low")  # low, medium, high, critical
    mitigation_plan = Column(Text)
    
    # Status
    status = Column(String(20), default="open")  # open, in_progress, resolved, accepted
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    project = relationship("Project")
    baseline = relationship("ProjectBaseline", back_populates="variances")
    task = relationship("Task")
