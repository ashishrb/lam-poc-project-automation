#!/usr/bin/env python3
"""
Comprehensive Seed Script for PPM+AI Database
Creates deterministic, repeatable demo data for testing and development
"""

import asyncio
import json
import os
import random
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from faker import Faker

from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User, Role, Tenant
from app.models.project import Project, ProjectStatus, ProjectPhase, Task, TaskStatus, TaskPriority
from app.models.resource import Resource, Skill, Timesheet
from app.models.status_update_policy import StatusUpdatePolicy, StatusUpdate, UpdateFrequency
from app.models.ai_draft import AIDraft, DraftType, DraftStatus
from app.models.document import Document, DocumentType
from app.models.audit import AuditLog, AuditAction
from app.models.finance import Budget, Actual
from app.core.config import settings

# Set deterministic randomness for repeatable data
random.seed(42)
fake = Faker()
fake.seed_instance(42)

# Configuration
BATCH_SIZE = 100
IST_TIMEZONE = "Asia/Kolkata"


class PPMSeedData:
    """Main class for seeding PPM+AI database"""
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
        self.tenant_id: Optional[int] = None
        self.users: Dict[str, int] = {}
        self.projects: Dict[str, int] = {}
        self.resources: Dict[str, int] = {}
        self.skills: Dict[str, int] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = AsyncSessionLocal()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def seed_all(self):
        """Seed all data in the correct order"""
        print("🚀 Starting comprehensive PPM+AI database seeding...")
        
        try:
            # Initialize database
            await init_db()
            
            # Seed in dependency order
            await self._seed_tenants()
            await self._seed_roles()
            await self._seed_users()
            await self._seed_skills()
            await self._seed_resources()
            await self._seed_projects()
            await self._seed_tasks()
            await self._seed_status_update_policies()
            await self._seed_status_updates()
            await self._seed_documents()
            await self._seed_ai_drafts()
            await self._seed_audit_logs()
            await self._seed_financial_data()
            
            print("✅ All data seeded successfully!")
            await self._print_summary()
            
        except Exception as e:
            print(f"❌ Error during seeding: {e}")
            await self.session.rollback()
            raise
    
    async def _seed_tenants(self):
        """Seed tenant data"""
        print("📋 Seeding tenants...")
        
        # Check if tenant exists
        result = await self.session.execute(
            select(Tenant).where(Tenant.name == "Demo Organization")
        )
        existing_tenant = result.scalar_one_or_none()
        
        if existing_tenant:
            self.tenant_id = existing_tenant.id
            print(f"✅ Using existing tenant: {existing_tenant.name}")
            return
        
        # Create new tenant
        tenant = Tenant(
            name="Demo Organization",
            description="Demo organization for AI-First PPM system",
            domain="demo.local",
            settings=json.dumps({
                "timezone": IST_TIMEZONE,
                "ai_autopublish": True,
                "ai_guardrails": True
            }),
            is_active=True
        )
        
        self.session.add(tenant)
        await self.session.flush()
        self.tenant_id = tenant.id
        
        print(f"✅ Created tenant: {tenant.name} (ID: {tenant.id})")
    
    async def _seed_roles(self):
        """Seed role data"""
        print("👥 Seeding roles...")
        
        roles_data = [
            {"name": "ADMIN", "description": "System Administrator", "permissions": {"*": ["*"]}},
            {"name": "MANAGER", "description": "Project Manager", "permissions": {"projects": ["*"], "tasks": ["*"], "resources": ["read"]}},
            {"name": "DEVELOPER", "description": "Team Developer", "permissions": {"tasks": ["read", "update"], "timesheets": ["*"]}}
        ]
        
        for role_data in roles_data:
            result = await self.session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            if not result.scalar_one_or_none():
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    permissions=json.dumps(role_data["permissions"]),
                    tenant_id=self.tenant_id,
                    is_active=True
                )
                self.session.add(role)
        
        await self.session.commit()
        print("✅ Roles created")
    
    async def _seed_users(self):
        """Seed user data with realistic profiles"""
        print("👤 Seeding users...")
        
        # Get roles
        admin_role = await self.session.execute(
            select(Role).where(Role.name == "ADMIN")
        )
        admin_role = admin_role.scalar_one()
        
        manager_role = await self.session.execute(
            select(Role).where(Role.name == "MANAGER")
        )
        manager_role = manager_role.scalar_one()
        
        dev_role = await self.session.execute(
            select(Role).where(Role.name == "DEVELOPER")
        )
        dev_role = dev_role.scalar_one()
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@demo.local",
            full_name="System Administrator",
            role=Role.ADMIN,
            tenant_id=self.tenant_id,
            is_active=True,
            created_at=datetime.now()
        )
        admin_user.set_password("admin123")
        self.session.add(admin_user)
        await self.session.flush()
        self.users["admin"] = admin_user.id
        
        # Create manager user
        manager_user = User(
            username="manager",
            email="manager@demo.local",
            full_name="Sarah Johnson",
            role=Role.MANAGER,
            tenant_id=self.tenant_id,
            is_active=True,
            created_at=datetime.now()
        )
        manager_user.set_password("manager123")
        self.session.add(manager_user)
        await self.session.flush()
        self.users["manager"] = manager_user.id
        
        # Create 20 developer users
        dev_names = [
            "John Smith", "Jane Doe", "Mike Chen", "Emily Davis", "Alex Brown",
            "Lisa Wang", "David Lee", "Rachel Green", "Tom Wilson", "Maria Garcia",
            "James Taylor", "Anna Kim", "Chris Martinez", "Jennifer White", "Ryan Thompson",
            "Amanda Clark", "Kevin Rodriguez", "Nicole Lewis", "Brian Hall", "Stephanie Allen"
        ]
        
        for i, name in enumerate(dev_names):
            username = f"dev{i+1}"
            email = f"{username}@demo.local"
            
            dev_user = User(
                username=username,
                email=email,
                full_name=name,
                role=Role.DEVELOPER,
                tenant_id=self.tenant_id,
                is_active=True,
                created_at=datetime.now()
            )
            dev_user.set_password("dev123")
            self.session.add(dev_user)
            await self.session.flush()
            self.users[username] = dev_user.id
        
        await self.session.commit()
        print(f"✅ Created {len(self.users)} users")
    
    async def _seed_skills(self):
        """Seed skill data"""
        print("🛠️ Seeding skills...")
        
        skills_data = [
            "Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Redis",
            "Docker", "AWS", "DevOps", "UI/UX Design", "Project Management",
            "Data Analysis", "Machine Learning", "API Development", "Testing"
        ]
        
        for skill_name in skills_data:
            result = await self.session.execute(
                select(Skill).where(Skill.name == skill_name)
            )
            if not result.scalar_one_or_none():
                skill = Skill(
                    name=skill_name,
                    description=f"Expertise in {skill_name}",
                    category="Technical",
                    tenant_id=self.tenant_id
                )
                self.session.add(skill)
                await self.session.flush()
                self.skills[skill_name] = skill.id
        
        await self.session.commit()
        print(f"✅ Created {len(self.skills)} skills")
    
    async def _seed_resources(self):
        """Seed resource profiles"""
        print("👷 Seeding resource profiles...")
        
        # Get skills for assignment
        python_skill = await self.session.execute(
            select(Skill).where(Skill.name == "Python")
        )
        python_skill = python_skill.scalar_one()
        
        # Create resource profiles for developers
        for username, user_id in self.users.items():
            if username.startswith("dev"):
                # Assign random skills
                user_skills = random.sample(list(self.skills.keys()), random.randint(2, 5))
                
                resource = Resource(
                    user_id=user_id,
                    resource_type="employee",
                    status="active",
                    hourly_rate=random.uniform(50.0, 120.0),
                    capacity_hours_per_week=40.0,
                    skills=json.dumps(user_skills),
                    tenant_id=self.tenant_id
                )
                self.session.add(resource)
                await self.session.flush()
                self.resources[username] = resource.id
        
        await self.session.commit()
        print(f"✅ Created {len(self.resources)} resource profiles")
    
    async def _seed_projects(self):
        """Seed project data"""
        print("📊 Seeding projects...")
        
        projects_data = [
            {
                "name": "ALPHA",
                "description": "AI-Powered Project Management Platform",
                "status": ProjectStatus.ACTIVE,
                "phase": ProjectPhase.EXECUTION,
                "start_date": datetime.now() - timedelta(days=30),
                "planned_end_date": datetime.now() + timedelta(days=90),
                "ai_autopublish": True,
                "ai_guardrails": True
            },
            {
                "name": "BETA",
                "description": "Machine Learning Model Deployment System",
                "status": ProjectStatus.PLANNING,
                "phase": ProjectPhase.PLANNING,
                "start_date": datetime.now() + timedelta(days=15),
                "planned_end_date": datetime.now() + timedelta(days=120),
                "ai_autopublish": False,
                "ai_guardrails": True
            }
        ]
        
        for project_data in projects_data:
            project = Project(
                **project_data,
                project_manager_id=self.users["manager"],
                tenant_id=self.tenant_id,
                created_at=datetime.now()
            )
            self.session.add(project)
            await self.session.flush()
            self.projects[project_data["name"]] = project.id
        
        await self.session.commit()
        print(f"✅ Created {len(self.projects)} projects")
    
    async def _seed_tasks(self):
        """Seed task data with realistic dependencies"""
        print("📝 Seeding tasks...")
        
        # ALPHA project tasks
        alpha_tasks = [
            {"name": "Project Setup", "description": "Initialize project structure", "priority": TaskPriority.HIGH, "estimated_hours": 8},
            {"name": "Database Design", "description": "Design database schema", "priority": TaskPriority.HIGH, "estimated_hours": 16},
            {"name": "API Development", "description": "Develop REST API endpoints", "priority": TaskPriority.MEDIUM, "estimated_hours": 40},
            {"name": "Frontend Development", "description": "Build React frontend", "priority": TaskPriority.MEDIUM, "estimated_hours": 60},
            {"name": "AI Integration", "description": "Integrate Ollama LLM", "priority": TaskPriority.HIGH, "estimated_hours": 32},
            {"name": "Testing", "description": "Unit and integration tests", "priority": TaskPriority.MEDIUM, "estimated_hours": 24},
            {"name": "Deployment", "description": "Deploy to production", "priority": TaskPriority.HIGH, "estimated_hours": 8}
        ]
        
        # BETA project tasks
        beta_tasks = [
            {"name": "Requirements Analysis", "description": "Analyze ML requirements", "priority": TaskPriority.HIGH, "estimated_hours": 12},
            {"name": "Model Selection", "description": "Select appropriate ML models", "priority": TaskPriority.MEDIUM, "estimated_hours": 16},
            {"name": "Data Pipeline", "description": "Build data processing pipeline", "priority": TaskPriority.HIGH, "estimated_hours": 32},
            {"name": "Model Training", "description": "Train ML models", "priority": TaskPriority.MEDIUM, "estimated_hours": 48},
            {"name": "Model Deployment", "description": "Deploy models to production", "priority": TaskPriority.HIGH, "estimated_hours": 20}
        ]
        
        all_tasks = []
        
        # Create ALPHA tasks
        for i, task_data in enumerate(alpha_tasks):
            task = Task(
                **task_data,
                project_id=self.projects["ALPHA"],
                status=TaskStatus.IN_PROGRESS if i < 3 else TaskStatus.TODO,
                assignee_id=random.choice(list(self.users.values()) if i < 3 else [None]),
                created_at=datetime.now()
            )
            self.session.add(task)
            await self.session.flush()
            all_tasks.append(task)
        
        # Create BETA tasks
        for task_data in beta_tasks:
            task = Task(
                **task_data,
                project_id=self.projects["BETA"],
                status=TaskStatus.TODO,
                created_at=datetime.now()
            )
            self.session.add(task)
            await self.session.flush()
            all_tasks.append(task)
        
        # Add dependencies (no cycles)
        if len(all_tasks) >= 4:
            # ALPHA: Setup -> Database -> API -> Frontend
            all_tasks[1].dependencies = [all_tasks[0].id]  # Database depends on Setup
            all_tasks[2].dependencies = [all_tasks[1].id]  # API depends on Database
            all_tasks[3].dependencies = [all_tasks[2].id]  # Frontend depends on API
        
        await self.session.commit()
        print(f"✅ Created {len(all_tasks)} tasks")
    
    async def _seed_status_update_policies(self):
        """Seed status update policies"""
        print("📅 Seeding status update policies...")
        
        policies = [
            {
                "name": "Daily Updates",
                "frequency": UpdateFrequency.DAILY,
                "project_id": self.projects["ALPHA"],
                "is_active": True
            },
            {
                "name": "Weekly Updates",
                "frequency": UpdateFrequency.WEEKLY,
                "project_id": self.projects["BETA"],
                "is_active": True
            }
        ]
        
        for policy_data in policies:
            policy = StatusUpdatePolicy(
                **policy_data,
                tenant_id=self.tenant_id,
                created_by=self.users["manager"]
            )
            self.session.add(policy)
        
        await self.session.commit()
        print("✅ Status update policies created")
    
    async def _seed_status_updates(self):
        """Seed status updates"""
        print("📊 Seeding status updates...")
        
        # Get tasks for updates
        result = await self.session.execute(select(Task).where(Task.assignee_id.isnot(None)))
        assigned_tasks = result.scalars().all()
        
        for task in assigned_tasks:
            # Create recent status updates
            for days_ago in [0, 1, 3, 7]:
                update_date = datetime.now() - timedelta(days=days_ago)
                if update_date >= task.created_at:
                    status_update = StatusUpdate(
                        task_id=task.id,
                        user_id=task.assignee_id,
                        status=task.status,
                        progress=random.randint(0, 100),
                        description=f"Status update for {task.name}",
                        created_at=update_date
                    )
                    self.session.add(status_update)
        
        await self.session.commit()
        print("✅ Status updates created")
    
    async def _seed_documents(self):
        """Seed document data"""
        print("📄 Seeding documents...")
        
        documents = [
            {
                "name": "Project Charter - ALPHA",
                "description": "Project charter document for ALPHA project",
                "document_type": DocumentType.PDF,
                "file_path": "documents/alpha_charter.pdf",
                "project_id": self.projects["ALPHA"]
            },
            {
                "name": "Technical Requirements - BETA",
                "description": "Technical requirements document for BETA project",
                "document_type": DocumentType.MARKDOWN,
                "file_path": "documents/beta_requirements.md",
                "project_id": self.projects["BETA"]
            }
        ]
        
        for doc_data in documents:
            document = Document(
                **doc_data,
                uploaded_by=self.users["manager"],
                tenant_id=self.tenant_id,
                created_at=datetime.now()
            )
            self.session.add(document)
        
        await self.session.commit()
        print("✅ Documents created")
    
    async def _seed_ai_drafts(self):
        """Seed AI draft data"""
        print("🤖 Seeding AI drafts...")
        
        # Create AI drafts for tasks
        result = await self.session.execute(select(Task).limit(5))
        tasks = result.scalars().all()
        
        for task in tasks:
            draft = AIDraft(
                draft_type=DraftType.TASK,
                content=json.dumps({
                    "name": f"AI-Generated {task.name}",
                    "description": f"AI-generated description for {task.name}",
                    "estimated_hours": task.estimated_hours,
                    "priority": task.priority.value
                }),
                metadata=json.dumps({
                    "project_id": task.project_id,
                    "source": "ai_autoplan",
                    "confidence": random.uniform(0.7, 0.95)
                }),
                status=DraftStatus.PENDING,
                created_by=self.users["manager"],
                tenant_id=self.tenant_id
            )
            self.session.add(draft)
        
        await self.session.commit()
        print("✅ AI drafts created")
    
    async def _seed_audit_logs(self):
        """Seed audit log data"""
        print("📋 Seeding audit logs...")
        
        # Create audit logs for various actions
        actions = [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]
        entities = ["User", "Project", "Task", "Document"]
        
        for _ in range(20):
            audit_log = AuditLog(
                action=random.choice(actions),
                entity_type=random.choice(entities),
                entity_id=random.randint(1, 100),
                user_id=random.choice(list(self.users.values())),
                details=f"Audit log entry for {random.choice(actions).value} action",
                tenant_id=self.tenant_id,
                created_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            self.session.add(audit_log)
        
        await self.session.commit()
        print("✅ Audit logs created")
    
    async def _seed_financial_data(self):
        """Seed financial data"""
        print("💰 Seeding financial data...")
        
        # Create budgets for projects
        for project_name, project_id in self.projects.items():
            budget = Budget(
                name=f"{project_name} Budget",
                project_id=project_id,
                total_amount=random.uniform(50000.0, 200000.0),
                currency="USD",
                fiscal_year=2024,
                status="approved",
                created_by=self.users["manager"],
                tenant_id=self.tenant_id
            )
            self.session.add(budget)
        
        await self.session.commit()
        print("✅ Financial data created")
    
    async def _print_summary(self):
        """Print seeding summary"""
        print("\n" + "="*60)
        print("📊 SEEDING SUMMARY")
        print("="*60)
        
        # Count records
        counts = {}
        for model_name in ["User", "Project", "Task", "Resource", "Document", "AIDraft", "AuditLog"]:
            result = await self.session.execute(select(func.count()).select_from(eval(f"{model_name}")))
            counts[model_name] = result.scalar()
        
        summary_table = f"""
| Entity        | Count |
|---------------|-------|
| Users         | {counts.get('User', 0):>6} |
| Projects      | {counts.get('Project', 0):>6} |
| Tasks         | {counts.get('Task', 0):>6} |
| Resources     | {counts.get('Resource', 0):>6} |
| Documents     | {counts.get('Document', 0):>6} |
| AI Drafts     | {counts.get('AIDraft', 0):>6} |
| Audit Logs    | {counts.get('AuditLog', 0):>6} |
"""
        print(summary_table)
        print("✅ Database seeding completed successfully!")
        print("🔑 Default credentials:")
        print("   Admin: admin@demo.local / admin123")
        print("   Manager: manager@demo.local / manager123")
        print("   Developer: dev1@demo.local / dev123")


async def main():
    """Main entry point"""
    async with PPMSeedData() as seeder:
        await seeder.seed_all()


if __name__ == "__main__":
    asyncio.run(main())
