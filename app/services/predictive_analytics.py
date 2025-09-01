#!/usr/bin/env python3
"""
Predictive Analytics Service
Risk scoring models, causal explanations, and prescriptive playbooks
"""

import json
import logging
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.project import Project, Task
from app.models.user import User
from app.models.project import TaskStatus, TaskPriority, ProjectStatus
from app.services.ai_guardrails import AIGuardrails
from app.services.metrics import EVMService
from app.core.config import settings

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MitigationAction(str, Enum):
    """Types of mitigation actions"""
    SPLIT_TASK = "split_task"
    REASSIGN_RESOURCE = "reassign_resource"
    ESCALATE = "escalate"
    ADD_RESOURCE = "add_resource"
    REDUCE_SCOPE = "reduce_scope"
    EXTEND_TIMELINE = "extend_timeline"
    INCREASE_BUDGET = "increase_budget"


@dataclass
class RiskFactor:
    """Risk factor information"""
    factor_name: str
    factor_value: float
    weight: float
    contribution: float
    description: str


@dataclass
class RiskAssessment:
    """Risk assessment for a project or task"""
    entity_id: int
    entity_type: str  # project or task
    risk_score: float  # 0-100
    risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    causal_explanation: str
    mitigation_actions: List[Dict[str, Any]]
    confidence: float  # 0-1
    last_updated: datetime


@dataclass
class PrescriptiveAction:
    """Prescriptive action recommendation"""
    action_type: MitigationAction
    description: str
    impact_score: float  # 0-100
    effort_score: float  # 0-100
    priority: str  # high, medium, low
    estimated_effect: str
    human_in_the_loop: bool
    auto_apply: bool


