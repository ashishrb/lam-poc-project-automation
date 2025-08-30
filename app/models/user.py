from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum




class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EXECUTIVE = "executive"
    PM = "pm"
    FINANCE_CONTROLLER = "finance_controller"
    RESOURCE_MANAGER = "resource_manager"
    TEAM_MEMBER = "team_member"
    VENDOR = "vendor"


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    domain = Column(String(100), unique=True, index=True)
    settings = Column(Text)  # JSON settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    projects = relationship("Project", back_populates="tenant")


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    permissions = Column(Text)  # JSON permissions
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    preferences = Column(Text)  # JSON preferences
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="users")
    tenant = relationship("Tenant", back_populates="users")
    projects = relationship("Project", back_populates="project_manager")
    tasks = relationship("Task", back_populates="assigned_to")
    timesheets = relationship("Timesheet", foreign_keys="[Timesheet.user_id]", back_populates="user")
    evaluations = relationship("Evaluation", foreign_keys="[Evaluation.evaluator_id]", back_populates="evaluator")
    alerts = relationship("Alert", foreign_keys="[Alert.assignee_id]", back_populates="assignee")
    audit_logs = relationship("AuditLog", back_populates="user")
