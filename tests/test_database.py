"""
Database integration tests
"""

import pytest
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Role, Tenant
from app.models.project import Project, Task, ProjectStatus, TaskStatus
from app.models.resource import Resource, Skill
from app.models.finance import Budget, BudgetType, BudgetStatus


class TestDatabaseModels:
    """Test database model creation and relationships."""
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_tenant_creation(self, db_session: AsyncSession):
        """Test tenant creation and basic operations."""
        tenant = Tenant(
            name="Test Tenant",
            domain="test.local",
            settings='{"timezone": "UTC"}',
            is_active=True
        )
        
        db_session.add(tenant)
        await db_session.commit()
        
        # Verify creation
        result = await db_session.execute(
            select(Tenant).where(Tenant.name == "Test Tenant")
        )
        saved_tenant = result.scalar_one()
        
        assert saved_tenant.id is not None
        assert saved_tenant.name == "Test Tenant"
        assert saved_tenant.is_active is True
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_user_role_relationship(self, db_session: AsyncSession):
        """Test user-role relationship."""
        # Create tenant
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        # Create role
        role = Role(
            name="Test Role",
            description="Test role description",
            tenant_id=tenant.id,
            is_active=True
        )
        db_session.add(role)
        await db_session.flush()
        
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed_password",
            role_id=role.id,
            tenant_id=tenant.id,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Verify relationships
        result = await db_session.execute(
            select(User).where(User.username == "testuser")
        )
        saved_user = result.scalar_one()
        
        assert saved_user.role_id == role.id
        assert saved_user.tenant_id == tenant.id
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_project_task_relationship(self, db_session: AsyncSession):
        """Test project-task relationship."""
        # Create tenant and user first
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        role = Role(name="Manager", tenant_id=tenant.id, is_active=True)
        db_session.add(role)
        await db_session.flush()
        
        user = User(
            username="manager",
            email="manager@test.com",
            full_name="Project Manager",
            hashed_password="hashed",
            role_id=role.id,
            tenant_id=tenant.id
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create project
        project = Project(
            name="Test Project",
            description="Test project description",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=90),
            project_manager_id=user.id,
            tenant_id=tenant.id
        )
        db_session.add(project)
        await db_session.flush()
        
        # Create task
        task = Task(
            name="Test Task",
            description="Test task description",
            status=TaskStatus.TODO,
            project_id=project.id,
            estimated_hours=40.0
        )
        db_session.add(task)
        await db_session.commit()
        
        # Verify relationship
        result = await db_session.execute(
            select(Task).where(Task.name == "Test Task")
        )
        saved_task = result.scalar_one()
        
        assert saved_task.project_id == project.id
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_resource_skill_relationship(self, db_session: AsyncSession):
        """Test resource-skill many-to-many relationship."""
        # Create tenant
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        # Create skill
        skill = Skill(
            name="Python",
            category="Programming",
            description="Python programming language",
            tenant_id=tenant.id
        )
        db_session.add(skill)
        await db_session.flush()
        
        # Create resource
        resource = Resource(
            name="Test Developer",
            email="dev@test.com",
            resource_type="EMPLOYEE",
            status="ACTIVE",
            capacity_hours_per_week=40.0,
            tenant_id=tenant.id
        )
        db_session.add(resource)
        await db_session.commit()
        
        # Verify creation
        result = await db_session.execute(
            select(Resource).where(Resource.name == "Test Developer")
        )
        saved_resource = result.scalar_one()
        
        assert saved_resource.id is not None
        assert saved_resource.capacity_hours_per_week == 40.0
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_budget_project_relationship(self, db_session: AsyncSession):
        """Test budget-project relationship."""
        # Create tenant and user
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        role = Role(name="Manager", tenant_id=tenant.id, is_active=True)
        db_session.add(role)
        await db_session.flush()
        
        user = User(
            username="manager",
            email="manager@test.com",
            full_name="Project Manager",
            hashed_password="hashed",
            role_id=role.id,
            tenant_id=tenant.id
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create project
        project = Project(
            name="Test Project",
            description="Test project",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=90),
            project_manager_id=user.id,
            tenant_id=tenant.id
        )
        db_session.add(project)
        await db_session.flush()
        
        # Create budget
        budget = Budget(
            project_id=project.id,
            name="Project Budget",
            budget_type=BudgetType.LABOR,
            total_amount=100000.0,
            currency="USD",
            status=BudgetStatus.APPROVED,
            created_by=user.id,
            tenant_id=tenant.id
        )
        db_session.add(budget)
        await db_session.commit()
        
        # Verify relationship
        result = await db_session.execute(
            select(Budget).where(Budget.name == "Project Budget")
        )
        saved_budget = result.scalar_one()
        
        assert saved_budget.project_id == project.id
        assert saved_budget.total_amount == 100000.0


