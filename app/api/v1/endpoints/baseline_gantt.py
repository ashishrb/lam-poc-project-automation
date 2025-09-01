#!/usr/bin/env python3
"""
Baseline and Gantt API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.baseline_service import BaselineService
from app.services.gantt_cpm_service import GanttCPMService
from app.schemas.baseline import (
    BaselineCreate, BaselineApprove, BaselineCompare,
    BaselineResponse, BaselineListResponse, VarianceResponse
)
from app.schemas.gantt import (
    GanttDataResponse, CriticalPathResponse, GanttExportResponse
)

router = APIRouter()
baseline_service = BaselineService()
gantt_service = GanttCPMService()


@router.post("/baselines", response_model=BaselineResponse)
async def create_baseline(
    baseline_data: BaselineCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project baseline"""
    try:
        result = await baseline_service.create_baseline(
            project_id=baseline_data.project_id,
            name=baseline_data.name,
            description=baseline_data.description,
            version=baseline_data.version,
            created_by_id=baseline_data.created_by_id,
            db=db
        )
        
        return JSONResponse(
            status_code=201,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating baseline: {str(e)}")


@router.post("/baselines/{baseline_id}/approve", response_model=BaselineResponse)
async def approve_baseline(
    baseline_id: int,
    approval_data: BaselineApprove,
    db: AsyncSession = Depends(get_db)
):
    """Approve a baseline"""
    try:
        result = await baseline_service.approve_baseline(
            baseline_id=baseline_id,
            approved_by_id=approval_data.approved_by_id,
            db=db
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving baseline: {str(e)}")


@router.get("/baselines/compare", response_model=BaselineResponse)
async def compare_baselines(
    baseline_id_1: int = Query(..., description="First baseline ID"),
    baseline_id_2: int = Query(..., description="Second baseline ID"),
    db: AsyncSession = Depends(get_db)
):
    """Compare two baselines"""
    try:
        result = await baseline_service.compare_baselines(
            baseline_id_1=baseline_id_1,
            baseline_id_2=baseline_id_2,
            db=db
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing baselines: {str(e)}")


@router.post("/projects/{project_id}/variances", response_model=VarianceResponse)
async def calculate_variances(
    project_id: int,
    baseline_id: int = Query(..., description="Baseline ID to compare against"),
    db: AsyncSession = Depends(get_db)
):
    """Calculate variances between baseline and current project state"""
    try:
        result = await baseline_service.calculate_variances(
            project_id=project_id,
            baseline_id=baseline_id,
            db=db
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating variances: {str(e)}")


@router.get("/projects/{project_id}/gantt", response_model=GanttDataResponse)
async def get_gantt_data(
    project_id: int,
    include_completed: bool = Query(True, description="Include completed tasks"),
    include_dependencies: bool = Query(True, description="Include task dependencies"),
    db: AsyncSession = Depends(get_db)
):
    """Get Gantt chart data for a project"""
    try:
        result = await gantt_service.generate_gantt_data(
            project_id=project_id,
            db=db,
            include_completed=include_completed,
            include_dependencies=include_dependencies
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Gantt data: {str(e)}")


@router.get("/projects/{project_id}/critical-path", response_model=CriticalPathResponse)
async def get_critical_path(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Calculate critical path for a project"""
    try:
        result = await gantt_service.calculate_critical_path(
            project_id=project_id,
            db=db
        )
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating critical path: {str(e)}")


@router.get("/projects/{project_id}/gantt/export", response_model=GanttExportResponse)
async def export_gantt_data(
    project_id: int,
    format_type: str = Query("json", description="Export format (json, csv, pdf)"),
    db: AsyncSession = Depends(get_db)
):
    """Export Gantt chart data in various formats"""
    try:
        result = await gantt_service.generate_gantt_export(
            project_id=project_id,
            format_type=format_type,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting Gantt data: {str(e)}")


@router.get("/baselines", response_model=BaselineListResponse)
async def list_baselines(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by baseline status"),
    db: AsyncSession = Depends(get_db)
):
    """List project baselines with optional filtering"""
    try:
        # This would need to be implemented in the baseline service
        # For now, return a placeholder response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "baselines": [],
                "total": 0,
                "message": "Baseline listing not yet implemented"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing baselines: {str(e)}")


@router.get("/projects/{project_id}/baselines", response_model=BaselineListResponse)
async def get_project_baselines(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all baselines for a specific project"""
    try:
        # This would need to be implemented in the baseline service
        # For now, return a placeholder response
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "project_id": project_id,
                "baselines": [],
                "total": 0,
                "message": "Project baseline listing not yet implemented"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting project baselines: {str(e)}")
