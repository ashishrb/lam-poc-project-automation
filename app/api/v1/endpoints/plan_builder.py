from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime, date

from app.core.database import get_db
from app.services.plan_builder import PlanBuilderService
from app.services.resource_optimization import ResourceOptimizationService
from app.services.plan_analysis import PlanAnalysisService
from app.models.project import Project, Task, Milestone, ProjectPlan, PlanTask, PlanMilestone, PlanType, PlanStatus
from app.models.resource import Resource
from app.schemas.project import ProjectCreate, TaskCreate, MilestoneCreate
from app.schemas.resource import ResourceAssignment

router = APIRouter()
plan_builder_service = PlanBuilderService()
resource_service = ResourceOptimizationService()
plan_analysis_service = PlanAnalysisService()

logger = logging.getLogger(__name__)


@router.post("/extract-from-documents")
async def extract_plan_from_documents(
    documents: List[UploadFile] = File(...),
    project_name: Optional[str] = Form(None),
    project_description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract project plan from uploaded BRD/HLD documents using AI
    """
    try:
        if not documents:
            raise HTTPException(status_code=400, detail="No documents provided")
        
        # Process uploaded documents
        document_contents = []
        document_metadata = []
        
        for doc in documents:
            content = await doc.read()
            content_text = content.decode('utf-8')
            
            document_contents.append(content_text)
            document_metadata.append({
                "filename": doc.filename,
                "content_type": doc.content_type,
                "size": len(content)
            })
        
        # Combine all document contents
        combined_content = "\n\n".join(document_contents)
        
        # Extract plan using AI
        extraction_result = await plan_builder_service.extract_plan_from_document(
            document_content=combined_content,
            document_metadata={
                "filenames": [doc.filename for doc in documents],
                "total_size": sum(len(content) for content in document_contents)
            },
            project_id=None,
            db=db
        )
        
        # Format the response
        plan_data = {
            "epics": extraction_result.get("epics", []),
            "features": extraction_result.get("features", []),
            "tasks": extraction_result.get("tasks", []),
            "milestones": extraction_result.get("milestones", []),
            "dependencies": extraction_result.get("dependencies", []),
            "risks": extraction_result.get("risks", []),
            "estimated_duration": extraction_result.get("estimated_duration", 0),
            "required_resources": extraction_result.get("required_resources", 0),
            "confidence_score": extraction_result.get("confidence_score", 0.0),
            "extraction_metadata": {
                "documents_processed": len(documents),
                "total_content_length": len(combined_content),
                "extraction_method": "ai_powered"
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "plan": plan_data,
            "message": f"Successfully extracted plan from {len(documents)} document(s)"
        })
        
    except Exception as e:
        logger.error(f"Error extracting plan from documents: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error extracting plan: {str(e)}"
            }
        )


@router.post("/create-project-with-plan")
async def create_project_with_plan(
    project_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project with the generated plan and resource assignments
    """
    try:
        # Extract project information
        project_info = {
            "name": project_data.get("name"),
            "description": project_data.get("description"),
            "project_manager_id": project_data.get("project_manager_id"),
            "start_date": project_data.get("start_date"),
            "end_date": project_data.get("end_date"),
            "status": "planning",
            "phase": "initiation"
        }
        
        # Create project
        project = Project(**project_info)
        db.add(project)
        await db.flush()
        
        # Create comprehensive project plan
        plan_type = PlanType.AI_GENERATED if project_data.get("plan_method") == "ai" else PlanType.MANUAL
        
        # Calculate plan metrics
        tasks_data = project_data.get("tasks", [])
        milestones_data = project_data.get("milestones", [])
        total_hours = sum(task.get("estimated_hours", 0) for task in tasks_data)
        estimated_days = max(1, int(total_hours / 8))  # Assuming 8 hours per day
        
        # Create project plan
        project_plan = ProjectPlan(
            project_id=project.id,
            name=f"{project.name} - Plan v1.0",
            description=f"Initial project plan for {project.name}",
            version="1.0",
            status=PlanStatus.DRAFT,
            plan_type=plan_type,
            creation_method=project_data.get("plan_method", "manual"),
            source_documents=project_data.get("generated_plan", {}).get("extraction_metadata", {}),
            extraction_confidence=project_data.get("generated_plan", {}).get("confidence_score", 0.0),
            
            # Plan structure
            epics=project_data.get("generated_plan", {}).get("epics", []),
            features=project_data.get("generated_plan", {}).get("features", []),
            tasks=project_data.get("generated_plan", {}).get("tasks", []),
            milestones=project_data.get("generated_plan", {}).get("milestones", []),
            dependencies=project_data.get("generated_plan", {}).get("dependencies", []),
            risks=project_data.get("generated_plan", {}).get("risks", []),
            resource_requirements=project_data.get("resource_assignments", []),
            
            # Plan metrics
            total_tasks=len(tasks_data),
            total_milestones=len(milestones_data),
            estimated_duration_days=estimated_days,
            estimated_hours=total_hours,
            required_resources=len(set(assignment.get("resource_id") for assignment in project_data.get("resource_assignments", []) if assignment.get("resource_id"))),
            total_budget=project_data.get("budget", 0.0),
            
            # Validation
            validation_score=85.0,  # Default validation score
            validation_issues=[],
            quality_metrics={
                "completeness": 90.0,
                "consistency": 85.0,
                "feasibility": 80.0
            },
            
            # Metadata
            created_by_id=project_data.get("project_manager_id", 1),
            approved_by_id=None
        )
        
        db.add(project_plan)
        await db.flush()
        
        # Update project with current plan
        project.current_plan_id = project_plan.id
        await db.flush()
        
        # Create plan tasks
        created_plan_tasks = []
        for task_data in tasks_data:
            plan_task = PlanTask(
                plan_id=project_plan.id,
                name=task_data.get("name"),
                description=task_data.get("description"),
                epic=task_data.get("epic", "General"),
                feature=task_data.get("feature", "General"),
                priority=task_data.get("priority", "medium"),
                estimated_hours=task_data.get("estimated_hours", 0),
                start_date=datetime.strptime(task_data.get("start_date"), "%Y-%m-%d").date() if task_data.get("start_date") else None,
                due_date=datetime.strptime(task_data.get("due_date"), "%Y-%m-%d").date() if task_data.get("due_date") else None,
                dependencies=task_data.get("dependencies", []),
                skill_requirements=task_data.get("skill_requirements", []),
                confidence_score=task_data.get("confidence_score", 0.0),
                reasoning=task_data.get("reasoning", {}),
                source=task_data.get("source", "manual")
            )
            db.add(plan_task)
            created_plan_tasks.append(plan_task)
        
        await db.flush()
        
        # Create plan milestones
        for milestone_data in milestones_data:
            plan_milestone = PlanMilestone(
                plan_id=project_plan.id,
                name=milestone_data.get("name"),
                description=milestone_data.get("description"),
                due_date=datetime.strptime(milestone_data.get("due_date"), "%Y-%m-%d").date() if milestone_data.get("due_date") else None,
                is_critical=milestone_data.get("is_critical", False),
                associated_tasks=milestone_data.get("associated_tasks", [])
            )
            db.add(plan_milestone)
        
        await db.flush()
        
        # Create actual tasks from plan
        created_tasks = []
        for i, task_data in enumerate(tasks_data):
            task = Task(
                name=task_data.get("name"),
                description=task_data.get("description"),
                priority=task_data.get("priority", "medium"),
                status=task_data.get("status", "todo"),
                project_id=project.id,
                estimated_hours=task_data.get("estimated_hours", 0),
                start_date=datetime.strptime(task_data.get("start_date"), "%Y-%m-%d").date() if task_data.get("start_date") else None,
                due_date=datetime.strptime(task_data.get("due_date"), "%Y-%m-%d").date() if task_data.get("due_date") else None,
                dependencies=json.dumps(task_data.get("dependencies", [])),
                source=project_data.get("plan_method", "manual"),
                confidence_score=task_data.get("confidence_score", 0.0),
                reasoning=task_data.get("reasoning", {}),
                plan_task_id=created_plan_tasks[i].id if i < len(created_plan_tasks) else None
            )
            db.add(task)
            created_tasks.append(task)
        
        await db.flush()
        
        # Create actual milestones from plan
        created_milestones = []
        for milestone_data in milestones_data:
            milestone = Milestone(
                name=milestone_data.get("name"),
                description=milestone_data.get("description"),
                project_id=project.id,
                due_date=datetime.strptime(milestone_data.get("due_date"), "%Y-%m-%d").date() if milestone_data.get("due_date") else None,
                is_critical=milestone_data.get("is_critical", False)
            )
            db.add(milestone)
            created_milestones.append(milestone)
        
        await db.flush()
        
        # Process resource assignments
        assignments_data = project_data.get("resource_assignments", [])
        for assignment_data in assignments_data:
            task_id = assignment_data.get("task_id")
            resource_id = assignment_data.get("resource_id")
            
            if task_id and resource_id:
                # Update task assignment
                task = next((t for t in created_tasks if t.id == task_id), None)
                if task:
                    task.assigned_to_id = resource_id
                
                # Update plan task assignment
                plan_task = next((pt for pt in created_plan_tasks if pt.name == assignment_data.get("task_name")), None)
                if plan_task:
                    plan_task.assigned_resource_id = resource_id
                    plan_task.skill_match_score = assignment_data.get("skill_match", 0.0)
        
        await db.commit()
        
        return JSONResponse(content={
            "success": True,
            "project_id": project.id,
            "plan_id": project_plan.id,
            "message": f"Project '{project.name}' created successfully with {len(created_tasks)} tasks and comprehensive plan storage"
        })
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating project with plan: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error creating project: {str(e)}"
            }
        )


