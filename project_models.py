#!/usr/bin/env python3
"""
Project Models - Comprehensive Data Structures for Autonomous Project Management
Defines all data models, enums, and utility classes for enterprise project management
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum, IntEnum
import json
import uuid
from abc import ABC, abstractmethod

# ========================================================================================
# ENUMERATIONS
# ========================================================================================

class ProjectStatus(Enum):
    """Project lifecycle status"""
    PLANNING = "planning"
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    UNDER_REVIEW = "under_review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"

class TaskStatus(Enum):
    """Task lifecycle status"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    UNDER_REVIEW = "under_review"
    TESTING = "testing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Priority(IntEnum):
    """Priority levels with numeric values for sorting"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

class RiskLevel(Enum):
    """Risk assessment levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class StakeholderRole(Enum):
    """Stakeholder roles in projects"""
    PROJECT_MANAGER = "project_manager"
    TECHNICAL_LEAD = "technical_lead"
    TEAM_LEAD = "team_lead"
    SENIOR_DEVELOPER = "senior_developer"
    DEVELOPER = "developer"
    QA_ENGINEER = "qa_engineer"
    QA_LEAD = "qa_lead"
    BUSINESS_ANALYST = "business_analyst"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    CLIENT = "client"
    CLIENT_REPRESENTATIVE = "client_representative"
    SPONSOR = "sponsor"
    DIRECTOR = "director"
    VP_ENGINEERING = "vp_engineering"
    CTO = "cto"
    EXTERNAL_CONSULTANT = "external_consultant"

