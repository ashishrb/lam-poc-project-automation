#!/usr/bin/env python3
"""
Autonomous System API Endpoints
Provides endpoints for autonomous guardrails, state management, and AI orchestration.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.autonomous_guardrails import AutonomousGuardrails, ActionType, GuardrailConfig
from app.services.autonomous_state_manager import AutonomousStateManager, WorkflowType, StateManagerConfig
from app.services.enhanced_ai_orchestrator import EnhancedAIOrchestrator
from app.models.project import Project, Task, ProjectPlan
from app.models.user import User
from app.models.audit import AuditLog

router = APIRouter()

# Initialize services (lazy initialization)
guardrails = None
state_manager = None
ai_orchestrator = None

def get_guardrails():
    global guardrails
    if guardrails is None:
        guardrails = AutonomousGuardrails()
    return guardrails

def get_state_manager():
    global state_manager
    if state_manager is None:
        state_manager = AutonomousStateManager()
    return state_manager

def get_ai_orchestrator():
    global ai_orchestrator
    if ai_orchestrator is None:
        ai_orchestrator = EnhancedAIOrchestrator()
    return ai_orchestrator

logger = logging.getLogger(__name__)


@router.post("/validate-action")
async def validate_autonomous_action(
    action_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Validate an autonomous action against security rules and business logic
    """
    try:
        action_type = ActionType(action_data.get("action_type", "automated_decision"))
        confidence_score = action_data.get("confidence_score", 0.8)
        context = action_data.get("context", {})
        
        validation_result = await get_guardrails().validate_action(
            action_type=action_type,
            action_data=action_data.get("action_data", {}),
            confidence_score=confidence_score,
            context=context,
            db=db
        )
        
        return JSONResponse(content={
            "success": True,
            "validation_result": validation_result
        })
        
    except Exception as e:
        logger.error(f"Error validating autonomous action: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Validation failed: {str(e)}"
            }
        )


