from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class AuditAction(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    AI_QUERY = "ai_query"
    AI_ACTION = "ai_action"
    DOCUMENT_INGEST = "document_ingest"
    ALERT_TRIGGER = "alert_trigger"
    REPORT_GENERATE = "report_generate"


class AuditEntityType(str, enum.Enum):
    USER = "user"
    PROJECT = "project"
    TASK = "task"
    RESOURCE = "resource"
    BUDGET = "budget"
    DOCUMENT = "document"
    ALERT = "alert"
    REPORT = "report"
    SYSTEM = "system"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(Enum(AuditAction), nullable=False)
    entity_type = Column(Enum(AuditEntityType))
    entity_id = Column(Integer)
    resource_path = Column(String(500))  # API endpoint or page
    method = Column(String(10))  # HTTP method
    status_code = Column(Integer)
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    request_data = Column(JSON)  # JSON request data
    response_data = Column(JSON)  # JSON response data
    error_message = Column(Text)
    duration_ms = Column(Integer)  # request duration in milliseconds
    metadata = Column(JSON)  # Additional metadata
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    tenant = relationship("Tenant")
