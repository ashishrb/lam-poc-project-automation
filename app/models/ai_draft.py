from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DraftType(str, enum.Enum):
    TASK = "task"
    MILESTONE = "milestone"
    WBS = "wbs"
    ALLOCATION = "allocation"
    SCHEDULE = "schedule"
    RISK = "risk"
    REPORT = "report"


class DraftStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AIDraft(Base):
    __tablename__ = "ai_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    draft_type = Column(Enum(DraftType), nullable=False)
    status = Column(Enum(DraftStatus), default=DraftStatus.DRAFT)
    
    # AI-generated content
    payload = Column(JSON, nullable=False)  # The actual AI output
    rationale = Column(JSON, nullable=False)  # AI reasoning and confidence scores
    
    # Metadata
    created_by_ai = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"))
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    
    # AI Model Info
    model_name = Column(String(100))
    model_version = Column(String(50))
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    # Validation and Guardrails
    validation_errors = Column(JSON)  # Any validation issues found
    guardrail_violations = Column(JSON)  # Any guardrail violations
    repair_attempts = Column(Integer, default=0)  # Number of repair attempts
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="ai_drafts")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    reviewed_by_user = relationship("User", foreign_keys=[reviewed_by_user_id])
    
    def __repr__(self):
        return f"<AIDraft(id={self.id}, type={self.draft_type}, status={self.status})>"
    
    @property
    def is_ready_for_review(self) -> bool:
        """Check if draft is ready for human review"""
        return (
            self.status == DraftStatus.DRAFT and 
            not self.validation_errors and 
            not self.guardrail_violations
        )
    
    @property
    def confidence_score(self) -> float:
        """Extract overall confidence score from rationale"""
        if self.rationale and isinstance(self.rationale, dict):
            return self.rationale.get("confidence", 0.0)
        return 0.0
    
    @property
    def can_be_published(self) -> bool:
        """Check if draft can be published"""
        return (
            self.status == DraftStatus.APPROVED and 
            not self.validation_errors and 
            not self.guardrail_violations
        )
