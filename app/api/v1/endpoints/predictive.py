#!/usr/bin/env python3
"""
API endpoints for Predictive Analytics Service
Risk scoring, causal explanations, and prescriptive playbooks
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.predictive_analytics import PredictiveAnalyticsService, RiskLevel, MitigationAction
from app.schemas.predictive import (
    RiskAssessmentResponse,
    PrescriptivePlaybookResponse,
    MitigationActionRequest,
    MitigationActionResponse,
    OutcomePredictionResponse,
    PortfolioRiskResponse
)

router = APIRouter()
predictive_service = PredictiveAnalyticsService()


@router.get("/projects/{project_id}/risk-assessment", response_model=RiskAssessmentResponse)
async def get_project_risk_assessment(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive risk assessment for a project"""
    result = await predictive_service.calculate_project_risk_score(project_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return RiskAssessmentResponse(**result)


@router.get("/tasks/{task_id}/risk-assessment", response_model=RiskAssessmentResponse)
async def get_task_risk_assessment(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get risk assessment for a specific task"""
    result = await predictive_service.calculate_task_risk_score(task_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return RiskAssessmentResponse(**result)


@router.get("/projects/{project_id}/prescriptive-playbook", response_model=PrescriptivePlaybookResponse)
async def get_prescriptive_playbook(
    project_id: int,
    risk_level: Optional[RiskLevel] = Query(None, description="Filter by risk level"),
    db: AsyncSession = Depends(get_db)
):
    """Get prescriptive playbook with actionable recommendations"""
    result = await predictive_service.generate_prescriptive_playbook(project_id, risk_level, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return PrescriptivePlaybookResponse(**result)


@router.post("/projects/{project_id}/apply-mitigation", response_model=MitigationActionResponse)
async def apply_mitigation_action(
    project_id: int,
    request: MitigationActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """Apply a mitigation action to a project"""
    result = await predictive_service.apply_mitigation_action(
        project_id, 
        request.action_type, 
        request.action_params, 
        db
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return MitigationActionResponse(**result)


@router.get("/projects/{project_id}/predict-outcomes", response_model=OutcomePredictionResponse)
async def predict_project_outcomes(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Predict project outcomes based on current state"""
    result = await predictive_service.predict_project_outcomes(project_id, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return OutcomePredictionResponse(**result)


@router.get("/portfolio/risk-overview", response_model=PortfolioRiskResponse)
async def get_portfolio_risk_overview(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio-level risk overview"""
    try:
        # Get all active projects
        from app.models.project import Project, ProjectStatus
        from sqlalchemy import select
        
        result = await db.execute(
            select(Project).where(Project.status == ProjectStatus.ACTIVE)
        )
        projects = result.scalars().all()
        
        risk_cards = []
        high_risk_count = 0
        critical_risk_count = 0
        total_risk_score = 0
        
        for project in projects:
            risk_result = await predictive_service.calculate_project_risk_score(project.id, db)
            if risk_result["success"]:
                risk_level = RiskLevel(risk_result["risk_level"])
                risk_score = risk_result["risk_score"]
                
                if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    high_risk_count += 1
                if risk_level == RiskLevel.CRITICAL:
                    critical_risk_count += 1
                
                total_risk_score += risk_score
                
                risk_cards.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "critical_factors": risk_result["summary"]["critical_factors"],
                    "high_impact_actions": risk_result["summary"]["high_impact_actions"],
                    "last_updated": risk_result["last_updated"],
                    "trend": "stable"  # Placeholder - would be calculated from historical data
                })
        
        average_risk_score = total_risk_score / len(projects) if projects else 0
        
        return PortfolioRiskResponse(
            success=True,
            total_projects=len(projects),
            high_risk_projects=high_risk_count,
            critical_risk_projects=critical_risk_count,
            average_risk_score=average_risk_score,
            risk_cards=risk_cards
        )
        
    except Exception as e:
        return PortfolioRiskResponse(
            success=False,
            total_projects=0,
            high_risk_projects=0,
            critical_risk_projects=0,
            average_risk_score=0,
            risk_cards=[],
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "predictive_analytics"}
