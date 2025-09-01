#!/usr/bin/env python3
"""
Approval Engine Service
Handles approval workflows, RBAC, JWT refresh, PII redaction, and audit trails
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import json
import logging
import jwt
import hashlib
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload

from app.models.project import Project, Task
from app.models.user import User
from app.core.config import settings
from app.core.security import create_access_token, verify_password

logger = logging.getLogger(__name__)

class ApprovalStatus(Enum):
    """Approval status values"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"

class ApprovalType(Enum):
    """Types of approvals"""
    PROJECT_CREATION = "project_creation"
    PROJECT_MODIFICATION = "project_modification"
    BUDGET_CHANGE = "budget_change"
    TIMELINE_CHANGE = "timeline_change"
    RESOURCE_ASSIGNMENT = "resource_assignment"
    RISK_ESCALATION = "risk_escalation"
    DOCUMENT_APPROVAL = "document_approval"
    EXPENSE_APPROVAL = "expense_approval"

class UserRole(Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"
    DEVELOPER = "developer"
    STAKEHOLDER = "stakeholder"
    VIEWER = "viewer"

class AuditAction(Enum):
    """Audit action types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"

@dataclass
class ApprovalRequest:
    """Approval request data"""
    id: int
    requester_id: int
    approver_id: Optional[int]
    approval_type: ApprovalType
    entity_type: str  # project, task, document, etc.
    entity_id: int
    title: str
    description: str
    data: Dict[str, Any]
    status: ApprovalStatus
    priority: str  # low, medium, high, critical
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime]
    escalation_level: int = 0
    comments: List[Dict[str, Any]] = None

@dataclass
class ApprovalWorkflow:
    """Approval workflow definition"""
    id: int
    name: str
    approval_type: ApprovalType
    steps: List[Dict[str, Any]]
    auto_approve: bool = False
    require_all_approvers: bool = True
    escalation_timeout_hours: int = 24
    max_escalation_levels: int = 3

@dataclass
class AuditLog:
    """Audit log entry"""
    id: int
    user_id: int
    action: AuditAction
    entity_type: str
    entity_id: int
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    ip_address: str
    user_agent: str
    timestamp: datetime
    session_id: str
    metadata: Dict[str, Any] = None

@dataclass
class RBACPermission:
    """RBAC permission definition"""
    role: UserRole
    resource: str
    action: str
    conditions: Dict[str, Any] = None

class ApprovalEngine:
    """Service for approval workflows and governance"""
    
    def __init__(self):
        # Default approval workflows
        self.workflows = {
            ApprovalType.PROJECT_CREATION: ApprovalWorkflow(
                id=1,
                name="Project Creation Approval",
                approval_type=ApprovalType.PROJECT_CREATION,
                steps=[
                    {"role": UserRole.TEAM_LEAD, "order": 1, "required": True},
                    {"role": UserRole.PROJECT_MANAGER, "order": 2, "required": True},
                    {"role": UserRole.STAKEHOLDER, "order": 3, "required": False}
                ],
                escalation_timeout_hours=48,
                max_escalation_levels=2
            ),
            ApprovalType.BUDGET_CHANGE: ApprovalWorkflow(
                id=2,
                name="Budget Change Approval",
                approval_type=ApprovalType.BUDGET_CHANGE,
                steps=[
                    {"role": UserRole.PROJECT_MANAGER, "order": 1, "required": True},
                    {"role": UserRole.ADMIN, "order": 2, "required": True}
                ],
                escalation_timeout_hours=24,
                max_escalation_levels=1
            ),
            ApprovalType.RISK_ESCALATION: ApprovalWorkflow(
                id=3,
                name="Risk Escalation Approval",
                approval_type=ApprovalType.RISK_ESCALATION,
                steps=[
                    {"role": UserRole.TEAM_LEAD, "order": 1, "required": True},
                    {"role": UserRole.PROJECT_MANAGER, "order": 2, "required": True},
                    {"role": UserRole.ADMIN, "order": 3, "required": True}
                ],
                escalation_timeout_hours=12,
                max_escalation_levels=3
            )
        }
        
        # RBAC permissions matrix
        self.permissions = {
            UserRole.ADMIN: {
                "projects": ["create", "read", "update", "delete", "approve"],
                "tasks": ["create", "read", "update", "delete", "approve"],
                "users": ["create", "read", "update", "delete"],
                "approvals": ["create", "read", "update", "delete", "approve"],
                "audit": ["read", "export"]
            },
            UserRole.PROJECT_MANAGER: {
                "projects": ["create", "read", "update"],
                "tasks": ["create", "read", "update", "delete"],
                "users": ["read"],
                "approvals": ["create", "read", "approve"],
                "audit": ["read"]
            },
            UserRole.TEAM_LEAD: {
                "projects": ["read", "update"],
                "tasks": ["create", "read", "update"],
                "users": ["read"],
                "approvals": ["create", "read", "approve"],
                "audit": ["read"]
            },
            UserRole.DEVELOPER: {
                "projects": ["read"],
                "tasks": ["read", "update"],
                "users": ["read"],
                "approvals": ["read"],
                "audit": ["read"]
            },
            UserRole.STAKEHOLDER: {
                "projects": ["read"],
                "tasks": ["read"],
                "users": ["read"],
                "approvals": ["read", "approve"],
                "audit": ["read"]
            },
            UserRole.VIEWER: {
                "projects": ["read"],
                "tasks": ["read"],
                "users": ["read"],
                "approvals": ["read"],
                "audit": ["read"]
            }
        }
        
        # PII patterns for redaction
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
    
    async def create_approval_request(self, requester_id: int, approval_type: ApprovalType,
                                    entity_type: str, entity_id: int, title: str, description: str,
                                    data: Dict[str, Any], db: AsyncSession, priority: str = "medium",
                                    due_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a new approval request"""
        try:
            # Get workflow for approval type
            workflow = self.workflows.get(approval_type)
            if not workflow:
                return {"success": False, "error": f"No workflow defined for {approval_type.value}"}
            
            # Find next approver
            next_approver = await self._find_next_approver(workflow, 0, db)
            
            # Create approval request
            approval_request = ApprovalRequest(
                id=0,  # Will be set by database
                requester_id=requester_id,
                approver_id=next_approver["user_id"] if next_approver else None,
                approval_type=approval_type,
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                description=description,
                data=data,
                status=ApprovalStatus.PENDING,
                priority=priority,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                due_date=due_date,
                escalation_level=0,
                comments=[]
            )
            
            # In a real implementation, this would save to database
            # For now, return the request
            return {
                "success": True,
                "approval_request": approval_request,
                "next_approver": next_approver
            }
        except Exception as e:
            logger.error(f"Error creating approval request: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_approval(self, approval_id: int, approver_id: int, action: str,
                             comments: str = "", db: AsyncSession) -> Dict[str, Any]:
        """Process an approval (approve/reject)"""
        try:
            # Get approval request (in real implementation, fetch from database)
            approval_request = await self._get_approval_request(approval_id, db)
            if not approval_request:
                return {"success": False, "error": "Approval request not found"}
            
            # Check if user can approve
            can_approve = await self._can_user_approve(approval_request, approver_id, db)
            if not can_approve:
                return {"success": False, "error": "User not authorized to approve this request"}
            
            # Update approval status
            if action == "approve":
                approval_request.status = ApprovalStatus.APPROVED
            elif action == "reject":
                approval_request.status = ApprovalStatus.REJECTED
            else:
                return {"success": False, "error": "Invalid action"}
            
            # Add comment
            approval_request.comments.append({
                "user_id": approver_id,
                "action": action,
                "comments": comments,
                "timestamp": datetime.utcnow()
            })
            
            # If approved, check if more approvals needed
            if action == "approve":
                workflow = self.workflows.get(approval_request.approval_type)
                next_approver = await self._find_next_approver(workflow, approval_request.escalation_level + 1, db)
                
                if next_approver:
                    approval_request.approver_id = next_approver["user_id"]
                    approval_request.escalation_level += 1
                    approval_request.status = ApprovalStatus.PENDING
                else:
                    # All approvals complete
                    await self._complete_approval(approval_request, db)
            
            approval_request.updated_at = datetime.utcnow()
            
            return {
                "success": True,
                "approval_request": approval_request,
                "next_approver": next_approver if action == "approve" else None
            }
        except Exception as e:
            logger.error(f"Error processing approval: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_pending_approvals(self, user_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get pending approvals for a user"""
        try:
            # In real implementation, query database for pending approvals
            # For now, return mock data
            pending_approvals = [
                {
                    "id": 1,
                    "title": "New Project: Alpha Development",
                    "description": "Request to create new project for Alpha product development",
                    "approval_type": ApprovalType.PROJECT_CREATION.value,
                    "entity_type": "project",
                    "entity_id": 1,
                    "priority": "high",
                    "created_at": datetime.utcnow() - timedelta(hours=2),
                    "due_date": datetime.utcnow() + timedelta(hours=22),
                    "requester": "John Doe"
                },
                {
                    "id": 2,
                    "title": "Budget Increase: Beta Project",
                    "description": "Request to increase budget by $50,000 for additional resources",
                    "approval_type": ApprovalType.BUDGET_CHANGE.value,
                    "entity_type": "project",
                    "entity_id": 2,
                    "priority": "medium",
                    "created_at": datetime.utcnow() - timedelta(hours=5),
                    "due_date": datetime.utcnow() + timedelta(hours=19),
                    "requester": "Jane Smith"
                }
            ]
            
            return {
                "success": True,
                "pending_approvals": pending_approvals,
                "total_count": len(pending_approvals)
            }
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_permission(self, user_id: int, resource: str, action: str, db: AsyncSession,
                             entity_id: Optional[int] = None) -> bool:
        """Check if user has permission for resource and action"""
        try:
            # Get user role
            user_role = await self._get_user_role(user_id, db)
            if not user_role:
                return False
            
            # Check basic permission
            role_permissions = self.permissions.get(user_role, {})
            resource_permissions = role_permissions.get(resource, [])
            
            if action not in resource_permissions:
                return False
            
            # Check entity-specific conditions
            if entity_id and resource in ["projects", "tasks"]:
                return await self._check_entity_permission(user_id, resource, entity_id, db)
            
            return True
        except Exception as e:
            logger.error(f"Error checking permission: {e}")
            return False
    
    async def create_audit_log(self, user_id: int, action: AuditAction, entity_type: str,
                              entity_id: int, old_values: Optional[Dict[str, Any]],
                              new_values: Optional[Dict[str, Any]], ip_address: str,
                              user_agent: str, session_id: str,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an audit log entry"""
        try:
            # Redact PII from values
            redacted_old_values = self._redact_pii(old_values) if old_values else None
            redacted_new_values = self._redact_pii(new_values) if new_values else None
            
            audit_log = AuditLog(
                id=0,  # Will be set by database
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=redacted_old_values,
                new_values=redacted_new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                session_id=session_id,
                metadata=metadata or {}
            )
            
            # In real implementation, save to database
            # For now, return the log entry
            return {
                "success": True,
                "audit_log": audit_log
            }
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_audit_trail(self, entity_type: str, entity_id: int, db: AsyncSession,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            user_id: Optional[int] = None,
                            action: Optional[AuditAction] = None) -> Dict[str, Any]:
        """Get audit trail for an entity"""
        try:
            # In real implementation, query database
            # For now, return mock data
            audit_trail = [
                {
                    "id": 1,
                    "user_id": 1,
                    "user_name": "John Doe",
                    "action": AuditAction.CREATE.value,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "timestamp": datetime.utcnow() - timedelta(days=1),
                    "ip_address": "192.168.1.100",
                    "changes": "Created new project"
                },
                {
                    "id": 2,
                    "user_id": 2,
                    "user_name": "Jane Smith",
                    "action": AuditAction.UPDATE.value,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "timestamp": datetime.utcnow() - timedelta(hours=6),
                    "ip_address": "192.168.1.101",
                    "changes": "Updated project description"
                }
            ]
            
            # Apply filters
            if start_date:
                audit_trail = [log for log in audit_trail if log["timestamp"] >= start_date]
            if end_date:
                audit_trail = [log for log in audit_trail if log["timestamp"] <= end_date]
            if user_id:
                audit_trail = [log for log in audit_trail if log["user_id"] == user_id]
            if action:
                audit_trail = [log for log in audit_trail if log["action"] == action.value]
            
            return {
                "success": True,
                "audit_trail": audit_trail,
                "total_count": len(audit_trail)
            }
        except Exception as e:
            logger.error(f"Error getting audit trail: {e}")
            return {"success": False, "error": str(e)}
    
    async def refresh_jwt_token(self, user_id: int, current_token: str) -> Dict[str, Any]:
        """Refresh JWT token"""
        try:
            # Verify current token
            payload = jwt.decode(current_token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("sub") != str(user_id):
                return {"success": False, "error": "Invalid token"}
            
            # Create new token
            new_token = create_access_token(data={"sub": str(user_id)})
            
            return {
                "success": True,
                "access_token": new_token,
                "token_type": "bearer"
            }
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}
        except Exception as e:
            logger.error(f"Error refreshing JWT token: {e}")
            return {"success": False, "error": str(e)}
    
    def _redact_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact PII from data"""
        if not data:
            return data
        
        redacted_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted_value = value
                for pattern_name, pattern in self.pii_patterns.items():
                    redacted_value = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", redacted_value)
                redacted_data[key] = redacted_value
            elif isinstance(value, dict):
                redacted_data[key] = self._redact_pii(value)
            elif isinstance(value, list):
                redacted_data[key] = [self._redact_pii(item) if isinstance(item, dict) else item for item in value]
            else:
                redacted_data[key] = value
        
        return redacted_data
    
    async def _find_next_approver(self, workflow: ApprovalWorkflow, escalation_level: int,
                                 db: AsyncSession) -> Optional[Dict[str, Any]]:
        """Find the next approver in the workflow"""
        try:
            if escalation_level >= workflow.max_escalation_levels:
                return None
            
            # Get step for current escalation level
            step = workflow.steps[escalation_level] if escalation_level < len(workflow.steps) else None
            if not step:
                return None
            
            # Find users with the required role
            # In real implementation, query database
            # For now, return mock data
            return {
                "user_id": 1,
                "user_name": "John Doe",
                "role": step["role"].value,
                "email": "john.doe@example.com"
            }
        except Exception as e:
            logger.error(f"Error finding next approver: {e}")
            return None
    
    async def _get_approval_request(self, approval_id: int, db: AsyncSession) -> Optional[ApprovalRequest]:
        """Get approval request by ID"""
        # In real implementation, query database
        # For now, return None
        return None
    
    async def _can_user_approve(self, approval_request: ApprovalRequest, user_id: int,
                               db: AsyncSession) -> bool:
        """Check if user can approve the request"""
        # In real implementation, check user role and workflow step
        # For now, return True
        return True
    
    async def _complete_approval(self, approval_request: ApprovalRequest, db: AsyncSession):
        """Complete the approval process"""
        # In real implementation, trigger the approved action
        # For now, just log
        logger.info(f"Approval completed for {approval_request.approval_type.value}")
    
    async def _get_user_role(self, user_id: int, db: AsyncSession) -> Optional[UserRole]:
        """Get user role"""
        # In real implementation, query database
        # For now, return PROJECT_MANAGER
        return UserRole.PROJECT_MANAGER
    
    async def _check_entity_permission(self, user_id: int, resource: str, entity_id: int,
                                     db: AsyncSession) -> bool:
        """Check entity-specific permission"""
        # In real implementation, check if user has access to specific entity
        # For now, return True
        return True
