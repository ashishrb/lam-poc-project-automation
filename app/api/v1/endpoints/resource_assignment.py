from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Dict, Any, Optional
import json
import logging

from app.core.database import get_db
from app.models.resource import Resource, Skill, ResourceSkill
from app.models.project import Task, Project
from app.models.user import User
from app.services.resource_optimization import ResourceOptimizationService
from app.schemas.resource import ResourceAssignment, SkillMatch

router = APIRouter()
resource_service = ResourceOptimizationService()

logger = logging.getLogger(__name__)


@router.post("/auto-assign")
async def auto_assign_resources(
    assignment_request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Automatically assign resources to tasks based on skills and availability
    """
    try:
        tasks = assignment_request.get("tasks", [])
        project_id = assignment_request.get("project_id")
        
        if not tasks:
            raise HTTPException(status_code=400, detail="No tasks provided for assignment")
        
        # Get all available resources
        resources_query = select(Resource).where(Resource.is_active == True)
        resources_result = await db.execute(resources_query)
        available_resources = resources_result.scalars().all()
        
        if not available_resources:
            raise HTTPException(status_code=404, detail="No active resources found")
        
        # Get resource skills
        resource_skills = {}
        for resource in available_resources:
            skills_query = select(ResourceSkill).where(ResourceSkill.resource_id == resource.id)
            skills_result = await db.execute(skills_query)
            resource_skills[resource.id] = [
                {
                    "skill_name": skill.skill.name,
                    "proficiency_level": skill.proficiency_level,
                    "years_experience": skill.years_experience
                }
                for skill in skills_result.scalars().all()
            ]
        
        # Perform intelligent assignment
        assignments = []
        
        for task in tasks:
            best_match = await find_best_resource_match(
                task=task,
                resources=available_resources,
                resource_skills=resource_skills,
                db=db
            )
            
            if best_match:
                assignments.append({
                    "task_id": task.get("id"),
                    "task_name": task.get("name"),
                    "resource_id": best_match["resource_id"],
                    "resource_name": best_match["resource_name"],
                    "skill_match": best_match["skill_match"],
                    "confidence_score": best_match["confidence_score"],
                    "reasoning": best_match["reasoning"]
                })
            else:
                assignments.append({
                    "task_id": task.get("id"),
                    "task_name": task.get("name"),
                    "resource_id": None,
                    "resource_name": "Unassigned",
                    "skill_match": 0,
                    "confidence_score": 0,
                    "reasoning": "No suitable resource found"
                })
        
        return JSONResponse(content={
            "success": True,
            "assignments": assignments,
            "summary": {
                "total_tasks": len(tasks),
                "assigned_tasks": len([a for a in assignments if a["resource_id"] is not None]),
                "unassigned_tasks": len([a for a in assignments if a["resource_id"] is None]),
                "average_skill_match": sum(a["skill_match"] for a in assignments) / len(assignments) if assignments else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error in auto-assign resources: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error assigning resources: {str(e)}"
            }
        )


async def find_best_resource_match(
    task: Dict[str, Any],
    resources: List[Resource],
    resource_skills: Dict[int, List[Dict[str, Any]]],
    db: AsyncSession
) -> Optional[Dict[str, Any]]:
    """
    Find the best resource match for a given task
    """
    task_name = task.get("name", "").lower()
    task_description = task.get("description", "").lower()
    
    best_match = None
    best_score = 0
    
    for resource in resources:
        # Calculate skill match score
        skill_score = calculate_skill_match(
            task_name=task_name,
            task_description=task_description,
            resource_skills=resource_skills.get(resource.id, [])
        )
        
        # Calculate availability score
        availability_score = await calculate_availability_score(
            resource_id=resource.id,
            task_start_date=task.get("start_date"),
            task_end_date=task.get("due_date"),
            db=db
        )
        
        # Calculate overall score (weighted combination)
        overall_score = (skill_score * 0.7) + (availability_score * 0.3)
        
        if overall_score > best_score:
            best_score = overall_score
            best_match = {
                "resource_id": resource.id,
                "resource_name": resource.name,
                "skill_match": skill_score,
                "availability_score": availability_score,
                "confidence_score": overall_score,
                "reasoning": generate_assignment_reasoning(
                    task_name=task_name,
                    resource_skills=resource_skills.get(resource.id, []),
                    skill_score=skill_score,
                    availability_score=availability_score
                )
            }
    
    return best_match if best_score > 0.3 else None  # Minimum threshold


def calculate_skill_match(
    task_name: str,
    task_description: str,
    resource_skills: List[Dict[str, Any]]
) -> float:
    """
    Calculate skill match between task requirements and resource skills
    """
    if not resource_skills:
        return 0.0
    
    # Define skill keywords for different task types
    skill_keywords = {
        "development": ["programming", "coding", "development", "software", "code", "implement"],
        "design": ["design", "ui", "ux", "interface", "wireframe", "prototype"],
        "testing": ["testing", "qa", "quality", "test", "validation", "verification"],
        "analysis": ["analysis", "requirements", "business", "research", "investigation"],
        "documentation": ["documentation", "writing", "technical writing", "user guide", "manual"],
        "deployment": ["deployment", "devops", "infrastructure", "server", "configuration"],
        "project_management": ["project management", "planning", "coordination", "leadership"]
    }
    
    # Extract task type from name and description
    task_text = f"{task_name} {task_description}".lower()
    task_skills = []
    
    for skill_type, keywords in skill_keywords.items():
        if any(keyword in task_text for keyword in keywords):
            task_skills.append(skill_type)
    
    if not task_skills:
        # Default to general development if no specific skills detected
        task_skills = ["development"]
    
    # Calculate match score
    total_score = 0
    max_possible_score = len(task_skills)
    
    for task_skill in task_skills:
        best_skill_match = 0
        
        for resource_skill in resource_skills:
            skill_name = resource_skill["skill_name"].lower()
            proficiency = resource_skill["proficiency_level"]
            experience = resource_skill["years_experience"]
            
            # Check if skill matches
            if task_skill in skill_name or any(keyword in skill_name for keyword in skill_keywords.get(task_skill, [])):
                # Calculate skill score based on proficiency and experience
                skill_score = min(1.0, (proficiency * 0.6) + (min(experience, 10) / 10 * 0.4))
                best_skill_match = max(best_skill_match, skill_score)
        
        total_score += best_skill_match
    
    return total_score / max_possible_score if max_possible_score > 0 else 0.0


async def calculate_availability_score(
    resource_id: int,
    task_start_date: Optional[str],
    task_end_date: Optional[str],
    db: AsyncSession
) -> float:
    """
    Calculate resource availability score for the given time period
    """
    if not task_start_date or not task_end_date:
        return 0.5  # Default score if dates not provided
    
    try:
        # Get existing task assignments for the resource
        existing_tasks_query = select(Task).where(
            and_(
                Task.assigned_to_id == resource_id,
                Task.status.in_(["todo", "in_progress"])
            )
        )
        existing_tasks_result = await db.execute(existing_tasks_query)
        existing_tasks = existing_tasks_result.scalars().all()
        
        # Calculate workload overlap
        task_start = task_start_date
        task_end = task_end_date
        
        overlapping_hours = 0
        total_task_hours = 0
        
        for existing_task in existing_tasks:
            if existing_task.start_date and existing_task.due_date:
                # Check for date overlap
                if (existing_task.start_date <= task_end and 
                    existing_task.due_date >= task_start):
                    # Calculate overlapping hours
                    overlap_start = max(existing_task.start_date, task_start)
                    overlap_end = min(existing_task.due_date, task_end)
                    overlap_hours = (overlap_end - overlap_start).days * 8  # Assuming 8 hours per day
                    overlapping_hours += overlap_hours
        
        # Calculate availability score
        if overlapping_hours == 0:
            return 1.0  # Fully available
        elif overlapping_hours > 40:  # More than 1 week of overlap
            return 0.1  # Very low availability
        else:
            return max(0.1, 1.0 - (overlapping_hours / 40))  # Linear decrease
            
    except Exception as e:
        logger.error(f"Error calculating availability for resource {resource_id}: {str(e)}")
        return 0.5  # Default score on error


def generate_assignment_reasoning(
    task_name: str,
    resource_skills: List[Dict[str, Any]],
    skill_score: float,
    availability_score: float
) -> str:
    """
    Generate human-readable reasoning for the assignment
    """
    if skill_score == 0:
        return "No relevant skills found for this task"
    
    # Find best matching skills
    relevant_skills = []
    for skill in resource_skills:
        if skill["proficiency_level"] > 0.5:  # Only consider proficient skills
            relevant_skills.append(f"{skill['skill_name']} ({skill['proficiency_level']:.0%})")
    
    reasoning_parts = []
    
    if relevant_skills:
        reasoning_parts.append(f"Strong skills in: {', '.join(relevant_skills[:3])}")
    
    if skill_score > 0.8:
        reasoning_parts.append("Excellent skill match")
    elif skill_score > 0.6:
        reasoning_parts.append("Good skill match")
    elif skill_score > 0.4:
        reasoning_parts.append("Moderate skill match")
    
    if availability_score > 0.8:
        reasoning_parts.append("High availability")
    elif availability_score < 0.3:
        reasoning_parts.append("Limited availability")
    
    return ". ".join(reasoning_parts) if reasoning_parts else "Suitable for task requirements"


@router.post("/manual-assign")
async def manual_assign_resource(
    assignment_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Manually assign a specific resource to a task
    """
    try:
        task_id = assignment_data.get("task_id")
        resource_id = assignment_data.get("resource_id")
        
        if not task_id or not resource_id:
            raise HTTPException(status_code=400, detail="Task ID and Resource ID are required")
        
        # Get task and resource
        task_query = select(Task).where(Task.id == task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        resource_query = select(Resource).where(Resource.id == resource_id)
        resource_result = await db.execute(resource_query)
        resource = resource_result.scalar_one_or_none()
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Update task assignment
        task.assigned_to_id = resource_id
        await db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": f"Task '{task.name}' assigned to '{resource.name}' successfully"
        })
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in manual assign: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error assigning resource: {str(e)}"
            }
        )


