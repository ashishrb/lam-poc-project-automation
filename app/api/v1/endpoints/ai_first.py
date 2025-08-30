from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import json
import logging

from app.core.database import get_db
from app.core.config import settings
from app.services.ai_first_service import AIFirstService
from app.services.ai_guardrails import AIGuardrails
from app.models.ai_draft import AIDraft, DraftType, DraftStatus
from app.models.status_update_policy import StatusUpdatePolicy, StatusUpdate
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
ai_first_service = AIFirstService()
guardrails = AIGuardrails()


@router.post("/autoplan", response_model=Dict[str, Any])
async def auto_plan_project(
    project_id: int,
    document_content: Optional[str] = None,
    constraints: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Automatically plan a project using AI"""
    try:
        result = await ai_first_service.auto_plan_project(
            project_id=project_id,
            document_content=document_content,
            constraints=constraints,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in auto_plan_project: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-planning failed: {str(e)}")


@router.post("/upload-and-plan", response_model=Dict[str, Any])
async def upload_document_and_plan(
    project_id: int,
    file: UploadFile = File(...),
    constraints: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Upload a document and automatically plan the project using AI"""
    try:
        # Validate file type
        if not file.filename or not any(
            file.filename.lower().endswith(ext) for ext in settings.ALLOWED_EXTENSIONS
        ):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content (for now, just text files)
        content = ""
        if file.filename.lower().endswith('.txt'):
            content = await file.read()
            content = content.decode('utf-8')
        elif file.filename.lower().endswith('.md'):
            content = await file.read()
            content = content.decode('utf-8')
        else:
            # For other file types, you would implement proper text extraction
            content = f"Document: {file.filename}"
        
        # Auto-plan the project
        result = await ai_first_service.auto_plan_project(
            project_id=project_id,
            document_content=content,
            constraints=constraints,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "filename": file.filename,
            "file_size": len(content),
            "planning_result": result
        }
        
    except Exception as e:
        logger.error(f"Error in upload_andPlan: {e}")
        raise HTTPException(status_code=500, detail=f"Upload and planning failed: {str(e)}")


@router.post("/allocate-resources", response_model=Dict[str, Any])
async def auto_allocate_resources(
    project_id: int,
    task_ids: List[int],
    resource_constraints: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Automatically allocate resources to tasks using AI"""
    try:
        result = await ai_first_service.auto_allocate_resources(
            project_id=project_id,
            task_ids=task_ids,
            resource_constraints=resource_constraints,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in auto_allocate_resources: {e}")
        raise HTTPException(status_code=500, detail=f"Resource allocation failed: {str(e)}")


@router.post("/generate-status-update", response_model=Dict[str, Any])
async def generate_status_update_draft(
    user_id: int,
    project_id: int,
    policy_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate AI draft for status update"""
    try:
        result = await ai_first_service.generate_status_update_draft(
            user_id=user_id,
            project_id=project_id,
            policy_id=policy_id,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate_status_update_draft: {e}")
        raise HTTPException(status_code=500, detail=f"Status update generation failed: {str(e)}")


@router.post("/refine-task", response_model=Dict[str, Any])
async def refine_task_with_ai(
    task_id: int,
    refinement_request: str,
    db: AsyncSession = Depends(get_db)
):
    """Ask AI to refine a specific task"""
    try:
        # This would implement task refinement logic
        # For now, return a placeholder response
        return {
            "success": True,
            "task_id": task_id,
            "refined_task": {
                "name": "Refined Task Name",
                "description": "Refined task description based on AI analysis",
                "estimated_hours": 35,
                "confidence": 0.85
            },
            "refinement_reasoning": "AI analyzed the task and suggested improvements based on similar completed tasks and best practices."
        }
        
    except Exception as e:
        logger.error(f"Error in refine_task_with_ai: {e}")
        raise HTTPException(status_code=500, detail=f"Task refinement failed: {str(e)}")


@router.post("/publish-from-draft", response_model=Dict[str, Any])
async def publish_from_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Publish content from AI draft"""
    try:
        # Get the AI draft
        result = await db.execute(
            db.query(AIDraft).where(AIDraft.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        
        if not draft:
            raise HTTPException(status_code=404, detail="AI draft not found")
        
        if draft.status != DraftStatus.APPROVED:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot publish draft with status: {draft.status}"
            )
        
        # Publish based on draft type
        if draft.draft_type == DraftType.WBS:
            success = await ai_first_service._publish_wbs_from_draft(draft_id, db)
            if success:
                return {
                    "success": True,
                    "message": "WBS published successfully",
                    "draft_id": draft_id
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to publish WBS")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Publishing {draft.draft_type} drafts not yet implemented"
            )
        
    except Exception as e:
        logger.error(f"Error in publish_from_draft: {e}")
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")


@router.post("/reallocate", response_model=Dict[str, Any])
async def reallocate_resources(
    project_id: int,
    task_ids: List[int],
    resource_constraints: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db)
):
    """Re-run AI allocation for selected tasks"""
    try:
        result = await ai_first_service.auto_allocate_resources(
            project_id=project_id,
            task_ids=task_ids,
            resource_constraints=resource_constraints,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in reallocate_resources: {e}")
        raise HTTPException(status_code=500, detail=f"Resource reallocation failed: {str(e)}")


@router.get("/drafts/{project_id}", response_model=List[Dict[str, Any]])
async def get_project_drafts(
    project_id: int,
    draft_type: Optional[DraftType] = None,
    status: Optional[DraftStatus] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get AI drafts for a project"""
    try:
        query = db.query(AIDraft).where(AIDraft.project_id == project_id)
        
        if draft_type:
            query = query.where(AIDraft.draft_type == draft_type)
        
        if status:
            query = query.where(AIDraft.status == status)
        
        result = await db.execute(query)
        drafts = result.scalars().all()
        
        return [
            {
                "id": draft.id,
                "type": draft.draft_type,
                "status": draft.status,
                "created_at": draft.created_at.isoformat(),
                "confidence_score": draft.confidence_score,
                "validation_errors": draft.validation_errors,
                "guardrail_violations": draft.guardrail_violations
            }
            for draft in drafts
        ]
        
    except Exception as e:
        logger.error(f"Error getting project drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")


@router.put("/drafts/{draft_id}/approve", response_model=Dict[str, Any])
async def approve_draft(
    draft_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Approve an AI draft"""
    try:
        result = await db.execute(
            db.query(AIDraft).where(AIDraft.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        
        if not draft:
            raise HTTPException(status_code=404, detail="AI draft not found")
        
        if draft.status != DraftStatus.DRAFT:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot approve draft with status: {draft.status}"
            )
        
        # Update draft status
        draft.status = DraftStatus.APPROVED
        await db.commit()
        
        return {
            "success": True,
            "message": "Draft approved successfully",
            "draft_id": draft_id
        }
        
    except Exception as e:
        logger.error(f"Error approving draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to approve draft: {str(e)}")


@router.put("/drafts/{draft_id}/reject", response_model=Dict[str, Any])
async def reject_draft(
    draft_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Reject an AI draft"""
    try:
        result = await db.execute(
            db.query(AIDraft).where(AIDraft.id == draft_id)
        )
        draft = result.scalar_one_or_none()
        
        if not draft:
            raise HTTPException(status_code=404, detail="AI draft not found")
        
        if draft.status != DraftStatus.DRAFT:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot reject draft with status: {draft.status}"
            )
        
        # Update draft status and add rejection reason
        draft.status = DraftStatus.REJECTED
        if not draft.rationale:
            draft.rationale = {}
        draft.rationale["rejection_reason"] = reason
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Draft rejected successfully",
            "draft_id": draft_id
        }
        
    except Exception as e:
        logger.error(f"Error rejecting draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reject draft: {str(e)}")


@router.post("/validate-output", response_model=Dict[str, Any])
async def validate_ai_output(
    output_type: str,
    output_data: Dict[str, Any],
    constraints: Optional[Dict[str, Any]] = None
):
    """Validate AI output using guardrails"""
    try:
        if output_type == "wbs":
            validation_result = await guardrails.validate_wbs_output(
                output_data, 
                constraints or {}
            )
        elif output_type == "allocation":
            validation_result = await guardrails.validate_allocation_output(
                output_data, 
                constraints or {}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported output type: {output_type}"
            )
        
        return {
            "is_valid": validation_result.is_valid,
            "confidence_score": validation_result.confidence_score,
            "violations": [
                {
                    "rule": v.rule_name,
                    "severity": v.severity,
                    "message": v.message,
                    "field_path": v.field_path,
                    "suggestion": v.suggestion
                } for v in validation_result.violations
            ],
            "repair_suggestions": validation_result.repair_suggestions
        }
        
    except Exception as e:
        logger.error(f"Error validating AI output: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/status-update-policies/{project_id}", response_model=List[Dict[str, Any]])
async def get_status_update_policies(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get status update policies for a project"""
    try:
        result = await db.execute(
            db.query(StatusUpdatePolicy).where(
                StatusUpdatePolicy.project_id == project_id,
                StatusUpdatePolicy.is_active == True
            )
        )
        policies = result.scalars().all()
        
        return [
            {
                "id": policy.id,
                "name": policy.name,
                "description": policy.description,
                "frequency": policy.frequency,
                "custom_days": policy.custom_days,
                "reminder_time": policy.reminder_time.isoformat() if policy.reminder_time else None,
                "timezone": policy.timezone,
                "ai_generate_draft": policy.ai_generate_draft,
                "ai_suggest_improvements": policy.ai_suggest_improvements
            }
            for policy in policies
        ]
        
    except Exception as e:
        logger.error(f"Error getting status update policies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")


@router.get("/required-updates/{user_id}", response_model=List[Dict[str, Any]])
async def get_required_updates(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get required status updates for a user"""
    try:
        # This would implement logic to determine which updates are due
        # For now, return a placeholder
        return [
            {
                "project_id": 1,
                "project_name": "Sample Project",
                "policy_id": 1,
                "policy_name": "Weekly Updates",
                "due_date": "2025-01-20",
                "status": "overdue"
            }
        ]
        
    except Exception as e:
        logger.error(f"Error getting required updates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get required updates: {str(e)}")


@router.get("/ai-insights/{project_id}", response_model=Dict[str, Any])
async def get_ai_insights(
    project_id: int,
    insight_type: str = "general",
    db: AsyncSession = Depends(get_db)
):
    """Get AI-generated insights for a project"""
    try:
        # This would implement AI insight generation
        # For now, return placeholder insights
        insights = {
            "general": {
                "project_health": "Good",
                "risk_level": "Low",
                "key_metrics": {
                    "progress": "75%",
                    "budget_utilization": "60%",
                    "schedule_variance": "2 days ahead"
                }
            },
            "risks": [
                {
                    "description": "Resource availability in Q2",
                    "probability": "Medium",
                    "impact": "High",
                    "mitigation": "Start resource planning early"
                }
            ],
            "recommendations": [
                "Consider adding a QA resource for the testing phase",
                "Review task dependencies to optimize critical path"
            ]
        }
        
        return {
            "project_id": project_id,
            "insight_type": insight_type,
            "insights": insights.get(insight_type, insights["general"]),
            "generated_at": "2025-01-20T10:00:00Z",
            "confidence": 0.85
        }
        
    except Exception as e:
        logger.error(f"Error getting AI insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def get_ai_first_health():
    """Get AI-first service health status"""
    try:
        # Check Ollama connection
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        ollama_status = "unreachable"
    
    return {
        "status": "operational",
        "ai_first_mode": settings.AI_FIRST_MODE,
        "ai_autopublish_default": settings.AI_AUTOPUBLISH_DEFAULT,
        "ai_guardrails_enabled": settings.AI_GUARDRAILS_ENABLED,
        "ollama_status": ollama_status,
        "ai_model": settings.AI_MODEL_NAME,
        "timestamp": "2025-01-20T10:00:00Z"
    }