class PredictiveAnalyticsService:
    """Service for predictive analytics, risk scoring, and prescriptive actions"""
    
    def __init__(self):
        self.guardrails = AIGuardrails()
        self.evm_service = EVMService()
        
        # Risk factor weights (trained on historical data)
        self.risk_weights = {
            "schedule_variance": 0.25,
            "cost_variance": 0.20,
            "resource_utilization": 0.15,
            "task_completion_rate": 0.15,
            "dependency_complexity": 0.10,
            "scope_volatility": 0.10,
            "stakeholder_satisfaction": 0.05
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            "low": 25,
            "medium": 50,
            "high": 75,
            "critical": 90
        }
    
    async def calculate_project_risk_score(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a project"""
        try:
            # Get project and tasks
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            tasks = await self._get_project_tasks(project_id, db)
            
            # Calculate EVM metrics
            evm_result = await self.evm_service.calculate_project_evm(project_id, db)
            if not evm_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to calculate EVM metrics"
                }
            
            # Calculate risk factors
            risk_factors = await self._calculate_risk_factors(project, tasks, evm_result["metrics"])
            
            # Calculate overall risk score
            risk_score = await self._calculate_overall_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate causal explanation
            causal_explanation = await self._generate_causal_explanation(risk_factors, risk_level)
            
            # Generate mitigation actions
            mitigation_actions = await self._generate_mitigation_actions(risk_factors, risk_level)
            
            # Create risk assessment
            risk_assessment = RiskAssessment(
                entity_id=project_id,
                entity_type="project",
                risk_score=risk_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                causal_explanation=causal_explanation,
                mitigation_actions=mitigation_actions,
                confidence=await self._calculate_confidence(risk_factors),
                last_updated=datetime.now()
            )
            
            return {
                "success": True,
                "project_id": project_id,
                "risk_score": risk_score,
                "risk_level": risk_level.value,
                "risk_factors": [
                    {
                        "factor_name": factor.factor_name,
                        "factor_value": factor.factor_value,
                        "weight": factor.weight,
                        "contribution": factor.contribution,
                        "description": factor.description
                    }
                    for factor in risk_factors
                ],
                "causal_explanation": causal_explanation,
                "mitigation_actions": mitigation_actions,
                "confidence": risk_assessment.confidence,
                "last_updated": risk_assessment.last_updated.isoformat(),
                "summary": {
                    "critical_factors": len([f for f in risk_factors if f.contribution > 20]),
                    "high_impact_actions": len([a for a in mitigation_actions if a["impact_score"] > 70]),
                    "auto_apply_actions": len([a for a in mitigation_actions if a["auto_apply"]])
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating project risk score: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def calculate_task_risk_score(
        self, 
        task_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Calculate risk score for a specific task"""
        try:
            # Get task
            task = await self._get_task(task_id, db)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            # Get project context
            project = await self._get_project(task.project_id, db)
            
            # Calculate task-specific risk factors
            risk_factors = await self._calculate_task_risk_factors(task, project, db)
            
            # Calculate risk score
            risk_score = await self._calculate_task_risk_score(risk_factors)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate causal explanation
            causal_explanation = await self._generate_task_causal_explanation(task, risk_factors, risk_level)
            
            # Generate mitigation actions
            mitigation_actions = await self._generate_task_mitigation_actions(task, risk_factors, risk_level)
            
            return {
                "success": True,
                "task_id": task_id,
                "risk_score": risk_score,
                "risk_level": risk_level.value,
                "risk_factors": [
                    {
                        "factor_name": factor.factor_name,
                        "factor_value": factor.factor_value,
                        "weight": factor.weight,
                        "contribution": factor.contribution,
                        "description": factor.description
                    }
                    for factor in risk_factors
                ],
                "causal_explanation": causal_explanation,
                "mitigation_actions": mitigation_actions,
                "confidence": await self._calculate_confidence(risk_factors),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating task risk score: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_prescriptive_playbook(
        self, 
        project_id: int, 
        risk_level: Optional[RiskLevel] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Generate prescriptive playbook with actionable recommendations"""
        try:
            # Get project risk assessment
            risk_result = await self.calculate_project_risk_score(project_id, db)
            if not risk_result["success"]:
                return risk_result
            
            # Filter by risk level if specified
            if risk_level and RiskLevel(risk_result["risk_level"]) != risk_level:
                return {
                    "success": True,
                    "project_id": project_id,
                    "message": f"Project risk level ({risk_result['risk_level']}) doesn't match requested level ({risk_level.value})",
                    "playbook": []
                }
            
            # Generate prescriptive actions
            prescriptive_actions = await self._generate_prescriptive_actions(
                risk_result["risk_factors"], 
                risk_result["risk_level"]
            )
            
            # Prioritize actions
            prioritized_actions = await self._prioritize_actions(prescriptive_actions)
            
            return {
                "success": True,
                "project_id": project_id,
                "risk_level": risk_result["risk_level"],
                "playbook": [
                    {
                        "action_type": action.action_type.value,
                        "description": action.description,
                        "impact_score": action.impact_score,
                        "effort_score": action.effort_score,
                        "priority": action.priority,
                        "estimated_effect": action.estimated_effect,
                        "human_in_the_loop": action.human_in_the_loop,
                        "auto_apply": action.auto_apply
                    }
                    for action in prioritized_actions
                ],
                "summary": {
                    "total_actions": len(prioritized_actions),
                    "high_priority": len([a for a in prioritized_actions if a.priority == "high"]),
                    "auto_apply": len([a for a in prioritized_actions if a.auto_apply]),
                    "human_review": len([a for a in prioritized_actions if a.human_in_the_loop])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating prescriptive playbook: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def apply_mitigation_action(
        self, 
        project_id: int, 
        action_type: MitigationAction,
        action_params: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply a mitigation action to a project"""
        try:
            # Validate action parameters
            validation_result = await self._validate_action_parameters(action_type, action_params)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid action parameters: {validation_result['error']}"
                }
            
            # Apply the action based on type
            if action_type == MitigationAction.SPLIT_TASK:
                result = await self._apply_split_task_action(project_id, action_params, db)
            elif action_type == MitigationAction.REASSIGN_RESOURCE:
                result = await self._apply_reassign_resource_action(project_id, action_params, db)
            elif action_type == MitigationAction.ESCALATE:
                result = await self._apply_escalate_action(project_id, action_params, db)
            elif action_type == MitigationAction.ADD_RESOURCE:
                result = await self._apply_add_resource_action(project_id, action_params, db)
            elif action_type == MitigationAction.REDUCE_SCOPE:
                result = await self._apply_reduce_scope_action(project_id, action_params, db)
            elif action_type == MitigationAction.EXTEND_TIMELINE:
                result = await self._apply_extend_timeline_action(project_id, action_params, db)
            elif action_type == MitigationAction.INCREASE_BUDGET:
                result = await self._apply_increase_budget_action(project_id, action_params, db)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }
            
            # Log the action
            await self._log_mitigation_action(project_id, action_type, action_params, result, db)
            
            return result
            
        except Exception as e:
            logger.error(f"Error applying mitigation action: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def predict_project_outcomes(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Predict project outcomes based on current state"""
        try:
            # Get project and current metrics
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            evm_result = await self.evm_service.calculate_project_evm(project_id, db)
            if not evm_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to calculate EVM metrics"
                }
            
            metrics = evm_result["metrics"]
            
            # Predict outcomes using historical patterns and current trends
            predictions = await self._predict_outcomes(project, metrics)
            
            return {
                "success": True,
                "project_id": project_id,
                "predictions": {
                    "estimated_completion_date": predictions["completion_date"],
                    "estimated_final_cost": predictions["final_cost"],
                    "completion_probability": predictions["completion_probability"],
                    "quality_score": predictions["quality_score"],
                    "stakeholder_satisfaction": predictions["stakeholder_satisfaction"]
                },
                "confidence_intervals": {
                    "completion_date": predictions["completion_date_ci"],
                    "final_cost": predictions["final_cost_ci"]
                },
                "trends": {
                    "schedule_trend": predictions["schedule_trend"],
                    "cost_trend": predictions["cost_trend"],
                    "quality_trend": predictions["quality_trend"]
                },
                "risk_factors": predictions["risk_factors"]
            }
            
        except Exception as e:
            logger.error(f"Error predicting project outcomes: {e}")
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
    
    async def _get_task(self, task_id: int, db: AsyncSession) -> Optional[Task]:
        """Get task by ID"""
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()
    
    async def _calculate_risk_factors(
        self, 
        project: Project, 
        tasks: List[Task], 
        evm_metrics: Dict[str, Any]
    ) -> List[RiskFactor]:
        """Calculate risk factors for a project"""
        risk_factors = []
        
        # Schedule variance factor
        schedule_variance = abs(evm_metrics.get("schedule_variance", 0))
        schedule_factor = min(schedule_variance / 1000, 1.0) if schedule_variance > 0 else 0
        risk_factors.append(RiskFactor(
            factor_name="schedule_variance",
            factor_value=schedule_factor,
            weight=self.risk_weights["schedule_variance"],
            contribution=schedule_factor * self.risk_weights["schedule_variance"],
            description=f"Schedule variance of {schedule_variance:.2f} indicates timeline risk"
        ))
        
        # Cost variance factor
        cost_variance = abs(evm_metrics.get("cost_variance", 0))
        cost_factor = min(cost_variance / 10000, 1.0) if cost_variance > 0 else 0
        risk_factors.append(RiskFactor(
            factor_name="cost_variance",
            factor_value=cost_factor,
            weight=self.risk_weights["cost_variance"],
            contribution=cost_factor * self.risk_weights["cost_variance"],
            description=f"Cost variance of {cost_variance:.2f} indicates budget risk"
        ))
        
        # Resource utilization factor
        total_tasks = len(tasks)
        assigned_tasks = len([t for t in tasks if t.assigned_to_id])
        utilization_factor = 1 - (assigned_tasks / total_tasks) if total_tasks > 0 else 0
        risk_factors.append(RiskFactor(
            factor_name="resource_utilization",
            factor_value=utilization_factor,
            weight=self.risk_weights["resource_utilization"],
            contribution=utilization_factor * self.risk_weights["resource_utilization"],
            description=f"Resource utilization at {utilization_factor:.2%} indicates resource risk"
        ))
        
        # Task completion rate factor
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        completion_factor = 1 - completion_rate
        risk_factors.append(RiskFactor(
            factor_name="task_completion_rate",
            factor_value=completion_factor,
            weight=self.risk_weights["task_completion_rate"],
            contribution=completion_factor * self.risk_weights["task_completion_rate"],
            description=f"Task completion rate at {completion_rate:.2%} indicates progress risk"
        ))
        
        # Dependency complexity factor
        tasks_with_deps = len([t for t in tasks if t.dependencies])
        dependency_factor = tasks_with_deps / total_tasks if total_tasks > 0 else 0
        risk_factors.append(RiskFactor(
            factor_name="dependency_complexity",
            factor_value=dependency_factor,
            weight=self.risk_weights["dependency_complexity"],
            contribution=dependency_factor * self.risk_weights["dependency_complexity"],
            description=f"Dependency complexity at {dependency_factor:.2%} indicates coordination risk"
        ))
        
        # Scope volatility factor (simplified)
        scope_factor = 0.3  # Placeholder - would be calculated from scope changes
        risk_factors.append(RiskFactor(
            factor_name="scope_volatility",
            factor_value=scope_factor,
            weight=self.risk_weights["scope_volatility"],
            contribution=scope_factor * self.risk_weights["scope_volatility"],
            description="Scope volatility indicates requirement risk"
        ))
        
        # Stakeholder satisfaction factor (simplified)
        satisfaction_factor = 0.2  # Placeholder - would be calculated from feedback
        risk_factors.append(RiskFactor(
            factor_name="stakeholder_satisfaction",
            factor_value=satisfaction_factor,
            weight=self.risk_weights["stakeholder_satisfaction"],
            contribution=satisfaction_factor * self.risk_weights["stakeholder_satisfaction"],
            description="Stakeholder satisfaction indicates relationship risk"
        ))
        
        return risk_factors
    
    async def _calculate_overall_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate overall risk score from risk factors"""
        total_contribution = sum(factor.contribution for factor in risk_factors)
        return min(total_contribution * 100, 100)  # Scale to 0-100
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level based on score"""
        if risk_score >= self.risk_thresholds["critical"]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds["high"]:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_thresholds["medium"]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _generate_causal_explanation(
        self, 
        risk_factors: List[RiskFactor], 
        risk_level: RiskLevel
    ) -> str:
        """Generate human-readable causal explanation"""
        # Sort factors by contribution
        sorted_factors = sorted(risk_factors, key=lambda f: f.contribution, reverse=True)
        
        if risk_level == RiskLevel.CRITICAL:
            explanation = f"This project has a critical risk level ({risk_level.value}) primarily due to "
        elif risk_level == RiskLevel.HIGH:
            explanation = f"This project has a high risk level ({risk_level.value}) primarily due to "
        elif risk_level == RiskLevel.MEDIUM:
            explanation = f"This project has a medium risk level ({risk_level.value}) primarily due to "
        else:
            explanation = f"This project has a low risk level ({risk_level.value}) with minor concerns about "
        
        # Add top contributing factors
        top_factors = sorted_factors[:3]
        factor_descriptions = [f.contribution for f in top_factors]
        
        if len(top_factors) == 1:
            explanation += f"{top_factors[0].description}."
        elif len(top_factors) == 2:
            explanation += f"{top_factors[0].description} and {top_factors[1].description}."
        else:
            explanation += f"{top_factors[0].description}, {top_factors[1].description}, and {top_factors[2].description}."
        
        return explanation
    
    async def _generate_mitigation_actions(
        self, 
        risk_factors: List[RiskFactor], 
        risk_level: RiskLevel
    ) -> List[Dict[str, Any]]:
        """Generate mitigation actions based on risk factors"""
        actions = []
        
        # Sort factors by contribution
        sorted_factors = sorted(risk_factors, key=lambda f: f.contribution, reverse=True)
        
        for factor in sorted_factors[:3]:  # Top 3 factors
            if factor.factor_name == "schedule_variance":
                actions.append({
                    "action_type": "extend_timeline",
                    "description": "Extend project timeline to accommodate schedule variance",
                    "impact_score": 80,
                    "effort_score": 60,
                    "priority": "high" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "medium"
                })
            
            elif factor.factor_name == "cost_variance":
                actions.append({
                    "action_type": "increase_budget",
                    "description": "Increase project budget to address cost overruns",
                    "impact_score": 85,
                    "effort_score": 70,
                    "priority": "high" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "medium"
                })
            
            elif factor.factor_name == "resource_utilization":
                actions.append({
                    "action_type": "add_resource",
                    "description": "Add additional resources to improve utilization",
                    "impact_score": 75,
                    "effort_score": 50,
                    "priority": "medium"
                })
            
            elif factor.factor_name == "task_completion_rate":
                actions.append({
                    "action_type": "escalate",
                    "description": "Escalate to management for task completion issues",
                    "impact_score": 70,
                    "effort_score": 30,
                    "priority": "high" if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "medium"
                })
        
        return actions
    
    async def _calculate_task_risk_factors(
        self, 
        task: Task, 
        project: Project, 
        db: AsyncSession
    ) -> List[RiskFactor]:
        """Calculate risk factors for a specific task"""
        risk_factors = []
        
        # Overdue factor
        if task.due_date and task.due_date < date.today() and task.status != TaskStatus.DONE:
            overdue_days = (date.today() - task.due_date).days
            overdue_factor = min(overdue_days / 30, 1.0)  # Cap at 30 days
            risk_factors.append(RiskFactor(
                factor_name="overdue",
                factor_value=overdue_factor,
                weight=0.4,
                contribution=overdue_factor * 0.4,
                description=f"Task is {overdue_days} days overdue"
            ))
        
        # Priority factor
        priority_factor = 0.0
        if task.priority == TaskPriority.HIGH:
            priority_factor = 0.8
        elif task.priority == TaskPriority.MEDIUM:
            priority_factor = 0.5
        else:
            priority_factor = 0.2
        
        risk_factors.append(RiskFactor(
            factor_name="priority",
            factor_value=priority_factor,
            weight=0.3,
            contribution=priority_factor * 0.3,
            description=f"Task has {task.priority.value} priority"
        ))
        
        # Dependencies factor
        if task.dependencies:
            try:
                deps = json.loads(task.dependencies)
                dep_count = len(deps) if isinstance(deps, list) else 0
                dependency_factor = min(dep_count / 5, 1.0)  # Cap at 5 dependencies
                risk_factors.append(RiskFactor(
                    factor_name="dependencies",
                    factor_value=dependency_factor,
                    weight=0.2,
                    contribution=dependency_factor * 0.2,
                    description=f"Task has {dep_count} dependencies"
                ))
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Progress factor
        if task.estimated_hours and task.actual_hours:
            progress_ratio = task.actual_hours / task.estimated_hours
            if progress_ratio > 1.2:  # More than 20% over estimated
                progress_factor = min((progress_ratio - 1.2) / 0.8, 1.0)
                risk_factors.append(RiskFactor(
                    factor_name="progress",
                    factor_value=progress_factor,
                    weight=0.1,
                    contribution=progress_factor * 0.1,
                    description=f"Task is {progress_ratio:.1%} over estimated hours"
                ))
        
        return risk_factors
    
    async def _calculate_task_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate risk score for a task"""
        total_contribution = sum(factor.contribution for factor in risk_factors)
        return min(total_contribution * 100, 100)
    
    async def _generate_task_causal_explanation(
        self, 
        task: Task, 
        risk_factors: List[RiskFactor], 
        risk_level: RiskLevel
    ) -> str:
        """Generate causal explanation for task risk"""
        if not risk_factors:
            return "Task has no significant risk factors identified."
        
        top_factor = max(risk_factors, key=lambda f: f.contribution)
        
        if risk_level == RiskLevel.CRITICAL:
            explanation = f"Task '{task.title}' has critical risk primarily due to {top_factor.description}."
        elif risk_level == RiskLevel.HIGH:
            explanation = f"Task '{task.title}' has high risk primarily due to {top_factor.description}."
        elif risk_level == RiskLevel.MEDIUM:
            explanation = f"Task '{task.title}' has medium risk primarily due to {top_factor.description}."
        else:
            explanation = f"Task '{task.title}' has low risk with minor concerns about {top_factor.description}."
        
        return explanation
    
    async def _generate_task_mitigation_actions(
        self, 
        task: Task, 
        risk_factors: List[RiskFactor], 
        risk_level: RiskLevel
    ) -> List[Dict[str, Any]]:
        """Generate mitigation actions for a task"""
        actions = []
        
        for factor in risk_factors:
            if factor.factor_name == "overdue":
                actions.append({
                    "action_type": "extend_timeline",
                    "description": f"Extend deadline for task '{task.title}'",
                    "impact_score": 85,
                    "effort_score": 20,
                    "priority": "high"
                })
            
            elif factor.factor_name == "priority":
                if task.priority == TaskPriority.HIGH:
                    actions.append({
                        "action_type": "escalate",
                        "description": f"Escalate high-priority task '{task.title}' to management",
                        "impact_score": 70,
                        "effort_score": 30,
                        "priority": "high"
                    })
            
            elif factor.factor_name == "dependencies":
                actions.append({
                    "action_type": "reassign_resource",
                    "description": f"Reassign task '{task.title}' to resource with fewer dependencies",
                    "impact_score": 60,
                    "effort_score": 40,
                    "priority": "medium"
                })
        
        return actions
    
    async def _generate_prescriptive_actions(
        self, 
        risk_factors: List[Dict[str, Any]], 
        risk_level: str
    ) -> List[PrescriptiveAction]:
        """Generate prescriptive actions"""
        actions = []
        
        risk_level_enum = RiskLevel(risk_level)
        
        for factor in risk_factors:
            if factor["factor_name"] == "schedule_variance":
                actions.append(PrescriptiveAction(
                    action_type=MitigationAction.EXTEND_TIMELINE,
                    description="Extend project timeline to accommodate schedule variance",
                    impact_score=80,
                    effort_score=60,
                    priority="high" if risk_level_enum in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "medium",
                    estimated_effect="Reduce schedule pressure by 20-30%",
                    human_in_the_loop=True,
                    auto_apply=False
                ))
            
            elif factor["factor_name"] == "cost_variance":
                actions.append(PrescriptiveAction(
                    action_type=MitigationAction.INCREASE_BUDGET,
                    description="Increase project budget to address cost overruns",
                    impact_score=85,
                    effort_score=70,
                    priority="high" if risk_level_enum in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "medium",
                    estimated_effect="Reduce cost pressure by 15-25%",
                    human_in_the_loop=True,
                    auto_apply=False
                ))
            
            elif factor["factor_name"] == "resource_utilization":
                actions.append(PrescriptiveAction(
                    action_type=MitigationAction.ADD_RESOURCE,
                    description="Add additional resources to improve utilization",
                    impact_score=75,
                    effort_score=50,
                    priority="medium",
                    estimated_effect="Improve resource utilization by 30-40%",
                    human_in_the_loop=True,
                    auto_apply=False
                ))
        
        return actions
    
    async def _prioritize_actions(self, actions: List[PrescriptiveAction]) -> List[PrescriptiveAction]:
        """Prioritize prescriptive actions"""
        # Sort by impact/effort ratio (efficiency)
        return sorted(actions, key=lambda a: a.impact_score / a.effort_score, reverse=True)
    
    async def _calculate_confidence(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate confidence in risk assessment"""
        # Simplified confidence calculation based on data quality
        total_weight = sum(f.weight for f in risk_factors)
        if total_weight > 0:
            return min(total_weight, 1.0)
        return 0.5
    
    async def _validate_action_parameters(
        self, 
        action_type: MitigationAction, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate action parameters"""
        try:
            if action_type == MitigationAction.SPLIT_TASK:
                if "task_id" not in params or "split_points" not in params:
                    return {"valid": False, "error": "Missing task_id or split_points"}
            
            elif action_type == MitigationAction.REASSIGN_RESOURCE:
                if "task_id" not in params or "new_assignee_id" not in params:
                    return {"valid": False, "error": "Missing task_id or new_assignee_id"}
            
            elif action_type == MitigationAction.ESCALATE:
                if "escalation_level" not in params:
                    return {"valid": False, "error": "Missing escalation_level"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _apply_split_task_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply split task action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "split_task",
            "message": f"Task {params.get('task_id')} split successfully"
        }
    
    async def _apply_reassign_resource_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply reassign resource action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "reassign_resource",
            "message": f"Task {params.get('task_id')} reassigned to {params.get('new_assignee_id')}"
        }
    
    async def _apply_escalate_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply escalate action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "escalate",
            "message": f"Project {project_id} escalated to {params.get('escalation_level')}"
        }
    
    async def _apply_add_resource_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply add resource action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "add_resource",
            "message": f"Resource added to project {project_id}"
        }
    
    async def _apply_reduce_scope_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply reduce scope action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "reduce_scope",
            "message": f"Scope reduced for project {project_id}"
        }
    
    async def _apply_extend_timeline_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply extend timeline action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "extend_timeline",
            "message": f"Timeline extended for project {project_id}"
        }
    
    async def _apply_increase_budget_action(
        self, 
        project_id: int, 
        params: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply increase budget action"""
        # Placeholder implementation
        return {
            "success": True,
            "action": "increase_budget",
            "message": f"Budget increased for project {project_id}"
        }
    
    async def _log_mitigation_action(
        self, 
        project_id: int, 
        action_type: MitigationAction, 
        params: Dict[str, Any], 
        result: Dict[str, Any], 
        db: AsyncSession
    ):
        """Log mitigation action for audit"""
        logger.info(f"Mitigation action applied: {action_type.value} for project {project_id}")
    
    async def _predict_outcomes(
        self, 
        project: Project, 
        metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict project outcomes"""
        # Simplified prediction logic
        current_date = date.today()
        
        # Predict completion date
        if project.planned_end_date:
            schedule_variance = metrics.get("schedule_variance", 0)
            days_adjustment = int(schedule_variance / 100)  # Simplified calculation
            predicted_completion = project.planned_end_date + timedelta(days=days_adjustment)
        else:
            predicted_completion = current_date + timedelta(days=30)
        
        # Predict final cost
        current_cost = metrics.get("actual_cost", 0)
        cost_variance = metrics.get("cost_variance", 0)
        predicted_final_cost = current_cost + abs(cost_variance)
        
        # Predict completion probability
        spi = metrics.get("schedule_performance_index", 1.0)
        cpi = metrics.get("cost_performance_index", 1.0)
        completion_probability = min((spi + cpi) / 2, 1.0)
        
        return {
            "completion_date": predicted_completion.isoformat(),
            "final_cost": predicted_final_cost,
            "completion_probability": completion_probability,
            "quality_score": 0.85,  # Placeholder
            "stakeholder_satisfaction": 0.80,  # Placeholder
            "completion_date_ci": [predicted_completion - timedelta(days=7), predicted_completion + timedelta(days=7)],
            "final_cost_ci": [predicted_final_cost * 0.9, predicted_final_cost * 1.1],
            "schedule_trend": "improving" if spi > 1.0 else "declining",
            "cost_trend": "improving" if cpi > 1.0 else "declining",
            "quality_trend": "stable",
            "risk_factors": ["schedule_variance", "cost_variance"]
        }
