from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Time, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UpdateFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class UpdateChannel(str, enum.Enum):
    EMAIL = "email"
    WEB = "web"
    MOBILE = "mobile"
    SLACK = "slack"
    TEAMS = "teams"


class StatusUpdatePolicy(Base):
    __tablename__ = "status_update_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Update Schedule
    frequency = Column(Enum(UpdateFrequency), default=UpdateFrequency.WEEKLY)
    custom_days = Column(JSON)  # For custom frequency (e.g., [1, 3, 5] for Mon, Wed, Fri)
    reminder_time = Column(Time, default=func.time("09:00:00"))  # When to send reminders
    timezone = Column(String(50), default="UTC")
    
    # Update Requirements
    require_progress = Column(Boolean, default=True)
    require_blockers = Column(Boolean, default=True)
    require_next_steps = Column(Boolean, default=True)
    require_effort = Column(Boolean, default=False)
    require_confidence = Column(Boolean, default=False)
    
    # AI Features
    ai_generate_draft = Column(Boolean, default=True)  # Generate AI draft updates
    ai_suggest_improvements = Column(Boolean, default=True)  # Suggest improvements
    ai_escalate_missing = Column(Boolean, default=True)  # Escalate missing updates
    
    # Notification Settings
    channels = Column(JSON)  # List of notification channels
    escalation_delay_hours = Column(Integer, default=24)  # Hours before escalation
    escalation_recipients = Column(JSON)  # Who to notify on escalation
    
    # Status
    is_active = Column(Boolean, default=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])
    status_updates = relationship("StatusUpdate", back_populates="policy")
    
    def __repr__(self):
        return f"<StatusUpdatePolicy(id={self.id}, name={self.name}, frequency={self.frequency})>"
    
    @property
    def next_update_due(self) -> bool:
        """Check if an update is due based on the policy"""
        # This would be implemented with business logic
        # to check against the last update and frequency
        return True
    
    def get_weekday_numbers(self) -> list:
        """Get list of weekday numbers for custom frequency"""
        if self.frequency == UpdateFrequency.CUSTOM and self.custom_days:
            return self.custom_days
        elif self.frequency == UpdateFrequency.DAILY:
            return [0, 1, 2, 3, 4, 5, 6]  # All days
        elif self.frequency == UpdateFrequency.WEEKLY:
            return [0]  # Monday
        elif self.frequency == UpdateFrequency.BIWEEKLY:
            return [0, 3]  # Monday and Thursday
        elif self.frequency == UpdateFrequency.MONTHLY:
            return [0]  # First Monday of month
        return [0]  # Default to Monday


class StatusUpdate(Base):
    __tablename__ = "status_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("status_update_policies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Update Content
    progress_summary = Column(Text)
    blockers = Column(Text)
    next_steps = Column(Text)
    effort_hours = Column(Float)
    confidence_score = Column(Float)  # 0-100 confidence in estimates
    
    # AI-Generated Content
    ai_draft = Column(Text)  # AI-generated draft update
    ai_suggestions = Column(JSON)  # AI suggestions for improvement
    
    # Status
    status = Column(String(20), default="draft")  # draft, submitted, overdue
    submitted_at = Column(DateTime(timezone=True))
    
    # Metadata
    is_ai_generated = Column(Boolean, default=False)
    ai_model_used = Column(String(100))
    ai_confidence = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    policy = relationship("StatusUpdatePolicy", back_populates="status_updates")
    user = relationship("User")
    project = relationship("Project")
    
    def __repr__(self):
        return f"<StatusUpdate(id={self.id}, user_id={self.user_id}, status={self.status})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if this update is overdue"""
        if not self.submitted_at:
            # Check against policy frequency
            return True
        return False
    
    @property
    def is_complete(self) -> bool:
        """Check if the update is complete based on policy requirements"""
        if not self.policy:
            return False
        
        required_fields = []
        if self.policy.require_progress:
            required_fields.append(self.progress_summary)
        if self.policy.require_blockers:
            required_fields.append(self.blockers)
        if self.policy.require_next_steps:
            required_fields.append(self.next_steps)
        if self.policy.require_effort:
            required_fields.append(self.effort_hours)
        if self.policy.require_confidence:
            required_fields.append(self.confidence_score)
        
        return all(field is not None and str(field).strip() for field in required_fields)
