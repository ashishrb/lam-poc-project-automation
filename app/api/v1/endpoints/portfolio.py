#!/usr/bin/env python3
"""
API endpoints for Portfolio Analytics Service
Portfolio-level analytics, predictive resource allocation, and advanced reporting
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.portfolio_analytics import PortfolioAnalyticsService, AnalyticsPeriod, ResourceAllocationType
from app.schemas.portfolio import (
    PortfolioMetricsResponse,
    ResourceAllocationResponse,
    PortfolioTrendsResponse,
    PortfolioReportResponse,
    DashboardResponse,
    ReportFilters
)

router = APIRouter()
portfolio_service = PortfolioAnalyticsService()


@router.get("/portfolio/metrics", response_model=PortfolioMetricsResponse)
async def get_portfolio_metrics(
    period: Optional[AnalyticsPeriod] = Query(None, description="Analytics period"),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive portfolio metrics"""
    result = await portfolio_service.calculate_portfolio_metrics(db, period)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return PortfolioMetricsResponse(**result)


@router.get("/portfolio/resource-allocation", response_model=ResourceAllocationResponse)
async def get_resource_allocation(
    allocation_type: ResourceAllocationType = Query(ResourceAllocationType.OPTIMAL, description="Allocation type"),
    db: AsyncSession = Depends(get_db)
):
    """Get predictive resource allocation recommendations"""
    result = await portfolio_service.predict_resource_allocation(allocation_type, db)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return ResourceAllocationResponse(**result)


@router.get("/portfolio/trends/{metric_name}", response_model=PortfolioTrendsResponse)
async def get_portfolio_trends(
    metric_name: str,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTHLY, description="Analytics period"),
    lookback_periods: int = Query(12, description="Number of lookback periods"),
    db: AsyncSession = Depends(get_db)
):
    """Analyze trends for a specific metric over time"""
    result = await portfolio_service.analyze_portfolio_trends(metric_name, period, db, lookback_periods)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return PortfolioTrendsResponse(**result)


