#!/usr/bin/env python3
"""
API endpoints for Dynamic Re-planning & Scenario Simulation (Phase 2)
"""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.scheduler import SchedulerService
from app.services.metrics import EVMService
from app.services.scenario_sim import ScenarioSimulator
from app.schemas.scheduler import (
    ConstraintAnalysisResponse, RescheduleProposalResponse, 
    ResourceOptimizationResponse, ProposalApplyRequest
)
from app.schemas.metrics import (
    EVMMetricsResponse, PortfolioEVMResponse, EVMReportResponse
)
from app.schemas.scenario import (
    ScenarioCreateRequest, ScenarioResponse, ScenarioComparisonResponse,
    ScenarioApplyRequest
)

router = APIRouter(prefix="/v1", tags=["Dynamic Re-planning & Scenario Simulation"])

# Initialize services
scheduler_service = SchedulerService()
evm_service = EVMService()
scenario_simulator = ScenarioSimulator()


# Scheduler endpoints
@router.get("/projects/{project_id}/constraints", response_model=ConstraintAnalysisResponse)
async def analyze_project_constraints(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Analyze all constraints for a project"""
    result = await scheduler_service.analyze_project_constraints(project_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ConstraintAnalysisResponse(**result)


@router.get("/projects/{project_id}/reschedule-proposals", response_model=RescheduleProposalResponse)
async def generate_reschedule_proposals(
    project_id: int,
    task_id: Optional[int] = Query(None, description="Specific task ID to reschedule"),
    db: AsyncSession = Depends(get_db)
):
    """Generate reschedule proposals for a project or specific task"""
    result = await scheduler_service.generate_reschedule_proposals(
        project_id, task_id, db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return RescheduleProposalResponse(**result)


@router.post("/projects/{project_id}/apply-proposal", response_model=dict)
async def apply_reschedule_proposal(
    project_id: int,
    proposal: ProposalApplyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Apply a reschedule proposal"""
    result = await scheduler_service.apply_reschedule_proposal(
        project_id, proposal.dict(), db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/projects/{project_id}/resource-optimization", response_model=ResourceOptimizationResponse)
async def optimize_resource_allocation(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Optimize resource allocation for a project"""
    result = await scheduler_service.optimize_resource_allocation(project_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ResourceOptimizationResponse(**result)


# EVM Metrics endpoints
@router.get("/projects/{project_id}/evm", response_model=EVMMetricsResponse)
async def calculate_project_evm(
    project_id: int,
    calculation_date: Optional[date] = Query(None, description="Date for EVM calculation"),
    db: AsyncSession = Depends(get_db)
):
    """Calculate EVM metrics for a project"""
    result = await evm_service.calculate_project_evm(
        project_id, db, calculation_date
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return EVMMetricsResponse(**result)


@router.get("/portfolio/evm", response_model=PortfolioEVMResponse)
async def calculate_portfolio_evm(
    calculation_date: Optional[date] = Query(None, description="Date for EVM calculation"),
    db: AsyncSession = Depends(get_db)
):
    """Calculate EVM metrics for entire portfolio"""
    result = await evm_service.calculate_portfolio_evm(db, calculation_date)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return PortfolioEVMResponse(**result)


@router.get("/projects/{project_id}/evm-report", response_model=EVMReportResponse)
async def generate_evm_report(
    project_id: int,
    report_type: str = Query("weekly", description="Report type: weekly, monthly, quarterly"),
    db: AsyncSession = Depends(get_db)
):
    """Generate EVM report for a project"""
    result = await evm_service.generate_evm_report(project_id, db, report_type)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return EVMReportResponse(**result)


# Scenario Simulation endpoints
@router.post("/projects/{project_id}/scenarios", response_model=dict)
async def create_scenario(
    project_id: int,
    scenario: ScenarioCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new scenario for simulation"""
    result = await scenario_simulator.create_scenario(
        project_id, scenario.scenario_name, scenario.scenario_type, 
        scenario.parameters, db
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def simulate_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Simulate a scenario and calculate impacts"""
    result = await scenario_simulator.simulate_scenario(scenario_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ScenarioResponse(**result)


@router.post("/projects/{project_id}/scenarios/compare", response_model=ScenarioComparisonResponse)
async def compare_scenarios(
    project_id: int,
    scenario_ids: List[str],
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple scenarios side by side"""
    result = await scenario_simulator.compare_scenarios(project_id, scenario_ids, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return ScenarioComparisonResponse(**result)


@router.post("/scenarios/{scenario_id}/apply", response_model=dict)
async def apply_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Apply a scenario to the actual project"""
    result = await scenario_simulator.apply_scenario(scenario_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


# Health check endpoint
@router.get("/replanning/health")
async def health_check():
    """Health check for re-planning services"""
    return {
        "status": "healthy",
        "services": {
            "scheduler": "available",
            "evm_metrics": "available", 
            "scenario_simulator": "available"
        }
    }
