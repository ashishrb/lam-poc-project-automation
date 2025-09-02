#!/usr/bin/env python3
"""
Financial Controls API Endpoints
Provides endpoints for budget management, cost tracking, and financial governance.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.financial_controls import (
    get_financial_controls,
    Currency,
    AlertLevel
)
from app.models.project import Project
from app.models.user import User

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/budgets")
async def create_budget(
    budget_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Create a new budget for a project"""
    try:
        project_id = budget_data.get("project_id")
        project_name = budget_data.get("project_name")
        total_budget = budget_data.get("total_budget")
        currency = Currency(budget_data.get("currency", "USD"))
        start_date = budget_data.get("start_date")
        end_date = budget_data.get("end_date")
        
        if not all([project_id, project_name, total_budget]):
            raise HTTPException(status_code=400, detail="project_id, project_name, and total_budget are required")
        
        # Parse dates if provided
        if start_date:
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        financial_controls = get_financial_controls()
        result = await financial_controls.create_budget(
            project_id=project_id,
            project_name=project_name,
            total_budget=total_budget,
            currency=currency,
            start_date=start_date,
            end_date=end_date
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to create budget: {str(e)}"
            }
        )


@router.get("/budgets/{project_id}")
async def get_budget_summary(project_id: int):
    """Get budget summary for a project"""
    try:
        financial_controls = get_financial_controls()
        result = await financial_controls.get_budget_summary(project_id)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting budget summary for project {project_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get budget summary: {str(e)}"
            }
        )


@router.get("/budgets")
async def get_portfolio_summary():
    """Get portfolio-wide budget summary"""
    try:
        financial_controls = get_financial_controls()
        result = await financial_controls.get_portfolio_summary()
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get portfolio summary: {str(e)}"
            }
        )


@router.post("/budgets/{project_id}/costs")
async def add_cost_entry(
    project_id: int,
    cost_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Add a cost entry to a project"""
    try:
        category = cost_data.get("category")
        amount = cost_data.get("amount")
        description = cost_data.get("description")
        currency = Currency(cost_data.get("currency", "USD"))
        approved_by = cost_data.get("approved_by")
        invoice_number = cost_data.get("invoice_number")
        vendor = cost_data.get("vendor")
        tags = cost_data.get("tags", [])
        
        if not all([category, amount, description]):
            raise HTTPException(status_code=400, detail="category, amount, and description are required")
        
        financial_controls = get_financial_controls()
        result = await financial_controls.add_cost_entry(
            project_id=project_id,
            category=category,
            amount=amount,
            description=description,
            currency=currency,
            approved_by=approved_by,
            invoice_number=invoice_number,
            vendor=vendor,
            tags=tags
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error adding cost entry for project {project_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to add cost entry: {str(e)}"
            }
        )


@router.post("/budgets/{project_id}/thresholds")
async def set_budget_threshold(
    project_id: int,
    threshold_data: Dict[str, Any]
):
    """Set a budget threshold for monitoring"""
    try:
        threshold_type = threshold_data.get("threshold_type")
        threshold_value = threshold_data.get("threshold_value")
        alert_level = AlertLevel(threshold_data.get("alert_level", "warning"))
        notification_emails = threshold_data.get("notification_emails", [])
        
        if not all([threshold_type, threshold_value, notification_emails]):
            raise HTTPException(status_code=400, detail="threshold_type, threshold_value, and notification_emails are required")
        
        if threshold_type not in ["percentage", "amount"]:
            raise HTTPException(status_code=400, detail="threshold_type must be 'percentage' or 'amount'")
        
        financial_controls = get_financial_controls()
        result = await financial_controls.set_budget_threshold(
            project_id=project_id,
            threshold_type=threshold_type,
            threshold_value=threshold_value,
            alert_level=alert_level,
            notification_emails=notification_emails
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error setting budget threshold for project {project_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to set budget threshold: {str(e)}"
            }
        )


@router.get("/costs/analysis")
async def get_cost_analysis(
    project_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None
):
    """Get cost analysis with filtering options"""
    try:
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        financial_controls = get_financial_controls()
        result = await financial_controls.get_cost_analysis(
            project_id=project_id,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            category=category
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting cost analysis: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get cost analysis: {str(e)}"
            }
        )


@router.get("/alerts")
async def get_alert_history(
    project_id: Optional[int] = None,
    alert_level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get alert history with filtering"""
    try:
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            parsed_start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            parsed_end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Parse alert level if provided
        parsed_alert_level = None
        if alert_level:
            parsed_alert_level = AlertLevel(alert_level)
        
        financial_controls = get_financial_controls()
        result = await financial_controls.get_alert_history(
            project_id=project_id,
            alert_level=parsed_alert_level,
            start_date=parsed_start_date,
            end_date=parsed_end_date
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Error getting alert history: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get alert history: {str(e)}"
            }
        )