class NotificationChannel(Enum):
    """Communication channels"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    IN_APP = "in_app"

class SkillCategory(Enum):
    """Skill categorization"""
    TECHNICAL = "technical"
    LEADERSHIP = "leadership"
    COMMUNICATION = "communication"
    DOMAIN_EXPERTISE = "domain_expertise"
    PROCESS = "process"
    TOOLS = "tools"
    SOFT_SKILLS = "soft_skills"

class PerformanceTrend(Enum):
    """Performance trend indicators"""
    DECLINING = "declining"
    STABLE = "stable"
    IMPROVING = "improving"
    EXCELLENT = "excellent"
    NEEDS_ATTENTION = "needs_attention"

class ActionType(Enum):
    """Types of autonomous actions"""
    STRATEGIC_DECISION = "strategic_decision"
    OPERATIONAL_DECISION = "operational_decision"
    COMMUNICATION = "communication"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_MITIGATION = "risk_mitigation"
    PERFORMANCE_INTERVENTION = "performance_intervention"
    ESCALATION = "escalation"
    PROCESS_OPTIMIZATION = "process_optimization"

class DecisionCategory(Enum):
    """Categories of autonomous decisions"""
    BUDGET_MANAGEMENT = "budget_management"
    SCHEDULE_MANAGEMENT = "schedule_management"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    QUALITY_ASSURANCE = "quality_assurance"
    RISK_MANAGEMENT = "risk_management"
    TEAM_DEVELOPMENT = "team_development"
    STAKEHOLDER_MANAGEMENT = "stakeholder_management"
    PROCESS_IMPROVEMENT = "process_improvement"

# ========================================================================================
# UTILITY CLASSES
# ========================================================================================

@dataclass
class TimeRange:
    """Time range representation"""
    start: datetime
    end: datetime
    
    @property
    def duration_days(self) -> int:
        """Get duration in days"""
        return (self.end - self.start).days
    
    @property
    def duration_hours(self) -> float:
        """Get duration in hours"""
        return (self.end - self.start).total_seconds() / 3600
    
    def overlaps_with(self, other: 'TimeRange') -> bool:
        """Check if this time range overlaps with another"""
        return self.start < other.end and self.end > other.start
    
    def contains(self, dt: datetime) -> bool:
        """Check if datetime is within this range"""
        return self.start <= dt <= self.end

@dataclass
class Budget:
    """Budget management with tracking"""
    allocated: float
    used: float = 0.0
    reserved: float = 0.0
    currency: str = "USD"
    
    @property
    def available(self) -> float:
        """Available budget"""
        return self.allocated - self.used - self.reserved
    
    @property
    def utilization_percentage(self) -> float:
        """Budget utilization percentage"""
        return (self.used / self.allocated * 100) if self.allocated > 0 else 0
    
    @property
    def is_over_budget(self) -> bool:
        """Check if over budget"""
        return self.used > self.allocated
    
    def add_expense(self, amount: float, description: str = "") -> bool:
        """Add expense and return success status"""
        if self.available >= amount:
            self.used += amount
            return True
        return False

@dataclass
class ContactInfo:
    """Contact information structure"""
    email: str
    phone: Optional[str] = None
    slack_id: Optional[str] = None
    teams_id: Optional[str] = None
    timezone: str = "UTC"
    preferred_contact_hours: Optional[TimeRange] = None

@dataclass
class NotificationPreferences:
    """Notification preferences for stakeholders"""
    channels: Dict[NotificationChannel, bool] = field(default_factory=dict)
    frequency: str = "daily"  # immediate, daily, weekly
    include_details: bool = True
    include_metrics: bool = True
    escalation_threshold: Priority = Priority.HIGH
    
    def __post_init__(self):
        # Set default preferences if not provided
        if not self.channels:
            self.channels = {
                NotificationChannel.EMAIL: True,
                NotificationChannel.SLACK: False,
                NotificationChannel.SMS: False,
                NotificationChannel.IN_APP: True
            }

@dataclass
class Skill:
    """Skill representation with proficiency"""
    name: str
    category: SkillCategory
    proficiency_level: int  # 1-10 scale
    years_experience: float
    last_used: Optional[datetime] = None
    certified: bool = False
    certification_date: Optional[datetime] = None
    
    @property
    def is_current(self) -> bool:
        """Check if skill was used recently (within 1 year)"""
        if not self.last_used:
            return False
        return (datetime.now() - self.last_used).days <= 365

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    quality_score: float  # 1-10 scale
    productivity_score: float  # 1-10 scale
    collaboration_score: float  # 1-10 scale
    innovation_score: float  # 1-10 scale
    reliability_score: float  # 1-10 scale
    communication_score: float  # 1-10 scale
    leadership_score: Optional[float] = None  # 1-10 scale, only for leads
    
    @property
    def overall_score(self) -> float:
        """Calculate overall performance score"""
        scores = [
            self.quality_score,
            self.productivity_score,
            self.collaboration_score,
            self.innovation_score,
            self.reliability_score,
            self.communication_score
        ]
        
        if self.leadership_score is not None:
            scores.append(self.leadership_score)
        
        return sum(scores) / len(scores)
    
    @property
    def performance_level(self) -> str:
        """Get performance level description"""
        score = self.overall_score
        if score >= 9.0:
            return "Exceptional"
        elif score >= 8.0:
            return "Excellent"
        elif score >= 7.0:
            return "Good"
        elif score >= 6.0:
            return "Satisfactory"
        else:
            return "Needs Improvement"

# ========================================================================================
# CORE MODELS
# ========================================================================================

@dataclass
class Project:
    """Comprehensive project model with autonomous capabilities"""
    # Basic Information
    project_id: str
    name: str
    description: str
    status: ProjectStatus
    
    # Timeline
    timeline: TimeRange
    
    # Financial
    budget: Budget
    
    # Team and Management
    project_manager_id: str
    team_size: int
    client_name: str
    department: str
    
    # Progress and Quality
    completion_percentage: float = 0.0
    quality_gate_passed: bool = False
    
    # Risk and Health
    risk_level: RiskLevel = RiskLevel.MEDIUM
    health_score: float = 7.0  # 1-10 scale
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    
    # Autonomous Features
    autonomous_monitoring: bool = True
    auto_escalation_enabled: bool = True
    predictive_analytics_enabled: bool = True
    
    # Additional Properties
    tags: List[str] = field(default_factory=list)
    external_links: Dict[str, str] = field(default_factory=dict)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.project_id:
            self.project_id = f"PROJ_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    @property
    def days_remaining(self) -> int:
        """Days remaining in project"""
        return max(0, (self.timeline.end - datetime.now()).days)
    
    @property
    def is_overdue(self) -> bool:
        """Check if project is overdue"""
        return datetime.now() > self.timeline.end and self.status != ProjectStatus.COMPLETED
    
    @property
    def is_behind_schedule(self) -> bool:
        """Check if project is behind schedule"""
        if self.timeline.duration_days == 0:
            return False
        
        elapsed_percentage = ((datetime.now() - self.timeline.start).days / self.timeline.duration_days) * 100
        return self.completion_percentage < elapsed_percentage - 10  # 10% tolerance
    
    @property
    def project_velocity(self) -> float:
        """Calculate project velocity (completion % per day)"""
        elapsed_days = (datetime.now() - self.timeline.start).days
        return self.completion_percentage / elapsed_days if elapsed_days > 0 else 0
    
    @property
    def estimated_completion_date(self) -> datetime:
        """Estimate completion date based on current velocity"""
        if self.project_velocity == 0:
            return self.timeline.end
        
        remaining_percentage = 100 - self.completion_percentage
        days_needed = remaining_percentage / self.project_velocity
        return datetime.now() + timedelta(days=days_needed)
    
    def update_health_score(self, budget_factor: float = 0.3, schedule_factor: float = 0.3, 
                           quality_factor: float = 0.2, team_factor: float = 0.2) -> float:
        """Update and return health score based on multiple factors"""
        # Budget health (0-10)
        budget_health = 10 - min(10, (self.budget.utilization_percentage - 70) / 3)  # Optimal at 70%
        
        # Schedule health (0-10)
        schedule_health = 10 if not self.is_behind_schedule else max(0, 10 - (abs(self.completion_percentage - 
                         ((datetime.now() - self.timeline.start).days / self.timeline.duration_days) * 100) / 10))
        
        # Quality health (assume 8.0 baseline)
        quality_health = 8.0
        
        # Team health (assume 7.5 baseline)
        team_health = 7.5
        
        self.health_score = (budget_health * budget_factor + 
                           schedule_health * schedule_factor + 
                           quality_health * quality_factor + 
                           team_health * team_factor)
        
        self.last_updated = datetime.now()
        return self.health_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums and datetime objects
        data['status'] = self.status.value
        data['risk_level'] = self.risk_level.value
        data['timeline'] = {
            'start': self.timeline.start.isoformat(),
            'end': self.timeline.end.isoformat()
        }
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data

@dataclass
class Stakeholder:
    """Comprehensive stakeholder model"""
    # Basic Information
    stakeholder_id: str
    name: str
    role: StakeholderRole
    project_id: str
    
    # Contact Information
    contact_info: ContactInfo
    
    # Preferences
    notification_preferences: NotificationPreferences
    
    # Organizational
    department: str
    organization: str = "Internal"
    manager_id: Optional[str] = None
    
    # Engagement
    engagement_level: int = 5  # 1-10 scale
    influence_level: int = 5   # 1-10 scale
    availability_percentage: float = 100.0
    
    # Communication History
    last_contacted: Optional[datetime] = None
    total_communications: int = 0
    response_rate: float = 100.0  # Percentage
    
    # Autonomous Features
    auto_communication_enabled: bool = True
    escalation_threshold: int = 3  # Days without response
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.stakeholder_id:
            self.stakeholder_id = f"STK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if self.last_contacted is None:
            self.last_contacted = datetime.now() - timedelta(days=7)
    
    @property
    def days_since_last_contact(self) -> int:
        """Days since last contact"""
        if not self.last_contacted:
            return float('inf')
        return (datetime.now() - self.last_contacted).days
    
    @property
    def needs_follow_up(self) -> bool:
        """Check if stakeholder needs follow-up"""
        return self.days_since_last_contact >= self.escalation_threshold
    
    @property
    def is_highly_engaged(self) -> bool:
        """Check if stakeholder is highly engaged"""
        return self.engagement_level >= 8 and self.response_rate >= 80
    
    def record_communication(self, response_received: bool = True):
        """Record a communication event"""
        self.last_contacted = datetime.now()
        self.total_communications += 1
        
        if response_received:
            # Recalculate response rate
            self.response_rate = min(100.0, self.response_rate * 0.9 + 10.0)
        else:
            self.response_rate = max(0.0, self.response_rate * 0.9)

# Fixed dataclass definitions - replace the problematic sections in project_models.py

@dataclass
class Task:
    """Comprehensive task model with dependencies and tracking"""
    # Basic Information (NO DEFAULTS - MUST BE FIRST)
    task_id: str
    project_id: str
    title: str
    description: str
    assigned_to: str
    timeline: TimeRange
    estimated_hours: float
    
    # Assignment and Status (NO DEFAULTS)
    created_by: str = "system"
    category: str = "development"
    
    # FIELDS WITH DEFAULTS (MUST BE LAST)
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    actual_hours: float = 0.0
    completion_percentage: float = 0.0
    quality_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_task_id: Optional[str] = None
    
    # Lists with defaults (MUST BE LAST)
    dependencies: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.task_id:
            self.task_id = f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

@dataclass
class Employee:
    """Comprehensive employee model with performance tracking"""
    # Basic Information (NO DEFAULTS - MUST BE FIRST)
    employee_id: str
    name: str
    email: str
    role: StakeholderRole
    department: str
    
    # FIELDS WITH DEFAULTS (MUST BE LAST)
    manager_id: Optional[str] = None
    hire_date: datetime = field(default_factory=datetime.now)
    availability_percentage: float = 100.0
    capacity_hours_per_week: float = 40.0
    current_utilization: float = 80.0
    total_hours_worked: float = 0.0
    tasks_completed: int = 0
    average_task_quality: float = 7.0
    performance_trend: PerformanceTrend = PerformanceTrend.STABLE
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    
    # Complex fields with defaults
    current_performance: PerformanceMetrics = field(default_factory=lambda: PerformanceMetrics(
        quality_score=7.0, productivity_score=7.0, collaboration_score=7.0,
        innovation_score=7.0, reliability_score=7.0, communication_score=7.0
    ))
    
    # Lists with defaults (MUST BE LAST)
    skills: List[Skill] = field(default_factory=list)
    skill_gaps: List[str] = field(default_factory=list)
    current_projects: List[str] = field(default_factory=list)
    development_goals: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.employee_id:
            self.employee_id = f"EMP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if self.next_review_date is None:
            self.next_review_date = datetime.now() + timedelta(days=90)

@dataclass
class AutonomousAction:
    """Model for tracking autonomous system actions"""
    # Basic Information (NO DEFAULTS - MUST BE FIRST)
    action_id: str
    action_type: ActionType
    category: DecisionCategory
    project_id: str
    triggered_by: str
    description: str
    reasoning: str
    confidence_score: float
    
    # FIELDS WITH DEFAULTS (MUST BE LAST)
    execution_status: str = "pending"
    executed_at: datetime = field(default_factory=datetime.now)
    result: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[datetime] = None
    effectiveness_score: Optional[float] = None
    feedback: Optional[str] = None
    
    # Complex fields with defaults
    context_data: Dict[str, Any] = field(default_factory=dict)
    stakeholders_notified: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.action_id:
            self.action_id = f"ACT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

@dataclass
class ProjectReport:
    """Comprehensive project report model"""
    # Basic Information (NO DEFAULTS - MUST BE FIRST)
    report_id: str
    project_id: str
    report_type: str
    generated_by: str = "autonomous_system"
    
    # FIELDS WITH DEFAULTS (MUST BE LAST)
    generated_at: datetime = field(default_factory=datetime.now)
    executive_summary: str = ""
    report_period: Optional[TimeRange] = None
    next_report_date: Optional[datetime] = None
    
    # Complex fields with defaults
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    autonomous_decisions: List[str] = field(default_factory=list)
    predictive_insights: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    target_audience: List[StakeholderRole] = field(default_factory=list)
    distribution_list: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing"""
        if not self.report_id:
            self.report_id = f"RPT_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if self.next_report_date is None:
            self.next_report_date = datetime.now() + timedelta(days=7)

