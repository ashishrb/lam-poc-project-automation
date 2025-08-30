#!/usr/bin/env python3
import asyncio
from app.core.database import engine
from app.models.project import Project
from app.models.user import User
from app.models.resource import Resource
from sqlalchemy import select, func

async def check_database():
    async with engine.begin() as conn:
        # Check projects
        result = await conn.execute(select(func.count()).select_from(Project))
        project_count = result.scalar()
        print(f"📊 Projects in database: {project_count}")
        
        # Check users
        result = await conn.execute(select(func.count()).select_from(User))
        user_count = result.scalar()
        print(f"👥 Users in database: {user_count}")
        
        # Check resources
        result = await conn.execute(select(func.count()).select_from(Resource))
        resource_count = result.scalar()
        print(f"👷 Resources in database: {resource_count}")
        
        # Get some sample data
        if project_count > 0:
            result = await conn.execute(select(Project).limit(3))
            projects = result.scalars().all()
            print("\n📋 Sample Projects:")
            for project in projects:
                print(f"  - {project.name} (ID: {project.id})")
        
        if user_count > 0:
            result = await conn.execute(select(User).limit(3))
            users = result.scalars().all()
            print("\n👤 Sample Users:")
            for user in users:
                print(f"  - {user.full_name} ({user.email})")

if __name__ == "__main__":
    asyncio.run(check_database())
