from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DocumentType(str, enum.Enum):
    SOW = "sow"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    TEST_PLAN = "test_plan"
    USER_MANUAL = "user_manual"
    MEETING_MINUTES = "meeting_minutes"
    EMAIL = "email"
    TICKET = "ticket"
    COMMIT = "commit"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    document_type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String(100))
    project_id = Column(Integer, ForeignKey("projects.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    tags = Column(JSON)  # JSON array of tags
    metadata = Column(JSON)  # JSON metadata
    sensitivity_level = Column(String(20), default="public")  # public, internal, confidential, restricted
    embedding_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    last_processed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")
    tenant = relationship("Tenant")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # order within document
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), index=True)  # SHA-256 hash
    embedding_id = Column(String(100))  # Chroma embedding ID
    metadata = Column(JSON)  # JSON metadata for the chunk
    page_number = Column(Integer)  # if applicable
    line_start = Column(Integer)  # if applicable
    line_end = Column(Integer)  # if applicable
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
