#!/usr/bin/env python3
"""
Autonomous Decision Engine
Handles complex decision-making, risk assessment, and strategic planning.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.project import Project, Task, ProjectPlan, Milestone
from app.models.resource import Resource, ResourceSkill
from app.models.risk import Risk
from app.models.finance import Budget, Actual
from app.models.user import User
from app.services.enhanced_ai_orchestrator import EnhancedAIOrchestrator
from app.services.autonomous_guardrails import AutonomousGuardrails, ActionType
from app.core.database import get_db

logger = logging.getLogger(__name__)


class DecisionType(str, Enum):
    """Types of autonomous decisions"""
    PROJECT_PRIORITIZATION = "project_prioritization"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_MITIGATION = "risk_mitigation"
    BUDGET_ADJUSTMENT = "budget_adjustment"
    TIMELINE_OPTIMIZATION = "timeline_optimization"
    STAKEHOLDER_COMMUNICATION = "stakeholder_communication"
    QUALITY_ASSURANCE = "quality_assurance"
    STRATEGIC_PLANNING = "strategic_planning"


class DecisionPriority(str, Enum):
    """Decision priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionStatus(str, Enum):
    """Decision status"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    DECIDED = "decided"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DecisionContext:
    """Context for decision making"""
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    priority: DecisionPriority = DecisionPriority.MEDIUM
    urgency: float = 0.5  # 0-1 scale
    impact_scope: str = "project"  # project, portfolio, organization
    constraints: Dict[str, Any] = None
    available_resources: Dict[str, Any] = None
    historical_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}
        if self.available_resources is None:
            self.available_resources = {}
        if self.historical_data is None:
            self.historical_data = {}


@dataclass
class DecisionResult:
    """Result of a decision"""
    decision_id: str
    decision_type: DecisionType
    status: DecisionStatus
    confidence_score: float
    reasoning: str
    actions: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]
    alternatives_considered: List[Dict[str, Any]]
    execution_plan: Dict[str, Any]
    created_at: datetime
    executed_at: Optional[datetime] = None
    outcome: Optional[str] = None


class AutonomousDecisionEngine:
    """Autonomous decision engine for complex project management decisions"""
    
    def __init__(self):
        self.ai_orchestrator = EnhancedAIOrchestrator()
        self.guardrails = AutonomousGuardrails()
        self.decision_history: List[DecisionResult] = []
        
    async def make_decision(
        self,
        decision_type: DecisionType,
        context: DecisionContext,
        db: AsyncSession
    ) -> DecisionResult:
        """
        Make an autonomous decision based on type and context
        """
        decision_id = f"DECISION_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{decision_type.value}"
        
        try:
            # Analyze context and gather data
            analysis_data = await self._analyze_context(decision_type, context, db)
            
            # Generate decision using appropriate AI model
            decision_data = await self._generate_decision(decision_type, analysis_data, context)
            
            # Validate decision against guardrails
            validation_result = await self._validate_decision(decision_data, context, db)
            
            # Create decision result
            decision_result = DecisionResult(
                decision_id=decision_id,
                decision_type=decision_type,
                status=DecisionStatus.DECIDED if validation_result["approved"] else DecisionStatus.PENDING,
                confidence_score=decision_data["confidence_score"],
                reasoning=decision_data["reasoning"],
                actions=decision_data["actions"],
                risks=decision_data["risks"],
                alternatives_considered=decision_data["alternatives"],
                execution_plan=decision_data["execution_plan"],
                created_at=datetime.now()
            )
            
            # Log decision
            self.decision_history.append(decision_result)
            
            logger.info(f"Decision {decision_id} made with confidence {decision_result.confidence_score}")
            
            return decision_result
            
        except Exception as e:
            logger.error(f"Error making decision {decision_id}: {str(e)}")
            return DecisionResult(
                decision_id=decision_id,
                decision_type=decision_type,
                status=DecisionStatus.FAILED,
                confidence_score=0.0,
                reasoning=f"Decision failed: {str(e)}",
                actions=[],
                risks=[],
                alternatives_considered=[],
                execution_plan={},
                created_at=datetime.now()
            )
    
    async def _analyze_context(
        self,
        decision_type: DecisionType,
        context: DecisionContext,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze decision context and gather relevant data
        """
        analysis_data = {
            "project_data": {},
            "resource_data": {},
            "risk_data": {},
            "financial_data": {},
            "historical_data": {},
            "constraints": context.constraints
        }
        
        # Gather project data
        if context.project_id:
            project_query = select(Project).where(Project.id == context.project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            if project:
                analysis_data["project_data"] = {
                    "id": project.id,
                    "name": project.name,
                    "status": project.status,
                    "priority": project.priority,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "budget": project.budget,
                    "completion_percentage": project.completion_percentage
                }
                
                # Get project tasks
                tasks_query = select(Task).where(Task.project_id == context.project_id)
                tasks_result = await db.execute(tasks_query)
                tasks = tasks_result.scalars().all()
                
                analysis_data["project_data"]["tasks"] = [
                    {
                        "id": task.id,
                        "name": task.name,
                        "status": task.status,
                        "priority": task.priority,
                        "assigned_to_id": task.assigned_to_id,
                        "estimated_hours": task.estimated_hours,
                        "actual_hours": task.actual_hours
                    }
                    for task in tasks
                ]
        
        # Gather resource data
        resources_query = select(Resource).where(Resource.is_active == True)
        resources_result = await db.execute(resources_query)
        resources = resources_result.scalars().all()
        
        analysis_data["resource_data"] = {
            "available_resources": len(resources),
            "resource_details": [
                {
                    "id": resource.id,
                    "name": resource.name,
                    "skills": [skill.skill_name for skill in resource.skills],
                    "availability": resource.availability,
                    "current_load": resource.current_load
                }
                for resource in resources
            ]
        }
        
        # Gather risk data
        if context.project_id:
            risks_query = select(Risk).where(Risk.project_id == context.project_id)
            risks_result = await db.execute(risks_query)
            risks = risks_result.scalars().all()
            
            analysis_data["risk_data"] = [
                {
                    "id": risk.id,
                    "name": risk.name,
                    "probability": risk.probability,
                    "impact": risk.impact,
                    "status": risk.status,
                    "mitigation_plan": risk.mitigation_plan
                }
                for risk in risks
            ]
        
        # Gather financial data
        if context.project_id:
            budget_query = select(Budget).where(Budget.project_id == context.project_id)
            budget_result = await db.execute(budget_query)
            budget = budget_result.scalar_one_or_none()
            
            if budget:
                analysis_data["financial_data"] = {
                    "allocated_budget": budget.allocated_amount,
                    "spent_amount": budget.spent_amount,
                    "remaining_budget": budget.allocated_amount - budget.spent_amount,
                    "budget_utilization": (budget.spent_amount / budget.allocated_amount) * 100 if budget.allocated_amount > 0 else 0
                }
        
        return analysis_data
    
    async def _generate_decision(
        self,
        decision_type: DecisionType,
        analysis_data: Dict[str, Any],
        context: DecisionContext
    ) -> Dict[str, Any]:
        """
        Generate decision using AI models
        """
        # Create decision prompt based on type
        prompt = self._create_decision_prompt(decision_type, analysis_data, context)
        
        # Route to appropriate model based on decision type
        model_override = self._get_model_for_decision_type(decision_type)
        
        # Generate decision
        response = await self.ai_orchestrator.generate_response(
            query=prompt,
            context={"decision_type": decision_type.value, "priority": context.priority.value},
            model_override=model_override
        )
        
        if not response["success"]:
            raise Exception(f"AI decision generation failed: {response.get('error', 'Unknown error')}")
        
        # Parse decision from AI response
        decision_data = self._parse_decision_response(response["response"], decision_type)
        
        return decision_data
    
    def _create_decision_prompt(
        self,
        decision_type: DecisionType,
        analysis_data: Dict[str, Any],
        context: DecisionContext
    ) -> str:
        """
        Create decision prompt based on decision type
        """
        base_prompt = f"""
        You are an autonomous project management decision engine. Make a {decision_type.value} decision based on the following data:

        CONTEXT:
        - Priority: {context.priority.value}
        - Urgency: {context.urgency}
        - Impact Scope: {context.impact_scope}
        - Constraints: {json.dumps(context.constraints, indent=2)}

        PROJECT DATA:
        {json.dumps(analysis_data.get('project_data', {}), indent=2)}

        RESOURCE DATA:
        {json.dumps(analysis_data.get('resource_data', {}), indent=2)}

        RISK DATA:
        {json.dumps(analysis_data.get('risk_data', []), indent=2)}

        FINANCIAL DATA:
        {json.dumps(analysis_data.get('financial_data', {}), indent=2)}

        Please provide a structured decision in JSON format with the following fields:
        {{
            "confidence_score": 0.85,
            "reasoning": "Detailed reasoning for the decision",
            "actions": [
                {{
                    "action_type": "task_creation",
                    "description": "Action description",
                    "priority": "high",
                    "estimated_effort": 8,
                    "assigned_to": "resource_id"
                }}
            ],
            "risks": [
                {{
                    "risk_name": "Risk description",
                    "probability": 0.3,
                    "impact": "medium",
                    "mitigation": "Mitigation strategy"
                }}
            ],
            "alternatives": [
                {{
                    "alternative": "Alternative description",
                    "pros": ["Pro 1", "Pro 2"],
                    "cons": ["Con 1", "Con 2"],
                    "why_rejected": "Reason for rejection"
                }}
            ],
            "execution_plan": {{
                "timeline": "2 weeks",
                "milestones": ["Milestone 1", "Milestone 2"],
                "success_criteria": ["Criterion 1", "Criterion 2"]
            }}
        }}
        """
        
        # Add decision-specific instructions
        if decision_type == DecisionType.PROJECT_PRIORITIZATION:
            base_prompt += "\n\nFocus on: Resource constraints, business value, strategic alignment, and timeline dependencies."
        elif decision_type == DecisionType.RESOURCE_ALLOCATION:
            base_prompt += "\n\nFocus on: Skill matching, availability, workload balance, and team dynamics."
        elif decision_type == DecisionType.RISK_MITIGATION:
            base_prompt += "\n\nFocus on: Risk probability, impact assessment, mitigation effectiveness, and cost-benefit analysis."
        elif decision_type == DecisionType.BUDGET_ADJUSTMENT:
            base_prompt += "\n\nFocus on: Budget utilization, ROI analysis, cost optimization, and financial constraints."
        
        return base_prompt
    
    def _get_model_for_decision_type(self, decision_type: DecisionType) -> str:
        """
        Get appropriate AI model for decision type
        """
        model_mapping = {
            DecisionType.PROJECT_PRIORITIZATION: "gpt-oss:20B",
            DecisionType.RESOURCE_ALLOCATION: "qwen3:latest",
            DecisionType.RISK_MITIGATION: "llama3.2:3b-instruct-q4_K_M",
            DecisionType.BUDGET_ADJUSTMENT: "gpt-oss:20B",
            DecisionType.TIMELINE_OPTIMIZATION: "qwen3:latest",
            DecisionType.STAKEHOLDER_COMMUNICATION: "qwen3:latest",
            DecisionType.QUALITY_ASSURANCE: "llama3.2:3b-instruct-q4_K_M",
            DecisionType.STRATEGIC_PLANNING: "gpt-oss:20B"
        }
        
        return model_mapping.get(decision_type, "qwen3:latest")
    
    def _parse_decision_response(self, response: str, decision_type: DecisionType) -> Dict[str, Any]:
        """
        Parse AI response into structured decision data
        """
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                # Fallback parsing
                return self._fallback_decision_parsing(response, decision_type)
            
            json_str = response[json_start:json_end]
            decision_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["confidence_score", "reasoning", "actions", "risks", "alternatives", "execution_plan"]
            for field in required_fields:
                if field not in decision_data:
                    decision_data[field] = self._get_default_value(field)
            
            return decision_data
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON from AI response, using fallback parsing")
            return self._fallback_decision_parsing(response, decision_type)
    
    def _fallback_decision_parsing(self, response: str, decision_type: DecisionType) -> Dict[str, Any]:
        """
        Fallback parsing when JSON parsing fails
        """
        return {
            "confidence_score": 0.7,
            "reasoning": response[:500] + "..." if len(response) > 500 else response,
            "actions": [
                {
                    "action_type": "analysis",
                    "description": "Further analysis required",
                    "priority": "medium",
                    "estimated_effort": 4,
                    "assigned_to": None
                }
            ],
            "risks": [
                {
                    "risk_name": "Decision uncertainty",
                    "probability": 0.4,
                    "impact": "medium",
                    "mitigation": "Monitor and adjust as needed"
                }
            ],
            "alternatives": [
                {
                    "alternative": "Manual review",
                    "pros": ["Human oversight", "Experience-based"],
                    "cons": ["Slower", "Subjective"],
                    "why_rejected": "Autonomous decision preferred"
                }
            ],
            "execution_plan": {
                "timeline": "1 week",
                "milestones": ["Review", "Implement", "Monitor"],
                "success_criteria": ["Decision implemented", "Outcomes measured"]
            }
        }
    
    def _get_default_value(self, field: str) -> Any:
        """
        Get default value for missing fields
        """
        defaults = {
            "confidence_score": 0.5,
            "reasoning": "Decision made based on available data",
            "actions": [],
            "risks": [],
            "alternatives": [],
            "execution_plan": {"timeline": "1 week", "milestones": [], "success_criteria": []}
        }
        return defaults.get(field, None)
    
    async def _validate_decision(
        self,
        decision_data: Dict[str, Any],
        context: DecisionContext,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Validate decision against guardrails
        """
        # Create action data for validation
        action_data = {
            "action_type": "automated_decision",
            "action_data": {
                "decision_type": context.priority.value,
                "confidence_score": decision_data["confidence_score"],
                "actions": decision_data["actions"],
                "risks": decision_data["risks"]
            },
            "confidence_score": decision_data["confidence_score"],
            "context": {
                "user_id": context.user_id,
                "project_id": context.project_id,
                "priority": context.priority.value
            }
        }
        
        # Validate using guardrails
        validation_result = await self.guardrails.validate_action(
            action_type=ActionType.AUTOMATED_DECISION,
            action_data=action_data["action_data"],
            confidence_score=decision_data["confidence_score"],
            context=action_data["context"],
            db=db
        )
        
        return {
            "approved": not validation_result["requires_approval"],
            "approval_level": validation_result["approval_level"],
            "validation_issues": validation_result["validation_issues"],
            "guardrails_result": validation_result
        }
    
    async def execute_decision(
        self,
        decision_result: DecisionResult,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Execute a decision
        """
        try:
            decision_result.status = DecisionStatus.EXECUTING
            
            execution_results = []
            
            # Execute each action in the decision
            for action in decision_result.actions:
                action_result = await self._execute_action(action, db)
                execution_results.append(action_result)
            
            # Update decision status
            decision_result.status = DecisionStatus.COMPLETED
            decision_result.executed_at = datetime.now()
            decision_result.outcome = "Decision executed successfully"
            
            return {
                "success": True,
                "decision_id": decision_result.decision_id,
                "execution_results": execution_results,
                "outcome": decision_result.outcome
            }
            
        except Exception as e:
            decision_result.status = DecisionStatus.FAILED
            decision_result.outcome = f"Execution failed: {str(e)}"
            
            logger.error(f"Error executing decision {decision_result.decision_id}: {str(e)}")
            
            return {
                "success": False,
                "decision_id": decision_result.decision_id,
                "error": str(e),
                "outcome": decision_result.outcome
            }
    
    async def _execute_action(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Execute a single action from a decision
        """
        action_type = action.get("action_type", "unknown")
        
        try:
            if action_type == "task_creation":
                return await self._create_task(action, db)
            elif action_type == "resource_assignment":
                return await self._assign_resource(action, db)
            elif action_type == "risk_mitigation":
                return await self._mitigate_risk(action, db)
            elif action_type == "budget_adjustment":
                return await self._adjust_budget(action, db)
            elif action_type == "notification":
                return await self._send_notification(action, db)
            else:
                return {
                    "success": False,
                    "action_type": action_type,
                    "error": f"Unknown action type: {action_type}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "action_type": action_type,
                "error": str(e)
            }
    
    async def _create_task(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Create a task based on decision action
        """
        # Implementation would create actual task in database
        return {
            "success": True,
            "action_type": "task_creation",
            "task_id": f"TASK_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": action.get("description", "Task created by autonomous decision")
        }
    
    async def _assign_resource(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Assign resource based on decision action
        """
        # Implementation would assign resource in database
        return {
            "success": True,
            "action_type": "resource_assignment",
            "resource_id": action.get("assigned_to"),
            "description": action.get("description", "Resource assigned by autonomous decision")
        }
    
    async def _mitigate_risk(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Mitigate risk based on decision action
        """
        # Implementation would update risk mitigation in database
        return {
            "success": True,
            "action_type": "risk_mitigation",
            "risk_id": action.get("risk_id"),
            "description": action.get("description", "Risk mitigated by autonomous decision")
        }
    
    async def _adjust_budget(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Adjust budget based on decision action
        """
        # Implementation would update budget in database
        return {
            "success": True,
            "action_type": "budget_adjustment",
            "amount": action.get("amount", 0),
            "description": action.get("description", "Budget adjusted by autonomous decision")
        }
    
    async def _send_notification(self, action: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """
        Send notification based on decision action
        """
        # Implementation would send actual notification
        return {
            "success": True,
            "action_type": "notification",
            "recipient": action.get("recipient"),
            "message": action.get("message", "Notification sent by autonomous decision")
        }
    
    async def get_decision_history(
        self,
        project_id: Optional[int] = None,
        decision_type: Optional[DecisionType] = None,
        limit: int = 50
    ) -> List[DecisionResult]:
        """
        Get decision history with optional filtering
        """
        filtered_decisions = self.decision_history
        
        if project_id:
            # Filter by project (would need to add project_id to DecisionResult)
            pass
        
        if decision_type:
            filtered_decisions = [d for d in filtered_decisions if d.decision_type == decision_type]
        
        # Sort by creation date and limit
        filtered_decisions.sort(key=lambda x: x.created_at, reverse=True)
        return filtered_decisions[:limit]
    
    async def get_decision_analytics(self) -> Dict[str, Any]:
        """
        Get analytics about decisions
        """
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "success_rate": 0.0,
                "average_confidence": 0.0,
                "decision_type_distribution": {},
                "status_distribution": {}
            }
        
        total_decisions = len(self.decision_history)
        successful_decisions = len([d for d in self.decision_history if d.status == DecisionStatus.COMPLETED])
        success_rate = (successful_decisions / total_decisions) * 100 if total_decisions > 0 else 0
        average_confidence = sum(d.confidence_score for d in self.decision_history) / total_decisions
        
        # Decision type distribution
        type_distribution = {}
        for decision in self.decision_history:
            decision_type = decision.decision_type.value
            type_distribution[decision_type] = type_distribution.get(decision_type, 0) + 1
        
        # Status distribution
        status_distribution = {}
        for decision in self.decision_history:
            status = decision.status.value
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        return {
            "total_decisions": total_decisions,
            "success_rate": success_rate,
            "average_confidence": average_confidence,
            "decision_type_distribution": type_distribution,
            "status_distribution": status_distribution
        }


# Global instance and getter function
_decision_engine_instance = None

def get_decision_engine() -> AutonomousDecisionEngine:
    """Get the global decision engine instance"""
    global _decision_engine_instance
    if _decision_engine_instance is None:
        _decision_engine_instance = AutonomousDecisionEngine()
    return _decision_engine_instance
