#!/usr/bin/env python3
"""
Autonomous Guardrails System
Provides security framework, approval workflows, and decision validation for autonomous actions.
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

from app.models.user import User, Role, Tenant
from app.models.project import Project, Task, ProjectPlan
from app.models.audit import AuditLog
from app.core.database import get_db

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """Types of autonomous actions"""
    TASK_CREATION = "task_creation"
    RESOURCE_ALLOCATION = "resource_allocation"
    BUDGET_MODIFICATION = "budget_modification"
    RISK_MITIGATION = "risk_mitigation"
    STAKEHOLDER_COMMUNICATION = "stakeholder_communication"
    PROJECT_STATUS_CHANGE = "project_status_change"
    PLAN_MODIFICATION = "plan_modification"
    AUTOMATED_DECISION = "automated_decision"


class ApprovalLevel(str, Enum):
    """Approval levels for autonomous actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(str, Enum):
    """Status of autonomous actions"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class GuardrailConfig:
    """Configuration for autonomous guardrails"""
    # Approval thresholds
    budget_threshold: float = 1000.0  # Require approval above $1000
    resource_allocation_threshold: float = 0.8  # 80% confidence required
    risk_mitigation_threshold: float = 0.85  # 85% confidence required
    stakeholder_communication_threshold: float = 0.9  # 90% confidence required
    
    # Time limits
    approval_timeout_hours: int = 24  # Auto-approve after 24 hours for low-risk actions
    execution_timeout_minutes: int = 30  # Timeout for action execution
    
    # Rollback settings
    enable_auto_rollback: bool = True
    rollback_timeout_minutes: int = 60  # Time to detect and rollback failed actions
    
    # Audit settings
    log_all_actions: bool = True
    log_approval_decisions: bool = True
    log_execution_results: bool = True


class AutonomousGuardrails:
    """Autonomous guardrails system for security and approval workflows"""
    
    def __init__(self, config: GuardrailConfig = None):
        self.config = config or GuardrailConfig()
        self.approval_thresholds = {
            ActionType.TASK_CREATION: 0.7,
            ActionType.RESOURCE_ALLOCATION: self.config.resource_allocation_threshold,
            ActionType.BUDGET_MODIFICATION: 0.9,
            ActionType.RISK_MITIGATION: self.config.risk_mitigation_threshold,
            ActionType.STAKEHOLDER_COMMUNICATION: self.config.stakeholder_communication_threshold,
            ActionType.PROJECT_STATUS_CHANGE: 0.8,
            ActionType.PLAN_MODIFICATION: 0.85,
            ActionType.AUTOMATED_DECISION: 0.75
        }
    
    async def validate_action(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        confidence_score: float,
        context: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Validate autonomous action against security rules and business logic
        """
        try:
            validation_result = {
                "action_id": f"ACTION_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "action_type": action_type.value,
                "timestamp": datetime.now(),
                "requires_approval": False,
                "approval_level": ApprovalLevel.LOW,
                "validation_issues": [],
                "security_checks": [],
                "business_rule_checks": [],
                "confidence_score": confidence_score,
                "status": ActionStatus.PENDING
            }
            
            # Security checks
            security_checks = await self._perform_security_checks(action_type, action_data, context, db)
            validation_result["security_checks"] = security_checks
            
            if any(check["failed"] for check in security_checks):
                validation_result["validation_issues"].extend([
                    check["issue"] for check in security_checks if check["failed"]
                ])
            
            # Business rule checks
            business_checks = await self._perform_business_rule_checks(action_type, action_data, context, db)
            validation_result["business_rule_checks"] = business_checks
            
            if any(check["failed"] for check in business_checks):
                validation_result["validation_issues"].extend([
                    check["issue"] for check in business_checks if check["failed"]
                ])
            
            # Determine approval requirements
            approval_requirements = await self._determine_approval_requirements(
                action_type, action_data, confidence_score, validation_result, db
            )
            validation_result.update(approval_requirements)
            
            # Log validation result
            await self._log_validation_result(validation_result, db)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating action: {str(e)}")
            return {
                "action_id": f"ACTION_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "action_type": action_type.value,
                "timestamp": datetime.now(),
                "requires_approval": True,
                "approval_level": ApprovalLevel.CRITICAL,
                "validation_issues": [f"Validation error: {str(e)}"],
                "status": ActionStatus.FAILED,
                "error": str(e)
            }
    
    async def _perform_security_checks(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        context: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Perform security checks on autonomous action
        """
        security_checks = []
        
        # Check for unauthorized access
        user_id = context.get("user_id")
        if user_id:
            user_query = select(User).where(User.id == user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user or not user.is_active:
                security_checks.append({
                    "check": "user_authorization",
                    "failed": True,
                    "issue": "User not authorized or inactive"
                })
            else:
                security_checks.append({
                    "check": "user_authorization",
                    "failed": False,
                    "details": f"User {user.username} authorized"
                })
        
        # Check for data access permissions
        if "project_id" in action_data:
            project_id = action_data["project_id"]
            project_query = select(Project).where(Project.id == project_id)
            project_result = await db.execute(project_query)
            project = project_result.scalar_one_or_none()
            
            if not project:
                security_checks.append({
                    "check": "project_access",
                    "failed": True,
                    "issue": f"Project {project_id} not found"
                })
            else:
                security_checks.append({
                    "check": "project_access",
                    "failed": False,
                    "details": f"Access to project {project.name} verified"
                })
        
        # Check for PII exposure
        pii_check = await self._check_pii_exposure(action_data)
        security_checks.append(pii_check)
        
        # Check for budget overruns
        if action_type == ActionType.BUDGET_MODIFICATION:
            budget_check = await self._check_budget_limits(action_data, context, db)
            security_checks.append(budget_check)
        
        return security_checks
    
    async def _perform_business_rule_checks(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        context: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Perform business rule checks on autonomous action
        """
        business_checks = []
        
        # Check for business hours (if applicable)
        if action_type in [ActionType.STAKEHOLDER_COMMUNICATION, ActionType.PROJECT_STATUS_CHANGE]:
            business_hours_check = self._check_business_hours()
            business_checks.append(business_hours_check)
        
        # Check for resource availability
        if action_type == ActionType.RESOURCE_ALLOCATION:
            resource_check = await self._check_resource_availability(action_data, db)
            business_checks.append(resource_check)
        
        # Check for project constraints
        if "project_id" in action_data:
            constraint_check = await self._check_project_constraints(action_data, db)
            business_checks.append(constraint_check)
        
        # Check for dependency conflicts
        if action_type == ActionType.TASK_CREATION:
            dependency_check = await self._check_dependency_conflicts(action_data, db)
            business_checks.append(dependency_check)
        
        return business_checks
    
    async def _determine_approval_requirements(
        self,
        action_type: ActionType,
        action_data: Dict[str, Any],
        confidence_score: float,
        validation_result: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Determine approval requirements based on action type, confidence, and validation results
        """
        requires_approval = False
        approval_level = ApprovalLevel.LOW
        
        # Check confidence threshold
        threshold = self.approval_thresholds.get(action_type, 0.8)
        if confidence_score < threshold:
            requires_approval = True
            approval_level = ApprovalLevel.MEDIUM
        
        # Check for validation issues
        if validation_result["validation_issues"]:
            requires_approval = True
            if len(validation_result["validation_issues"]) > 2:
                approval_level = ApprovalLevel.HIGH
        
        # Check for critical actions
        if action_type in [ActionType.BUDGET_MODIFICATION, ActionType.PROJECT_STATUS_CHANGE]:
            if action_data.get("amount", 0) > self.config.budget_threshold:
                requires_approval = True
                approval_level = ApprovalLevel.HIGH
        
        # Check for high-risk actions
        if action_type == ActionType.RISK_MITIGATION:
            risk_level = action_data.get("risk_level", "low")
            if risk_level in ["high", "critical"]:
                requires_approval = True
                approval_level = ApprovalLevel.CRITICAL
        
        return {
            "requires_approval": requires_approval,
            "approval_level": approval_level.value,
            "approval_threshold": threshold,
            "confidence_met": confidence_score >= threshold
        }
    
    async def _check_pii_exposure(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for potential PII exposure in action data
        """
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
            r'\b\d{4}-\d{4}-\d{4}-\d{4}\b'  # Credit card
        ]
        
        import re
        action_str = json.dumps(action_data, default=str)
        
        for pattern in pii_patterns:
            if re.search(pattern, action_str):
                return {
                    "check": "pii_exposure",
                    "failed": True,
                    "issue": "Potential PII exposure detected"
                }
        
        return {
            "check": "pii_exposure",
            "failed": False,
            "details": "No PII exposure detected"
        }
    
    async def _check_budget_limits(
        self,
        action_data: Dict[str, Any],
        context: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Check budget limits for budget modifications
        """
        amount = action_data.get("amount", 0)
        project_id = action_data.get("project_id")
        
        if amount > self.config.budget_threshold:
            return {
                "check": "budget_limits",
                "failed": True,
                "issue": f"Budget modification {amount} exceeds threshold {self.config.budget_threshold}"
            }
        
        return {
            "check": "budget_limits",
            "failed": False,
            "details": f"Budget modification {amount} within limits"
        }
    
    def _check_business_hours(self) -> Dict[str, Any]:
        """
        Check if action is within business hours
        """
        now = datetime.now()
        business_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        business_end = now.replace(hour=17, minute=0, second=0, microsecond=0)
        
        if now.weekday() >= 5:  # Weekend
            return {
                "check": "business_hours",
                "failed": True,
                "issue": "Action attempted outside business hours (weekend)"
            }
        
        if now < business_start or now > business_end:
            return {
                "check": "business_hours",
                "failed": True,
                "issue": "Action attempted outside business hours"
            }
        
        return {
            "check": "business_hours",
            "failed": False,
            "details": "Action within business hours"
        }
    
    async def _check_resource_availability(
        self,
        action_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Check resource availability for resource allocation
        """
        resource_id = action_data.get("resource_id")
        if not resource_id:
            return {
                "check": "resource_availability",
                "failed": True,
                "issue": "No resource ID specified"
            }
        
        # Check if resource exists and is available
        resource_query = select(User).where(User.id == resource_id, User.is_active == True)
        resource_result = await db.execute(resource_query)
        resource = resource_result.scalar_one_or_none()
        
        if not resource:
            return {
                "check": "resource_availability",
                "failed": True,
                "issue": f"Resource {resource_id} not found or inactive"
            }
        
        return {
            "check": "resource_availability",
            "failed": False,
            "details": f"Resource {resource.username} available"
        }
    
    async def _check_project_constraints(
        self,
        action_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Check project constraints
        """
        project_id = action_data.get("project_id")
        if not project_id:
            return {
                "check": "project_constraints",
                "failed": True,
                "issue": "No project ID specified"
            }
        
        project_query = select(Project).where(Project.id == project_id)
        project_result = await db.execute(project_query)
        project = project_result.scalar_one_or_none()
        
        if not project:
            return {
                "check": "project_constraints",
                "failed": True,
                "issue": f"Project {project_id} not found"
            }
        
        # Check if project is in a state that allows modifications
        if project.status in ["completed", "cancelled"]:
            return {
                "check": "project_constraints",
                "failed": True,
                "issue": f"Project {project.name} is {project.status} and cannot be modified"
            }
        
        return {
            "check": "project_constraints",
            "failed": False,
            "details": f"Project {project.name} allows modifications"
        }
    
    async def _check_dependency_conflicts(
        self,
        action_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Check for dependency conflicts in task creation
        """
        dependencies = action_data.get("dependencies", [])
        if not dependencies:
            return {
                "check": "dependency_conflicts",
                "failed": False,
                "details": "No dependencies specified"
            }
        
        # Check if all dependencies exist
        for dep_id in dependencies:
            task_query = select(Task).where(Task.id == dep_id)
            task_result = await db.execute(task_query)
            task = task_result.scalar_one_or_none()
            
            if not task:
                return {
                    "check": "dependency_conflicts",
                    "failed": True,
                    "issue": f"Dependency task {dep_id} not found"
                }
        
        return {
            "check": "dependency_conflicts",
            "failed": False,
            "details": f"All {len(dependencies)} dependencies valid"
        }
    
    async def _log_validation_result(
        self,
        validation_result: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """
        Log validation result to audit trail
        """
        try:
            audit_log = AuditLog(
                user_id=validation_result.get("user_id"),
                action="autonomous_action_validation",
                resource_type="autonomous_action",
                resource_id=validation_result["action_id"],
                details=json.dumps(validation_result),
                ip_address="system",
                user_agent="autonomous_system"
            )
            
            db.add(audit_log)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error logging validation result: {str(e)}")
    
    async def get_approval_workflow(
        self,
        action_id: str,
        approval_level: ApprovalLevel,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get approval workflow for autonomous action
        """
        approval_workflow = {
            "action_id": action_id,
            "approval_level": approval_level.value,
            "approvers": [],
            "current_step": 0,
            "total_steps": 0,
            "status": "pending"
        }
        
        # Define approval hierarchy based on level
        if approval_level == ApprovalLevel.LOW:
            approval_workflow["approvers"] = ["manager"]
            approval_workflow["total_steps"] = 1
        elif approval_level == ApprovalLevel.MEDIUM:
            approval_workflow["approvers"] = ["manager", "director"]
            approval_workflow["total_steps"] = 2
        elif approval_level == ApprovalLevel.HIGH:
            approval_workflow["approvers"] = ["manager", "director", "vp"]
            approval_workflow["total_steps"] = 3
        elif approval_level == ApprovalLevel.CRITICAL:
            approval_workflow["approvers"] = ["manager", "director", "vp", "executive"]
            approval_workflow["total_steps"] = 4
        
        return approval_workflow
