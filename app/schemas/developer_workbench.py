from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class QueryType(str, Enum):
    CODE_REVIEW = "code_review"
    DEBUG = "debug"
    OPTIMIZE = "optimize"
    TEST = "test"
    EXPLAIN = "explain"
    GENERAL = "general"

class ActivityType(str, Enum):
    TASK_COMPLETED = "task_completed"
    TIME_LOGGED = "time_logged"
    CODE_REVIEW = "code_review"
    STATUS_UPDATE = "status_update"
    BUG_FIXED = "bug_fixed"

class DeveloperStats(BaseModel):
    active_tasks: int = Field(..., description="Number of active tasks")
    completed_this_week: int = Field(..., description="Tasks completed this week")
    hours_logged: float = Field(..., description="Hours logged this week")
    productivity: float = Field(..., description="Productivity score (0-100)")
    code_reviews_pending: int = Field(..., description="Pending code reviews")
    last_activity: datetime = Field(..., description="Last activity timestamp")

class TaskInfo(BaseModel):
    id: int = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: TaskStatus = Field(..., description="Task status")
    priority: TaskPriority = Field(..., description="Task priority")
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(None, description="Estimated hours")
    project_name: Optional[str] = Field(None, description="Project name")

class CodeReviewRequest(BaseModel):
    code: str = Field(..., description="Code to review")
    language: str = Field(..., description="Programming language")
    context: Optional[str] = Field(None, description="Additional context")
    user_id: int = Field(..., description="User requesting review")
    project_id: Optional[int] = Field(None, description="Project ID")

class CodeReviewResponse(BaseModel):
    analysis: str = Field(..., description="Code analysis")
    recommendations: str = Field(..., description="Recommendations")
    score: int = Field(..., description="Code quality score (0-100)")
    issues_found: int = Field(..., description="Number of issues found")
    review_date: datetime = Field(..., description="Review timestamp")

class TimeEntry(BaseModel):
    user_id: int = Field(..., description="User ID")
    task_id: int = Field(..., description="Task ID")
    hours: float = Field(..., description="Hours worked")
    description: str = Field(..., description="Work description")
    date: datetime = Field(..., description="Date of work")
    task_progress: Optional[int] = Field(None, description="Task progress percentage")

class StatusUpdate(BaseModel):
    user_id: int = Field(..., description="User ID")
    content: str = Field(..., description="Status update content")
    project_id: Optional[int] = Field(None, description="Project ID")
    date: datetime = Field(..., description="Update timestamp")

class AIQuery(BaseModel):
    user_id: int = Field(..., description="User ID")
    question: str = Field(..., description="User's question")
    query_type: QueryType = Field(..., description="Type of query")
    project_id: Optional[int] = Field(None, description="Project ID")
    recent_tasks: Optional[List[str]] = Field(None, description="Recent tasks")
    code_context: Optional[str] = Field(None, description="Code context")

class AIResponse(BaseModel):
    response: str = Field(..., description="AI response")
    suggestions: List[str] = Field(..., description="Suggestions")
    related_resources: List[str] = Field(..., description="Related resources")

class DeveloperActivity(BaseModel):
    type: ActivityType = Field(..., description="Activity type")
    description: str = Field(..., description="Activity description")
    timestamp: datetime = Field(..., description="Activity timestamp")
    project_name: Optional[str] = Field(None, description="Project name")

class CodeAnalysisResult(BaseModel):
    quality_score: int = Field(..., description="Code quality score")
    security_issues: List[str] = Field(..., description="Security issues found")
    performance_issues: List[str] = Field(..., description="Performance issues")
    best_practices: List[str] = Field(..., description="Best practices suggestions")
    complexity_score: float = Field(..., description="Code complexity score")

class TimeTrackingSummary(BaseModel):
    total_hours: float = Field(..., description="Total hours logged")
    hours_today: float = Field(..., description="Hours logged today")
    hours_this_week: float = Field(..., description="Hours logged this week")
    active_tasks: int = Field(..., description="Number of active tasks")
    productivity_trend: float = Field(..., description="Productivity trend")

class ProjectContext(BaseModel):
    project_id: int = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    current_tasks: List[TaskInfo] = Field(..., description="Current tasks")
    recent_activities: List[DeveloperActivity] = Field(..., description="Recent activities")
    team_members: List[str] = Field(..., description="Team members")

class WorkbenchSettings(BaseModel):
    user_id: int = Field(..., description="User ID")
    theme: str = Field(default="light", description="UI theme")
    notifications_enabled: bool = Field(default=True, description="Enable notifications")
    auto_save: bool = Field(default=True, description="Auto-save enabled")
    ai_assistant_enabled: bool = Field(default=True, description="AI assistant enabled")
    time_tracking_auto: bool = Field(default=False, description="Auto time tracking")

class Notification(BaseModel):
    id: int = Field(..., description="Notification ID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    timestamp: datetime = Field(..., description="Notification timestamp")
    read: bool = Field(default=False, description="Read status")
    action_url: Optional[str] = Field(None, description="Action URL")

class CodeSnippet(BaseModel):
    id: int = Field(..., description="Snippet ID")
    title: str = Field(..., description="Snippet title")
    code: str = Field(..., description="Code content")
    language: str = Field(..., description="Programming language")
    description: Optional[str] = Field(None, description="Description")
    tags: List[str] = Field(default=[], description="Tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    user_id: int = Field(..., description="User ID")

class DocumentationEntry(BaseModel):
    id: int = Field(..., description="Documentation ID")
    title: str = Field(..., description="Documentation title")
    content: str = Field(..., description="Documentation content")
    category: str = Field(..., description="Documentation category")
    tags: List[str] = Field(default=[], description="Tags")
    last_updated: datetime = Field(..., description="Last update timestamp")
    author_id: int = Field(..., description="Author ID")

class WorkbenchDashboard(BaseModel):
    stats: DeveloperStats = Field(..., description="Developer statistics")
    recent_tasks: List[TaskInfo] = Field(..., description="Recent tasks")
    recent_activities: List[DeveloperActivity] = Field(..., description="Recent activities")
    notifications: List[Notification] = Field(..., description="Notifications")
    time_summary: TimeTrackingSummary = Field(..., description="Time tracking summary")
    project_context: Optional[ProjectContext] = Field(None, description="Current project context")