@router.get("/currencies")
async def get_supported_currencies():
    """Get list of supported currencies"""
    try:
        currencies = [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
            {"code": "GBP", "name": "British Pound", "symbol": "£"},
            {"code": "INR", "name": "Indian Rupee", "symbol": "₹"},
            {"code": "CAD", "name": "Canadian Dollar", "symbol": "C$"}
        ]
        
        return JSONResponse(content={
            "success": True,
            "currencies": currencies
        })
        
    except Exception as e:
        logger.error(f"Error getting currencies: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get currencies: {str(e)}"
            }
        )


@router.post("/budgets/{project_id}/forecast")
async def generate_budget_forecast(
    project_id: int,
    forecast_data: Dict[str, Any]
):
    """Generate budget forecast for a project"""
    try:
        forecast_months = forecast_data.get("forecast_months", 6)
        include_historical = forecast_data.get("include_historical", True)
        
        financial_controls = get_financial_controls()
        
        # Get current budget summary
        budget_summary = await financial_controls.get_budget_summary(project_id)
        if not budget_summary["success"]:
            return JSONResponse(content=budget_summary)
        
        budget = budget_summary["budget_summary"]
        
        # Calculate forecast
        current_spent = float(budget["spent_amount"])
        total_budget = float(budget["total_budget"])
        remaining_budget = float(budget["remaining_amount"])
        
        # Simple linear forecast based on current spending rate
        if include_historical:
            # Calculate average monthly spending
            # Assuming project started 3 months ago for demo
            months_elapsed = 3
            avg_monthly_spending = current_spent / months_elapsed
        else:
            avg_monthly_spending = current_spent / 1  # Current month only
        
        forecast = {
            "project_id": project_id,
            "forecast_months": forecast_months,
            "current_status": {
                "spent_amount": current_spent,
                "remaining_amount": remaining_budget,
                "utilization_percentage": budget["utilization_percentage"]
            },
            "monthly_forecast": [],
            "risk_assessment": "low"
        }
        
        # Generate monthly forecast
        for month in range(1, forecast_months + 1):
            projected_spending = avg_monthly_spending * month
            projected_total = current_spent + projected_spending
            projected_utilization = (projected_total / total_budget) * 100
            
            forecast["monthly_forecast"].append({
                "month": month,
                "projected_spending": projected_spending,
                "projected_total": projected_total,
                "projected_utilization": projected_utilization,
                "status": "under_budget" if projected_utilization < 100 else "over_budget"
            })
        
        # Assess risk
        final_projection = forecast["monthly_forecast"][-1]["projected_utilization"]
        if final_projection > 120:
            forecast["risk_assessment"] = "critical"
        elif final_projection > 100:
            forecast["risk_assessment"] = "high"
        elif final_projection > 80:
            forecast["risk_assessment"] = "medium"
        else:
            forecast["risk_assessment"] = "low"
        
        return JSONResponse(content={
            "success": True,
            "forecast": forecast
        })
        
    except Exception as e:
        logger.error(f"Error generating budget forecast for project {project_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to generate forecast: {str(e)}"
            }
        )