@router.get("/project-plans/{project_id}")
async def get_project_plans(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all plans for a specific project
    """
    try:
        from sqlalchemy import select
        
        # Get project plans
        plans_query = select(ProjectPlan).where(ProjectPlan.project_id == project_id)
        plans_result = await db.execute(plans_query)
        plans = plans_result.scalars().all()
        
        plan_data = []
        for plan in plans:
            plan_data.append({
                "id": plan.id,
                "name": plan.name,
                "version": plan.version,
                "status": plan.status.value,
                "plan_type": plan.plan_type.value,
                "creation_method": plan.creation_method,
                "extraction_confidence": plan.extraction_confidence,
                "total_tasks": plan.total_tasks,
                "total_milestones": plan.total_milestones,
                "estimated_duration_days": plan.estimated_duration_days,
                "estimated_hours": plan.estimated_hours,
                "required_resources": plan.required_resources,
                "validation_score": plan.validation_score,
                "created_at": plan.created_at.isoformat(),
                "approved_at": plan.approved_at.isoformat() if plan.approved_at else None
            })
        
        return JSONResponse(content={
            "success": True,
            "plans": plan_data,
            "total_plans": len(plan_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting project plans: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error retrieving project plans: {str(e)}"
            }
        )


@router.get("/plan-details/{plan_id}")
async def get_plan_details(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific plan
    """
    try:
        from sqlalchemy import select
        
        # Get plan details
        plan_query = select(ProjectPlan).where(ProjectPlan.id == plan_id)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Get plan tasks
        tasks_query = select(PlanTask).where(PlanTask.plan_id == plan_id)
        tasks_result = await db.execute(tasks_query)
        plan_tasks = tasks_result.scalars().all()
        
        # Get plan milestones
        milestones_query = select(PlanMilestone).where(PlanMilestone.plan_id == plan_id)
        milestones_result = await db.execute(milestones_query)
        plan_milestones = milestones_result.scalars().all()
        
        plan_details = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "version": plan.version,
            "status": plan.status.value,
            "plan_type": plan.plan_type.value,
            "creation_method": plan.creation_method,
            "source_documents": plan.source_documents,
            "extraction_confidence": plan.extraction_confidence,
            
            # Plan structure
            "epics": plan.epics,
            "features": plan.features,
            "tasks": plan.tasks,
            "milestones": plan.milestones,
            "dependencies": plan.dependencies,
            "risks": plan.risks,
            "resource_requirements": plan.resource_requirements,
            
            # Metrics
            "total_tasks": plan.total_tasks,
            "total_milestones": plan.total_milestones,
            "estimated_duration_days": plan.estimated_duration_days,
            "estimated_hours": plan.estimated_hours,
            "required_resources": plan.required_resources,
            "total_budget": plan.total_budget,
            
            # Quality
            "validation_score": plan.validation_score,
            "validation_issues": plan.validation_issues,
            "quality_metrics": plan.quality_metrics,
            
            # Plan tasks
            "plan_tasks": [
                {
                    "id": pt.id,
                    "name": pt.name,
                    "description": pt.description,
                    "epic": pt.epic,
                    "feature": pt.feature,
                    "priority": pt.priority.value,
                    "estimated_hours": pt.estimated_hours,
                    "start_date": pt.start_date.isoformat() if pt.start_date else None,
                    "due_date": pt.due_date.isoformat() if pt.due_date else None,
                    "dependencies": pt.dependencies,
                    "skill_requirements": pt.skill_requirements,
                    "skill_match_score": pt.skill_match_score,
                    "confidence_score": pt.confidence_score,
                    "reasoning": pt.reasoning,
                    "source": pt.source
                }
                for pt in plan_tasks
            ],
            
            # Plan milestones
            "plan_milestones": [
                {
                    "id": pm.id,
                    "name": pm.name,
                    "description": pm.description,
                    "due_date": pm.due_date.isoformat() if pm.due_date else None,
                    "is_critical": pm.is_critical,
                    "associated_tasks": pm.associated_tasks
                }
                for pm in plan_milestones
            ],
            
            # Metadata
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
            "approved_at": plan.approved_at.isoformat() if plan.approved_at else None
        }
        
        return JSONResponse(content={
            "success": True,
            "plan": plan_details
        })
        
    except Exception as e:
        logger.error(f"Error getting plan details: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error retrieving plan details: {str(e)}"
            }
        )


