"""
API endpoints for AI Risk Mitigation functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.services.ai_risk_mitigation import (
    get_ai_risk_mitigation_service, 
    AIRiskMitigationService,
    RiskMitigationPlan,
    RiskMitigationAction,
    RiskLevel,
    MitigationStatus
)
# from app.schemas.common import BaseResponse  # Not needed for this endpoint

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze-risk", response_model=Dict[str, Any])
async def analyze_risk_and_generate_plan(
    risk_data: Dict[str, Any],
    risk_service: AIRiskMitigationService = Depends(get_ai_risk_mitigation_service)
):
    """
    Analyze a risk and generate AI-powered mitigation plan
    """
    try:
        # Extract risk data
        risk_title = risk_data.get("title", "Unknown Risk")
        risk_description = risk_data.get("description", "")
        probability = risk_data.get("probability", "medium")
        impact = risk_data.get("impact", "medium")
        project_context = risk_data.get("project_context", {})
        
        # Generate AI mitigation plan
        mitigation_plan = await risk_service.analyze_risk_and_generate_plan(
            risk_title=risk_title,
            risk_description=risk_description,
            probability=probability,
            impact=impact,
            project_context=project_context
        )
        
        # Convert to JSON-serializable format
        plan_data = {
            "risk_id": mitigation_plan.risk_id,
            "risk_title": mitigation_plan.risk_title,
            "risk_description": mitigation_plan.risk_description,
            "risk_level": mitigation_plan.risk_level.value,
            "probability": mitigation_plan.probability,
            "impact": mitigation_plan.impact,
            "mitigation_strategy": mitigation_plan.mitigation_strategy,
            "actions": [
                {
                    "id": action.id,
                    "title": action.title,
                    "description": action.description,
                    "priority": action.priority,
                    "estimated_effort": action.estimated_effort,
                    "owner": action.owner,
                    "due_date": action.due_date,
                    "status": action.status.value,
                    "dependencies": action.dependencies,
                    "success_criteria": action.success_criteria
                }
                for action in mitigation_plan.actions
            ],
            "timeline": mitigation_plan.timeline,
            "success_metrics": mitigation_plan.success_metrics,
            "monitoring_plan": mitigation_plan.monitoring_plan,
            "contingency_plan": mitigation_plan.contingency_plan,
            "generated_at": mitigation_plan.generated_at.isoformat(),
            "confidence_score": mitigation_plan.confidence_score
        }
        
        return {
            "success": True,
            "message": "AI risk mitigation plan generated successfully",
            "data": plan_data
        }
        
    except Exception as e:
        logger.error(f"Error generating risk mitigation plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate risk mitigation plan: {str(e)}")

@router.get("/risk-levels", response_model=Dict[str, Any])
async def get_risk_levels():
    """
    Get available risk levels
    """
    return {
        "success": True,
        "data": {
            "levels": [
                {"value": "low", "label": "Low", "color": "success"},
                {"value": "medium", "label": "Medium", "color": "warning"},
                {"value": "high", "label": "High", "color": "danger"},
                {"value": "critical", "label": "Critical", "color": "dark"}
            ]
        }
    }

@router.get("/mitigation-statuses", response_model=Dict[str, Any])
async def get_mitigation_statuses():
    """
    Get available mitigation action statuses
    """
    return {
        "success": True,
        "data": {
            "statuses": [
                {"value": "pending", "label": "Pending", "color": "secondary"},
                {"value": "in_progress", "label": "In Progress", "color": "primary"},
                {"value": "completed", "label": "Completed", "color": "success"},
                {"value": "failed", "label": "Failed", "color": "danger"}
            ]
        }
    }

@router.post("/update-action-status", response_model=Dict[str, Any])
async def update_action_status(
    action_data: Dict[str, Any],
    risk_service: AIRiskMitigationService = Depends(get_ai_risk_mitigation_service)
):
    """
    Update the status of a mitigation action
    """
    try:
        action_id = action_data.get("action_id")
        new_status = action_data.get("status")
        
        if not action_id or not new_status:
            raise HTTPException(status_code=400, detail="action_id and status are required")
        
        # Validate status
        valid_statuses = [status.value for status in MitigationStatus]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        # In a real implementation, this would update the database
        # For demo purposes, we'll just return success
        return {
            "success": True,
            "message": f"Action {action_id} status updated to {new_status}",
            "data": {
                "action_id": action_id,
                "status": new_status,
                "updated_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating action status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update action status: {str(e)}")

@router.get("/demo-risks", response_model=Dict[str, Any])
async def get_demo_risks():
    """
    Get demo risk data for testing
    """
    return {
        "success": True,
        "data": {
            "risks": [
                {
                    "id": "risk_1",
                    "title": "Key developer leaves",
                    "description": "Critical team member may leave during project execution",
                    "probability": "medium",
                    "impact": "high",
                    "current_mitigation": "Cross-training, documentation",
                    "status": "active"
                },
                {
                    "id": "risk_2", 
                    "title": "Technology stack changes",
                    "description": "Required technology may change or become unavailable",
                    "probability": "low",
                    "impact": "medium",
                    "current_mitigation": "Flexible architecture",
                    "status": "mitigated"
                },
                {
                    "id": "risk_3",
                    "title": "Scope creep",
                    "description": "Project scope may expand beyond original requirements",
                    "probability": "medium",
                    "impact": "medium",
                    "current_mitigation": "Change control process",
                    "status": "active"
                },
                {
                    "id": "risk_4",
                    "title": "Budget overrun",
                    "description": "Project costs may exceed allocated budget",
                    "probability": "medium",
                    "impact": "high",
                    "current_mitigation": "Regular budget reviews",
                    "status": "active"
                },
                {
                    "id": "risk_5",
                    "title": "Timeline delays",
                    "description": "Project may not meet critical deadlines",
                    "probability": "high",
                    "impact": "high",
                    "current_mitigation": "Buffer time, parallel work",
                    "status": "active"
                }
            ]
        }
    }

@router.get("/mitigation-templates", response_model=Dict[str, Any])
async def get_mitigation_templates():
    """
    Get common risk mitigation templates
    """
    return {
        "success": True,
        "data": {
            "templates": [
                {
                    "risk_type": "Resource Risk",
                    "common_actions": [
                        "Cross-train team members",
                        "Document critical processes",
                        "Identify backup resources",
                        "Implement knowledge sharing"
                    ]
                },
                {
                    "risk_type": "Technology Risk",
                    "common_actions": [
                        "Conduct technology assessment",
                        "Create migration plan",
                        "Implement flexible architecture",
                        "Establish vendor relationships"
                    ]
                },
                {
                    "risk_type": "Scope Risk",
                    "common_actions": [
                        "Implement change control process",
                        "Define scope boundaries",
                        "Regular scope reviews",
                        "Stakeholder alignment"
                    ]
                },
                {
                    "risk_type": "Schedule Risk",
                    "common_actions": [
                        "Add buffer time",
                        "Identify critical path",
                        "Parallel task execution",
                        "Regular progress monitoring"
                    ]
                },
                {
                    "risk_type": "Budget Risk",
                    "common_actions": [
                        "Regular budget reviews",
                        "Cost tracking system",
                        "Contingency planning",
                        "Stakeholder communication"
                    ]
                }
            ]
        }
    }
