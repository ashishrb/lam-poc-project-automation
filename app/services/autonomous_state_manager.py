#!/usr/bin/env python3
"""
Autonomous State Manager
Manages state for autonomous workflows, tracks decisions, and handles rollback mechanisms.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload

from app.models.project import Project, Task, ProjectPlan
from app.models.audit import AuditLog
from app.models.user import User
from app.core.database import get_db

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Status of autonomous workflows"""
    INITIATED = "initiated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    TIMEOUT = "timeout"


class WorkflowType(str, Enum):
    """Types of autonomous workflows"""
    PROJECT_HEALTH_ANALYSIS = "project_health_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    BUDGET_ANALYSIS = "budget_analysis"
    STAKEHOLDER_COMMUNICATION = "stakeholder_communication"
    PLAN_GENERATION = "plan_generation"
    TASK_AUTOMATION = "task_automation"
    DECISION_MAKING = "decision_making"


@dataclass
class WorkflowState:
    """State of an autonomous workflow"""
    workflow_id: str
    workflow_type: WorkflowType
    status: WorkflowStatus
    project_id: Optional[int] = None
    user_id: Optional[int] = None
    initiated_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    steps_completed: List[str] = None
    decisions_made: List[Dict[str, Any]] = None
    actions_taken: List[Dict[str, Any]] = None
    rollback_points: List[Dict[str, Any]] = None
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.initiated_at is None:
            self.initiated_at = datetime.now()
        if self.steps_completed is None:
            self.steps_completed = []
        if self.decisions_made is None:
            self.decisions_made = []
        if self.actions_taken is None:
            self.actions_taken = []
        if self.rollback_points is None:
            self.rollback_points = []


@dataclass
class StateManagerConfig:
    """Configuration for state manager"""
    # Timeout settings
    workflow_timeout_minutes: int = 30
    step_timeout_minutes: int = 5
    rollback_timeout_minutes: int = 10
    
    # State persistence
    persist_state: bool = True
    state_retention_days: int = 30
    
    # Rollback settings
    enable_auto_rollback: bool = True
    max_rollback_attempts: int = 3
    
    # Monitoring
    enable_monitoring: bool = True
    monitoring_interval_seconds: int = 30


