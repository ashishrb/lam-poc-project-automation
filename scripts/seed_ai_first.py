#!/usr/bin/env python3
"""
Seed script for AI-First PPM System
Creates demo users, projects, and initial data for testing
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import AsyncSessionLocal, init_db
from app.models.user import User, Role, Tenant
from app.models.project import Project, ProjectStatus, ProjectPhase, Task, TaskStatus, TaskPriority
from app.models.resource import Resource, Skill
from app.models.status_update_policy import StatusUpdatePolicy, UpdateFrequency
from app.models.ai_draft import AIDraft, DraftType, DraftStatus
from app.core.config import settings


async def create_tenants(session: AsyncSessionLocal) -> Dict[str, int]:
    """Create demo tenants"""
    tenants = {}
    
    # Create default tenant
    default_tenant = Tenant(
        name="Demo Organization",
        description="Demo organization for AI-First PPM system",
        is_active=True
    )
    session.add(default_tenant)
    await session.flush()
    tenants["demo"] = default_tenant.id
    
    print(f"Created tenant: {default_tenant.name} (ID: {default_tenant.id})")
    return tenants


async def create_users(session: AsyncSessionLocal, tenant_id: int) -> Dict[str, int]:
    """Create demo users with different roles"""
    users = {}
    
    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@demo.com",
        full_name="System Administrator",
        role=Role.ADMIN,
        tenant_id=tenant_id,
        is_active=True
    )
    admin_user.set_password("admin123")
    session.add(admin_user)
    await session.flush()
    users["admin"] = admin_user.id
    
    # Create manager user
    manager_user = User(
        username="manager",
        email="manager@demo.com",
        full_name="Project Manager",
        role=Role.MANAGER,
        tenant_id=tenant_id,
        is_active=True
    )
    manager_user.set_password("manager123")
    session.add(manager_user)
    await session.flush()
    users["manager"] = manager_user.id
    
    # Create developer users
    dev1_user = User(
        username="dev1",
        email="dev1@demo.com",
        full_name="John Developer",
        role=Role.DEVELOPER,
        tenant_id=tenant_id,
        is_active=True
    )
    dev1_user.set_password("dev123")
    session.add(dev1_user)
    await session.flush()
    users["dev1"] = dev1_user.id
    
    dev2_user = User(
        username="dev2",
        email="dev2@demo.com",
        full_name="Jane Developer",
        role=Role.DEVELOPER,
        tenant_id=tenant_id,
        is_active=True
    )
    dev2_user.set_password("dev123")
    session.add(dev2_user)
    await session.flush()
    users["dev2"] = dev2_user.id
    
    print(f"Created users: {list(users.keys())}")
    return users


async def create_skills(session: AsyncSessionLocal) -> Dict[str, int]:
    """Create demo skills"""
    skills = {}
    
    skill_data = [
        "Python", "FastAPI", "PostgreSQL", "Redis", "Docker",
        "React", "TypeScript", "Node.js", "AWS", "Kubernetes",
        "Project Management", "Agile", "Scrum", "Risk Management"
    ]
    
    for skill_name in skill_data:
        skill = Skill(
            name=skill_name,
            description=f"Skill in {skill_name}",
            category="Technical" if skill_name not in ["Project Management", "Agile", "Scrum", "Risk Management"] else "Management"
        )
        session.add(skill)
        await session.flush()
        skills[skill_name] = skill.id
    
    print(f"Created {len(skills)} skills")
    return skills


async def create_resources(session: AsyncSessionLocal, users: Dict[str, int], skills: Dict[str, int]) -> Dict[str, int]:
    """Create demo resources"""
    resources = {}
    
    # Create resource for dev1
    dev1_resource = Resource(
        user_id=users["dev1"],
        name="John Developer",
        skills=[skills["Python"], skills["FastAPI"], skills["PostgreSQL"]],
        availability=8.0,
        performance_score=0.85,
        hourly_rate=75.0
    )
    session.add(dev1_resource)
    await session.flush()
    resources["dev1"] = dev1_resource.id
    
    # Create resource for dev2
    dev2_resource = Resource(
        user_id=users["dev2"],
        name="Jane Developer",
        skills=[skills["React"], skills["TypeScript"], skills["Node.js"]],
        availability=8.0,
        performance_score=0.90,
        hourly_rate=80.0
    )
    session.add(dev2_resource)
    await session.flush()
    resources["dev2"] = dev2_resource.id
    
    print(f"Created {len(resources)} resources")
    return resources


async def create_projects(session: AsyncSessionLocal, users: Dict[str, int], tenant_id: int) -> Dict[str, int]:
    """Create demo projects"""
    projects = {}
    
    # Create main project
    main_project = Project(
        name="AI-First PPM System",
        description="A comprehensive project portfolio management system with AI-first approach",
        status=ProjectStatus.ACTIVE,
        phase=ProjectPhase.EXECUTION,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() + timedelta(days=150),
        planned_end_date=datetime.now() + timedelta(days=180),
        project_manager_id=users["manager"],
        tenant_id=tenant_id,
        client_name="Internal",
        tags="ai,ppm,automation",
        health_score=75.0,
        risk_level="medium",
        ai_autopublish=True,
        allow_dev_task_create=True
    )
    session.add(main_project)
    await session.flush()
    projects["main"] = main_project.id
    
    # Create secondary project
    secondary_project = Project(
        name="Mobile App Development",
        description="Cross-platform mobile application for project management",
        status=ProjectStatus.PLANNING,
        phase=ProjectPhase.PLANNING,
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=120),
        planned_end_date=datetime.now() + timedelta(days=120),
        project_manager_id=users["manager"],
        tenant_id=tenant_id,
        client_name="External Client",
        tags="mobile,react-native,app",
        health_score=90.0,
        risk_level="low",
        ai_autopublish=False,
        allow_dev_task_create=False
    )
    session.add(secondary_project)
    await session.flush()
    projects["mobile"] = secondary_project.id
    
    print(f"Created {len(projects)} projects")
    return projects


async def create_tasks(session: AsyncSessionLocal, projects: Dict[str, int], users: Dict[str, int]) -> Dict[str, int]:
    """Create demo tasks"""
    tasks = {}
    
    # Tasks for main project
    main_tasks = [
        {
            "name": "Database Design",
            "description": "Design and implement database schema for PPM system",
            "status": TaskStatus.DONE,
            "priority": TaskPriority.HIGH,
            "assigned_to_id": users["dev1"],
            "estimated_hours": 40.0,
            "actual_hours": 38.0,
            "start_date": datetime.now() - timedelta(days=25),
            "due_date": datetime.now() - timedelta(days=5),
            "completed_date": datetime.now() - timedelta(days=5),
            "confidence_score": 0.95,
            "source": "ai"
        },
        {
            "name": "API Development",
            "description": "Develop RESTful API endpoints for core functionality",
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.HIGH,
            "assigned_to_id": users["dev1"],
            "estimated_hours": 60.0,
            "actual_hours": 25.0,
            "start_date": datetime.now() - timedelta(days=20),
            "due_date": datetime.now() + timedelta(days=15),
            "confidence_score": 0.88,
            "source": "ai"
        },
        {
            "name": "Frontend Development",
            "description": "Develop user interface components and dashboards",
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.MEDIUM,
            "assigned_to_id": users["dev2"],
            "estimated_hours": 80.0,
            "actual_hours": 35.0,
            "start_date": datetime.now() - timedelta(days=15),
            "due_date": datetime.now() + timedelta(days=25),
            "confidence_score": 0.82,
            "source": "ai"
        },
        {
            "name": "AI Integration",
            "description": "Integrate AI services and implement guardrails",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.CRITICAL,
            "assigned_to_id": users["dev1"],
            "estimated_hours": 50.0,
            "start_date": datetime.now() + timedelta(days=10),
            "due_date": datetime.now() + timedelta(days=35),
            "confidence_score": 0.75,
            "source": "ai"
        }
    ]
    
    for i, task_data in enumerate(main_tasks):
        task = Task(
            project_id=projects["main"],
            **task_data
        )
        session.add(task)
        await session.flush()
        tasks[f"main_task_{i+1}"] = task.id
    
    # Tasks for mobile project
    mobile_tasks = [
        {
            "name": "Requirements Analysis",
            "description": "Analyze and document mobile app requirements",
            "status": TaskStatus.TODO,
            "priority": TaskPriority.HIGH,
            "estimated_hours": 20.0,
            "start_date": datetime.now() + timedelta(days=35),
            "due_date": datetime.now() + timedelta(days=45),
            "confidence_score": 0.90,
            "source": "human"
        }
    ]
    
    for i, task_data in enumerate(mobile_tasks):
        task = Task(
            project_id=projects["mobile"],
            **task_data
        )
        session.add(task)
        await session.flush()
        tasks[f"mobile_task_{i+1}"] = task.id
    
    print(f"Created {len(tasks)} tasks")
    return tasks


async def create_status_update_policies(session: AsyncSessionLocal, projects: Dict[str, int], users: Dict[str, int]) -> Dict[str, int]:
    """Create demo status update policies"""
    policies = {}
    
    # Weekly policy for main project
    weekly_policy = StatusUpdatePolicy(
        project_id=projects["main"],
        name="Weekly Team Updates",
        description="Weekly status updates from all team members",
        frequency=UpdateFrequency.WEEKLY,
        reminder_time=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0).time(),
        timezone="UTC",
        require_progress=True,
        require_blockers=True,
        require_next_steps=True,
        require_effort=False,
        require_confidence=False,
        ai_generate_draft=True,
        ai_suggest_improvements=True,
        ai_escalate_missing=True,
        channels=["email", "slack"],
        escalation_delay_hours=24,
        escalation_recipients=[users["manager"]],
        is_active=True,
        created_by_user_id=users["manager"]
    )
    session.add(weekly_policy)
    await session.flush()
    policies["weekly"] = weekly_policy.id
    
    # Bi-weekly policy for mobile project
    biweekly_policy = StatusUpdatePolicy(
        project_id=projects["mobile"],
        name="Bi-weekly Updates",
        description="Bi-weekly updates during planning phase",
        frequency=UpdateFrequency.BIWEEKLY,
        reminder_time=datetime.now().replace(hour=10, minute=0, second=0, microsecond=0).time(),
        timezone="UTC",
        require_progress=True,
        require_blockers=True,
        require_next_steps=True,
        require_effort=False,
        require_confidence=False,
        ai_generate_draft=True,
        ai_suggest_improvements=False,
        ai_escalate_missing=False,
        channels=["email"],
        escalation_delay_hours=48,
        escalation_recipients=[users["manager"]],
        is_active=True,
        created_by_user_id=users["manager"]
    )
    session.add(biweekly_policy)
    await session.flush()
    policies["biweekly"] = biweekly_policy.id
    
    print(f"Created {len(policies)} status update policies")
    return policies


async def create_ai_drafts(session: AsyncSessionLocal, projects: Dict[str, int], users: Dict[str, int]) -> Dict[str, int]:
    """Create demo AI drafts"""
    drafts = {}
    
    # WBS draft for main project
    wbs_draft = AIDraft(
        project_id=projects["main"],
        draft_type=DraftType.WBS,
        status=DraftStatus.APPROVED,
        payload={
            "tasks": [
                {
                    "id": 1,
                    "name": "Database Design",
                    "description": "Design and implement database schema",
                    "estimated_hours": 40,
                    "dependencies": []
                },
                {
                    "id": 2,
                    "name": "API Development",
                    "description": "Develop RESTful API endpoints",
                    "estimated_hours": 60,
                    "dependencies": [1]
                }
            ],
            "dependencies": [
                {"from": 1, "to": 2, "type": "finish_to_start"}
            ]
        },
        rationale={
            "confidence": 0.88,
            "reasoning": "Based on project requirements and team capacity analysis",
            "ai_model": settings.AI_MODEL_NAME
        },
        model_name=settings.AI_MODEL_NAME,
        model_version="1.0",
        prompt_tokens=1500,
        completion_tokens=800,
        total_tokens=2300
    )
    session.add(wbs_draft)
    await session.flush()
    drafts["wbs"] = wbs_draft.id
    
    # Allocation draft for main project
    allocation_draft = AIDraft(
        project_id=projects["main"],
        draft_type=DraftType.ALLOCATION,
        status=DraftStatus.DRAFT,
        payload={
            "allocations": [
                {
                    "resource_id": 1,
                    "task_id": 1,
                    "hours_per_day": 8.0,
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-15"
                }
            ]
        },
        rationale={
            "confidence": 0.75,
            "reasoning": "Resource allocation based on skill matching and availability",
            "ai_model": settings.AI_MODEL_NAME
        },
        model_name=settings.AI_MODEL_NAME,
        model_version="1.0",
        prompt_tokens=800,
        completion_tokens=400,
        total_tokens=1200
    )
    session.add(allocation_draft)
    await session.flush()
    drafts["allocation"] = allocation_draft.id
    
    print(f"Created {len(drafts)} AI drafts")
    return drafts


async def main():
    """Main seeding function"""
    print("Starting AI-First PPM System seeding...")
    
    try:
        # Initialize database
        await init_db()
        print("Database initialized successfully")
        
        async with AsyncSessionLocal() as session:
            # Create data in order
            tenants = await create_tenants(session)
            users = await create_users(session, tenants["demo"])
            skills = await create_skills(session)
            resources = await create_resources(session, users, skills)
            projects = await create_projects(session, users, tenants["demo"])
            tasks = await create_tasks(session, projects, users)
            policies = await create_status_update_policies(session, projects, users)
            drafts = await create_ai_drafts(session, projects, users)
            
            # Commit all changes
            await session.commit()
            print("All data committed successfully")
        
        print("\n🎉 Seeding completed successfully!")
        print("\nDemo accounts created:")
        print("  Admin: admin@demo.com / admin123")
        print("  Manager: manager@demo.com / manager123")
        print("  Developer 1: dev1@demo.com / dev123")
        print("  Developer 2: dev2@demo.com / dev123")
        print("\nProjects created:")
        print("  - AI-First PPM System (Active)")
        print("  - Mobile App Development (Planning)")
        print("\nAI drafts created:")
        print("  - WBS draft (Approved)")
        print("  - Resource allocation draft (Draft)")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
