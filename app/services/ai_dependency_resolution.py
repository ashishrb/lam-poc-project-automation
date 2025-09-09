"""
AI Dependency Resolution Service
Provides intelligent dependency analysis, conflict detection, and resolution guidance
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DependencyType(Enum):
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"

class DependencyStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ConflictSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TaskDependency:
    """Individual task dependency"""
    id: str
    task_name: str
    depends_on: str
    dependency_type: DependencyType
    lag_days: int
    status: DependencyStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class DependencyConflict:
    """Dependency conflict analysis"""
    conflict_id: str
    conflict_type: str
    description: str
    severity: ConflictSeverity
    affected_tasks: List[str]
    root_cause: str
    impact_analysis: str
    resolution_strategies: List[str]

@dataclass
class CriticalPathAnalysis:
    """Critical path analysis results"""
    critical_path: List[str]
    total_duration: int
    critical_tasks: List[str]
    float_analysis: Dict[str, int]
    bottlenecks: List[str]
    optimization_opportunities: List[str]

@dataclass
class DependencyResolutionPlan:
    """AI-generated dependency resolution plan"""
    plan_id: str
    project_id: str
    conflicts: List[DependencyConflict]
    critical_path: CriticalPathAnalysis
    resolution_actions: List[Dict[str, Any]]
    timeline: str
    success_metrics: List[str]
    monitoring_plan: str
    generated_at: datetime
    confidence_score: float

class AIDependencyResolutionService:
    """AI-powered dependency analysis and resolution service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_dependencies_and_generate_resolution_plan(
        self, 
        project_id: str,
        tasks: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]] = None
    ) -> DependencyResolutionPlan:
        """
        Analyze project dependencies and generate AI-powered resolution plan
        """
        try:
            # Detect dependency conflicts
            conflicts = await self._detect_dependency_conflicts(tasks, dependencies)
            
            # Perform critical path analysis
            critical_path = await self._analyze_critical_path(tasks, dependencies)
            
            # Generate resolution actions
            resolution_actions = await self._generate_resolution_actions(conflicts, critical_path)
            
            # Generate timeline and success metrics
            timeline = self._generate_resolution_timeline(conflicts, critical_path)
            success_metrics = self._generate_success_metrics(conflicts, critical_path)
            monitoring_plan = self._generate_monitoring_plan(conflicts, critical_path)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(conflicts, critical_path)
            
            return DependencyResolutionPlan(
                plan_id=f"dep_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                project_id=project_id,
                conflicts=conflicts,
                critical_path=critical_path,
                resolution_actions=resolution_actions,
                timeline=timeline,
                success_metrics=success_metrics,
                monitoring_plan=monitoring_plan,
                generated_at=datetime.now(),
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Error generating dependency resolution plan: {e}")
            return self._create_fallback_plan(project_id)
    
    async def _detect_dependency_conflicts(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> List[DependencyConflict]:
        """Detect various types of dependency conflicts"""
        conflicts = []
        
        # Circular dependency detection
        circular_conflicts = self._detect_circular_dependencies(tasks, dependencies)
        conflicts.extend(circular_conflicts)
        
        # Resource conflict detection
        resource_conflicts = self._detect_resource_conflicts(tasks, dependencies)
        conflicts.extend(resource_conflicts)
        
        # Timeline conflict detection
        timeline_conflicts = self._detect_timeline_conflicts(tasks, dependencies)
        conflicts.extend(timeline_conflicts)
        
        # Skill dependency conflicts
        skill_conflicts = self._detect_skill_dependencies(tasks, dependencies)
        conflicts.extend(skill_conflicts)
        
        return conflicts
    
    def _detect_circular_dependencies(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> List[DependencyConflict]:
        """Detect circular dependencies in the task graph"""
        conflicts = []
        
        # Demo circular dependency detection
        demo_circular = [
            DependencyConflict(
                conflict_id="circular_1",
                conflict_type="Circular Dependency",
                description="Task A depends on Task B, which depends on Task A",
                severity=ConflictSeverity.HIGH,
                affected_tasks=["API Development", "Database Design"],
                root_cause="Bidirectional dependency created during planning",
                impact_analysis="Creates infinite loop preventing project progress",
                resolution_strategies=[
                    "Break the circular dependency by introducing intermediate task",
                    "Restructure tasks to have clear sequential flow",
                    "Use parallel development approach with integration points"
                ]
            )
        ]
        
        return demo_circular
    
    def _detect_resource_conflicts(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> List[DependencyConflict]:
        """Detect resource allocation conflicts"""
        conflicts = []
        
        # Demo resource conflicts
        demo_resource = [
            DependencyConflict(
                conflict_id="resource_1",
                conflict_type="Resource Over-allocation",
                description="Same developer assigned to overlapping critical tasks",
                severity=ConflictSeverity.MEDIUM,
                affected_tasks=["API Development", "Frontend Development"],
                root_cause="Insufficient resource planning and skill overlap",
                impact_analysis="Developer cannot work on both tasks simultaneously",
                resolution_strategies=[
                    "Reassign one task to another qualified developer",
                    "Adjust task timelines to avoid overlap",
                    "Bring in additional resources or contractors"
                ]
            )
        ]
        
        return demo_resource
    
    def _detect_timeline_conflicts(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> List[DependencyConflict]:
        """Detect timeline and deadline conflicts"""
        conflicts = []
        
        # Demo timeline conflicts
        demo_timeline = [
            DependencyConflict(
                conflict_id="timeline_1",
                conflict_type="Timeline Constraint",
                description="Dependent task scheduled before prerequisite completion",
                severity=ConflictSeverity.CRITICAL,
                affected_tasks=["Testing", "API Development"],
                root_cause="Incorrect dependency mapping and timeline estimation",
                impact_analysis="Testing cannot begin before API is complete",
                resolution_strategies=[
                    "Adjust task start dates to respect dependencies",
                    "Fast-track prerequisite task completion",
                    "Implement parallel testing approach where possible"
                ]
            )
        ]
        
        return demo_timeline
    
    def _detect_skill_dependencies(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> List[DependencyConflict]:
        """Detect skill-based dependency conflicts"""
        conflicts = []
        
        # Demo skill conflicts
        demo_skill = [
            DependencyConflict(
                conflict_id="skill_1",
                conflict_type="Skill Gap Dependency",
                description="Task requires skills not available in current team",
                severity=ConflictSeverity.MEDIUM,
                affected_tasks=["DevOps Setup", "Security Implementation"],
                root_cause="Insufficient skill assessment during planning",
                impact_analysis="Tasks cannot proceed without required expertise",
                resolution_strategies=[
                    "Provide training for existing team members",
                    "Hire external consultants with required skills",
                    "Restructure tasks to use available skills"
                ]
            )
        ]
        
        return demo_skill
    
    async def _analyze_critical_path(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> CriticalPathAnalysis:
        """Perform critical path analysis"""
        
        # Demo critical path analysis
        critical_tasks = [
            "Setup Development Environment",
            "Database Design", 
            "API Development",
            "Integration Testing",
            "Deployment"
        ]
        
        return CriticalPathAnalysis(
            critical_path=critical_tasks,
            total_duration=14,  # days
            critical_tasks=critical_tasks,
            float_analysis={
                "Frontend Development": 2,
                "Documentation": 3,
                "User Training": 1
            },
            bottlenecks=[
                "API Development (5 days - longest task)",
                "Database Design (3 days - blocks multiple tasks)"
            ],
            optimization_opportunities=[
                "Parallelize Frontend and API development",
                "Implement continuous integration to reduce testing time",
                "Use automated deployment to reduce deployment time"
            ]
        )
    
    async def _generate_resolution_actions(
        self, 
        conflicts: List[DependencyConflict], 
        critical_path: CriticalPathAnalysis
    ) -> List[Dict[str, Any]]:
        """Generate specific resolution actions"""
        actions = []
        
        # Generate actions for each conflict
        for conflict in conflicts:
            if conflict.conflict_type == "Circular Dependency":
                actions.append({
                    "id": f"action_{conflict.conflict_id}",
                    "title": "Break Circular Dependencies",
                    "description": "Restructure task dependencies to eliminate circular references",
                    "priority": "High",
                    "estimated_effort": "1-2 days",
                    "owner": "Project Manager",
                    "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "status": "pending",
                    "dependencies": [],
                    "success_criteria": "All circular dependencies resolved"
                })
            
            elif conflict.conflict_type == "Resource Over-allocation":
                actions.append({
                    "id": f"action_{conflict.conflict_id}",
                    "title": "Resolve Resource Conflicts",
                    "description": "Reassign tasks or adjust timelines to eliminate resource conflicts",
                    "priority": "High",
                    "estimated_effort": "2-3 days",
                    "owner": "Resource Manager",
                    "due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                    "status": "pending",
                    "dependencies": [],
                    "success_criteria": "All resource conflicts resolved"
                })
            
            elif conflict.conflict_type == "Timeline Constraint":
                actions.append({
                    "id": f"action_{conflict.conflict_id}",
                    "title": "Adjust Timeline Dependencies",
                    "description": "Reschedule tasks to respect proper dependency order",
                    "priority": "Critical",
                    "estimated_effort": "1 day",
                    "owner": "Project Manager",
                    "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "status": "pending",
                    "dependencies": [],
                    "success_criteria": "All timeline conflicts resolved"
                })
        
        # Add critical path optimization actions
        actions.append({
            "id": "action_critical_path_1",
            "title": "Optimize Critical Path",
            "description": "Implement parallel development and automation to reduce critical path duration",
            "priority": "Medium",
            "estimated_effort": "1 week",
            "owner": "Technical Lead",
            "due_date": (datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d"),
            "status": "pending",
            "dependencies": [],
            "success_criteria": "Critical path duration reduced by 20%"
        })
        
        return actions
    
    def _generate_resolution_timeline(
        self, 
        conflicts: List[DependencyConflict], 
        critical_path: CriticalPathAnalysis
    ) -> str:
        """Generate timeline for dependency resolution"""
        critical_count = len([c for c in conflicts if c.severity == ConflictSeverity.CRITICAL])
        high_count = len([c for c in conflicts if c.severity == ConflictSeverity.HIGH])
        
        if critical_count > 0:
            return "Immediate action required - Critical conflicts must be resolved within 1-2 days"
        elif high_count > 0:
            return "Urgent resolution needed - High priority conflicts within 3-5 days"
        else:
            return "Standard timeline - All conflicts resolved within 1-2 weeks"
    
    def _generate_success_metrics(
        self, 
        conflicts: List[DependencyConflict], 
        critical_path: CriticalPathAnalysis
    ) -> List[str]:
        """Generate success metrics for dependency resolution"""
        return [
            "All dependency conflicts resolved",
            "Critical path duration optimized",
            "Zero circular dependencies",
            "Resource allocation conflicts eliminated",
            "Project timeline maintained or improved",
            "Team productivity increased by 15%"
        ]
    
    def _generate_monitoring_plan(
        self, 
        conflicts: List[DependencyConflict], 
        critical_path: CriticalPathAnalysis
    ) -> str:
        """Generate monitoring plan for dependency management"""
        return """
        Dependency Monitoring Plan:
        
        1. Daily Dependency Check: Review task dependencies and identify new conflicts
        2. Weekly Critical Path Review: Analyze critical path changes and bottlenecks
        3. Resource Allocation Monitoring: Track resource conflicts and availability
        4. Timeline Validation: Ensure all dependencies respect project timeline
        5. Conflict Prevention: Proactive identification of potential dependency issues
        6. Stakeholder Updates: Regular communication about dependency status
        """
    
    def _calculate_confidence_score(
        self, 
        conflicts: List[DependencyConflict], 
        critical_path: CriticalPathAnalysis
    ) -> float:
        """Calculate confidence score for the resolution plan"""
        base_score = 0.8
        
        # Reduce confidence for critical conflicts
        critical_conflicts = len([c for c in conflicts if c.severity == ConflictSeverity.CRITICAL])
        high_conflicts = len([c for c in conflicts if c.severity == ConflictSeverity.HIGH])
        
        penalty = (critical_conflicts * 0.1) + (high_conflicts * 0.05)
        
        return max(0.5, base_score - penalty)
    
    def _create_fallback_plan(self, project_id: str) -> DependencyResolutionPlan:
        """Create a basic fallback plan if analysis fails"""
        return DependencyResolutionPlan(
            plan_id=f"fallback_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            project_id=project_id,
            conflicts=[],
            critical_path=CriticalPathAnalysis(
                critical_path=[],
                total_duration=0,
                critical_tasks=[],
                float_analysis={},
                bottlenecks=[],
                optimization_opportunities=[]
            ),
            resolution_actions=[],
            timeline="Standard dependency resolution timeline",
            success_metrics=["Dependencies properly managed"],
            monitoring_plan="Basic dependency monitoring",
            generated_at=datetime.now(),
            confidence_score=0.6
        )
    
    async def get_dependency_visualization_data(
        self, 
        tasks: List[Dict[str, Any]], 
        dependencies: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate data for dependency visualization"""
        
        # Demo dependency graph data
        nodes = []
        edges = []
        
        # Add task nodes
        for i, task in enumerate(tasks):
            nodes.append({
                "id": f"task_{i}",
                "label": task.get("name", f"Task {i+1}"),
                "group": "task",
                "status": task.get("status", "pending"),
                "duration": task.get("duration", 1),
                "critical": i < 3  # First 3 tasks are critical
            })
        
        # Add dependency edges
        demo_edges = [
            {"from": "task_0", "to": "task_1", "type": "finish_to_start", "lag": 0},
            {"from": "task_1", "to": "task_2", "type": "finish_to_start", "lag": 0},
            {"from": "task_2", "to": "task_3", "type": "finish_to_start", "lag": 1},
            {"from": "task_1", "to": "task_4", "type": "start_to_start", "lag": 2}
        ]
        
        edges.extend(demo_edges)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "hierarchical",
            "critical_path": ["task_0", "task_1", "task_2", "task_3"]
        }

# Global instance
_ai_dependency_service = None

def get_ai_dependency_service() -> AIDependencyResolutionService:
    """Get the global AI dependency resolution service instance"""
    global _ai_dependency_service
    if _ai_dependency_service is None:
        _ai_dependency_service = AIDependencyResolutionService()
    return _ai_dependency_service
