#!/usr/bin/env python3
"""
Pydantic schemas for approval engine
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ApprovalStatus(str, Enum):
    """Approval status values"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"

class ApprovalType(str, Enum):
    """Types of approvals"""
    PROJECT_CREATION = "project_creation"
    PROJECT_MODIFICATION = "project_modification"
    BUDGET_CHANGE = "budget_change"
    TIMELINE_CHANGE = "timeline_change"
    RESOURCE_ASSIGNMENT = "resource_assignment"
    RISK_ESCALATION = "risk_escalation"
    DOCUMENT_APPROVAL = "document_approval"
    EXPENSE_APPROVAL = "expense_approval"

class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    TEAM_LEAD = "team_lead"
    DEVELOPER = "developer"
    STAKEHOLDER = "stakeholder"
    VIEWER = "viewer"

class AuditAction(str, Enum):
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

# Approval Request Schemas
class ApprovalRequestCreate(BaseModel):
    approval_type: ApprovalType = Field(..., description="Type of approval")
    entity_type: str = Field(..., description="Entity type (project, task, etc.)")
    entity_id: int = Field(..., description="Entity ID")
    title: str = Field(..., description="Approval request title")
    description: str = Field(..., description="Approval request description")
    data: Dict[str, Any] = Field(..., description="Request data")
    priority: str = Field(default="medium", description="Priority level")
    due_date: Optional[datetime] = Field(None, description="Due date for approval")

class ApprovalComment(BaseModel):
    user_id: int = Field(..., description="User ID")
    action: str = Field(..., description="Action taken")
    comments: str = Field(..., description="Comment text")
    timestamp: datetime = Field(..., description="Comment timestamp")

class ApprovalRequestData(BaseModel):
    id: int = Field(..., description="Approval request ID")
    requester_id: int = Field(..., description="Requester user ID")
    approver_id: Optional[int] = Field(None, description="Current approver ID")
    approval_type: ApprovalType = Field(..., description="Approval type")
    entity_type: str = Field(..., description="Entity type")
    entity_id: int = Field(..., description="Entity ID")
    title: str = Field(..., description="Request title")
    description: str = Field(..., description="Request description")
    data: Dict[str, Any] = Field(..., description="Request data")
    status: ApprovalStatus = Field(..., description="Approval status")
    priority: str = Field(..., description="Priority level")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date")
    escalation_level: int = Field(..., description="Current escalation level")
    comments: List[ApprovalComment] = Field(default=[], description="Approval comments")

class ApprovalRequestResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    approval_request: Optional[ApprovalRequestData] = Field(None, description="Approval request data")
    next_approver: Optional[Dict[str, Any]] = Field(None, description="Next approver information")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Approval Processing Schemas
class ApprovalProcessRequest(BaseModel):
    action: str = Field(..., description="Action: approve or reject")
    comments: str = Field(default="", description="Comments for the approval/rejection")

class ApprovalProcessResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    approval_request: Optional[ApprovalRequestData] = Field(None, description="Updated approval request")
    next_approver: Optional[Dict[str, Any]] = Field(None, description="Next approver if approved")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Pending Approvals Schemas
class PendingApprovalSummary(BaseModel):
    id: int = Field(..., description="Approval request ID")
    title: str = Field(..., description="Request title")
    description: str = Field(..., description="Request description")
    approval_type: ApprovalType = Field(..., description="Approval type")
    entity_type: str = Field(..., description="Entity type")
    entity_id: int = Field(..., description="Entity ID")
    priority: str = Field(..., description="Priority level")
    created_at: datetime = Field(..., description="Creation timestamp")
    due_date: Optional[datetime] = Field(None, description="Due date")
    requester: str = Field(..., description="Requester name")

class PendingApprovalsResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    pending_approvals: List[PendingApprovalSummary] = Field(default=[], description="List of pending approvals")
    total_count: int = Field(..., description="Total number of pending approvals")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Permission Check Schemas
