#!/usr/bin/env python3
"""
Approval Engine API endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.approval_engine import ApprovalEngine, ApprovalType, ApprovalStatus, AuditAction, UserRole
from app.schemas.approval import (
    ApprovalRequestCreate, ApprovalRequestResponse, ApprovalProcessRequest,
    ApprovalProcessResponse, PendingApprovalsResponse, PermissionCheckRequest,
    PermissionCheckResponse, AuditTrailRequest, AuditTrailResponse,
    TokenRefreshRequest, TokenRefreshResponse, WorkflowResponse,
    RBACResponse, ApprovalDashboardResponse, NotificationResponse
)

router = APIRouter()
approval_service = ApprovalEngine()

@router.post("/approvals/create", response_model=ApprovalRequestResponse)
async def create_approval_request(
    request: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Create a new approval request"""
    result = await approval_service.create_approval_request(
        requester_id=current_user_id,
        approval_type=request.approval_type,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        title=request.title,
        description=request.description,
        data=request.data,
        db=db,
        priority=request.priority,
        due_date=request.due_date
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ApprovalRequestResponse(**result)

@router.post("/approvals/{approval_id}/process", response_model=ApprovalProcessResponse)
async def process_approval(
    approval_id: int,
    request: ApprovalProcessRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Process an approval (approve/reject)"""
    result = await approval_service.process_approval(
        approval_id=approval_id,
        approver_id=current_user_id,
        action=request.action,
        comments=request.comments,
        db=db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ApprovalProcessResponse(**result)

@router.get("/approvals/pending", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Get pending approvals for the current user"""
    result = await approval_service.get_pending_approvals(current_user_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return PendingApprovalsResponse(**result)

@router.post("/permissions/check", response_model=PermissionCheckResponse)
async def check_permission(
    request: PermissionCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Check if user has permission for a resource and action"""
    has_permission = await approval_service.check_permission(
        user_id=current_user_id,
        resource=request.resource,
        action=request.action,
        db=db,
        entity_id=request.entity_id
    )
    
    # Get user role for response
    user_role = await approval_service._get_user_role(current_user_id, db)
    
    return PermissionCheckResponse(
        success=True,
        has_permission=has_permission,
        user_role=user_role.value if user_role else None
    )

@router.post("/audit/trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    request: AuditTrailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Get audit trail for an entity"""
    result = await approval_service.get_audit_trail(
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        db=db,
        start_date=request.start_date,
        end_date=request.end_date,
        user_id=request.user_id,
        action=request.action
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return AuditTrailResponse(**result)

@router.post("/audit/log")
async def create_audit_log(
    action: AuditAction,
    entity_type: str,
    entity_id: int,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Create an audit log entry"""
    # Get client information
    ip_address = request.client.host if request else "unknown"
    user_agent = request.headers.get("user-agent", "unknown") if request else "unknown"
    session_id = request.headers.get("x-session-id", "unknown") if request else "unknown"
    
    result = await approval_service.create_audit_log(
        user_id=current_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        user_agent=user_agent,
        session_id=session_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/auth/refresh", response_model=TokenRefreshResponse)
async def refresh_jwt_token(request: TokenRefreshRequest):
    """Refresh JWT token"""
    # In real implementation, get user_id from current token
    user_id = 1
    
    result = await approval_service.refresh_jwt_token(user_id, request.current_token)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return TokenRefreshResponse(**result)

@router.get("/workflows/{approval_type}", response_model=WorkflowResponse)
async def get_approval_workflow(approval_type: ApprovalType):
    """Get approval workflow for a specific type"""
    workflow = approval_service.workflows.get(approval_type)
    
    if not workflow:
        raise HTTPException(status_code=404, detail=f"No workflow found for {approval_type.value}")
    
    return WorkflowResponse(
        success=True,
        workflow={
            "id": workflow.id,
            "name": workflow.name,
            "approval_type": workflow.approval_type,
            "steps": workflow.steps,
            "auto_approve": workflow.auto_approve,
            "require_all_approvers": workflow.require_all_approvers,
            "escalation_timeout_hours": workflow.escalation_timeout_hours,
            "max_escalation_levels": workflow.max_escalation_levels
        }
    )

@router.get("/rbac/user/{user_id}", response_model=RBACResponse)
async def get_user_role(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user role and permissions"""
    user_role = await approval_service._get_user_role(user_id, db)
    
    if not user_role:
        raise HTTPException(status_code=404, detail="User role not found")
    
    # Get permissions for the role
    permissions = approval_service.permissions.get(user_role, {})
    all_permissions = []
    for resource, actions in permissions.items():
        for action in actions:
            all_permissions.append(f"{resource}:{action}")
    
    return RBACResponse(
        success=True,
        user_role={
            "user_id": user_id,
            "role": user_role,
            "permissions": all_permissions
        }
    )

@router.get("/dashboard", response_model=ApprovalDashboardResponse)
async def get_approval_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Get approval dashboard data"""
    # Get pending approvals
    pending_result = await approval_service.get_pending_approvals(current_user_id, db)
    
    if not pending_result["success"]:
        raise HTTPException(status_code=400, detail=pending_result["error"])
    
    pending_approvals = pending_result["pending_approvals"]
    
    # Calculate statistics
    total_pending = len(pending_approvals)
    high_priority = len([a for a in pending_approvals if a["priority"] == "high"])
    overdue = len([a for a in pending_approvals if a.get("due_date") and a["due_date"] < datetime.utcnow()])
    my_approvals = len([a for a in pending_approvals if a.get("approver_id") == current_user_id])
    
    return ApprovalDashboardResponse(
        success=True,
        stats={
            "total_pending": total_pending,
            "high_priority": high_priority,
            "overdue": overdue,
            "my_approvals": my_approvals
        },
        recent_approvals=pending_approvals[:5]  # Show last 5 approvals
    )

@router.get("/notifications", response_model=NotificationResponse)
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Get notifications for the current user"""
    # In real implementation, query database for notifications
    # For now, return mock data
    notifications = [
        {
            "approval_id": 1,
            "title": "New approval request",
            "message": "You have a new approval request for Project Alpha",
            "priority": "high",
            "created_at": datetime.utcnow() - timedelta(hours=1),
            "read": False
        },
        {
            "approval_id": 2,
            "title": "Approval overdue",
            "message": "Approval request for Budget Change is overdue",
            "priority": "critical",
            "created_at": datetime.utcnow() - timedelta(hours=3),
            "read": True
        }
    ]
    
    unread_count = len([n for n in notifications if not n["read"]])
    
    return NotificationResponse(
        success=True,
        notifications=notifications,
        unread_count=unread_count
    )

@router.get("/approvals/{approval_id}")
async def get_approval_details(
    approval_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about an approval request"""
    # In real implementation, query database
    # For now, return mock data
    approval_details = {
        "id": approval_id,
        "title": "New Project: Alpha Development",
        "description": "Request to create new project for Alpha product development",
        "approval_type": ApprovalType.PROJECT_CREATION.value,
        "entity_type": "project",
        "entity_id": 1,
        "status": ApprovalStatus.PENDING.value,
        "priority": "high",
        "created_at": datetime.utcnow() - timedelta(hours=2),
        "due_date": datetime.utcnow() + timedelta(hours=22),
        "requester": "John Doe",
        "current_approver": "Jane Smith",
        "escalation_level": 0,
        "comments": [
            {
                "user": "John Doe",
                "action": "created",
                "comments": "Requesting approval for new project",
                "timestamp": datetime.utcnow() - timedelta(hours=2)
            }
        ]
    }
    
    return {"success": True, "approval": approval_details}

@router.get("/approvals")
async def get_all_approvals(
    status: Optional[ApprovalStatus] = Query(None, description="Filter by status"),
    approval_type: Optional[ApprovalType] = Query(None, description="Filter by approval type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # In real implementation, get from JWT token
):
    """Get all approvals with optional filters"""
    # In real implementation, query database with filters
    # For now, return mock data
    all_approvals = [
        {
            "id": 1,
            "title": "New Project: Alpha Development",
            "approval_type": ApprovalType.PROJECT_CREATION.value,
            "status": ApprovalStatus.PENDING.value,
            "priority": "high",
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "requester": "John Doe"
        },
        {
            "id": 2,
            "title": "Budget Increase: Beta Project",
            "approval_type": ApprovalType.BUDGET_CHANGE.value,
            "status": ApprovalStatus.APPROVED.value,
            "priority": "medium",
            "created_at": datetime.utcnow() - timedelta(days=1),
            "requester": "Jane Smith"
        }
    ]
    
    # Apply filters
    if status:
        all_approvals = [a for a in all_approvals if a["status"] == status.value]
    if approval_type:
        all_approvals = [a for a in all_approvals if a["approval_type"] == approval_type.value]
    if priority:
        all_approvals = [a for a in all_approvals if a["priority"] == priority]
    
    return {
        "success": True,
        "approvals": all_approvals,
        "total_count": len(all_approvals)
    }