@router.post("/analyze-plan/{plan_id}")
async def analyze_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform comprehensive analysis of a project plan
    """
    try:
        analysis_result = await plan_analysis_service.analyze_plan(plan_id, db)
        
        return JSONResponse(content={
            "success": True,
            "analysis": analysis_result
        })
        
    except Exception as e:
        logger.error(f"Error analyzing plan {plan_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error analyzing plan: {str(e)}"
            }
        )


@router.post("/create-plan-version/{plan_id}")
async def create_plan_version(
    plan_id: int,
    version_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new version of an existing plan
    """
    try:
        version_name = version_data.get("version_name", f"Plan v{version_data.get('version', '1.1')}")
        changes = version_data.get("changes", {})
        
        result = await plan_analysis_service.create_plan_version(plan_id, version_name, changes, db)
        
        return JSONResponse(content={
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error creating plan version: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error creating plan version: {str(e)}"
            }
        )


@router.post("/modify-plan/{plan_id}")
async def modify_plan(
    plan_id: int,
    modifications: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Modify an existing plan
    """
    try:
        from sqlalchemy import update
        
        # Get current plan
        plan_query = select(ProjectPlan).where(ProjectPlan.id == plan_id)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Apply modifications
        update_data = {}
        
        if "name" in modifications:
            update_data["name"] = modifications["name"]
        if "description" in modifications:
            update_data["description"] = modifications["description"]
        if "tasks" in modifications:
            update_data["tasks"] = modifications["tasks"]
            update_data["total_tasks"] = len(modifications["tasks"])
        if "milestones" in modifications:
            update_data["milestones"] = modifications["milestones"]
            update_data["total_milestones"] = len(modifications["milestones"])
        if "dependencies" in modifications:
            update_data["dependencies"] = modifications["dependencies"]
        if "resource_requirements" in modifications:
            update_data["resource_requirements"] = modifications["resource_requirements"]
        
        # Recalculate metrics if tasks were modified
        if "tasks" in modifications:
            total_hours = sum(task.get("estimated_hours", 0) for task in modifications["tasks"])
            estimated_days = max(1, int(total_hours / 8))
            update_data["estimated_hours"] = total_hours
            update_data["estimated_duration_days"] = estimated_days
        
        # Update plan
        if update_data:
            update_data["updated_at"] = datetime.now()
            update_query = update(ProjectPlan).where(ProjectPlan.id == plan_id).values(**update_data)
            await db.execute(update_query)
            await db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": f"Plan {plan_id} modified successfully",
            "modifications_applied": list(update_data.keys())
        })
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error modifying plan {plan_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error modifying plan: {str(e)}"
            }
        )


@router.get("/plan-comparison/{plan_id1}/{plan_id2}")
async def compare_plans(
    plan_id1: int,
    plan_id2: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Compare two project plans
    """
    try:
        from sqlalchemy import select
        
        # Get both plans
        plan1_query = select(ProjectPlan).where(ProjectPlan.id == plan_id1)
        plan1_result = await db.execute(plan1_query)
        plan1 = plan1_result.scalar_one_or_none()
        
        plan2_query = select(ProjectPlan).where(ProjectPlan.id == plan_id2)
        plan2_result = await db.execute(plan2_query)
        plan2 = plan2_result.scalar_one_or_none()
        
        if not plan1 or not plan2:
            raise HTTPException(status_code=404, detail="One or both plans not found")
        
        # Compare plans
        comparison = {
            "plan1": {
                "id": plan1.id,
                "name": plan1.name,
                "version": plan1.version,
                "total_tasks": plan1.total_tasks,
                "total_milestones": plan1.total_milestones,
                "estimated_hours": plan1.estimated_hours,
                "estimated_duration_days": plan1.estimated_duration_days,
                "required_resources": plan1.required_resources,
                "validation_score": plan1.validation_score
            },
            "plan2": {
                "id": plan2.id,
                "name": plan2.name,
                "version": plan2.version,
                "total_tasks": plan2.total_tasks,
                "total_milestones": plan2.total_milestones,
                "estimated_hours": plan2.estimated_hours,
                "estimated_duration_days": plan2.estimated_duration_days,
                "required_resources": plan2.required_resources,
                "validation_score": plan2.validation_score
            },
            "differences": {
                "task_difference": plan2.total_tasks - plan1.total_tasks,
                "milestone_difference": plan2.total_milestones - plan1.total_milestones,
                "hours_difference": plan2.estimated_hours - plan1.estimated_hours,
                "duration_difference": plan2.estimated_duration_days - plan1.estimated_duration_days,
                "resource_difference": plan2.required_resources - plan1.required_resources,
                "validation_difference": plan2.validation_score - plan1.validation_score
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "comparison": comparison
        })
        
    except Exception as e:
        logger.error(f"Error comparing plans: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error comparing plans: {str(e)}"
            }
        )


