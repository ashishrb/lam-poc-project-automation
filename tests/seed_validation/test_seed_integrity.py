#!/usr/bin/env python3
"""
Seed Data Integrity Tests
Validates the quality and consistency of seeded data
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.user import User, Role, Tenant
from app.models.project import Project, ProjectStatus, ProjectPhase, Task, TaskStatus, TaskPriority
from app.models.resource import Resource, Skill
from app.models.status_update_policy import StatusUpdatePolicy, StatusUpdate, UpdateFrequency
from app.models.ai_draft import AIDraft, DraftType, DraftStatus
from app.models.document import Document, DocumentType
from app.models.audit import AuditLog, AuditAction
from app.models.finance import Budget


class TestSeedDataIntegrity:
    """Test class for seed data integrity validation"""
    
    @pytest.fixture
    async def db_session(self):
        """Database session fixture"""
        async with AsyncSessionLocal() as session:
            yield session
    
    @pytest.mark.asyncio
    async def test_tenant_creation(self, db_session: AsyncSession):
        """Test that tenant was created correctly"""
        result = await db_session.execute(
            select(Tenant).where(Tenant.name == "Demo Organization")
        )
        tenant = result.scalar_one_or_none()
        
        assert tenant is not None, "Tenant should exist"
        assert tenant.is_active is True, "Tenant should be active"
        assert "timezone" in tenant.settings, "Tenant should have timezone settings"
        assert "ai_autopublish" in tenant.settings, "Tenant should have AI settings"
    
    @pytest.mark.asyncio
    async def test_roles_creation(self, db_session: AsyncSession):
        """Test that all required roles were created"""
        expected_roles = ["ADMIN", "MANAGER", "DEVELOPER"]
        
        for role_name in expected_roles:
            result = await db_session.execute(
                select(Role).where(Role.name == role_name)
            )
            role = result.scalar_one_or_none()
            assert role is not None, f"Role {role_name} should exist"
            assert role.is_active is True, f"Role {role_name} should be active"
    
    @pytest.mark.asyncio
    async def test_user_creation(self, db_session: AsyncSession):
        """Test that users were created with correct counts"""
        # Count total users
        result = await db_session.execute(select(func.count()).select_from(User))
        total_users = result.scalar()
        
        assert total_users >= 23, f"Should have at least 23 users, got {total_users}"
        
        # Check admin user
        admin_result = await db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = admin_result.scalar_one_or_none()
        assert admin is not None, "Admin user should exist"
        assert admin.role == Role.ADMIN, "Admin should have ADMIN role"
        assert admin.email == "admin@demo.local", "Admin should have correct email"
        
        # Check manager user
        manager_result = await db_session.execute(
            select(User).where(User.username == "manager")
        )
        manager = manager_result.scalar_one_or_none()
        assert manager is not None, "Manager user should exist"
        assert manager.role == Role.MANAGER, "Manager should have MANAGER role"
        
        # Check developer users
        dev_count = 0
        for i in range(1, 21):
            result = await db_session.execute(
                select(User).where(User.username == f"dev{i}")
            )
            if result.scalar_one_or_none():
                dev_count += 1
        
        assert dev_count >= 20, f"Should have at least 20 developer users, got {dev_count}"
    
    @pytest.mark.asyncio
    async def test_skills_creation(self, db_session: AsyncSession):
        """Test that skills were created"""
        expected_skills = [
            "Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Redis",
            "Docker", "AWS", "DevOps", "UI/UX Design", "Project Management"
        ]
        
        for skill_name in expected_skills:
            result = await db_session.execute(
                select(Skill).where(Skill.name == skill_name)
            )
            skill = result.scalar_one_or_none()
            assert skill is not None, f"Skill {skill_name} should exist"
    
    @pytest.mark.asyncio
    async def test_projects_creation(self, db_session: AsyncSession):
        """Test that projects were created correctly"""
        expected_projects = ["ALPHA", "BETA"]
        
        for project_name in expected_projects:
            result = await db_session.execute(
                select(Project).where(Project.name == project_name)
            )
            project = result.scalar_one_or_none()
            assert project is not None, f"Project {project_name} should exist"
            
            # Check project dates
            assert project.start_date is not None, f"Project {project_name} should have start date"
            assert project.planned_end_date is not None, f"Project {project_name} should have end date"
            assert project.start_date < project.planned_end_date, f"Project {project_name} should have valid date range"
            
            # Check AI settings
            if project_name == "ALPHA":
                assert project.ai_autopublish is True, "ALPHA project should have AI autopublish enabled"
            assert project.ai_guardrails is True, f"Project {project_name} should have AI guardrails enabled"
    
    @pytest.mark.asyncio
    async def test_tasks_creation(self, db_session: AsyncSession):
        """Test that tasks were created with correct relationships"""
        # Count tasks
        result = await db_session.execute(select(func.count()).select_from(Task))
        total_tasks = result.scalar()
        
        assert total_tasks >= 12, f"Should have at least 12 tasks, got {total_tasks}"
        
        # Check ALPHA project tasks
        alpha_result = await db_session.execute(
            select(Task).join(Project).where(Project.name == "ALPHA")
        )
        alpha_tasks = alpha_result.scalars().all()
        
        assert len(alpha_tasks) >= 7, f"ALPHA project should have at least 7 tasks, got {len(alpha_tasks)}"
        
        # Check BETA project tasks
        beta_result = await db_session.execute(
            select(Task).join(Project).where(Project.name == "BETA")
        )
        beta_tasks = beta_result.scalars().all()
        
        assert len(beta_tasks) >= 5, f"BETA project should have at least 5 tasks, got {len(beta_tasks)}"
        
        # Check task dependencies (no cycles)
        for task in alpha_tasks + beta_tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    # Check that dependency exists and is not the same task
                    assert dep_id != task.id, "Task should not depend on itself"
                    
                    dep_result = await db_session.execute(
                        select(Task).where(Task.id == dep_id)
                    )
                    dep_task = dep_result.scalar_one_or_none()
                    assert dep_task is not None, f"Dependency task {dep_id} should exist"
    
    @pytest.mark.asyncio
    async def test_resource_profiles(self, db_session: AsyncSession):
        """Test that resource profiles were created correctly"""
        # Count resources
        result = await db_session.execute(select(func.count()).select_from(Resource))
        total_resources = result.scalar()
        
        assert total_resources >= 20, f"Should have at least 20 resource profiles, got {total_resources}"
        
        # Check resource assignments
        for username in [f"dev{i}" for i in range(1, 21)]:
            result = await db_session.execute(
                select(Resource).join(User).where(User.username == username)
            )
            resource = result.scalar_one_or_none()
            assert resource is not None, f"Resource profile for {username} should exist"
            assert resource.status == "active", f"Resource {username} should be active"
            assert resource.capacity_hours_per_week == 40.0, f"Resource {username} should have 40h/week capacity"
    
    @pytest.mark.asyncio
    async def test_status_update_policies(self, db_session: AsyncSession):
        """Test that status update policies were created"""
        result = await db_session.execute(select(func.count()).select_from(StatusUpdatePolicy))
        total_policies = result.scalar()
        
        assert total_policies >= 2, f"Should have at least 2 status update policies, got {total_policies}"
        
        # Check ALPHA project policy
        alpha_policy = await db_session.execute(
            select(StatusUpdatePolicy).join(Project).where(Project.name == "ALPHA")
        )
        alpha_policy = alpha_policy.scalar_one_or_none()
        assert alpha_policy is not None, "ALPHA project should have status update policy"
        assert alpha_policy.frequency == UpdateFrequency.DAILY, "ALPHA should have daily updates"
        
        # Check BETA project policy
        beta_policy = await db_session.execute(
            select(StatusUpdatePolicy).join(Project).where(Project.name == "BETA")
        )
        beta_policy = beta_policy.scalar_one_or_none()
        assert beta_policy is not None, "BETA project should have status update policy"
        assert beta_policy.frequency == UpdateFrequency.WEEKLY, "BETA should have weekly updates"
    
    @pytest.mark.asyncio
    async def test_documents_creation(self, db_session: AsyncSession):
        """Test that documents were created"""
        result = await db_session.execute(select(func.count()).select_from(Document))
        total_documents = result.scalar()
        
        assert total_documents >= 2, f"Should have at least 2 documents, got {total_documents}"
        
        # Check ALPHA project document
        alpha_doc = await db_session.execute(
            select(Document).join(Project).where(Project.name == "ALPHA")
        )
        alpha_doc = alpha_doc.scalar_one_or_none()
        assert alpha_doc is not None, "ALPHA project should have document"
        assert "charter" in alpha_doc.name.lower(), "ALPHA should have charter document"
        
        # Check BETA project document
        beta_doc = await db_session.execute(
            select(Document).join(Project).where(Project.name == "BETA")
        )
        beta_doc = beta_doc.scalar_one_or_none()
        assert beta_doc is not None, "BETA project should have document"
        assert "requirements" in beta_doc.name.lower(), "BETA should have requirements document"
    
    @pytest.mark.asyncio
    async def test_ai_drafts_creation(self, db_session: AsyncSession):
        """Test that AI drafts were created"""
        result = await db_session.execute(select(func.count()).select_from(AIDraft))
        total_drafts = result.scalar()
        
        assert total_drafts >= 5, f"Should have at least 5 AI drafts, got {total_drafts}"
        
        # Check draft types
        task_drafts = await db_session.execute(
            select(AIDraft).where(AIDraft.draft_type == DraftType.TASK)
        )
        task_drafts = task_drafts.scalars().all()
        
        assert len(task_drafts) >= 5, "Should have at least 5 task drafts"
        
        # Check draft metadata
        for draft in task_drafts:
            assert draft.metadata is not None, "Draft should have metadata"
            metadata = draft.metadata
            assert "project_id" in metadata, "Draft metadata should have project_id"
            assert "confidence" in metadata, "Draft metadata should have confidence score"
    
    @pytest.mark.asyncio
    async def test_audit_logs_creation(self, db_session: AsyncSession):
        """Test that audit logs were created"""
        result = await db_session.execute(select(func.count()).select_from(AuditLog))
        total_logs = result.scalar()
        
        assert total_logs >= 20, f"Should have at least 20 audit logs, got {total_logs}"
        
        # Check audit log actions
        actions = await db_session.execute(select(AuditLog.action).distinct())
        actions = actions.scalars().all()
        
        expected_actions = [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]
        for action in expected_actions:
            assert action in actions, f"Audit action {action} should exist"
    
    @pytest.mark.asyncio
    async def test_financial_data_creation(self, db_session: AsyncSession):
        """Test that financial data was created"""
        result = await db_session.execute(select(func.count()).select_from(Budget))
        total_budgets = result.scalar()
        
        assert total_budgets >= 2, f"Should have at least 2 budgets, got {total_budgets}"
        
        # Check project budgets
        for project_name in ["ALPHA", "BETA"]:
            budget_result = await db_session.execute(
                select(Budget).join(Project).where(Project.name == project_name)
            )
            budget = budget_result.scalar_one_or_none()
            assert budget is not None, f"Project {project_name} should have budget"
            assert budget.status == "approved", f"Budget for {project_name} should be approved"
            assert budget.currency == "USD", f"Budget for {project_name} should be in USD"
    
    @pytest.mark.asyncio
    async def test_data_quality_constraints(self, db_session: AsyncSession):
        """Test data quality constraints"""
        # Check no duplicate emails
        email_result = await db_session.execute(
            select(User.email, func.count(User.email))
            .group_by(User.email)
            .having(func.count(User.email) > 1)
        )
        duplicate_emails = email_result.all()
        assert len(duplicate_emails) == 0, f"Should have no duplicate emails: {duplicate_emails}"
        
        # Check no duplicate usernames
        username_result = await db_session.execute(
            select(User.username, func.count(User.username))
            .group_by(User.username)
            .having(func.count(User.username) > 1)
        )
        duplicate_usernames = username_result.all()
        assert len(duplicate_usernames) == 0, f"Should have no duplicate usernames: {duplicate_usernames}"
        
        # Check no duplicate project names
        project_result = await db_session.execute(
            select(Project.name, func.count(Project.name))
            .group_by(Project.name)
            .having(func.count(Project.name) > 1)
        )
        duplicate_projects = project_result.all()
        assert len(duplicate_projects) == 0, f"Should have no duplicate project names: {duplicate_projects}"
    
    @pytest.mark.asyncio
    async def test_relationship_integrity(self, db_session: AsyncSession):
        """Test that all relationships are properly established"""
        # Check user-role relationships
        users_without_roles = await db_session.execute(
            select(User).where(User.role.is_(None))
        )
        users_without_roles = users_without_roles.scalars().all()
        assert len(users_without_roles) == 0, "All users should have roles assigned"
        
        # Check project-manager relationships
        projects_without_manager = await db_session.execute(
            select(Project).where(Project.project_manager_id.is_(None))
        )
        projects_without_manager = projects_without_manager.scalars().all()
        assert len(projects_without_manager) == 0, "All projects should have managers assigned"
        
        # Check task-project relationships
        tasks_without_project = await db_session.execute(
            select(Task).where(Task.project_id.is_(None))
        )
        tasks_without_project = tasks_without_project.scalars().all()
        assert len(tasks_without_project) == 0, "All tasks should have projects assigned"
    
    @pytest.mark.asyncio
    async def test_date_constraints(self, db_session: AsyncSession):
        """Test date-related constraints"""
        # Check project date ranges
        projects = await db_session.execute(select(Project))
        projects = projects.scalars().all()
        
        for project in projects:
            assert project.start_date < project.planned_end_date, f"Project {project.name} should have valid date range"
            
            # Check tasks don't have due dates beyond project end
            project_tasks = await db_session.execute(
                select(Task).where(Task.project_id == project.id)
            )
            project_tasks = project_tasks.scalars().all()
            
            for task in project_tasks:
                if task.due_date:
                    assert task.due_date <= project.planned_end_date, f"Task {task.name} due date should not exceed project end date"
        
        # Check audit log dates are reasonable
        audit_logs = await db_session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
        )
        audit_logs = audit_logs.scalars().all()
        
        for log in audit_logs:
            assert log.created_at <= datetime.now(), "Audit log should not have future dates"
            assert log.created_at >= datetime.now() - timedelta(days=365), "Audit log should not be too old"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