# ========================================================================================
# FACTORY CLASSES
# ========================================================================================

class ProjectFactory:
    """Factory for creating project instances"""
    
    @staticmethod
    def create_project(name: str, description: str, project_manager_id: str,
                      client_name: str, budget_amount: float,
                      start_date: datetime, end_date: datetime,
                      **kwargs) -> Project:
        """Create a new project with default settings"""
        
        timeline = TimeRange(start=start_date, end=end_date)
        budget = Budget(allocated=budget_amount)
        
        return Project(
            project_id=kwargs.get('project_id', ''),
            name=name,
            description=description,
            status=ProjectStatus.PLANNING,
            timeline=timeline,
            budget=budget,
            project_manager_id=project_manager_id,
            team_size=kwargs.get('team_size', 5),
            client_name=client_name,
            department=kwargs.get('department', 'IT'),
            **kwargs
        )
    
    @staticmethod
    def create_sample_project() -> Project:
        """Create a sample project for testing"""
        return ProjectFactory.create_project(
            name="AI-Powered Customer Portal",
            description="Develop an AI-powered customer service portal with natural language processing",
            project_manager_id="PM001",
            client_name="TechCorp Inc",
            budget_amount=150000,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() + timedelta(days=60),
            team_size=8,
            department="IT",
            risk_level=RiskLevel.MEDIUM
        )

