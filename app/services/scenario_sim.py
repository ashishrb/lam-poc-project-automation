#!/usr/bin/env python3
"""
Scenario Simulation Service
Handles what-if analysis and scenario comparison for project planning
"""

import json
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.project import Project, Task
from app.models.user import User
from app.models.project import TaskStatus, TaskPriority, ProjectStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class ScenarioType(str, Enum):
    """Types of scenario simulations"""
    DEADLINE_CHANGE = "deadline_change"
    RESOURCE_CHANGE = "resource_change"
    SCOPE_CHANGE = "scope_change"
    BUDGET_CHANGE = "budget_change"
    RISK_MITIGATION = "risk_mitigation"
    OPTIMIZATION = "optimization"


class ImpactLevel(str, Enum):
    """Impact levels for scenario changes"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ScenarioParameter:
    """Parameter for scenario simulation"""
    parameter_type: str
    current_value: Any
    proposed_value: Any
    unit: str
    description: str


@dataclass
class ScenarioResult:
    """Results of a scenario simulation"""
    scenario_id: str
    scenario_name: str
    scenario_type: ScenarioType
    parameters: List[ScenarioParameter]
    
    # Project-level impacts
    original_duration: int
    new_duration: int
    duration_change: int
    
    original_cost: float
    new_cost: float
    cost_change: float
    
    original_end_date: date
    new_end_date: date
    
    # Task-level impacts
    affected_tasks: List[int]
    new_critical_path: List[int]
    
    # Risk assessment
    risk_level: ImpactLevel
    risk_factors: List[str]
    
    # Recommendations
    recommendations: List[str]
    feasibility_score: float  # 0-1 scale


class ScenarioSimulator:
    """Service for scenario simulation and what-if analysis"""
    
    def __init__(self):
        self.scenario_counter = 0
        self.impact_weights = {
            "duration": 0.4,
            "cost": 0.3,
            "resources": 0.2,
            "quality": 0.1
        }
    
    async def create_scenario(
        self, 
        project_id: int,
        scenario_name: str,
        scenario_type: ScenarioType,
        parameters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new scenario for simulation"""
        try:
            # Validate project exists
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Generate scenario ID
            self.scenario_counter += 1
            scenario_id = f"scenario_{project_id}_{self.scenario_counter}"
            
            # Validate parameters based on scenario type
            validated_params = await self._validate_scenario_parameters(
                scenario_type, parameters, project, db
            )
            
            # Store scenario (in a real system, this would be in a database)
            scenario_data = {
                "scenario_id": scenario_id,
                "project_id": project_id,
                "scenario_name": scenario_name,
                "scenario_type": scenario_type.value,
                "parameters": validated_params,
                "created_at": datetime.now().isoformat(),
                "status": "created"
            }
            
            return {
                "success": True,
                "scenario_id": scenario_id,
                "scenario_data": scenario_data
            }
            
        except Exception as e:
            logger.error(f"Error creating scenario: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def simulate_scenario(
        self, 
        scenario_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Simulate a scenario and calculate impacts"""
        try:
            # Get scenario data (in a real system, this would be from database)
            scenario_data = await self._get_scenario_data(scenario_id)
            if not scenario_data:
                raise ValueError(f"Scenario {scenario_id} not found")
            
            project_id = scenario_data["project_id"]
            scenario_type = ScenarioType(scenario_data["scenario_type"])
            parameters = scenario_data["parameters"]
            
            # Get project and tasks
            project = await self._get_project(project_id, db)
            tasks = await self._get_project_tasks(project_id, db)
            
            # Create scenario parameters
            scenario_params = []
            for param_name, param_data in parameters.items():
                scenario_params.append(ScenarioParameter(
                    parameter_type=param_name,
                    current_value=param_data["current"],
                    proposed_value=param_data["proposed"],
                    unit=param_data.get("unit", ""),
                    description=param_data.get("description", "")
                ))
            
            # Simulate based on scenario type
            if scenario_type == ScenarioType.DEADLINE_CHANGE:
                result = await self._simulate_deadline_change(
                    project, tasks, parameters, db
                )
            elif scenario_type == ScenarioType.RESOURCE_CHANGE:
                result = await self._simulate_resource_change(
                    project, tasks, parameters, db
                )
            elif scenario_type == ScenarioType.SCOPE_CHANGE:
                result = await self._simulate_scope_change(
                    project, tasks, parameters, db
                )
            elif scenario_type == ScenarioType.BUDGET_CHANGE:
                result = await self._simulate_budget_change(
                    project, tasks, parameters, db
                )
            else:
                result = await self._simulate_generic_scenario(
                    project, tasks, parameters, db
                )
            
            # Create scenario result
            scenario_result = ScenarioResult(
                scenario_id=scenario_id,
                scenario_name=scenario_data["scenario_name"],
                scenario_type=scenario_type,
                parameters=scenario_params,
                original_duration=result["original_duration"],
                new_duration=result["new_duration"],
                duration_change=result["duration_change"],
                original_cost=result["original_cost"],
                new_cost=result["new_cost"],
                cost_change=result["cost_change"],
                original_end_date=result["original_end_date"],
                new_end_date=result["new_end_date"],
                affected_tasks=result["affected_tasks"],
                new_critical_path=result["new_critical_path"],
                risk_level=result["risk_level"],
                risk_factors=result["risk_factors"],
                recommendations=result["recommendations"],
                feasibility_score=result["feasibility_score"]
            )
            
            return {
                "success": True,
                "scenario_id": scenario_id,
                "result": {
                    "scenario_name": scenario_result.scenario_name,
                    "scenario_type": scenario_result.scenario_type.value,
                    "parameters": [
                        {
                            "parameter_type": p.parameter_type,
                            "current_value": p.current_value,
                            "proposed_value": p.proposed_value,
                            "unit": p.unit,
                            "description": p.description
                        }
                        for p in scenario_result.parameters
                    ],
                    "duration_impact": {
                        "original_duration": scenario_result.original_duration,
                        "new_duration": scenario_result.new_duration,
                        "duration_change": scenario_result.duration_change,
                        "original_end_date": scenario_result.original_end_date.isoformat(),
                        "new_end_date": scenario_result.new_end_date.isoformat()
                    },
                    "cost_impact": {
                        "original_cost": scenario_result.original_cost,
                        "new_cost": scenario_result.new_cost,
                        "cost_change": scenario_result.cost_change
                    },
                    "affected_tasks": scenario_result.affected_tasks,
                    "new_critical_path": scenario_result.new_critical_path,
                    "risk_assessment": {
                        "risk_level": scenario_result.risk_level.value,
                        "risk_factors": scenario_result.risk_factors
                    },
                    "recommendations": scenario_result.recommendations,
                    "feasibility_score": scenario_result.feasibility_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error simulating scenario: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_scenarios(
        self, 
        project_id: int,
        scenario_ids: List[str],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Compare multiple scenarios side by side"""
        try:
            if len(scenario_ids) < 2:
                raise ValueError("At least 2 scenarios required for comparison")
            
            scenario_results = []
            
            for scenario_id in scenario_ids:
                result = await self.simulate_scenario(scenario_id, db)
                if result["success"]:
                    scenario_results.append(result["result"])
                else:
                    return result
            
            # Generate comparison matrix
            comparison = await self._generate_comparison_matrix(scenario_results)
            
            # Find best scenario
            best_scenario = await self._find_best_scenario(scenario_results)
            
            return {
                "success": True,
                "project_id": project_id,
                "scenarios": scenario_results,
                "comparison": comparison,
                "best_scenario": best_scenario,
                "summary": {
                    "total_scenarios": len(scenario_results),
                    "scenarios_with_improvement": len([s for s in scenario_results if s["duration_impact"]["duration_change"] < 0]),
                    "scenarios_with_cost_savings": len([s for s in scenario_results if s["cost_impact"]["cost_change"] < 0])
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing scenarios: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def apply_scenario(
        self, 
        scenario_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply a scenario to the actual project"""
        try:
            # Simulate the scenario first
            simulation_result = await self.simulate_scenario(scenario_id, db)
            if not simulation_result["success"]:
                return simulation_result
            
            result = simulation_result["result"]
            project_id = await self._get_scenario_project_id(scenario_id)
            
            # Apply changes based on scenario type
            scenario_type = result["scenario_type"]
            
            if scenario_type == "deadline_change":
                await self._apply_deadline_changes(project_id, result, db)
            elif scenario_type == "resource_change":
                await self._apply_resource_changes(project_id, result, db)
            elif scenario_type == "scope_change":
                await self._apply_scope_changes(project_id, result, db)
            elif scenario_type == "budget_change":
                await self._apply_budget_changes(project_id, result, db)
            
            # Log the application
            await self._log_scenario_application(scenario_id, result, db)
            
            return {
                "success": True,
                "scenario_id": scenario_id,
                "message": f"Scenario '{result['scenario_name']}' applied successfully",
                "changes_applied": result
            }
            
        except Exception as e:
            logger.error(f"Error applying scenario: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _get_project(self, project_id: int, db: AsyncSession) -> Optional[Project]:
        """Get project by ID"""
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()
    
    async def _get_project_tasks(self, project_id: int, db: AsyncSession) -> List[Task]:
        """Get all tasks for a project"""
        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.start_date)
        )
        return result.scalars().all()
    
    async def _validate_scenario_parameters(
        self, 
        scenario_type: ScenarioType, 
        parameters: Dict[str, Any],
        project: Project,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Validate scenario parameters"""
        validated = {}
        
        if scenario_type == ScenarioType.DEADLINE_CHANGE:
            if "new_deadline" not in parameters:
                raise ValueError("new_deadline parameter required for deadline change scenario")
            
            new_deadline = datetime.fromisoformat(parameters["new_deadline"]).date()
            if new_deadline <= date.today():
                raise ValueError("New deadline must be in the future")
            
            validated["new_deadline"] = {
                "current": project.planned_end_date.isoformat() if project.planned_end_date else None,
                "proposed": parameters["new_deadline"],
                "unit": "date",
                "description": "Project completion deadline"
            }
        
        elif scenario_type == ScenarioType.RESOURCE_CHANGE:
            if "resource_changes" not in parameters:
                raise ValueError("resource_changes parameter required for resource change scenario")
            
            for task_id, resource_data in parameters["resource_changes"].items():
                if "new_assignee_id" not in resource_data:
                    raise ValueError(f"new_assignee_id required for task {task_id}")
                
                # Validate assignee exists
                assignee = await self._get_user(resource_data["new_assignee_id"], db)
                if not assignee:
                    raise ValueError(f"User {resource_data['new_assignee_id']} not found")
            
            validated["resource_changes"] = parameters["resource_changes"]
        
        elif scenario_type == ScenarioType.SCOPE_CHANGE:
            if "scope_changes" not in parameters:
                raise ValueError("scope_changes parameter required for scope change scenario")
            
            validated["scope_changes"] = parameters["scope_changes"]
        
        elif scenario_type == ScenarioType.BUDGET_CHANGE:
            if "budget_adjustment" not in parameters:
                raise ValueError("budget_adjustment parameter required for budget change scenario")
            
            validated["budget_adjustment"] = {
                "current": 0,  # Would get from budget table
                "proposed": parameters["budget_adjustment"],
                "unit": "currency",
                "description": "Project budget adjustment"
            }
        
        return validated
    
    async def _get_scenario_data(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario data (simplified - would be from database)"""
        # In a real system, this would query a scenarios table
        # For now, return a mock scenario
        return {
            "scenario_id": scenario_id,
            "project_id": 1,
            "scenario_name": "Test Scenario",
            "scenario_type": "deadline_change",
            "parameters": {
                "new_deadline": {
                    "current": "2024-12-31",
                    "proposed": "2024-11-30",
                    "unit": "date",
                    "description": "Project completion deadline"
                }
            }
        }
    
    async def _get_user(self, user_id: int, db: AsyncSession) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def _simulate_deadline_change(
        self, 
        project: Project, 
        tasks: List[Task], 
        parameters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Simulate deadline change scenario"""
        new_deadline = datetime.fromisoformat(parameters["new_deadline"]["proposed"]).date()
        original_end_date = project.planned_end_date or project.end_date
        
        # Calculate current project duration
        original_duration = (original_end_date - project.start_date).days if project.start_date and original_end_date else 0
        new_duration = (new_deadline - project.start_date).days if project.start_date else 0
        duration_change = new_duration - original_duration
        
        # Calculate cost impact (simplified)
        original_cost = sum(task.estimated_hours or 0 for task in tasks) * 100  # $100/hour
        cost_multiplier = 1.0 + (abs(duration_change) / original_duration * 0.1) if original_duration > 0 else 1.0
        new_cost = original_cost * cost_multiplier
        cost_change = new_cost - original_cost
        
        # Identify affected tasks (tasks that need to be compressed)
        affected_tasks = [task.id for task in tasks if task.due_date and task.due_date > new_deadline]
        
        # Calculate risk level
        risk_level = self._calculate_deadline_risk(duration_change, len(affected_tasks))
        
        # Generate recommendations
        recommendations = self._generate_deadline_recommendations(duration_change, affected_tasks)
        
        # Calculate feasibility score
        feasibility_score = self._calculate_deadline_feasibility(duration_change, len(affected_tasks))
        
        return {
            "original_duration": original_duration,
            "new_duration": new_duration,
            "duration_change": duration_change,
            "original_cost": original_cost,
            "new_cost": new_cost,
            "cost_change": cost_change,
            "original_end_date": original_end_date,
            "new_end_date": new_deadline,
            "affected_tasks": affected_tasks,
            "new_critical_path": affected_tasks,  # Simplified
            "risk_level": risk_level,
            "risk_factors": [
                "Schedule compression required",
                "Resource availability constraints",
                "Quality impact from rushed work"
            ],
            "recommendations": recommendations,
            "feasibility_score": feasibility_score
        }
    
    async def _simulate_resource_change(
        self, 
        project: Project, 
        tasks: List[Task], 
        parameters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Simulate resource change scenario"""
        resource_changes = parameters["resource_changes"]
        
        # Calculate impacts
        affected_tasks = list(resource_changes.keys())
        original_duration = self._calculate_project_duration(tasks)
        new_duration = original_duration  # Simplified - would calculate based on new resources
        duration_change = 0
        
        original_cost = sum(task.estimated_hours or 0 for task in tasks) * 100
        new_cost = original_cost  # Simplified - would calculate based on new resource rates
        cost_change = 0
        
        risk_level = ImpactLevel.MEDIUM if len(affected_tasks) > 2 else ImpactLevel.LOW
        
        return {
            "original_duration": original_duration,
            "new_duration": new_duration,
            "duration_change": duration_change,
            "original_cost": original_cost,
            "new_cost": new_cost,
            "cost_change": cost_change,
            "original_end_date": project.planned_end_date or project.end_date,
            "new_end_date": project.planned_end_date or project.end_date,
            "affected_tasks": [int(task_id) for task_id in affected_tasks],
            "new_critical_path": [],
            "risk_level": risk_level,
            "risk_factors": [
                "Resource ramp-up time",
                "Knowledge transfer requirements"
            ],
            "recommendations": [
                "Ensure proper handover documentation",
                "Plan for resource training time"
            ],
            "feasibility_score": 0.8
        }
    
    async def _simulate_scope_change(
        self, 
        project: Project, 
        tasks: List[Task], 
        parameters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Simulate scope change scenario"""
        scope_changes = parameters["scope_changes"]
        
        # Calculate impacts
        affected_tasks = list(scope_changes.keys())
        original_duration = self._calculate_project_duration(tasks)
        new_duration = original_duration + len(scope_changes) * 5  # Add 5 days per scope change
        duration_change = new_duration - original_duration
        
        original_cost = sum(task.estimated_hours or 0 for task in tasks) * 100
        new_cost = original_cost + len(scope_changes) * 40 * 100  # Add 40 hours per scope change
        cost_change = new_cost - original_cost
        
        risk_level = ImpactLevel.HIGH if len(scope_changes) > 3 else ImpactLevel.MEDIUM
        
        return {
            "original_duration": original_duration,
            "new_duration": new_duration,
            "duration_change": duration_change,
            "original_cost": original_cost,
            "new_cost": new_cost,
            "cost_change": cost_change,
            "original_end_date": project.planned_end_date or project.end_date,
            "new_end_date": (project.planned_end_date or project.end_date) + timedelta(days=duration_change),
            "affected_tasks": [int(task_id) for task_id in affected_tasks],
            "new_critical_path": [],
            "risk_level": risk_level,
            "risk_factors": [
                "Scope creep impact",
                "Resource availability for new work",
                "Quality impact from additional work"
            ],
            "recommendations": [
                "Review scope change impact on timeline",
                "Ensure additional resources are available",
                "Update stakeholder expectations"
            ],
            "feasibility_score": 0.6
        }
    
    async def _simulate_budget_change(
        self, 
        project: Project, 
        tasks: List[Task], 
        parameters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Simulate budget change scenario"""
        budget_adjustment = parameters["budget_adjustment"]["proposed"]
        
        original_cost = sum(task.estimated_hours or 0 for task in tasks) * 100
        new_cost = original_cost + budget_adjustment
        cost_change = budget_adjustment
        
        original_duration = self._calculate_project_duration(tasks)
        new_duration = original_duration
        duration_change = 0
        
        risk_level = ImpactLevel.LOW if budget_adjustment > 0 else ImpactLevel.MEDIUM
        
        return {
            "original_duration": original_duration,
            "new_duration": new_duration,
            "duration_change": duration_change,
            "original_cost": original_cost,
            "new_cost": new_cost,
            "cost_change": cost_change,
            "original_end_date": project.planned_end_date or project.end_date,
            "new_end_date": project.planned_end_date or project.end_date,
            "affected_tasks": [],
            "new_critical_path": [],
            "risk_level": risk_level,
            "risk_factors": [
                "Budget constraint impact on quality" if budget_adjustment < 0 else "Increased budget utilization"
            ],
            "recommendations": [
                "Review cost optimization opportunities" if budget_adjustment < 0 else "Plan for additional scope or quality improvements"
            ],
            "feasibility_score": 0.9
        }
    
    async def _simulate_generic_scenario(
        self, 
        project: Project, 
        tasks: List[Task], 
        parameters: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Simulate generic scenario"""
        original_duration = self._calculate_project_duration(tasks)
        original_cost = sum(task.estimated_hours or 0 for task in tasks) * 100
        
        return {
            "original_duration": original_duration,
            "new_duration": original_duration,
            "duration_change": 0,
            "original_cost": original_cost,
            "new_cost": original_cost,
            "cost_change": 0,
            "original_end_date": project.planned_end_date or project.end_date,
            "new_end_date": project.planned_end_date or project.end_date,
            "affected_tasks": [],
            "new_critical_path": [],
            "risk_level": ImpactLevel.LOW,
            "risk_factors": [],
            "recommendations": ["No significant changes detected"],
            "feasibility_score": 1.0
        }
    
    def _calculate_project_duration(self, tasks: List[Task]) -> int:
        """Calculate project duration from tasks"""
        if not tasks:
            return 0
        
        start_dates = [task.start_date for task in tasks if task.start_date]
        end_dates = [task.due_date for task in tasks if task.due_date]
        
        if not start_dates or not end_dates:
            return 0
        
        earliest_start = min(start_dates)
        latest_end = max(end_dates)
        
        return (latest_end - earliest_start).days + 1
    
    def _calculate_deadline_risk(self, duration_change: int, affected_tasks: int) -> ImpactLevel:
        """Calculate risk level for deadline change"""
        if duration_change < -30 or affected_tasks > 5:
            return ImpactLevel.CRITICAL
        elif duration_change < -15 or affected_tasks > 3:
            return ImpactLevel.HIGH
        elif duration_change < -7 or affected_tasks > 1:
            return ImpactLevel.MEDIUM
        else:
            return ImpactLevel.LOW
    
    def _generate_deadline_recommendations(self, duration_change: int, affected_tasks: List[int]) -> List[str]:
        """Generate recommendations for deadline change"""
        recommendations = []
        
        if duration_change < -30:
            recommendations.append("Consider scope reduction to meet deadline")
            recommendations.append("Add additional resources to critical path tasks")
        elif duration_change < -15:
            recommendations.append("Implement schedule compression techniques")
            recommendations.append("Review task dependencies for optimization")
        elif duration_change < -7:
            recommendations.append("Monitor progress closely and adjust as needed")
        
        if len(affected_tasks) > 3:
            recommendations.append("Prioritize affected tasks based on critical path")
        
        return recommendations
    
    def _calculate_deadline_feasibility(self, duration_change: int, affected_tasks: int) -> float:
        """Calculate feasibility score for deadline change"""
        base_score = 1.0
        
        # Reduce score based on compression amount
        if duration_change < -30:
            base_score -= 0.4
        elif duration_change < -15:
            base_score -= 0.2
        elif duration_change < -7:
            base_score -= 0.1
        
        # Reduce score based on affected tasks
        if affected_tasks > 5:
            base_score -= 0.3
        elif affected_tasks > 3:
            base_score -= 0.2
        elif affected_tasks > 1:
            base_score -= 0.1
        
        return max(0.0, base_score)
    
    async def _generate_comparison_matrix(self, scenario_results: List[Dict]) -> Dict[str, Any]:
        """Generate comparison matrix for scenarios"""
        matrix = {
            "duration_comparison": [],
            "cost_comparison": [],
            "risk_comparison": [],
            "feasibility_comparison": []
        }
        
        for result in scenario_results:
            matrix["duration_comparison"].append({
                "scenario_name": result["scenario_name"],
                "duration_change": result["duration_impact"]["duration_change"],
                "new_duration": result["duration_impact"]["new_duration"]
            })
            
            matrix["cost_comparison"].append({
                "scenario_name": result["scenario_name"],
                "cost_change": result["cost_impact"]["cost_change"],
                "new_cost": result["cost_impact"]["new_cost"]
            })
            
            matrix["risk_comparison"].append({
                "scenario_name": result["scenario_name"],
                "risk_level": result["risk_assessment"]["risk_level"],
                "risk_factors_count": len(result["risk_assessment"]["risk_factors"])
            })
            
            matrix["feasibility_comparison"].append({
                "scenario_name": result["scenario_name"],
                "feasibility_score": result["feasibility_score"]
            })
        
        return matrix
    
    async def _find_best_scenario(self, scenario_results: List[Dict]) -> Dict[str, Any]:
        """Find the best scenario based on multiple criteria"""
        if not scenario_results:
            return {}
        
        # Score each scenario
        scored_scenarios = []
        for result in scenario_results:
            score = 0
            
            # Duration score (lower is better)
            duration_change = result["duration_impact"]["duration_change"]
            if duration_change <= 0:  # On time or ahead
                score += 30
            elif duration_change <= 7:  # Minor delay
                score += 20
            elif duration_change <= 15:  # Moderate delay
                score += 10
            
            # Cost score (lower is better)
            cost_change = result["cost_impact"]["cost_change"]
            if cost_change <= 0:  # On budget or under
                score += 25
            elif cost_change <= 1000:  # Minor overrun
                score += 15
            elif cost_change <= 5000:  # Moderate overrun
                score += 5
            
            # Risk score (lower is better)
            risk_level = result["risk_assessment"]["risk_level"]
            if risk_level == "low":
                score += 25
            elif risk_level == "medium":
                score += 15
            elif risk_level == "high":
                score += 5
            
            # Feasibility score
            score += result["feasibility_score"] * 20
            
            scored_scenarios.append({
                "scenario_name": result["scenario_name"],
                "score": score,
                "result": result
            })
        
        # Sort by score and return best
        scored_scenarios.sort(key=lambda x: x["score"], reverse=True)
        return scored_scenarios[0] if scored_scenarios else {}
    
    async def _get_scenario_project_id(self, scenario_id: str) -> int:
        """Get project ID for a scenario"""
        scenario_data = await self._get_scenario_data(scenario_id)
        return scenario_data["project_id"] if scenario_data else 1
    
    async def _apply_deadline_changes(self, project_id: int, result: Dict, db: AsyncSession):
        """Apply deadline changes to project"""
        # Update project deadline
        project = await self._get_project(project_id, db)
        if project:
            new_end_date = datetime.fromisoformat(result["duration_impact"]["new_end_date"]).date()
            project.planned_end_date = new_end_date
            await db.commit()
    
    async def _apply_resource_changes(self, project_id: int, result: Dict, db: AsyncSession):
        """Apply resource changes to tasks"""
        # This would update task assignments based on scenario parameters
        pass
    
    async def _apply_scope_changes(self, project_id: int, result: Dict, db: AsyncSession):
        """Apply scope changes to project"""
        # This would add/remove/modify tasks based on scenario parameters
        pass
    
    async def _apply_budget_changes(self, project_id: int, result: Dict, db: AsyncSession):
        """Apply budget changes to project"""
        # This would update project budget
        pass
    
    async def _log_scenario_application(self, scenario_id: str, result: Dict, db: AsyncSession):
        """Log scenario application for audit"""
        logger.info(f"Scenario {scenario_id} applied: {result['scenario_name']}")
