from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.models.project import Project, Task, WorkItem, Milestone
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse
)
from app.schemas.common import PaginationParams, PaginatedResponse, FilterParams

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProjectResponse])
async def list_projects(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """List projects with pagination and filtering"""
    query = select(Project)
    
    # Apply filters
    if filters.search:
        query = query.where(
            Project.name.ilike(f"%{filters.search}%") |
            Project.description.ilike(f"%{filters.search}%")
        )
    
    if filters.filters:
        if "status" in filters.filters:
            query = query.where(Project.status == filters.filters["status"])
        if "phase" in filters.filters:
            query = query.where(Project.phase == filters.filters["phase"])
        if "risk_level" in filters.filters:
            query = query.where(Project.risk_level == filters.filters["risk_level"])
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)
    
    # Apply sorting
    if pagination.sort_by:
        if pagination.sort_by == "name":
            query = query.order_by(Project.name)
        elif pagination.sort_by == "start_date":
            query = query.order_by(Project.start_date)
        elif pagination.sort_by == "health_score":
            query = query.order_by(Project.health_score)
        else:
            query = query.order_by(Project.created_at)
    else:
        query = query.order_by(Project.created_at.desc())
    
    if pagination.sort_order == "desc":
        query = query.order_by(query.order_by().desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    pages = (total + pagination.size - 1) // pagination.size
    
    return PaginatedResponse(
        items=[ProjectResponse.from_orm(p) for p in projects],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pages,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1
    )


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    db_project = Project(**project.dict())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return ProjectResponse.from_orm(db_project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get project by ID"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse.from_orm(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    db_project = result.scalar_one_or_none()
    
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for field, value in project_update.dict(exclude_unset=True).items():
        setattr(db_project, field, value)
    
    await db.commit()
    await db.refresh(db_project)
    return ProjectResponse.from_orm(db_project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete project"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/{project_id}/tasks", response_model=List[TaskResponse])
async def get_project_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks for a project"""
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.due_date)
    )
    tasks = result.scalars().all()
    return [TaskResponse.from_orm(task) for task in tasks]


@router.post("/{project_id}/tasks", response_model=TaskResponse)
async def create_project_task(
    project_id: int,
    task: TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task for a project"""
    db_task = Task(**task.dict(), project_id=project_id)
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return TaskResponse.from_orm(db_task)


@router.get("/{project_id}/milestones", response_model=List[dict])
async def get_project_milestones(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all milestones for a project"""
    result = await db.execute(
        select(Milestone).where(Milestone.project_id == project_id).order_by(Milestone.due_date)
    )
    milestones = result.scalars().all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "due_date": m.due_date,
            "completed_date": m.completed_date,
            "is_critical": m.is_critical,
            "status": m.status
        }
        for m in milestones
    ]


@router.get("/{project_id}/health", response_model=dict)
async def get_project_health(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get project health metrics"""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get task statistics
    task_result = await db.execute(
        select(func.count(Task.id), func.count(Task.id).filter(Task.status == "done"))
        .where(Task.project_id == project_id)
    )
    total_tasks, completed_tasks = task_result.first()
    
    # Calculate completion percentage
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    return {
        "project_id": project_id,
        "health_score": project.health_score,
        "risk_level": project.risk_level,
        "status": project.status,
        "phase": project.phase,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_percentage": round(completion_percentage, 2),
        "days_remaining": (project.end_date - date.today()).days if project.end_date else None
    }