class AutonomousStateManager:
    """Manages state for autonomous workflows and provides rollback capabilities"""
    
    def __init__(self, config: StateManagerConfig = None):
        self.config = config or StateManagerConfig()
        self.active_workflows: Dict[str, WorkflowState] = {}
        self.workflow_history: List[WorkflowState] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_started = False
    
    async def start_workflow(
        self,
        workflow_type: WorkflowType,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        context: Dict[str, Any] = None
    ) -> str:
        # Start monitoring if not already started
        if self.config.enable_monitoring and not self._monitoring_started:
            try:
                self.monitoring_task = asyncio.create_task(self._monitor_workflows())
                self._monitoring_started = True
            except RuntimeError:
                # No event loop running, monitoring will start when first workflow is created
                pass
        """
        Start a new autonomous workflow
        """
        workflow_id = f"WORKFLOW_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{workflow_type.value}"
        
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            status=WorkflowStatus.INITIATED,
            project_id=project_id,
            user_id=user_id,
            timeout_at=datetime.now() + timedelta(minutes=self.config.workflow_timeout_minutes)
        )
        
        self.active_workflows[workflow_id] = workflow_state
        
        # Log workflow start
        await self._log_workflow_event(workflow_state, "workflow_started", context)
        
        logger.info(f"Started workflow {workflow_id} of type {workflow_type.value}")
        return workflow_id
    
    async def update_workflow_state(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        step_name: Optional[str] = None,
        decision: Optional[Dict[str, Any]] = None,
        action: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the state of an active workflow
        """
        if workflow_id not in self.active_workflows:
            logger.error(f"Workflow {workflow_id} not found")
            return False
        
        workflow_state = self.active_workflows[workflow_id]
        
        # Update status
        workflow_state.status = status
        
        # Update timestamps
        if status == WorkflowStatus.RUNNING and workflow_state.started_at is None:
            workflow_state.started_at = datetime.now()
        elif status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.ROLLED_BACK]:
            workflow_state.completed_at = datetime.now()
        
        # Add step if provided
        if step_name:
            workflow_state.steps_completed.append(step_name)
        
        # Add decision if provided
        if decision:
            decision["timestamp"] = datetime.now().isoformat()
            workflow_state.decisions_made.append(decision)
        
        # Add action if provided
        if action:
            action["timestamp"] = datetime.now().isoformat()
            workflow_state.actions_taken.append(action)
        
        # Add error message if provided
        if error_message:
            workflow_state.error_message = error_message
        
        # Add result data if provided
        if result_data:
            workflow_state.result_data = result_data
        
        # Create rollback point for completed steps
        if step_name and status == WorkflowStatus.RUNNING:
            await self._create_rollback_point(workflow_state, step_name)
        
        # Log state update
        await self._log_workflow_event(workflow_state, "state_updated", {
            "status": status.value,
            "step": step_name,
            "decision": decision,
            "action": action,
            "error": error_message
        })
        
        logger.info(f"Updated workflow {workflow_id} status to {status.value}")
        return True
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """
        Get the current state of a workflow
        """
        return self.active_workflows.get(workflow_id)
    
    async def get_workflow_history(self, project_id: Optional[int] = None) -> List[WorkflowState]:
        """
        Get workflow history, optionally filtered by project
        """
        if project_id:
            return [
                workflow for workflow in self.workflow_history
                if workflow.project_id == project_id
            ]
        return self.workflow_history.copy()
    
    async def rollback_workflow(
        self,
        workflow_id: str,
        rollback_to_step: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Rollback a workflow to a previous state
        """
        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "error": f"Workflow {workflow_id} not found"
            }
        
        workflow_state = self.active_workflows[workflow_id]
        
        try:
            # Find rollback point
            rollback_point = None
            if rollback_to_step:
                rollback_point = next(
                    (point for point in workflow_state.rollback_points 
                     if point["step_name"] == rollback_to_step),
                    None
                )
            else:
                # Rollback to last successful step
                rollback_point = workflow_state.rollback_points[-1] if workflow_state.rollback_points else None
            
            if not rollback_point:
                return {
                    "success": False,
                    "error": "No rollback point found"
                }
            
            # Perform rollback
            rollback_result = await self._perform_rollback(workflow_state, rollback_point, db)
            
            if rollback_result["success"]:
                await self.update_workflow_state(
                    workflow_id,
                    WorkflowStatus.ROLLED_BACK,
                    error_message=f"Rolled back to step: {rollback_point['step_name']}"
                )
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Error rolling back workflow {workflow_id}: {str(e)}")
            return {
                "success": False,
                "error": f"Rollback failed: {str(e)}"
            }
    
    async def _create_rollback_point(
        self,
        workflow_state: WorkflowState,
        step_name: str
    ) -> None:
        """
        Create a rollback point for the current workflow state
        """
        rollback_point = {
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "workflow_state": asdict(workflow_state),
            "actions_taken": workflow_state.actions_taken.copy(),
            "decisions_made": workflow_state.decisions_made.copy()
        }
        
        workflow_state.rollback_points.append(rollback_point)
        
        # Keep only recent rollback points to manage memory
        if len(workflow_state.rollback_points) > 10:
            workflow_state.rollback_points = workflow_state.rollback_points[-10:]
    
    async def _perform_rollback(
        self,
        workflow_state: WorkflowState,
        rollback_point: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Perform the actual rollback operation
        """
        try:
            # Restore workflow state
            workflow_state.steps_completed = [
                step for step in workflow_state.steps_completed
                if step != rollback_point["step_name"]
            ]
            workflow_state.actions_taken = rollback_point["actions_taken"]
            workflow_state.decisions_made = rollback_point["decisions_made"]
            
            # Rollback database changes if needed
            if db:
                await self._rollback_database_changes(workflow_state, rollback_point, db)
            
            return {
                "success": True,
                "rollback_point": rollback_point["step_name"],
                "timestamp": rollback_point["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Error performing rollback: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _rollback_database_changes(
        self,
        workflow_state: WorkflowState,
        rollback_point: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """
        Rollback database changes made after the rollback point
        """
        # This is a simplified rollback - in a real system, you'd need more sophisticated
        # transaction management and change tracking
        
        # For now, we'll just log the rollback attempt
        logger.info(f"Rolling back database changes for workflow {workflow_state.workflow_id}")
        
        # In a real implementation, you would:
        # 1. Track all database changes made during the workflow
        # 2. Reverse changes made after the rollback point
        # 3. Restore previous state of affected records
        
        # For demonstration, we'll create an audit log entry
        audit_log = AuditLog(
            user_id=workflow_state.user_id,
            action="workflow_rollback",
            resource_type="autonomous_workflow",
            resource_id=workflow_state.workflow_id,
            details=json.dumps({
                "rollback_point": rollback_point["step_name"],
                "workflow_type": workflow_state.workflow_type.value,
                "project_id": workflow_state.project_id
            }),
            ip_address="system",
            user_agent="autonomous_system"
        )
        
        db.add(audit_log)
        await db.commit()
    
    async def _monitor_workflows(self) -> None:
        """
        Monitor active workflows for timeouts and issues
        """
        while True:
            try:
                current_time = datetime.now()
                workflows_to_timeout = []
                
                for workflow_id, workflow_state in self.active_workflows.items():
                    # Check for timeout
                    if (workflow_state.timeout_at and 
                        current_time > workflow_state.timeout_at and
                        workflow_state.status == WorkflowStatus.RUNNING):
                        workflows_to_timeout.append(workflow_id)
                    
                    # Check for stuck workflows
                    if (workflow_state.status == WorkflowStatus.RUNNING and
                        workflow_state.started_at and
                        current_time - workflow_state.started_at > timedelta(minutes=self.config.workflow_timeout_minutes)):
                        workflows_to_timeout.append(workflow_id)
                
                # Handle timeouts
                for workflow_id in workflows_to_timeout:
                    await self.update_workflow_state(
                        workflow_id,
                        WorkflowStatus.TIMEOUT,
                        error_message="Workflow timed out"
                    )
                    logger.warning(f"Workflow {workflow_id} timed out")
                
                # Clean up completed workflows
                completed_workflows = [
                    workflow_id for workflow_id, workflow_state in self.active_workflows.items()
                    if workflow_state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.ROLLED_BACK, WorkflowStatus.TIMEOUT]
                ]
                
                for workflow_id in completed_workflows:
                    workflow_state = self.active_workflows.pop(workflow_id)
                    self.workflow_history.append(workflow_state)
                    
                    # Clean up old history
                    cutoff_date = datetime.now() - timedelta(days=self.config.state_retention_days)
                    self.workflow_history = [
                        workflow for workflow in self.workflow_history
                        if workflow.initiated_at > cutoff_date
                    ]
                
                await asyncio.sleep(self.config.monitoring_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in workflow monitoring: {str(e)}")
                await asyncio.sleep(self.config.monitoring_interval_seconds)
    
    async def _log_workflow_event(
        self,
        workflow_state: WorkflowState,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """
        Log workflow events to audit trail
        """
        try:
            audit_log = AuditLog(
                user_id=workflow_state.user_id,
                action=f"autonomous_workflow_{event_type}",
                resource_type="autonomous_workflow",
                resource_id=workflow_state.workflow_id,
                details=json.dumps({
                    "workflow_type": workflow_state.workflow_type.value,
                    "status": workflow_state.status.value,
                    "project_id": workflow_state.project_id,
                    "event_type": event_type,
                    "event_data": event_data
                }),
                ip_address="system",
                user_agent="autonomous_system"
            )
            
            # Note: We're not committing here since we don't have a db session
            # In a real implementation, you'd pass the db session or use a background task
            
        except Exception as e:
            logger.error(f"Error logging workflow event: {str(e)}")
    
    async def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about workflows
        """
        total_workflows = len(self.active_workflows) + len(self.workflow_history)
        active_workflows = len(self.active_workflows)
        
        # Count by status
        status_counts = {}
        for workflow in list(self.active_workflows.values()) + self.workflow_history:
            status = workflow.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by type
        type_counts = {}
        for workflow in list(self.active_workflows.values()) + self.workflow_history:
            workflow_type = workflow.workflow_type.value
            type_counts[workflow_type] = type_counts.get(workflow_type, 0) + 1
        
        return {
            "total_workflows": total_workflows,
            "active_workflows": active_workflows,
            "completed_workflows": len(self.workflow_history),
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "average_completion_time_minutes": self._calculate_average_completion_time()
        }
    
    def _calculate_average_completion_time(self) -> float:
        """
        Calculate average completion time for workflows
        """
        completed_workflows = [
            workflow for workflow in self.workflow_history
            if workflow.completed_at and workflow.started_at
        ]
        
        if not completed_workflows:
            return 0.0
        
        total_time = sum(
            (workflow.completed_at - workflow.started_at).total_seconds()
            for workflow in completed_workflows
        )
        
        return total_time / len(completed_workflows) / 60  # Convert to minutes
    
    async def cleanup(self) -> None:
        """
        Cleanup resources and stop monitoring
        """
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Autonomous state manager cleaned up")