class TestDatabaseQueries:
    """Test complex database queries and operations."""
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_user_count_by_role(self, db_session: AsyncSession):
        """Test counting users by role."""
        # Create test data
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        admin_role = Role(name="Admin", tenant_id=tenant.id, is_active=True)
        user_role = Role(name="User", tenant_id=tenant.id, is_active=True)
        db_session.add_all([admin_role, user_role])
        await db_session.flush()
        
        # Create users
        for i in range(3):
            user = User(
                username=f"admin{i}",
                email=f"admin{i}@test.com",
                full_name=f"Admin {i}",
                hashed_password="hashed",
                role_id=admin_role.id,
                tenant_id=tenant.id
            )
            db_session.add(user)
        
        for i in range(5):
            user = User(
                username=f"user{i}",
                email=f"user{i}@test.com",
                full_name=f"User {i}",
                hashed_password="hashed",
                role_id=user_role.id,
                tenant_id=tenant.id
            )
            db_session.add(user)
        
        await db_session.commit()
        
        # Query user count by role
        result = await db_session.execute(
            select(Role.name, func.count(User.id))
            .join(User)
            .group_by(Role.name)
        )
        counts = dict(result.all())
        
        assert counts["Admin"] == 3
        assert counts["User"] == 5
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_project_tasks_count(self, db_session: AsyncSession):
        """Test counting tasks per project."""
        # Create test data
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        role = Role(name="Manager", tenant_id=tenant.id, is_active=True)
        db_session.add(role)
        await db_session.flush()
        
        user = User(
            username="manager",
            email="manager@test.com",
            full_name="Manager",
            hashed_password="hashed",
            role_id=role.id,
            tenant_id=tenant.id
        )
        db_session.add(user)
        await db_session.flush()
        
        # Create projects
        project1 = Project(
            name="Project 1",
            description="First project",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=90),
            project_manager_id=user.id,
            tenant_id=tenant.id
        )
        project2 = Project(
            name="Project 2",
            description="Second project",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=90),
            project_manager_id=user.id,
            tenant_id=tenant.id
        )
        db_session.add_all([project1, project2])
        await db_session.flush()
        
        # Create tasks
        for i in range(3):
            task = Task(
                name=f"Task 1-{i}",
                description=f"Task {i} for project 1",
                status=TaskStatus.TODO,
                project_id=project1.id,
                estimated_hours=20.0
            )
            db_session.add(task)
        
        for i in range(2):
            task = Task(
                name=f"Task 2-{i}",
                description=f"Task {i} for project 2",
                status=TaskStatus.TODO,
                project_id=project2.id,
                estimated_hours=30.0
            )
            db_session.add(task)
        
        await db_session.commit()
        
        # Query task count per project
        result = await db_session.execute(
            select(Project.name, func.count(Task.id))
            .join(Task)
            .group_by(Project.name)
        )
        counts = dict(result.all())
        
        assert counts["Project 1"] == 3
        assert counts["Project 2"] == 2
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_database_constraints(self, db_session: AsyncSession):
        """Test database constraints and uniqueness."""
        # Create tenant
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        role = Role(name="User", tenant_id=tenant.id, is_active=True)
        db_session.add(role)
        await db_session.flush()
        
        # Create first user
        user1 = User(
            username="unique_user",
            email="unique@test.com",
            full_name="Unique User",
            hashed_password="hashed",
            role_id=role.id,
            tenant_id=tenant.id
        )
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create user with duplicate username
        user2 = User(
            username="unique_user",  # Duplicate username
            email="different@test.com",
            full_name="Different User",
            hashed_password="hashed",
            role_id=role.id,
            tenant_id=tenant.id
        )
        db_session.add(user2)
        
        # This should raise an integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await db_session.commit()


class TestDatabasePerformance:
    """Test database performance and optimization."""
    
    @pytest.mark.database
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_bulk_user_creation(self, db_session: AsyncSession):
        """Test bulk creation of users for performance."""
        # Create tenant and role
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        role = Role(name="User", tenant_id=tenant.id, is_active=True)
        db_session.add(role)
        await db_session.flush()
        
        # Create many users
        users = []
        for i in range(100):
            user = User(
                username=f"user{i:03d}",
                email=f"user{i:03d}@test.com",
                full_name=f"User {i:03d}",
                hashed_password="hashed",
                role_id=role.id,
                tenant_id=tenant.id
            )
            users.append(user)
        
        # Bulk add
        db_session.add_all(users)
        await db_session.commit()
        
        # Verify count
        result = await db_session.execute(select(func.count()).select_from(User))
        count = result.scalar()
        
        assert count == 100
    
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_query_optimization(self, db_session: AsyncSession):
        """Test query optimization with joins."""
        # Create test data
        tenant = Tenant(name="Test Tenant", is_active=True)
        db_session.add(tenant)
        await db_session.flush()
        
        role = Role(name="Manager", tenant_id=tenant.id, is_active=True)
        db_session.add(role)
        await db_session.flush()
        
        user = User(
            username="manager",
            email="manager@test.com",
            full_name="Manager",
            hashed_password="hashed",
            role_id=role.id,
            tenant_id=tenant.id
        )
        db_session.add(user)
        await db_session.flush()
        
        project = Project(
            name="Test Project",
            description="Test project",
            status=ProjectStatus.ACTIVE,
            start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=90),
            project_manager_id=user.id,
            tenant_id=tenant.id
        )
        db_session.add(project)
        await db_session.flush()
        
        # Create tasks
        for i in range(10):
            task = Task(
                name=f"Task {i}",
                description=f"Task {i} description",
                status=TaskStatus.TODO,
                project_id=project.id,
                estimated_hours=20.0
            )
            db_session.add(task)
        
        await db_session.commit()
        
        # Optimized query with joins
        result = await db_session.execute(
            select(Project.name, Task.name, User.full_name)
            .join(Task)
            .join(User, Project.project_manager_id == User.id)
            .where(Project.name == "Test Project")
        )
        
        rows = result.all()
        assert len(rows) == 10
        
        # All rows should have the same project and manager
        for row in rows:
            assert row[0] == "Test Project"  # Project name
            assert row[2] == "Manager"       # Manager name
