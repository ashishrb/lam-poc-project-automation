"""
AI Risk Mitigation Service
Provides intelligent risk analysis and mitigation plan generation
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MitigationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class RiskMitigationAction:
    """Individual mitigation action"""
    id: str
    title: str
    description: str
    priority: str
    estimated_effort: str
    owner: str
    due_date: str
    status: MitigationStatus
    dependencies: List[str]
    success_criteria: str

@dataclass
class RiskMitigationPlan:
    """Complete AI-generated risk mitigation plan"""
    risk_id: str
    risk_title: str
    risk_description: str
    risk_level: RiskLevel
    probability: str
    impact: str
    mitigation_strategy: str
    actions: List[RiskMitigationAction]
    timeline: str
    success_metrics: List[str]
    monitoring_plan: str
    contingency_plan: str
    generated_at: datetime
    confidence_score: float

class AIRiskMitigationService:
    """AI-powered risk analysis and mitigation planning service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_risk_and_generate_plan(
        self, 
        risk_title: str,
        risk_description: str,
        probability: str,
        impact: str,
        project_context: Dict[str, Any] = None
    ) -> RiskMitigationPlan:
        """
        Analyze a risk and generate a comprehensive mitigation plan using AI
        """
        try:
            # Determine risk level based on probability and impact
            risk_level = self._calculate_risk_level(probability, impact)
            
            # Generate AI-powered mitigation strategy
            mitigation_strategy = await self._generate_mitigation_strategy(
                risk_title, risk_description, probability, impact, project_context
            )
            
            # Generate specific mitigation actions
            actions = await self._generate_mitigation_actions(
                risk_title, risk_description, mitigation_strategy, project_context
            )
            
            # Generate timeline and success metrics
            timeline = self._generate_timeline(actions, risk_level)
            success_metrics = self._generate_success_metrics(risk_title, mitigation_strategy)
            monitoring_plan = self._generate_monitoring_plan(risk_title, actions)
            contingency_plan = self._generate_contingency_plan(risk_title, risk_level)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(risk_level, len(actions))
            
            return RiskMitigationPlan(
                risk_id=f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                risk_title=risk_title,
                risk_description=risk_description,
                risk_level=risk_level,
                probability=probability,
                impact=impact,
                mitigation_strategy=mitigation_strategy,
                actions=actions,
                timeline=timeline,
                success_metrics=success_metrics,
                monitoring_plan=monitoring_plan,
                contingency_plan=contingency_plan,
                generated_at=datetime.now(),
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Error generating risk mitigation plan: {e}")
            # Return a basic plan as fallback
            return self._create_fallback_plan(risk_title, risk_description, probability, impact)
    
    def _calculate_risk_level(self, probability: str, impact: str) -> RiskLevel:
        """Calculate risk level based on probability and impact"""
        prob_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        impact_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        
        prob_score = prob_scores.get(probability.lower(), 2)
        impact_score = impact_scores.get(impact.lower(), 2)
        
        risk_score = prob_score * impact_score
        
        if risk_score >= 12:
            return RiskLevel.CRITICAL
        elif risk_score >= 8:
            return RiskLevel.HIGH
        elif risk_score >= 4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def _generate_mitigation_strategy(
        self, 
        risk_title: str, 
        risk_description: str, 
        probability: str, 
        impact: str,
        project_context: Dict[str, Any] = None
    ) -> str:
        """Generate AI-powered mitigation strategy"""
        
        # AI prompt for mitigation strategy
        prompt = f"""
        As an AI project management expert, analyze this risk and provide a comprehensive mitigation strategy:
        
        Risk: {risk_title}
        Description: {risk_description}
        Probability: {probability}
        Impact: {impact}
        
        Project Context: {project_context or "General project"}
        
        Provide a detailed mitigation strategy that includes:
        1. Root cause analysis
        2. Prevention measures
        3. Detection mechanisms
        4. Response procedures
        5. Recovery plans
        
        Focus on practical, actionable strategies that can be implemented immediately.
        """
        
        # For demo purposes, return a structured strategy based on risk type
        return self._get_demo_mitigation_strategy(risk_title, probability, impact)
    
    async def _generate_mitigation_actions(
        self, 
        risk_title: str, 
        risk_description: str, 
        mitigation_strategy: str,
        project_context: Dict[str, Any] = None
    ) -> List[RiskMitigationAction]:
        """Generate specific mitigation actions"""
        
        # Generate actions based on risk type and strategy
        actions = []
        
        if "developer" in risk_title.lower() or "team" in risk_title.lower():
            actions.extend([
                RiskMitigationAction(
                    id="action_1",
                    title="Cross-train team members",
                    description="Ensure at least 2 team members can handle critical tasks",
                    priority="High",
                    estimated_effort="2-3 weeks",
                    owner="Team Lead",
                    due_date=(datetime.now() + timedelta(weeks=3)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="All critical tasks have backup resources"
                ),
                RiskMitigationAction(
                    id="action_2",
                    title="Document critical processes",
                    description="Create comprehensive documentation for all critical workflows",
                    priority="High",
                    estimated_effort="1-2 weeks",
                    owner="Technical Lead",
                    due_date=(datetime.now() + timedelta(weeks=2)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="100% of critical processes documented"
                ),
                RiskMitigationAction(
                    id="action_3",
                    title="Implement knowledge sharing sessions",
                    description="Weekly knowledge sharing sessions to spread expertise",
                    priority="Medium",
                    estimated_effort="Ongoing",
                    owner="Project Manager",
                    due_date=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=["action_2"],
                    success_criteria="Weekly sessions established and attended"
                )
            ])
        
        elif "technology" in risk_title.lower() or "stack" in risk_title.lower():
            actions.extend([
                RiskMitigationAction(
                    id="action_1",
                    title="Conduct technology assessment",
                    description="Evaluate current technology stack and identify alternatives",
                    priority="High",
                    estimated_effort="1 week",
                    owner="Architecture Team",
                    due_date=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="Technology assessment report completed"
                ),
                RiskMitigationAction(
                    id="action_2",
                    title="Create migration plan",
                    description="Develop detailed plan for technology migration if needed",
                    priority="High",
                    estimated_effort="2-3 weeks",
                    owner="Technical Lead",
                    due_date=(datetime.now() + timedelta(weeks=4)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=["action_1"],
                    success_criteria="Migration plan approved by stakeholders"
                ),
                RiskMitigationAction(
                    id="action_3",
                    title="Implement flexible architecture",
                    description="Design system to be technology-agnostic where possible",
                    priority="Medium",
                    estimated_effort="Ongoing",
                    owner="Development Team",
                    due_date=(datetime.now() + timedelta(weeks=6)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=["action_2"],
                    success_criteria="Architecture flexibility implemented"
                )
            ])
        
        elif "scope" in risk_title.lower() or "creep" in risk_title.lower():
            actions.extend([
                RiskMitigationAction(
                    id="action_1",
                    title="Implement change control process",
                    description="Establish formal process for scope change requests",
                    priority="High",
                    estimated_effort="1 week",
                    owner="Project Manager",
                    due_date=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="Change control process documented and communicated"
                ),
                RiskMitigationAction(
                    id="action_2",
                    title="Define scope boundaries",
                    description="Clearly document what is in and out of scope",
                    priority="High",
                    estimated_effort="3-5 days",
                    owner="Product Owner",
                    due_date=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="Scope document approved by all stakeholders"
                ),
                RiskMitigationAction(
                    id="action_3",
                    title="Regular scope reviews",
                    description="Weekly scope review meetings with stakeholders",
                    priority="Medium",
                    estimated_effort="Ongoing",
                    owner="Project Manager",
                    due_date=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=["action_1", "action_2"],
                    success_criteria="Weekly scope reviews established"
                )
            ])
        
        else:
            # Generic risk mitigation actions
            actions.extend([
                RiskMitigationAction(
                    id="action_1",
                    title="Risk assessment and monitoring",
                    description="Implement continuous monitoring of risk indicators",
                    priority="High",
                    estimated_effort="Ongoing",
                    owner="Project Manager",
                    due_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="Monitoring system in place"
                ),
                RiskMitigationAction(
                    id="action_2",
                    title="Stakeholder communication",
                    description="Regular communication with stakeholders about risk status",
                    priority="Medium",
                    estimated_effort="Ongoing",
                    owner="Project Manager",
                    due_date=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="Communication plan established"
                )
            ])
        
        return actions
    
    def _generate_timeline(self, actions: List[RiskMitigationAction], risk_level: RiskLevel) -> str:
        """Generate timeline for mitigation plan"""
        if risk_level == RiskLevel.CRITICAL:
            return "Immediate action required - All critical actions within 1 week, full plan within 2 weeks"
        elif risk_level == RiskLevel.HIGH:
            return "Urgent action required - Priority actions within 1 week, full plan within 3 weeks"
        elif risk_level == RiskLevel.MEDIUM:
            return "Moderate timeline - Priority actions within 2 weeks, full plan within 4 weeks"
        else:
            return "Standard timeline - Actions within 3-4 weeks"
    
    def _generate_success_metrics(self, risk_title: str, mitigation_strategy: str) -> List[str]:
        """Generate success metrics for the mitigation plan"""
        return [
            "Risk probability reduced by 50%",
            "All mitigation actions completed on time",
            "Zero incidents related to this risk",
            "Stakeholder confidence in risk management increased",
            "Team preparedness for similar risks improved"
        ]
    
    def _generate_monitoring_plan(self, risk_title: str, actions: List[RiskMitigationAction]) -> str:
        """Generate monitoring plan for the risk"""
        return f"""
        Weekly Risk Monitoring Plan for: {risk_title}
        
        1. Progress Review: Check completion status of all mitigation actions
        2. Risk Indicators: Monitor key metrics that indicate risk probability
        3. Stakeholder Updates: Regular communication with project stakeholders
        4. Contingency Check: Verify contingency plans are ready if needed
        5. Lessons Learned: Document insights for future risk management
        """
    
    def _generate_contingency_plan(self, risk_title: str, risk_level: RiskLevel) -> str:
        """Generate contingency plan if mitigation fails"""
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return f"""
            Emergency Contingency Plan for: {risk_title}
            
            1. Immediate Response: Activate emergency response team within 2 hours
            2. Communication: Notify all stakeholders within 4 hours
            3. Resource Allocation: Reallocate resources to address the risk
            4. Timeline Adjustment: Revise project timeline if necessary
            5. Recovery Plan: Implement recovery procedures to minimize impact
            """
        else:
            return f"""
            Standard Contingency Plan for: {risk_title}
            
            1. Assessment: Evaluate impact within 24 hours
            2. Communication: Update stakeholders within 48 hours
            3. Adjustment: Make necessary project adjustments
            4. Recovery: Implement recovery procedures
            """
    
    def _calculate_confidence_score(self, risk_level: RiskLevel, action_count: int) -> float:
        """Calculate confidence score for the mitigation plan"""
        base_scores = {
            RiskLevel.LOW: 0.9,
            RiskLevel.MEDIUM: 0.8,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.6
        }
        
        base_score = base_scores.get(risk_level, 0.7)
        action_bonus = min(action_count * 0.05, 0.2)  # Up to 20% bonus for more actions
        
        return min(base_score + action_bonus, 1.0)
    
    def _get_demo_mitigation_strategy(self, risk_title: str, probability: str, impact: str) -> str:
        """Get demo mitigation strategy based on risk type"""
        if "developer" in risk_title.lower():
            return """
            Comprehensive Team Risk Mitigation Strategy:
            
            1. Root Cause Analysis: Identify knowledge silos and single points of failure
            2. Prevention: Implement cross-training programs and knowledge sharing
            3. Detection: Regular team health checks and skill assessments
            4. Response: Immediate knowledge transfer and backup resource activation
            5. Recovery: Rapid team restructuring and external contractor support
            """
        elif "technology" in risk_title.lower():
            return """
            Technology Risk Mitigation Strategy:
            
            1. Root Cause Analysis: Evaluate technology dependencies and alternatives
            2. Prevention: Flexible architecture design and technology abstraction layers
            3. Detection: Continuous technology monitoring and vendor communication
            4. Response: Rapid technology assessment and migration planning
            5. Recovery: Technology rollback procedures and alternative solutions
            """
        elif "scope" in risk_title.lower():
            return """
            Scope Creep Mitigation Strategy:
            
            1. Root Cause Analysis: Identify scope definition gaps and stakeholder misalignment
            2. Prevention: Clear scope documentation and change control processes
            3. Detection: Regular scope reviews and stakeholder check-ins
            4. Response: Formal change request evaluation and impact assessment
            5. Recovery: Scope renegotiation and timeline adjustment procedures
            """
        else:
            return """
            General Risk Mitigation Strategy:
            
            1. Root Cause Analysis: Identify underlying causes and contributing factors
            2. Prevention: Implement proactive measures to reduce risk probability
            3. Detection: Establish monitoring systems and early warning indicators
            4. Response: Develop rapid response procedures and escalation paths
            5. Recovery: Create recovery plans to minimize impact and restore normal operations
            """
    
    def _create_fallback_plan(
        self, 
        risk_title: str, 
        risk_description: str, 
        probability: str, 
        impact: str
    ) -> RiskMitigationPlan:
        """Create a basic fallback plan if AI generation fails"""
        return RiskMitigationPlan(
            risk_id=f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            risk_title=risk_title,
            risk_description=risk_description,
            risk_level=RiskLevel.MEDIUM,
            probability=probability,
            impact=impact,
            mitigation_strategy="Standard risk mitigation approach with monitoring and response procedures",
            actions=[
                RiskMitigationAction(
                    id="fallback_1",
                    title="Risk monitoring",
                    description="Implement basic risk monitoring",
                    priority="High",
                    estimated_effort="1 week",
                    owner="Project Manager",
                    due_date=(datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                    status=MitigationStatus.PENDING,
                    dependencies=[],
                    success_criteria="Monitoring system in place"
                )
            ],
            timeline="Standard 2-4 week implementation timeline",
            success_metrics=["Risk monitored", "Response plan ready"],
            monitoring_plan="Weekly risk assessment and reporting",
            contingency_plan="Standard contingency procedures",
            generated_at=datetime.now(),
            confidence_score=0.6
        )

# Global instance
_ai_risk_mitigation_service = None

def get_ai_risk_mitigation_service() -> AIRiskMitigationService:
    """Get the global AI risk mitigation service instance"""
    global _ai_risk_mitigation_service
    if _ai_risk_mitigation_service is None:
        _ai_risk_mitigation_service = AIRiskMitigationService()
    return _ai_risk_mitigation_service
