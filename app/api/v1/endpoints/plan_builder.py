from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.services.plan_builder import PlanBuilderService
from app.services.rag_engine import RAGEngine
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
plan_builder = PlanBuilderService()
rag_engine = RAGEngine()


@router.post("/extract-plan", response_model=Dict[str, Any])
async def extract_plan_from_document(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Extract project plan from uploaded document (HLD/BRD/SRS)"""
    try:
        # Validate file type
        allowed_extensions = ['.txt', '.md', '.pdf', '.docx', '.doc']
        file_extension = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        if file_extension not in [ext[1:] for ext in allowed_extensions]:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # For now, handle text files only (extend for PDF/DOCX later)
        if file_extension in ['txt', 'md']:
            document_content = content.decode('utf-8')
        else:
            # For now, return error for non-text files
            raise HTTPException(
                status_code=400,
                detail="PDF and DOCX processing not yet implemented. Please upload .txt or .md files."
            )
        
        # Prepare document metadata
        document_metadata = {
            "file_name": file.filename,
            "file_size": len(content),
            "file_type": file_extension,
            "source": "upload",
            "upload_date": datetime.now().isoformat()
        }
        
        # Extract plan using AI
        extraction_result = await plan_builder.extract_plan_from_document(
            document_content=document_content,
            document_metadata=document_metadata,
            project_id=project_id,
            db=db
        )
        
        if not extraction_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Plan extraction failed: {extraction_result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": f"Plan extracted successfully from {file.filename}",
            "data": extraction_result,
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "type": file_extension
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in plan extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Plan extraction error: {str(e)}")


@router.post("/extract-from-text", response_model=Dict[str, Any])
async def extract_plan_from_text(
    document_content: str = Form(...),
    document_name: str = Form("Untitled Document"),
    project_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Extract project plan from text content"""
    try:
        # Prepare document metadata
        document_metadata = {
            "file_name": document_name,
            "file_size": len(document_content),
            "file_type": "text",
            "source": "text_input",
            "upload_date": datetime.now().isoformat()
        }
        
        # Extract plan using AI
        extraction_result = await plan_builder.extract_plan_from_document(
            document_content=document_content,
            document_metadata=document_metadata,
            project_id=project_id,
            db=db
        )
        
        if not extraction_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Plan extraction failed: {extraction_result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": f"Plan extracted successfully from text content",
            "data": extraction_result,
            "file_info": {
                "filename": document_name,
                "size": len(document_content),
                "type": "text"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in text plan extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Plan extraction error: {str(e)}")


@router.get("/document-types", response_model=Dict[str, Any])
async def get_supported_document_types():
    """Get supported document types for plan extraction"""
    return {
        "success": True,
        "supported_types": {
            "hld": {
                "name": "High-Level Design",
                "description": "System architecture and technical design documents",
                "patterns": ["high level design", "hld", "architecture", "system design", "technical design"],
                "extensions": [".txt", ".md", ".pdf", ".docx"]
            },
            "brd": {
                "name": "Business Requirements Document",
                "description": "Business requirements and use case documents",
                "patterns": ["business requirements", "brd", "requirements document", "business case"],
                "extensions": [".txt", ".md", ".pdf", ".docx"]
            },
            "srs": {
                "name": "Software Requirements Specification",
                "description": "Functional and non-functional requirements documents",
                "patterns": ["software requirements", "srs", "functional requirements", "specification"],
                "extensions": [".txt", ".md", ".pdf", ".docx"]
            }
        },
        "file_extensions": [".txt", ".md", ".pdf", ".docx", ".doc"],
        "max_file_size": "10MB"
    }


@router.post("/validate-plan", response_model=Dict[str, Any])
async def validate_extracted_plan(
    plan_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Validate an extracted plan structure"""
    try:
        # Extract components from plan data
        extraction_result = plan_data.get("extraction", {})
        dependency_result = plan_data.get("dependencies", {})
        risk_result = plan_data.get("risks", {})
        effort_result = plan_data.get("efforts", {})
        
        # Validate using guardrails
        validation_result = await plan_builder.guardrails.validate_extracted_plan(
            extraction_result,
            dependency_result,
            risk_result,
            effort_result
        )
        
        return {
            "success": True,
            "validation": {
                "is_valid": validation_result.is_valid,
                "violations": [
                    {
                        "rule_name": v.rule_name,
                        "severity": v.severity,
                        "message": v.message,
                        "field_path": v.field_path,
                        "current_value": v.current_value,
                        "expected_value": v.expected_value,
                        "suggestion": v.suggestion
                    }
                    for v in validation_result.violations
                ],
                "repair_suggestions": validation_result.repair_suggestions,
                "confidence_score": validation_result.confidence_score
            }
        }
        
    except Exception as e:
        logger.error(f"Error validating plan: {e}")
        raise HTTPException(status_code=500, detail=f"Plan validation error: {str(e)}")


@router.post("/repair-plan", response_model=Dict[str, Any])
async def repair_extracted_plan(
    plan_data: Dict[str, Any],
    violations: List[Dict[str, Any]],
    db: AsyncSession = Depends(get_db)
):
    """Repair an extracted plan based on validation violations"""
    try:
        # Convert violations back to GuardrailViolation objects
        from app.services.ai_guardrails import GuardrailViolation
        
        guardrail_violations = []
        for v in violations:
            guardrail_violations.append(GuardrailViolation(
                rule_name=v.get("rule_name", ""),
                severity=v.get("severity", "error"),
                message=v.get("message", ""),
                field_path=v.get("field_path", ""),
                current_value=v.get("current_value"),
                expected_value=v.get("expected_value"),
                suggestion=v.get("suggestion")
            ))
        
        # Repair the plan
        repaired_plan = await plan_builder.guardrails.repair_extracted_plan(
            plan_data.get("extraction", {}),
            guardrail_violations
        )
        
        return {
            "success": True,
            "message": "Plan repaired successfully",
            "repaired_plan": repaired_plan
        }
        
    except Exception as e:
        logger.error(f"Error repairing plan: {e}")
        raise HTTPException(status_code=500, detail=f"Plan repair error: {str(e)}")
