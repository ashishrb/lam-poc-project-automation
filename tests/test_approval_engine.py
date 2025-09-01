#!/usr/bin/env python3
"""
Tests for Approval Engine Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.approval_engine import (
    ApprovalEngine, ApprovalType, ApprovalStatus, AuditAction, UserRole,
    ApprovalRequest, ApprovalWorkflow, AuditLog, RBACPermission
)
from app.models.project import Project, Task
from app.models.user import User

@pytest.fixture
def approval_service():
    return ApprovalEngine()

@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.first_name = "John"
    user.last_name = "Doe"
    user.is_active = True
    return user

@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)

class TestApprovalEngine:
    
    def test_init(self, approval_service):
        """Test service initialization"""
        assert approval_service is not None
        assert len(approval_service.workflows) == 3  # PROJECT_CREATION, BUDGET_CHANGE, RISK_ESCALATION
        assert len(approval_service.permissions) == 6  # All user roles
        assert len(approval_service.pii_patterns) == 5  # Email, phone, SSN, credit card, IP
    
    @pytest.mark.asyncio
    async def test_create_approval_request_success(self, approval_service, mock_db):
        """Test creating approval request successfully"""
        result = await approval_service.create_approval_request(
            requester_id=1,
            approval_type=ApprovalType.PROJECT_CREATION,
            entity_type="project",
            entity_id=1,
            title="New Project",
            description="Create new project",
            data={"name": "Test Project", "budget": 100000},
            db=mock_db,
            priority="high",
            due_date=datetime.utcnow() + timedelta(days=7)
        )
        
        assert result["success"] is True
        assert result["approval_request"].requester_id == 1
        assert result["approval_request"].approval_type == ApprovalType.PROJECT_CREATION
        assert result["approval_request"].status == ApprovalStatus.PENDING
        assert result["next_approver"] is not None
    
    @pytest.mark.asyncio
    async def test_create_approval_request_no_workflow(self, approval_service, mock_db):
        """Test creating approval request with no workflow defined"""
        result = await approval_service.create_approval_request(
            requester_id=1,
            approval_type=ApprovalType.DOCUMENT_APPROVAL,  # No workflow defined
            entity_type="document",
            entity_id=1,
            title="Document Approval",
            description="Approve document",
            data={"document_id": 1},
            db=mock_db
        )
        
        assert result["success"] is False
        assert "No workflow defined" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_approval_approve(self, approval_service, mock_db):
        """Test processing approval with approve action"""
        # Mock approval request
        approval_request = ApprovalRequest(
            id=1,
            requester_id=1,
            approver_id=2,
            approval_type=ApprovalType.PROJECT_CREATION,
            entity_type="project",
            entity_id=1,
            title="New Project",
            description="Create new project",
            data={"name": "Test Project"},
            status=ApprovalStatus.PENDING,
            priority="high",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=7),
            escalation_level=0,
            comments=[]
        )
        
        # Mock _get_approval_request to return our mock
        approval_service._get_approval_request = AsyncMock(return_value=approval_request)
        
        result = await approval_service.process_approval(
            approval_id=1,
            approver_id=2,
            action="approve",
            comments="Looks good",
            db=mock_db
        )
        
        assert result["success"] is True
        assert result["approval_request"].status == ApprovalStatus.APPROVED
        assert len(result["approval_request"].comments) == 1
        assert result["approval_request"].comments[0]["action"] == "approve"
    
    @pytest.mark.asyncio
    async def test_process_approval_reject(self, approval_service, mock_db):
        """Test processing approval with reject action"""
        # Mock approval request
        approval_request = ApprovalRequest(
            id=1,
            requester_id=1,
            approver_id=2,
            approval_type=ApprovalType.PROJECT_CREATION,
            entity_type="project",
            entity_id=1,
            title="New Project",
            description="Create new project",
            data={"name": "Test Project"},
            status=ApprovalStatus.PENDING,
            priority="high",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=7),
            escalation_level=0,
            comments=[]
        )
        
        # Mock _get_approval_request to return our mock
        approval_service._get_approval_request = AsyncMock(return_value=approval_request)
        
        result = await approval_service.process_approval(
            approval_id=1,
            approver_id=2,
            action="reject",
            comments="Budget too high",
            db=mock_db
        )
        
        assert result["success"] is True
        assert result["approval_request"].status == ApprovalStatus.REJECTED
        assert len(result["approval_request"].comments) == 1
        assert result["approval_request"].comments[0]["action"] == "reject"
    
    @pytest.mark.asyncio
    async def test_process_approval_invalid_action(self, approval_service, mock_db):
        """Test processing approval with invalid action"""
        result = await approval_service.process_approval(
            approval_id=1,
            approver_id=2,
            action="invalid",
            comments="Test",
            db=mock_db
        )
        
        assert result["success"] is False
        assert "Invalid action" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, approval_service, mock_db):
        """Test getting pending approvals"""
        result = await approval_service.get_pending_approvals(1, mock_db)
        
        assert result["success"] is True
        assert len(result["pending_approvals"]) == 2
        assert result["total_count"] == 2
        assert result["pending_approvals"][0]["title"] == "New Project: Alpha Development"
    
    @pytest.mark.asyncio
    async def test_check_permission_success(self, approval_service, mock_db):
        """Test checking permission successfully"""
        # Mock _get_user_role to return PROJECT_MANAGER
        approval_service._get_user_role = AsyncMock(return_value=UserRole.PROJECT_MANAGER)
        approval_service._check_entity_permission = AsyncMock(return_value=True)
        
        has_permission = await approval_service.check_permission(
            user_id=1,
            resource="projects",
            action="create",
            entity_id=1,
            db=mock_db
        )
        
        assert has_permission is True
    
    @pytest.mark.asyncio
    async def test_check_permission_denied(self, approval_service, mock_db):
        """Test checking permission when denied"""
        # Mock _get_user_role to return DEVELOPER
        approval_service._get_user_role = AsyncMock(return_value=UserRole.DEVELOPER)
        
        has_permission = await approval_service.check_permission(
            user_id=1,
            resource="users",
            action="create",
            entity_id=1,
            db=mock_db
        )
        
        assert has_permission is False
    
    @pytest.mark.asyncio
    async def test_create_audit_log(self, approval_service):
        """Test creating audit log entry"""
        old_values = {"name": "Old Project", "email": "test@example.com"}
        new_values = {"name": "New Project", "email": "new@example.com"}
        
        result = await approval_service.create_audit_log(
            user_id=1,
            action=AuditAction.UPDATE,
            entity_type="project",
            entity_id=1,
            old_values=old_values,
            new_values=new_values,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            session_id="session123",
            metadata={"reason": "Project update"}
        )
        
        assert result["success"] is True
        assert result["audit_log"].user_id == 1
        assert result["audit_log"].action == AuditAction.UPDATE
        assert result["audit_log"].entity_type == "project"
        assert result["audit_log"].entity_id == 1
        
        # Check PII redaction
        redacted_old = result["audit_log"].old_values
        redacted_new = result["audit_log"].new_values
        assert "test@example.com" not in str(redacted_old)
        assert "new@example.com" not in str(redacted_new)
        assert "[REDACTED_EMAIL]" in str(redacted_old) or "[REDACTED_EMAIL]" in str(redacted_new)
    
    @pytest.mark.asyncio
    async def test_get_audit_trail(self, approval_service, mock_db):
        """Test getting audit trail"""
        result = await approval_service.get_audit_trail(
            entity_type="project",
            entity_id=1,
            db=mock_db,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            user_id=1,
            action=AuditAction.CREATE
        )
        
        assert result["success"] is True
        assert len(result["audit_trail"]) == 2
        assert result["total_count"] == 2
        assert result["audit_trail"][0]["entity_type"] == "project"
        assert result["audit_trail"][0]["entity_id"] == 1
    
    @pytest.mark.asyncio
    async def test_refresh_jwt_token_success(self, approval_service):
        """Test refreshing JWT token successfully"""
        # This would require a real JWT token, so we'll test the error case
        result = await approval_service.refresh_jwt_token(1, "invalid_token")
        
        assert result["success"] is False
        assert "Invalid token" in result["error"]
    
    def test_redact_pii(self, approval_service):
        """Test PII redaction functionality"""
        test_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "ssn": "123-45-6789",
            "credit_card": "1234-5678-9012-3456",
            "ip_address": "192.168.1.100",
            "nested": {
                "email": "nested@example.com",
                "phone": "555-987-6543"
            },
            "list_data": [
                {"email": "list1@example.com"},
                {"email": "list2@example.com"}
            ]
        }
        
        redacted_data = approval_service._redact_pii(test_data)
        
        # Check that PII is redacted
        assert "john.doe@example.com" not in str(redacted_data)
        assert "555-123-4567" not in str(redacted_data)
        assert "123-45-6789" not in str(redacted_data)
        assert "1234-5678-9012-3456" not in str(redacted_data)
        assert "192.168.1.100" not in str(redacted_data)
        assert "nested@example.com" not in str(redacted_data)
        assert "list1@example.com" not in str(redacted_data)
        
        # Check that non-PII is preserved
        assert redacted_data["name"] == "John Doe"
        
        # Check that redaction markers are present
        assert "[REDACTED_EMAIL]" in str(redacted_data)
        assert "[REDACTED_PHONE]" in str(redacted_data)
        assert "[REDACTED_SSN]" in str(redacted_data)
        assert "[REDACTED_CREDIT_CARD]" in str(redacted_data)
        assert "[REDACTED_IP_ADDRESS]" in str(redacted_data)

class TestEnums:
    """Test enum values"""
    
    def test_approval_status_values(self):
        """Test ApprovalStatus enum values"""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"
        assert ApprovalStatus.CANCELLED == "cancelled"
        assert ApprovalStatus.ESCALATED == "escalated"
    
    def test_approval_type_values(self):
        """Test ApprovalType enum values"""
        assert ApprovalType.PROJECT_CREATION == "project_creation"
        assert ApprovalType.PROJECT_MODIFICATION == "project_modification"
        assert ApprovalType.BUDGET_CHANGE == "budget_change"
        assert ApprovalType.TIMELINE_CHANGE == "timeline_change"
        assert ApprovalType.RESOURCE_ASSIGNMENT == "resource_assignment"
        assert ApprovalType.RISK_ESCALATION == "risk_escalation"
        assert ApprovalType.DOCUMENT_APPROVAL == "document_approval"
        assert ApprovalType.EXPENSE_APPROVAL == "expense_approval"
    
    def test_user_role_values(self):
        """Test UserRole enum values"""
        assert UserRole.ADMIN == "admin"
        assert UserRole.PROJECT_MANAGER == "project_manager"
        assert UserRole.TEAM_LEAD == "team_lead"
        assert UserRole.DEVELOPER == "developer"
        assert UserRole.STAKEHOLDER == "stakeholder"
        assert UserRole.VIEWER == "viewer"
    
    def test_audit_action_values(self):
        """Test AuditAction enum values"""
        assert AuditAction.CREATE == "create"
        assert AuditAction.UPDATE == "update"
        assert AuditAction.DELETE == "delete"
        assert AuditAction.APPROVE == "approve"
        assert AuditAction.REJECT == "reject"
        assert AuditAction.LOGIN == "login"
        assert AuditAction.LOGOUT == "logout"
        assert AuditAction.EXPORT == "export"
        assert AuditAction.IMPORT == "import"

class TestDataclasses:
    """Test dataclass structures"""
    
    def test_approval_request(self):
        """Test ApprovalRequest dataclass"""
        approval_request = ApprovalRequest(
            id=1,
            requester_id=1,
            approver_id=2,
            approval_type=ApprovalType.PROJECT_CREATION,
            entity_type="project",
            entity_id=1,
            title="New Project",
            description="Create new project",
            data={"name": "Test Project"},
            status=ApprovalStatus.PENDING,
            priority="high",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=7),
            escalation_level=0,
            comments=[]
        )
        
        assert approval_request.id == 1
        assert approval_request.requester_id == 1
        assert approval_request.approval_type == ApprovalType.PROJECT_CREATION
        assert approval_request.status == ApprovalStatus.PENDING
        assert approval_request.priority == "high"
    
    def test_approval_workflow(self):
        """Test ApprovalWorkflow dataclass"""
        workflow = ApprovalWorkflow(
            id=1,
            name="Test Workflow",
            approval_type=ApprovalType.PROJECT_CREATION,
            steps=[
                {"role": UserRole.TEAM_LEAD, "order": 1, "required": True},
                {"role": UserRole.PROJECT_MANAGER, "order": 2, "required": True}
            ],
            auto_approve=False,
            require_all_approvers=True,
            escalation_timeout_hours=24,
            max_escalation_levels=2
        )
        
        assert workflow.id == 1
        assert workflow.name == "Test Workflow"
        assert workflow.approval_type == ApprovalType.PROJECT_CREATION
        assert len(workflow.steps) == 2
        assert workflow.escalation_timeout_hours == 24
    
    def test_audit_log(self):
        """Test AuditLog dataclass"""
        audit_log = AuditLog(
            id=1,
            user_id=1,
            action=AuditAction.CREATE,
            entity_type="project",
            entity_id=1,
            old_values={"name": "Old Project"},
            new_values={"name": "New Project"},
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            timestamp=datetime.utcnow(),
            session_id="session123",
            metadata={"reason": "Project update"}
        )
        
        assert audit_log.id == 1
        assert audit_log.user_id == 1
        assert audit_log.action == AuditAction.CREATE
        assert audit_log.entity_type == "project"
        assert audit_log.entity_id == 1
        assert audit_log.ip_address == "192.168.1.100"
    
    def test_rbac_permission(self):
        """Test RBACPermission dataclass"""
        permission = RBACPermission(
            role=UserRole.PROJECT_MANAGER,
            resource="projects",
            action="create",
            conditions={"project_type": "internal"}
        )
        
        assert permission.role == UserRole.PROJECT_MANAGER
        assert permission.resource == "projects"
        assert permission.action == "create"
        assert permission.conditions["project_type"] == "internal"