class PermissionCheckRequest(BaseModel):
    resource: str = Field(..., description="Resource to check permission for")
    action: str = Field(..., description="Action to check permission for")
    entity_id: Optional[int] = Field(None, description="Entity ID for entity-specific permissions")

class PermissionCheckResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    has_permission: bool = Field(..., description="Whether user has permission")
    user_role: Optional[str] = Field(None, description="User's role")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Audit Trail Schemas
class AuditLogEntry(BaseModel):
    id: int = Field(..., description="Audit log entry ID")
    user_id: int = Field(..., description="User ID")
    user_name: str = Field(..., description="User name")
    action: AuditAction = Field(..., description="Action performed")
    entity_type: str = Field(..., description="Entity type")
    entity_id: int = Field(..., description="Entity ID")
    timestamp: datetime = Field(..., description="Action timestamp")
    ip_address: str = Field(..., description="IP address")
    changes: str = Field(..., description="Description of changes")

class AuditTrailRequest(BaseModel):
    entity_type: str = Field(..., description="Entity type")
    entity_id: int = Field(..., description="Entity ID")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    user_id: Optional[int] = Field(None, description="User ID for filtering")
    action: Optional[AuditAction] = Field(None, description="Action for filtering")

class AuditTrailResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    audit_trail: List[AuditLogEntry] = Field(default=[], description="Audit trail entries")
    total_count: int = Field(..., description="Total number of audit entries")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# JWT Token Schemas
class TokenRefreshRequest(BaseModel):
    current_token: str = Field(..., description="Current JWT token")

class TokenRefreshResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    access_token: Optional[str] = Field(None, description="New access token")
    token_type: Optional[str] = Field(None, description="Token type")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Workflow Schemas
class WorkflowStep(BaseModel):
    role: UserRole = Field(..., description="Required role for this step")
    order: int = Field(..., description="Step order")
    required: bool = Field(..., description="Whether this step is required")

class ApprovalWorkflowData(BaseModel):
    id: int = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    approval_type: ApprovalType = Field(..., description="Approval type")
    steps: List[WorkflowStep] = Field(..., description="Workflow steps")
    auto_approve: bool = Field(..., description="Whether to auto-approve")
    require_all_approvers: bool = Field(..., description="Whether all approvers are required")
    escalation_timeout_hours: int = Field(..., description="Escalation timeout in hours")
    max_escalation_levels: int = Field(..., description="Maximum escalation levels")

class WorkflowResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    workflow: Optional[ApprovalWorkflowData] = Field(None, description="Workflow data")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# RBAC Schemas
class UserRoleData(BaseModel):
    user_id: int = Field(..., description="User ID")
    role: UserRole = Field(..., description="User role")
    permissions: List[str] = Field(..., description="User permissions")

class RBACResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    user_role: Optional[UserRoleData] = Field(None, description="User role data")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Dashboard Schemas
class ApprovalStats(BaseModel):
    total_pending: int = Field(..., description="Total pending approvals")
    high_priority: int = Field(..., description="High priority approvals")
    overdue: int = Field(..., description="Overdue approvals")
    my_approvals: int = Field(..., description="Approvals assigned to current user")

class ApprovalDashboardResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    stats: Optional[ApprovalStats] = Field(None, description="Approval statistics")
    recent_approvals: List[PendingApprovalSummary] = Field(default=[], description="Recent approvals")
    error: Optional[str] = Field(None, description="Error message if operation failed")

# Notification Schemas
class ApprovalNotification(BaseModel):
    approval_id: int = Field(..., description="Approval request ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    priority: str = Field(..., description="Notification priority")
    created_at: datetime = Field(..., description="Notification timestamp")
    read: bool = Field(..., description="Whether notification has been read")

class NotificationResponse(BaseModel):
    success: bool = Field(..., description="Operation success status")
    notifications: List[ApprovalNotification] = Field(default=[], description="List of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")
    error: Optional[str] = Field(None, description="Error message if operation failed")