class EmployeeFactory:
    """Factory for creating employee instances"""
    
    @staticmethod
    def create_employee(name: str, email: str, role: StakeholderRole,
                       department: str, **kwargs) -> Employee:
        """Create a new employee with default settings"""
        
        performance = PerformanceMetrics(
            quality_score=kwargs.get('quality_score', 7.0),
            productivity_score=kwargs.get('productivity_score', 7.0),
            collaboration_score=kwargs.get('collaboration_score', 7.0),
            innovation_score=kwargs.get('innovation_score', 7.0),
            reliability_score=kwargs.get('reliability_score', 7.0),
            communication_score=kwargs.get('communication_score', 7.0)
        )
        
        return Employee(
            employee_id=kwargs.get('employee_id', ''),
            name=name,
            email=email,
            role=role,
            department=department,
            current_performance=performance,
            **kwargs
        )

class ProjectAnalytics:
    """Analytics and calculations for project data"""
    
    @staticmethod
    def calculate_project_health(project, tasks: List = None, 
                               team_performance: List = None) -> Dict[str, Any]:
        """Calculate comprehensive project health metrics"""
        health_data = {
            'overall_health': project.health_score if hasattr(project, 'health_score') else 7.5,
            'budget_health': ProjectAnalytics._calculate_budget_health(project),
            'schedule_health': ProjectAnalytics._calculate_schedule_health(project),
            'team_health': ProjectAnalytics._calculate_team_health(team_performance) if team_performance else 7.5,
            'quality_health': ProjectAnalytics._calculate_quality_health(tasks) if tasks else 8.0,
            'risk_factors': ProjectAnalytics._identify_risk_factors(project, tasks, team_performance)
        }
        
        # Calculate weighted overall health
        weights = {'budget': 0.25, 'schedule': 0.25, 'team': 0.25, 'quality': 0.25}
        health_data['calculated_health'] = (
            health_data['budget_health'] * weights['budget'] +
            health_data['schedule_health'] * weights['schedule'] +
            health_data['team_health'] * weights['team'] +
            health_data['quality_health'] * weights['quality']
        )
        
        return health_data
    
    @staticmethod
    def _calculate_budget_health(project) -> float:
        """Calculate budget health score (1-10)"""
        if hasattr(project, 'budget') and hasattr(project.budget, 'utilization_percentage'):
            utilization = project.budget.utilization_percentage
        else:
            utilization = 75.0  # Default
        
        if utilization <= 70:
            return 10.0
        elif utilization <= 80:
            return 8.0
        elif utilization <= 90:
            return 6.0
        elif utilization <= 100:
            return 4.0
        else:
            return 2.0
    
    @staticmethod
    def _calculate_schedule_health(project) -> float:
        """Calculate schedule health score (1-10)"""
        if hasattr(project, 'is_overdue') and project.is_overdue:
            return 2.0
        elif hasattr(project, 'is_behind_schedule') and project.is_behind_schedule:
            return 4.0
        else:
            return 8.0
    
    @staticmethod
    def _calculate_team_health(team_performance) -> float:
        """Calculate team health score (1-10)"""
        if not team_performance:
            return 7.5
        
        # Simple average for demo
        total_score = 0
        for emp in team_performance:
            if hasattr(emp, 'current_performance'):
                total_score += emp.current_performance.overall_score
            else:
                total_score += 7.5
        
        return total_score / len(team_performance)
    
    @staticmethod
    def _calculate_quality_health(tasks) -> float:
        """Calculate quality health score (1-10)"""
        if not tasks:
            return 8.0
        
        completed_tasks = [task for task in tasks if hasattr(task, 'quality_score') and task.quality_score]
        
        if not completed_tasks:
            return 7.0
        
        avg_quality = sum(task.quality_score for task in completed_tasks) / len(completed_tasks)
        return avg_quality
    
    @staticmethod
    def _identify_risk_factors(project, tasks=None, team_performance=None) -> List[Dict[str, Any]]:
        """Identify project risk factors"""
        risks = []
        
        # Budget risks
        if hasattr(project, 'budget') and hasattr(project.budget, 'utilization_percentage'):
            if project.budget.utilization_percentage > 90:
                risks.append({
                    'type': 'budget',
                    'severity': 'high' if project.budget.utilization_percentage > 100 else 'medium',
                    'description': f'Budget utilization at {project.budget.utilization_percentage:.1f}%',
                    'impact': 'financial'
                })
        
        # Schedule risks
        if hasattr(project, 'is_behind_schedule') and project.is_behind_schedule:
            risks.append({
                'type': 'schedule',
                'severity': 'high' if hasattr(project, 'is_overdue') and project.is_overdue else 'medium',
                'description': 'Project behind schedule',
                'impact': 'delivery'
            })
        
        return risks