@router.get("/analytics/spending")
async def get_spending_analytics():
    """Get spending analytics across all projects"""
    try:
        financial_controls = get_financial_controls()
        
        # Get portfolio summary
        portfolio_summary = await financial_controls.get_portfolio_summary()
        if not portfolio_summary["success"]:
            return JSONResponse(content=portfolio_summary)
        
        portfolio = portfolio_summary["portfolio_summary"]
        
        # Get cost analysis for all projects
        cost_analysis = await financial_controls.get_cost_analysis()
        if not cost_analysis["success"]:
            return JSONResponse(content=cost_analysis)
        
        analysis = cost_analysis["cost_analysis"]
        
        # Calculate additional analytics
        analytics = {
            "portfolio_overview": {
                "total_projects": portfolio["total_projects"],
                "total_budget": float(portfolio["total_budget"]),
                "total_spent": float(portfolio["total_spent"]),
                "total_remaining": float(portfolio["total_remaining"]),
                "average_utilization": portfolio["average_utilization"],
                "projects_at_risk": portfolio["projects_at_risk"],
                "projects_over_budget": portfolio["projects_over_budget"]
            },
            "spending_patterns": {
                "total_cost": float(analysis["total_cost"]),
                "cost_by_category": {k: float(v) for k, v in analysis["cost_by_category"].items()},
                "cost_by_month": {k: float(v) for k, v in analysis["cost_by_month"].items()},
                "cost_by_vendor": {k: float(v) for k, v in analysis["cost_by_vendor"].items()},
                "currency_breakdown": {k: float(v) for k, v in analysis["currency_breakdown"].items()}
            },
            "top_expenses": analysis["top_expenses"][:10],
            "trends": {
                "monthly_growth": 0.0,  # Would calculate from historical data
                "category_growth": {},
                "budget_variance": 0.0
            }
        }
        
        return JSONResponse(content={
            "success": True,
            "analytics": analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting spending analytics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to get analytics: {str(e)}"
            }
        )


@router.post("/budgets/{project_id}/adjust")
async def adjust_budget(
    project_id: int,
    adjustment_data: Dict[str, Any]
):
    """Adjust budget for a project"""
    try:
        adjustment_amount = adjustment_data.get("adjustment_amount")
        adjustment_type = adjustment_data.get("adjustment_type")  # "increase" or "decrease"
        reason = adjustment_data.get("reason", "")
        approved_by = adjustment_data.get("approved_by")
        
        if not all([adjustment_amount, adjustment_type]):
            raise HTTPException(status_code=400, detail="adjustment_amount and adjustment_type are required")
        
        if adjustment_type not in ["increase", "decrease"]:
            raise HTTPException(status_code=400, detail="adjustment_type must be 'increase' or 'decrease'")
        
        financial_controls = get_financial_controls()
        
        # Get current budget
        budget_summary = await financial_controls.get_budget_summary(project_id)
        if not budget_summary["success"]:
            return JSONResponse(content=budget_summary)
        
        current_budget = budget_summary["budget_summary"]
        
        # Calculate new budget
        if adjustment_type == "increase":
            new_budget = float(current_budget["total_budget"]) + adjustment_amount
        else:
            new_budget = float(current_budget["total_budget"]) - adjustment_amount
        
        if new_budget < 0:
            raise HTTPException(status_code=400, detail="Adjustment would result in negative budget")
        
        # Update budget (in a real system, this would update the database)
        # For demo purposes, we'll just return the calculated values
        
        return JSONResponse(content={
            "success": True,
            "adjustment": {
                "project_id": project_id,
                "adjustment_amount": adjustment_amount,
                "adjustment_type": adjustment_type,
                "old_budget": float(current_budget["total_budget"]),
                "new_budget": new_budget,
                "reason": reason,
                "approved_by": approved_by,
                "adjustment_date": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error adjusting budget for project {project_id}: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to adjust budget: {str(e)}"
            }
        )