@router.post("/start-workflow")
async def start_autonomous_workflow(
    workflow_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new autonomous workflow
    """
    try:
        workflow_type = WorkflowType(workflow_data.get("workflow_type", "decision_making"))
        project_id = workflow_data.get("project_id")
        user_id = workflow_data.get("user_id")
        context = workflow_data.get("context", {})
        
        workflow_id = await get_state_manager().start_workflow(
            workflow_type=workflow_type,
            project_id=project_id,
            user_id=user_id,
            context=context
        )
        
        return JSONResponse(content={
            "success": True,
            "workflow_id": workflow_id,
            "workflow_type": workflow_type.value,
            "status": "initiated"
        })
        
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to start workflow: {str(e)}"
            }
        )


@router.get("/workflow-status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow
    """
    try:
        workflow_state = await get_state_manager().get_workflow_state(workflow_id)
        
        if not workflow_state:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return JSONResponse(content={
            "success": True,
            "workflow": {
                "workflow_id": workflow_state.workflow_id,
                "workflow_type": workflow_state.workflow_type.value,
                "status": workflow_state.status.value,
                "project_id": workflow_state.project_id,
                "user_id": workflow_state.user_id,
                "initiated_at": workflow_state.initiated_at.isoformat(),
                "started_at": workflow_state.started_at.isoformat() if workflow_state.started_at else None,
                "completed_at": workflow_state.completed_at.isoformat() if workflow_state.completed_at else None,
                "steps_completed": workflow_state.steps_completed,
                "decisions_made": workflow_state.decisions_made,
                "actions_taken": workflow_state.actions_taken,
                "error_message": workflow_state.error_message,
                "result_data": workflow_state.result_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get workflow status: {str(e)}"
            }
        )


@router.post("/update-workflow/{workflow_id}")
async def update_workflow_state(
    workflow_id: str,
    update_data: Dict[str, Any]
):
    """
    Update the state of a workflow
    """
    try:
        from app.services.autonomous_state_manager import WorkflowStatus
        
        status = WorkflowStatus(update_data.get("status", "running"))
        step_name = update_data.get("step_name")
        decision = update_data.get("decision")
        action = update_data.get("action")
        error_message = update_data.get("error_message")
        result_data = update_data.get("result_data")
        
        success = await get_state_manager().update_workflow_state(
            workflow_id=workflow_id,
            status=status,
            step_name=step_name,
            decision=decision,
            action=action,
            error_message=error_message,
            result_data=result_data
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Workflow {workflow_id} updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating workflow: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to update workflow: {str(e)}"
            }
        )


@router.post("/rollback-workflow/{workflow_id}")
async def rollback_workflow(
    workflow_id: str,
    rollback_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Rollback a workflow to a previous state
    """
    try:
        rollback_to_step = rollback_data.get("rollback_to_step")
        
        rollback_result = await get_state_manager().rollback_workflow(
            workflow_id=workflow_id,
            rollback_to_step=rollback_to_step,
            db=db
        )
        
        return JSONResponse(content={
            "success": rollback_result["success"],
            "result": rollback_result
        })
        
    except Exception as e:
        logger.error(f"Error rolling back workflow: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to rollback workflow: {str(e)}"
            }
        )


@router.get("/workflow-history")
async def get_workflow_history(project_id: Optional[int] = None):
    """
    Get workflow history, optionally filtered by project
    """
    try:
        workflows = await get_state_manager().get_workflow_history(project_id)
        
        workflow_data = []
        for workflow in workflows:
            workflow_data.append({
                "workflow_id": workflow.workflow_id,
                "workflow_type": workflow.workflow_type.value,
                "status": workflow.status.value,
                "project_id": workflow.project_id,
                "user_id": workflow.user_id,
                "initiated_at": workflow.initiated_at.isoformat(),
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
                "steps_completed": len(workflow.steps_completed),
                "decisions_made": len(workflow.decisions_made),
                "actions_taken": len(workflow.actions_taken),
                "error_message": workflow.error_message
            })
        
        return JSONResponse(content={
            "success": True,
            "workflows": workflow_data,
            "total_workflows": len(workflow_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting workflow history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get workflow history: {str(e)}"
            }
        )


@router.get("/workflow-statistics")
async def get_workflow_statistics():
    """
    Get statistics about workflows
    """
    try:
        stats = await get_state_manager().get_workflow_statistics()
        
        return JSONResponse(content={
            "success": True,
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting workflow statistics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get workflow statistics: {str(e)}"
            }
        )


@router.post("/ai-analysis")
async def perform_ai_analysis(
    analysis_data: Dict[str, Any]
):
    """
    Perform AI analysis using appropriate model
    """
    try:
        query = analysis_data.get("query", "")
        context = analysis_data.get("context", {})
        model_override = analysis_data.get("model_override")
        
        response = await get_ai_orchestrator().generate_response(
            query=query,
            context=context,
            model_override=model_override
        )
        
        return JSONResponse(content={
            "success": response["success"],
            "result": response
        })
        
    except Exception as e:
        logger.error(f"Error performing AI analysis: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"AI analysis failed: {str(e)}"
            }
        )


@router.post("/project-health-analysis")
async def analyze_project_health(
    project_data: Dict[str, Any]
):
    """
    Analyze project health using strategic AI model
    """
    try:
        context = project_data.get("context", {})
        
        response = await get_ai_orchestrator().analyze_project_health(
            project_data=project_data,
            context=context
        )
        
        return JSONResponse(content={
            "success": response["success"],
            "analysis": response
        })
        
    except Exception as e:
        logger.error(f"Error analyzing project health: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Project health analysis failed: {str(e)}"
            }
        )


@router.post("/security-risk-assessment")
async def assess_security_risks(
    action_data: Dict[str, Any]
):
    """
    Assess security risks using security-focused AI model
    """
    try:
        context = action_data.get("context", {})
        
        response = await get_ai_orchestrator().assess_security_risks(
            action_data=action_data,
            context=context
        )
        
        return JSONResponse(content={
            "success": response["success"],
            "assessment": response
        })
        
    except Exception as e:
        logger.error(f"Error assessing security risks: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Security risk assessment failed: {str(e)}"
            }
        )


@router.post("/code-generation")
async def generate_code(
    code_data: Dict[str, Any]
):
    """
    Generate code using code-focused AI model
    """
    try:
        requirements = code_data.get("requirements", "")
        language = code_data.get("language", "python")
        context = code_data.get("context", {})
        
        response = await get_ai_orchestrator().generate_code(
            requirements=requirements,
            language=language,
            context=context
        )
        
        return JSONResponse(content={
            "success": response["success"],
            "code": response
        })
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Code generation failed: {str(e)}"
            }
        )


@router.post("/quick-decision")
async def make_quick_decision(
    decision_data: Dict[str, Any]
):
    """
    Make quick decision using fast reasoning AI model
    """
    try:
        decision_context = decision_data.get("context", {})
        options = decision_data.get("options", [])
        context = decision_data.get("additional_context", {})
        
        response = await get_ai_orchestrator().make_quick_decision(
            decision_context=decision_context,
            options=options,
            context=context
        )
        
        return JSONResponse(content={
            "success": response["success"],
            "decision": response
        })
        
    except Exception as e:
        logger.error(f"Error making quick decision: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Quick decision failed: {str(e)}"
            }
        )


@router.get("/model-status")
async def get_model_status():
    """
    Get status of all available AI models
    """
    try:
        status = get_ai_orchestrator().get_model_status()
        
        return JSONResponse(content={
            "success": True,
            "model_status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get model status: {str(e)}"
            }
        )


@router.post("/test-models")
async def test_model_availability():
    """
    Test availability of all AI models
    """
    try:
        test_results = await get_ai_orchestrator().test_model_availability()
        
        return JSONResponse(content={
            "success": test_results["success"],
            "test_results": test_results
        })
        
    except Exception as e:
        logger.error(f"Error testing models: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Model testing failed: {str(e)}"
            }
        )


@router.get("/guardrails-config")
async def get_guardrails_config():
    """
    Get current guardrails configuration
    """
    try:
        config = get_guardrails().config
        
        return JSONResponse(content={
            "success": True,
            "config": {
                "budget_threshold": config.budget_threshold,
                "resource_allocation_threshold": config.resource_allocation_threshold,
                "risk_mitigation_threshold": config.risk_mitigation_threshold,
                "stakeholder_communication_threshold": config.stakeholder_communication_threshold,
                "approval_timeout_hours": config.approval_timeout_hours,
                "execution_timeout_minutes": config.execution_timeout_minutes,
                "enable_auto_rollback": config.enable_auto_rollback,
                "rollback_timeout_minutes": config.rollback_timeout_minutes,
                "log_all_actions": config.log_all_actions,
                "log_approval_decisions": config.log_approval_decisions,
                "log_execution_results": config.log_execution_results
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting guardrails config: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get guardrails config: {str(e)}"
            }
        )


@router.post("/update-guardrails-config")
async def update_guardrails_config(
    config_data: Dict[str, Any]
):
    """
    Update guardrails configuration
    """
    try:
        # Create new config with updated values
        new_config = GuardrailConfig(
            budget_threshold=config_data.get("budget_threshold", 1000.0),
            resource_allocation_threshold=config_data.get("resource_allocation_threshold", 0.8),
            risk_mitigation_threshold=config_data.get("risk_mitigation_threshold", 0.85),
            stakeholder_communication_threshold=config_data.get("stakeholder_communication_threshold", 0.9),
            approval_timeout_hours=config_data.get("approval_timeout_hours", 24),
            execution_timeout_minutes=config_data.get("execution_timeout_minutes", 30),
            enable_auto_rollback=config_data.get("enable_auto_rollback", True),
            rollback_timeout_minutes=config_data.get("rollback_timeout_minutes", 60),
            log_all_actions=config_data.get("log_all_actions", True),
            log_approval_decisions=config_data.get("log_approval_decisions", True),
            log_execution_results=config_data.get("log_execution_results", True)
        )
        
        # Update the guardrails instance
        get_guardrails().config = new_config
        
        return JSONResponse(content={
            "success": True,
            "message": "Guardrails configuration updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating guardrails config: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to update guardrails config: {str(e)}"
            }
        )


@router.get("/autonomous-system-status")
async def get_autonomous_system_status():
    """
    Get overall status of the autonomous system
    """
    try:
        # Get workflow statistics
        workflow_stats = await get_state_manager().get_workflow_statistics()
        
        # Get model status
        model_status = get_ai_orchestrator().get_model_status()
        
        # Get guardrails config
        guardrails_config = {
            "budget_threshold": get_guardrails().config.budget_threshold,
            "resource_allocation_threshold": get_guardrails().config.resource_allocation_threshold,
            "risk_mitigation_threshold": get_guardrails().config.risk_mitigation_threshold,
            "stakeholder_communication_threshold": get_guardrails().config.stakeholder_communication_threshold,
            "approval_timeout_hours": get_guardrails().config.approval_timeout_hours,
            "execution_timeout_minutes": get_guardrails().config.execution_timeout_minutes,
            "enable_auto_rollback": get_guardrails().config.enable_auto_rollback,
            "rollback_timeout_minutes": get_guardrails().config.rollback_timeout_minutes
        }
        
        return JSONResponse(content={
            "success": True,
            "system_status": {
                "workflows": workflow_stats,
                "models": model_status,
                "guardrails": guardrails_config,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting autonomous system status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get system status: {str(e)}"
            }
        )