class PerformanceAnalytics:
    """Analytics for employee and team performance"""
    
    @staticmethod
    def analyze_team_performance(employees) -> Dict[str, Any]:
        """Analyze team performance metrics"""
        if not employees:
            return {}
        
        # Calculate averages
        total_scores = {
            'quality': 0, 'productivity': 0, 'collaboration': 0, 
            'innovation': 0, 'reliability': 0, 'communication': 0
        }
        
        for emp in employees:
            if hasattr(emp, 'current_performance'):
                perf = emp.current_performance
                total_scores['quality'] += perf.quality_score
                total_scores['productivity'] += perf.productivity_score
                total_scores['collaboration'] += perf.collaboration_score
                total_scores['innovation'] += perf.innovation_score
                total_scores['reliability'] += perf.reliability_score
                total_scores['communication'] += perf.communication_score
        
        team_size = len(employees)
        avg_scores = {key: value/team_size for key, value in total_scores.items()}
        
        # Performance distribution
        distribution = {
            'top_performers': sum(1 for emp in employees if hasattr(emp, 'is_top_performer') and emp.is_top_performer),
            'good_performers': sum(1 for emp in employees 
                                 if hasattr(emp, 'current_performance') and 
                                 7.0 <= emp.current_performance.overall_score < 8.5),
            'average_performers': sum(1 for emp in employees 
                                    if hasattr(emp, 'current_performance') and 
                                    6.0 <= emp.current_performance.overall_score < 7.0),
            'needs_improvement': sum(1 for emp in employees if hasattr(emp, 'needs_development') and emp.needs_development)
        }
        
        return {
            'team_size': team_size,
            'average_scores': avg_scores,
            'overall_average': sum(avg_scores.values()) / len(avg_scores),
            'performance_distribution': distribution,
            'employees_due_for_review': sum(1 for emp in employees 
                                          if hasattr(emp, 'is_due_for_review') and emp.is_due_for_review)
        }
    
    @staticmethod
    def get_development_recommendations(employee) -> List[Dict[str, Any]]:
        """Get development recommendations for an employee"""
        recommendations = []
        
        if hasattr(employee, 'current_performance'):
            performance = employee.current_performance
            
            if performance.quality_score < 7.0:
                recommendations.append({
                    'type': 'quality_improvement',
                    'priority': 'high',
                    'description': 'Focus on code quality and best practices',
                    'actions': ['Code review training', 'Quality standards workshop']
                })
            
            if hasattr(employee, 'is_top_performer') and employee.is_top_performer:
                recommendations.append({
                    'type': 'career_advancement',
                    'priority': 'high',
                    'description': 'Prepare for leadership role',
                    'actions': ['Leadership training', 'Mentoring opportunities']
                })
        
        return recommendations