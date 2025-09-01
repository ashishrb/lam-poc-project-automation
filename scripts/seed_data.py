#!/usr/bin/env python3
"""Seed database with sample data"""

import asyncio
import json
import sys
import os
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, init_db
from app.models import *


async def seed_tenants():
    """Seed tenant data"""
    async with AsyncSessionLocal() as session:
        # Check if tenant exists
        result = await session.execute(select(Tenant).where(Tenant.name == "demo"))
        if result.scalar_one_or_none():
            return
        
        tenant = Tenant(
            name="demo",
            domain="demo.local",
            settings=json.dumps({"timezone": "Asia/Kolkata"}),
            is_active=True
        )
        session.add(tenant)
        await session.commit()
        print("✅ Tenant created")


async def seed_roles():
    """Seed role data"""
    async with AsyncSessionLocal() as session:
        # Get tenant
        tenant = await session.execute(select(Tenant).where(Tenant.name == "demo"))
        tenant = tenant.scalar_one()
        
        roles_data = [
            {"name": "admin", "description": "System Administrator"},
            {"name": "executive", "description": "Executive Management"},
            {"name": "pm", "description": "Project Manager"},
            {"name": "team_member", "description": "Team Member"},
            {"name": "vendor", "description": "External Vendor"}
        ]
        
        for role_data in roles_data:
            result = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            if not result.scalar_one_or_none():
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    tenant_id=tenant.id,
                    permissions=json.dumps({"*": ["*"]})
                )
                session.add(role)
        
        await session.commit()
        print("✅ Roles created")