@router.get("/portfolio/reports/{report_type}", response_model=PortfolioReportResponse)
async def generate_portfolio_report(
    report_type: str,
    filters: Optional[ReportFilters] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate comprehensive portfolio report"""
    filter_dict = filters.dict() if filters else None
    result = await portfolio_service.generate_portfolio_report(report_type, db, filter_dict)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return PortfolioReportResponse(**result)


@router.get("/portfolio/dashboard", response_model=DashboardResponse)
async def get_portfolio_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """Get real-time portfolio dashboard metrics"""
    try:
        # Get portfolio metrics
        metrics_result = await portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return DashboardResponse(
                success=False,
                metrics=None,
                last_updated=datetime.now().isoformat(),
                error=metrics_result["error"]
            )
        
        metrics = metrics_result["portfolio_metrics"]
        
        # Create dashboard metrics
        dashboard_metrics = {
            "portfolio_health": metrics["portfolio_health_score"],
            "active_projects": metrics["active_projects"],
            "completion_rate": metrics["average_completion_rate"],
            "budget_utilization": (metrics["spent_budget"] / metrics["total_budget"] * 100) if metrics["total_budget"] > 0 else 0,
            "risk_level": "medium",  # Would be calculated from risk distribution
            "trend_direction": "stable"  # Would be calculated from trends
        }
        
        return DashboardResponse(
            success=True,
            metrics=dashboard_metrics,
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        return DashboardResponse(
            success=False,
            metrics=None,
            last_updated=datetime.now().isoformat(),
            error=str(e)
        )


@router.get("/portfolio/health")
async def get_portfolio_health(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio health status"""
    try:
        metrics_result = await portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return {
                "success": False,
                "error": metrics_result["error"]
            }
        
        metrics = metrics_result["portfolio_metrics"]
        health_score = metrics["portfolio_health_score"]
        
        # Determine health status
        if health_score >= 0.8:
            status = "excellent"
            color = "green"
        elif health_score >= 0.6:
            status = "good"
            color = "blue"
        elif health_score >= 0.4:
            status = "fair"
            color = "yellow"
        else:
            status = "poor"
            color = "red"
        
        return {
            "success": True,
            "health_score": health_score,
            "status": status,
            "color": color,
            "active_projects": metrics["active_projects"],
            "completion_rate": metrics["average_completion_rate"],
            "risk_distribution": metrics["risk_distribution"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/portfolio/budget-overview")
async def get_budget_overview(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio budget overview"""
    try:
        metrics_result = await portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return {
                "success": False,
                "error": metrics_result["error"]
            }
        
        metrics = metrics_result["portfolio_metrics"]
        
        return {
            "success": True,
            "total_budget": metrics["total_budget"],
            "spent_budget": metrics["spent_budget"],
            "remaining_budget": metrics["remaining_budget"],
            "utilization_percentage": (metrics["spent_budget"] / metrics["total_budget"] * 100) if metrics["total_budget"] > 0 else 0,
            "average_cost_variance": metrics["average_cost_variance"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/portfolio/performance-summary")
async def get_performance_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio performance summary"""
    try:
        metrics_result = await portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return {
                "success": False,
                "error": metrics_result["error"]
            }
        
        metrics = metrics_result["portfolio_metrics"]
        
        return {
            "success": True,
            "completion_rate": metrics["average_completion_rate"],
            "schedule_variance": metrics["average_schedule_variance"],
            "cost_variance": metrics["average_cost_variance"],
            "total_projects": metrics["total_projects"],
            "active_projects": metrics["active_projects"],
            "completed_projects": metrics["completed_projects"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/portfolio/risk-overview")
async def get_risk_overview(
    db: AsyncSession = Depends(get_db)
):
    """Get portfolio risk overview"""
    try:
        metrics_result = await portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return {
                "success": False,
                "error": metrics_result["error"]
            }
        
        metrics = metrics_result["portfolio_metrics"]
        risk_distribution = metrics["risk_distribution"]
        
        # Calculate overall risk level
        total_projects = sum(risk_distribution.values())
        if total_projects > 0:
            weighted_risk = (
                risk_distribution["low"] * 0 +
                risk_distribution["medium"] * 1 +
                risk_distribution["high"] * 2 +
                risk_distribution["critical"] * 3
            ) / total_projects
            
            if weighted_risk >= 2.5:
                overall_risk = "critical"
            elif weighted_risk >= 1.5:
                overall_risk = "high"
            elif weighted_risk >= 0.5:
                overall_risk = "medium"
            else:
                overall_risk = "low"
        else:
            overall_risk = "low"
        
        return {
            "success": True,
            "overall_risk_level": overall_risk,
            "risk_distribution": risk_distribution,
            "total_projects": total_projects,
            "high_risk_projects": risk_distribution["high"] + risk_distribution["critical"],
            "critical_risk_projects": risk_distribution["critical"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/portfolio/resource-utilization")
async def get_resource_utilization(
    db: AsyncSession = Depends(get_db)
):
    """Get resource utilization overview"""
    try:
        # Get resource allocation with optimal strategy
        allocation_result = await portfolio_service.predict_resource_allocation(ResourceAllocationType.OPTIMAL, db)
        if not allocation_result["success"]:
            return {
                "success": False,
                "error": allocation_result["error"]
            }
        
        recommendations = allocation_result["recommendations"]
        
        # Calculate utilization statistics
        total_resources = len(recommendations)
        avg_current_utilization = sum(r["current_utilization"] for r in recommendations) / total_resources if total_resources > 0 else 0
        avg_recommended_utilization = sum(r["recommended_utilization"] for r in recommendations) / total_resources if total_resources > 0 else 0
        
        # Count resources by utilization level
        under_utilized = len([r for r in recommendations if r["current_utilization"] < 0.5])
        well_utilized = len([r for r in recommendations if 0.5 <= r["current_utilization"] < 0.8])
        over_utilized = len([r for r in recommendations if r["current_utilization"] >= 0.8])
        
        return {
            "success": True,
            "total_resources": total_resources,
            "average_current_utilization": avg_current_utilization,
            "average_recommended_utilization": avg_recommended_utilization,
            "utilization_distribution": {
                "under_utilized": under_utilized,
                "well_utilized": well_utilized,
                "over_utilized": over_utilized
            },
            "resources_needing_reallocation": allocation_result["summary"]["resources_needing_reallocation"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "portfolio_analytics"}