@router.post("/generate-wbs")
async def generate_wbs(
    project_id: int,
    constraints: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate Work Breakdown Structure for an existing project
    """
    try:
        # Get project details
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate WBS using AI
        wbs_result = await plan_builder_service.generate_wbs(
            project_id=project_id,
            constraints=constraints or {},
            db=db
        )
        
        return JSONResponse(content={
            "success": True,
            "wbs": wbs_result,
            "message": "WBS generated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error generating WBS: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error generating WBS: {str(e)}"
            }
        )


@router.post("/validate-plan")
async def validate_plan(
    plan_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Validate generated plan for completeness and feasibility
    """
    try:
        validation_result = await plan_builder_service.validate_extracted_plan(
            plan_data=plan_data,
            db=db
        )
        
        return JSONResponse(content={
            "success": True,
            "validation": validation_result,
            "message": "Plan validation completed"
        })
        
    except Exception as e:
        logger.error(f"Error validating plan: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error validating plan: {str(e)}"
            }
        )


@router.get("/plan-templates")
async def get_plan_templates():
    """
    Get available plan templates for different project types
    """
    templates = {
        "software_development": {
            "name": "Software Development Project",
            "phases": ["Requirements", "Design", "Development", "Testing", "Deployment"],
            "task_types": ["Analysis", "Design", "Coding", "Testing", "Documentation"],
            "milestones": ["Requirements Complete", "Design Complete", "Development Complete", "Testing Complete", "Deployment Complete"]
        },
        "infrastructure": {
            "name": "Infrastructure Project",
            "phases": ["Planning", "Design", "Implementation", "Testing", "Handover"],
            "task_types": ["Planning", "Design", "Installation", "Configuration", "Testing"],
            "milestones": ["Planning Complete", "Design Complete", "Implementation Complete", "Testing Complete", "Handover Complete"]
        },
        "migration": {
            "name": "Migration Project",
            "phases": ["Assessment", "Planning", "Migration", "Validation", "Cutover"],
            "task_types": ["Assessment", "Planning", "Migration", "Validation", "Documentation"],
            "milestones": ["Assessment Complete", "Planning Complete", "Migration Complete", "Validation Complete", "Cutover Complete"]
        }
    }
    
    return JSONResponse(content={
        "success": True,
        "templates": templates
    })


@router.post("/apply-template")
async def apply_template(
    project_id: int,
    template_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Apply a plan template to an existing project
    """
    try:
        # Get project
        project = await db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Apply template using plan builder service
        template_result = await plan_builder_service.apply_template(
            project_id=project_id,
            template_name=template_name,
            db=db
        )
        
        return JSONResponse(content={
            "success": True,
            "result": template_result,
            "message": f"Template '{template_name}' applied successfully"
        })
        
    except Exception as e:
        logger.error(f"Error applying template: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error applying template: {str(e)}"
            }
        )