@router.get("/resource-skills/{resource_id}")
async def get_resource_skills(
    resource_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed skills information for a specific resource
    """
    try:
        # Get resource
        resource_query = select(Resource).where(Resource.id == resource_id)
        resource_result = await db.execute(resource_query)
        resource = resource_result.scalar_one_or_none()
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        # Get resource skills
        skills_query = select(ResourceSkill).where(ResourceSkill.resource_id == resource_id)
        skills_result = await db.execute(skills_query)
        skills = skills_result.scalars().all()
        
        skill_details = []
        for skill in skills:
            skill_details.append({
                "skill_name": skill.skill.name,
                "skill_category": skill.skill.category,
                "proficiency_level": skill.proficiency_level,
                "years_experience": skill.years_experience,
                "last_used": skill.last_used.isoformat() if skill.last_used else None
            })
        
        return JSONResponse(content={
            "success": True,
            "resource": {
                "id": resource.id,
                "name": resource.name,
                "email": resource.email,
                "role": resource.role,
                "is_active": resource.is_active
            },
            "skills": skill_details,
            "total_skills": len(skill_details)
        })
        
    except Exception as e:
        logger.error(f"Error getting resource skills: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error retrieving resource skills: {str(e)}"
            }
        )


@router.get("/task-requirements/{task_id}")
async def get_task_requirements(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze task requirements and suggest suitable resources
    """
    try:
        # Get task
        task_query = select(Task).where(Task.id == task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Analyze task requirements
        task_text = f"{task.name} {task.description}".lower()
        
        # Extract required skills from task description
        required_skills = extract_required_skills(task_text)
        
        # Find matching resources
        matching_resources = await find_matching_resources(
            required_skills=required_skills,
            db=db
        )
        
        return JSONResponse(content={
            "success": True,
            "task": {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "priority": task.priority,
                "estimated_hours": task.estimated_hours
            },
            "required_skills": required_skills,
            "matching_resources": matching_resources
        })
        
    except Exception as e:
        logger.error(f"Error analyzing task requirements: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error analyzing task requirements: {str(e)}"
            }
        )


def extract_required_skills(task_text: str) -> List[str]:
    """
    Extract required skills from task text
    """
    skill_patterns = {
        "programming": ["programming", "coding", "development", "software", "code", "implement"],
        "design": ["design", "ui", "ux", "interface", "wireframe", "prototype"],
        "testing": ["testing", "qa", "quality", "test", "validation", "verification"],
        "analysis": ["analysis", "requirements", "business", "research", "investigation"],
        "documentation": ["documentation", "writing", "technical writing", "user guide", "manual"],
        "deployment": ["deployment", "devops", "infrastructure", "server", "configuration"],
        "project_management": ["project management", "planning", "coordination", "leadership"]
    }
    
    required_skills = []
    for skill_name, keywords in skill_patterns.items():
        if any(keyword in task_text for keyword in keywords):
            required_skills.append(skill_name)
    
    return required_skills if required_skills else ["general"]


async def find_matching_resources(
    required_skills: List[str],
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """
    Find resources that match the required skills
    """
    # Get all active resources with their skills
    resources_query = select(Resource).where(Resource.is_active == True)
    resources_result = await db.execute(resources_query)
    resources = resources_result.scalars().all()
    
    matching_resources = []
    
    for resource in resources:
        # Get resource skills
        skills_query = select(ResourceSkill).where(ResourceSkill.resource_id == resource.id)
        skills_result = await db.execute(skills_query)
        skills = skills_result.scalars().all()
        
        # Calculate match score
        match_score = 0
        matched_skills = []
        
        for skill in skills:
            skill_name = skill.skill.name.lower()
            for required_skill in required_skills:
                if required_skill in skill_name or any(keyword in skill_name for keyword in extract_required_skills(required_skill)):
                    match_score += skill.proficiency_level
                    matched_skills.append({
                        "skill_name": skill.skill.name,
                        "proficiency": skill.proficiency_level,
                        "experience": skill.years_experience
                    })
        
        if match_score > 0:
            matching_resources.append({
                "resource_id": resource.id,
                "resource_name": resource.name,
                "match_score": match_score / len(required_skills),
                "matched_skills": matched_skills
            })
    
    # Sort by match score
    matching_resources.sort(key=lambda x: x["match_score"], reverse=True)
    
    return matching_resources[:5]  # Return top 5 matches
