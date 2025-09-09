"""
API endpoints for AI Dependency Resolution functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.services.ai_dependency_resolution import (
    get_ai_dependency_service,
    AIDependencyResolutionService,
    DependencyResolutionPlan,
    DependencyConflict,
    CriticalPathAnalysis,
    ConflictSeverity
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze-dependencies", response_model=Dict[str, Any])
async def analyze_dependencies_and_generate_plan(
    dependency_data: Dict[str, Any],
    dep_service: AIDependencyResolutionService = Depends(get_ai_dependency_service)
):
    """
    Analyze project dependencies and generate AI-powered resolution plan
    """
    try:
        project_id = dependency_data.get("project_id", "demo_project")
        tasks = dependency_data.get("tasks", [])
        dependencies = dependency_data.get("dependencies", [])
        
        # Generate AI dependency resolution plan
        resolution_plan = await dep_service.analyze_dependencies_and_generate_resolution_plan(
            project_id=project_id,
            tasks=tasks,
            dependencies=dependencies
        )
        
        # Convert to JSON-serializable format
        plan_data = {
            "plan_id": resolution_plan.plan_id,
            "project_id": resolution_plan.project_id,
            "conflicts": [
                {
                    "conflict_id": conflict.conflict_id,
                    "conflict_type": conflict.conflict_type,
                    "description": conflict.description,
                    "severity": conflict.severity.value,
                    "affected_tasks": conflict.affected_tasks,
                    "root_cause": conflict.root_cause,
                    "impact_analysis": conflict.impact_analysis,
                    "resolution_strategies": conflict.resolution_strategies
                }
                for conflict in resolution_plan.conflicts
            ],
            "critical_path": {
                "critical_path": resolution_plan.critical_path.critical_path,
                "total_duration": resolution_plan.critical_path.total_duration,
                "critical_tasks": resolution_plan.critical_path.critical_tasks,
                "float_analysis": resolution_plan.critical_path.float_analysis,
                "bottlenecks": resolution_plan.critical_path.bottlenecks,
                "optimization_opportunities": resolution_plan.critical_path.optimization_opportunities
            },
            "resolution_actions": resolution_plan.resolution_actions,
            "timeline": resolution_plan.timeline,
            "success_metrics": resolution_plan.success_metrics,
            "monitoring_plan": resolution_plan.monitoring_plan,
            "generated_at": resolution_plan.generated_at.isoformat(),
            "confidence_score": resolution_plan.confidence_score
        }
        
        return {
            "success": True,
            "message": "AI dependency resolution plan generated successfully",
            "data": plan_data
        }
        
    except Exception as e:
        logger.error(f"Error generating dependency resolution plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dependency resolution plan: {str(e)}")

@router.get("/dependency-visualization", response_model=Dict[str, Any])
async def get_dependency_visualization(
    project_id: str = "demo_project",
    dep_service: AIDependencyResolutionService = Depends(get_ai_dependency_service)
):
    """
    Get dependency visualization data for the project
    """
    try:
        # Demo tasks data
        demo_tasks = [
            {"name": "Setup Development Environment", "status": "completed", "duration": 2},
            {"name": "Database Design", "status": "in_progress", "duration": 3},
            {"name": "API Development", "status": "pending", "duration": 5},
            {"name": "Frontend Development", "status": "pending", "duration": 4},
            {"name": "Testing & QA", "status": "pending", "duration": 3},
            {"name": "Deployment", "status": "pending", "duration": 1}
        ]
        
        # Generate visualization data
        viz_data = await dep_service.get_dependency_visualization_data(
            tasks=demo_tasks,
            dependencies=[]
        )
        
        return {
            "success": True,
            "data": viz_data
        }
        
    except Exception as e:
        logger.error(f"Error generating dependency visualization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate dependency visualization: {str(e)}")

@router.get("/conflict-types", response_model=Dict[str, Any])
async def get_conflict_types():
    """
    Get available dependency conflict types
    """
    return {
        "success": True,
        "data": {
            "conflict_types": [
                {
                    "type": "Circular Dependency",
                    "description": "Tasks that depend on each other creating a loop",
                    "severity": "high",
                    "icon": "fas fa-sync-alt"
                },
                {
                    "type": "Resource Over-allocation",
                    "description": "Same resource assigned to overlapping tasks",
                    "severity": "medium",
                    "icon": "fas fa-users"
                },
                {
                    "type": "Timeline Constraint",
                    "description": "Dependent task scheduled before prerequisite",
                    "severity": "critical",
                    "icon": "fas fa-clock"
                },
                {
                    "type": "Skill Gap Dependency",
                    "description": "Task requires unavailable skills",
                    "severity": "medium",
                    "icon": "fas fa-graduation-cap"
                }
            ]
        }
    }

@router.get("/severity-levels", response_model=Dict[str, Any])
async def get_severity_levels():
    """
    Get available conflict severity levels
    """
    return {
        "success": True,
        "data": {
            "severity_levels": [
                {"value": "low", "label": "Low", "color": "success", "priority": 1},
                {"value": "medium", "label": "Medium", "color": "warning", "priority": 2},
                {"value": "high", "label": "High", "color": "danger", "priority": 3},
                {"value": "critical", "label": "Critical", "color": "dark", "priority": 4}
            ]
        }
    }

@router.post("/resolve-conflict", response_model=Dict[str, Any])
async def resolve_conflict(
    conflict_data: Dict[str, Any],
    dep_service: AIDependencyResolutionService = Depends(get_ai_dependency_service)
):
    """
    Resolve a specific dependency conflict
    """
    try:
        conflict_id = conflict_data.get("conflict_id")
        resolution_strategy = conflict_data.get("strategy")
        
        if not conflict_id or not resolution_strategy:
            raise HTTPException(status_code=400, detail="conflict_id and strategy are required")
        
        # In a real implementation, this would update the database
        # For demo purposes, we'll just return success
        return {
            "success": True,
            "message": f"Conflict {conflict_id} resolved using strategy: {resolution_strategy}",
            "data": {
                "conflict_id": conflict_id,
                "resolution_strategy": resolution_strategy,
                "resolved_at": datetime.now().isoformat(),
                "status": "resolved"
            }
        }
        
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve conflict: {str(e)}")

@router.get("/demo-dependencies", response_model=Dict[str, Any])
async def get_demo_dependencies():
    """
    Get demo dependency data for testing
    """
    return {
        "success": True,
        "data": {
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Setup Development Environment",
                    "duration": 2,
                    "status": "completed",
                    "assigned_to": "DevOps Team",
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-17"
                },
                {
                    "id": "task_2", 
                    "name": "Database Design",
                    "duration": 3,
                    "status": "in_progress",
                    "assigned_to": "Database Architect",
                    "start_date": "2024-01-18",
                    "end_date": "2024-01-22"
                },
                {
                    "id": "task_3",
                    "name": "API Development",
                    "duration": 5,
                    "status": "pending",
                    "assigned_to": "Backend Developer",
                    "start_date": "2024-01-23",
                    "end_date": "2024-01-29"
                },
                {
                    "id": "task_4",
                    "name": "Frontend Development",
                    "duration": 4,
                    "status": "pending",
                    "assigned_to": "Frontend Developer",
                    "start_date": "2024-01-25",
                    "end_date": "2024-01-30"
                },
                {
                    "id": "task_5",
                    "name": "Testing & QA",
                    "duration": 3,
                    "status": "pending",
                    "assigned_to": "QA Team",
                    "start_date": "2024-01-31",
                    "end_date": "2024-02-04"
                },
                {
                    "id": "task_6",
                    "name": "Deployment",
                    "duration": 1,
                    "status": "pending",
                    "assigned_to": "DevOps Team",
                    "start_date": "2024-02-05",
                    "end_date": "2024-02-05"
                }
            ],
            "dependencies": [
                {
                    "id": "dep_1",
                    "from_task": "task_1",
                    "to_task": "task_2",
                    "type": "finish_to_start",
                    "lag_days": 0
                },
                {
                    "id": "dep_2",
                    "from_task": "task_2", 
                    "to_task": "task_3",
                    "type": "finish_to_start",
                    "lag_days": 0
                },
                {
                    "id": "dep_3",
                    "from_task": "task_3",
                    "to_task": "task_5",
                    "type": "finish_to_start",
                    "lag_days": 1
                },
                {
                    "id": "dep_4",
                    "from_task": "task_2",
                    "to_task": "task_4",
                    "type": "start_to_start",
                    "lag_days": 2
                },
                {
                    "id": "dep_5",
                    "from_task": "task_5",
                    "to_task": "task_6",
                    "type": "finish_to_start",
                    "lag_days": 0
                }
            ]
        }
    }

@router.get("/optimization-suggestions", response_model=Dict[str, Any])
async def get_optimization_suggestions(
    project_id: str = "demo_project"
):
    """
    Get AI-powered optimization suggestions for dependencies
    """
    return {
        "success": True,
        "data": {
            "suggestions": [
                {
                    "type": "Parallel Development",
                    "title": "Implement Parallel Frontend/Backend Development",
                    "description": "Start frontend development in parallel with API development to reduce timeline",
                    "impact": "high",
                    "effort": "medium",
                    "savings": "2-3 days"
                },
                {
                    "type": "Automation",
                    "title": "Automate Testing and Deployment",
                    "description": "Implement CI/CD pipeline to reduce manual testing and deployment time",
                    "impact": "high",
                    "effort": "high",
                    "savings": "1-2 days"
                },
                {
                    "type": "Resource Optimization",
                    "title": "Cross-train Team Members",
                    "description": "Enable team members to work on multiple task types",
                    "impact": "medium",
                    "effort": "medium",
                    "savings": "1 day"
                },
                {
                    "type": "Process Improvement",
                    "title": "Implement Daily Standups",
                    "description": "Daily coordination meetings to identify and resolve dependencies quickly",
                    "impact": "medium",
                    "effort": "low",
                    "savings": "0.5 days"
                }
            ]
        }
    }