async def seed_users():
    """Seed user data"""
    async with AsyncSessionLocal() as session:
        # Get tenant and roles
        tenant = await session.execute(select(Tenant).where(Tenant.name == "demo"))
        tenant = tenant.scalar_one()
        
        admin_role = await session.execute(select(Role).where(Role.name == "admin"))
        admin_role = admin_role.scalar_one()
        
        # Create admin user
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin_user = User(
                username="admin",
                email="admin@demo.local",
                full_name="System Administrator",
                hashed_password="hashed_password_here",
                role_id=admin_role.id,
                tenant_id=tenant.id,
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("✅ Admin user created")


async def seed_projects():
    """Seed project data"""
    async with AsyncSessionLocal() as session:
        # Get tenant and admin user
        tenant = await session.execute(select(Tenant).where(Tenant.name == "demo"))
        tenant = tenant.scalar_one()
        
        admin_user = await session.execute(select(User).where(User.username == "admin"))
        admin_user = admin_user.scalar_one()
        
        projects_data = [
            {
                "name": "E-commerce Platform Redesign",
                "description": "Modernize the existing e-commerce platform with new UI/UX",
                "status": "active",
                "phase": "execution",
                "start_date": date.today() - timedelta(days=30),
                "planned_end_date": date.today() + timedelta(days=90),
                "client_name": "RetailCorp Inc.",
                "health_score": 85.0,
                "risk_level": "medium"
            },
            {
                "name": "Mobile App Development",
                "description": "Develop a new mobile application for iOS and Android",
                "status": "planning",
                "phase": "planning",
                "start_date": date.today() + timedelta(days=15),
                "planned_end_date": date.today() + timedelta(days=120),
                "client_name": "TechStart Ltd.",
                "health_score": 95.0,
                "risk_level": "low"
            },
            {
                "name": "Data Migration Project",
                "description": "Migrate legacy data to new cloud-based system",
                "status": "active",
                "phase": "monitoring",
                "start_date": date.today() - timedelta(days=60),
                "planned_end_date": date.today() + timedelta(days=30),
                "client_name": "Enterprise Solutions",
                "health_score": 65.0,
                "risk_level": "high"
            }
        ]
        
        for project_data in projects_data:
            result = await session.execute(
                select(Project).where(Project.name == project_data["name"])
            )
            if not result.scalar_one_or_none():
                project = Project(
                    **project_data,
                    project_manager_id=admin_user.id,
                    tenant_id=tenant.id
                )
                session.add(project)
        
        await session.commit()
        print("✅ Projects created")


async def seed_resources():
    """Seed resource data"""
    async with AsyncSessionLocal() as session:
        # Get tenant
        tenant = await session.execute(select(Tenant).where(Tenant.name == "demo"))
        tenant = tenant.scalar_one()
        
        resources_data = [
            {"name": "John Smith", "email": "john.smith@demo.local", "department": "Engineering", "position": "Senior Developer"},
            {"name": "Sarah Johnson", "email": "sarah.johnson@demo.local", "department": "Design", "position": "UX Designer"},
            {"name": "Mike Chen", "email": "mike.chen@demo.local", "department": "Engineering", "position": "Backend Developer"},
            {"name": "Emily Davis", "email": "emily.davis@demo.local", "department": "Product", "position": "Product Manager"},
            {"name": "Alex Brown", "email": "alex.brown@demo.local", "department": "Engineering", "position": "DevOps Engineer"},
            {"name": "Lisa Wang", "email": "lisa.wang@demo.local", "department": "Design", "position": "UI Designer"},
            {"name": "David Lee", "email": "david.lee@demo.local", "department": "Engineering", "position": "Frontend Developer"},
            {"name": "Rachel Green", "email": "rachel.green@demo.local", "department": "Marketing", "position": "Marketing Manager"},
            {"name": "Tom Wilson", "email": "tom.wilson@demo.local", "department": "Engineering", "position": "QA Engineer"},
            {"name": "Maria Garcia", "email": "maria.garcia@demo.local", "department": "Sales", "position": "Sales Representative"},
            {"name": "James Taylor", "email": "james.taylor@demo.local", "department": "Engineering", "position": "Data Scientist"},
            {"name": "Anna Kim", "email": "anna.kim@demo.local", "department": "Design", "position": "Visual Designer"},
            {"name": "Chris Martinez", "email": "chris.martinez@demo.local", "department": "Engineering", "position": "Mobile Developer"},
            {"name": "Jennifer White", "email": "jennifer.white@demo.local", "department": "Product", "position": "Business Analyst"},
            {"name": "Ryan Thompson", "email": "ryan.thompson@demo.local", "department": "Engineering", "position": "System Architect"},
            {"name": "Amanda Clark", "email": "amanda.clark@demo.local", "department": "Design", "position": "Interaction Designer"},
            {"name": "Kevin Rodriguez", "email": "kevin.rodriguez@demo.local", "department": "Engineering", "position": "Security Engineer"},
            {"name": "Nicole Lewis", "email": "nicole.lewis@demo.local", "department": "Marketing", "position": "Digital Marketing Specialist"},
            {"name": "Brian Hall", "email": "brian.hall@demo.local", "department": "Engineering", "position": "Database Administrator"},
            {"name": "Stephanie Allen", "email": "stephanie.allen@demo.local", "department": "Product", "position": "Product Owner"}
        ]
        
        for resource_data in resources_data:
            result = await session.execute(
                select(Resource).where(Resource.email == resource_data["email"])
            )
            if not result.scalar_one_or_none():
                resource = Resource(
                    **resource_data,
                    resource_type="employee",
                    status="active",
                    hourly_rate=75.0,
                    capacity_hours_per_week=40.0,
                    tenant_id=tenant.id
                )
                session.add(resource)
        
        await session.commit()
        print("✅ Resources created")


async def seed_budgets():
    """Seed budget data"""
    async with AsyncSessionLocal() as session:
        # Get projects and admin user
        projects = await session.execute(select(Project))
        projects = projects.scalars().all()
        
        admin_user = await session.execute(select(User).where(User.username == "admin"))
        admin_user = admin_user.scalar_one()
        
        tenant = await session.execute(select(Tenant).where(Tenant.name == "demo"))
        tenant = tenant.scalar_one()
        
        budget_data = [
            {"project_id": 1, "name": "Development Budget", "total_amount": 150000.0, "budget_type": "labor"},
            {"project_id": 2, "name": "Design Budget", "total_amount": 80000.0, "budget_type": "labor"},
            {"project_id": 3, "name": "Infrastructure Budget", "total_amount": 120000.0, "budget_type": "equipment"}
        ]
        
        for budget_info in budget_data:
            result = await session.execute(
                select(Budget).where(
                    Budget.project_id == budget_info["project_id"],
                    Budget.name == budget_info["name"]
                )
            )
            if not result.scalar_one_or_none():
                budget = Budget(
                    **budget_info,
                    currency="USD",
                    fiscal_year=2024,
                    status="approved",
                    created_by=admin_user.id,
                    tenant_id=tenant.id
                )
                session.add(budget)
        
        await session.commit()
        print("✅ Budgets created")


async def main():
    """Main seeding function"""
    print("🚀 Starting database seeding...")
    
    # Initialize database
    await init_db()
    
    # Seed data
    await seed_tenants()
    await seed_roles()
    await seed_users()
    await seed_projects()
    await seed_resources()
    await seed_budgets()
    
    print("✅ Database seeding completed!")


if __name__ == "__main__":
    asyncio.run(main())
