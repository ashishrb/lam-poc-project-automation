from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import json
import logging

from app.core.database import get_db
from app.core.config import settings
from app.services.ai_copilot import AICopilotService
from app.services.rag_engine import RAGEngine
from app.schemas.common import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
ai_copilot = AICopilotService()
rag_engine = RAGEngine()


@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_copilot(
    message: str,
    context: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Chat with AI Copilot"""
    try:
        # Get relevant context from RAG
        if context and context.get("search_docs"):
            search_results = await rag_engine.search(
                query=message,
                filters=context.get("filters", {}),
                k=5
            )
            context["retrieved_docs"] = search_results
        
        # Process with AI Copilot
        response = await ai_copilot.process_message(
            message=message,
            context=context or {},
            db=db
        )
        
        return {
            "response": response["response"],
            "actions": response.get("actions", []),
            "citations": response.get("citations", []),
            "confidence": response.get("confidence", 0.0),
            "tools_used": response.get("tools_used", [])
        }
        
    except Exception as e:
        logger.error(f"Error in AI Copilot chat: {e}")
        raise HTTPException(status_code=500, detail=f"AI Copilot error: {str(e)}")


@router.post("/search", response_model=Dict[str, Any])
async def search_documents(
    query: str,
    filters: Dict[str, Any] = None,
    k: int = 5,
    db: AsyncSession = Depends(get_db)
):
    """Search documents using RAG"""
    try:
        results = await rag_engine.search(
            query=query,
            filters=filters or {},
            k=k
        )
        
        return {
            "query": query,
            "results": results["items"],
            "total_found": len(results["items"]),
            "search_metadata": results.get("metadata", {})
        }
        
    except Exception as e:
        logger.error(f"Error in document search: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/generate-wbs", response_model=Dict[str, Any])
async def generate_wbs(
    project_id: int,
    constraints: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Generate Work Breakdown Structure for a project"""
    try:
        wbs = await ai_copilot.generate_wbs(
            project_id=project_id,
            constraints=constraints or {},
            db=db
        )
        
        return {
            "project_id": project_id,
            "wbs": wbs["tasks"],
            "dependencies": wbs["dependencies"],
            "estimated_duration": wbs.get("estimated_duration"),
            "confidence": wbs.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error generating WBS: {e}")
        raise HTTPException(status_code=500, detail=f"WBS generation error: {str(e)}")


@router.post("/forecast-budget", response_model=Dict[str, Any])
async def forecast_budget(
    project_id: int,
    horizon: str = "3months",
    drivers: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Forecast project budget"""
    try:
        forecast = await ai_copilot.forecast_budget(
            project_id=project_id,
            horizon=horizon,
            drivers=drivers or {},
            db=db
        )
        
        return {
            "project_id": project_id,
            "forecast": forecast["forecast"],
            "variance_explained": forecast.get("variance_explained"),
            "recommendations": forecast.get("recommendations", []),
            "confidence": forecast.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error forecasting budget: {e}")
        raise HTTPException(status_code=500, detail=f"Budget forecast error: {str(e)}")


@router.post("/explain-variance", response_model=Dict[str, Any])
async def explain_variance(
    project_id: int,
    period: str = "current_month",
    db: AsyncSession = Depends(get_db)
):
    """Explain budget/schedule variance for a project"""
    try:
        explanation = await ai_copilot.explain_variance(
            project_id=project_id,
            period=period,
            db=db
        )
        
        return {
            "project_id": project_id,
            "period": period,
            "narrative": explanation["narrative"],
            "drivers": explanation.get("drivers", []),
            "actions": explanation.get("actions", []),
            "confidence": explanation.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error explaining variance: {e}")
        raise HTTPException(status_code=500, detail=f"Variance explanation error: {str(e)}")


@router.post("/plan-staffing", response_model=Dict[str, Any])
async def plan_staffing(
    project_id: int,
    sprint_range: str = "next_sprint",
    constraints: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Plan staffing for a project/sprint"""
    try:
        staffing_plan = await ai_copilot.plan_staffing(
            project_id=project_id,
            sprint_range=sprint_range,
            constraints=constraints or {},
            db=db
        )
        
        return {
            "project_id": project_id,
            "sprint_range": sprint_range,
            "allocations": staffing_plan["allocations"],
            "gaps": staffing_plan.get("gaps", []),
            "alternatives": staffing_plan.get("alternatives", []),
            "confidence": staffing_plan.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error planning staffing: {e}")
        raise HTTPException(status_code=500, detail=f"Staffing planning error: {str(e)}")


@router.post("/evaluate-resource", response_model=Dict[str, Any])
async def evaluate_resource(
    resource_id: int,
    rubric_id: int = None,
    evidence: Dict[str, Any] = None,
    db: AsyncSession = Depends(get_db)
):
    """Evaluate a resource using AI"""
    try:
        evaluation = await ai_copilot.evaluate_resource(
            resource_id=resource_id,
            rubric_id=rubric_id,
            evidence=evidence or {},
            db=db
        )
        
        return {
            "resource_id": resource_id,
            "scores": evaluation["scores"],
            "summary": evaluation.get("summary"),
            "recommendations": evaluation.get("recommendations", []),
            "confidence": evaluation.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error evaluating resource: {e}")
        raise HTTPException(status_code=500, detail=f"Resource evaluation error: {str(e)}")


@router.post("/create-risk", response_model=Dict[str, Any])
async def create_risk(
    project_id: int,
    risk_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Create a risk assessment using AI"""
    try:
        risk = await ai_copilot.create_risk(
            project_id=project_id,
            risk_data=risk_data,
            db=db
        )
        
        return {
            "project_id": project_id,
            "risk_id": risk["risk_id"],
            "status": risk["status"],
            "assessment": risk.get("assessment"),
            "mitigation_suggestions": risk.get("mitigation_suggestions", [])
        }
        
    except Exception as e:
        logger.error(f"Error creating risk: {e}")
        raise HTTPException(status_code=500, detail=f"Risk creation error: {str(e)}")


@router.post("/generate-report", response_model=Dict[str, Any])
async def generate_report(
    report_type: str,
    scope: Dict[str, Any],
    period: str = "current_month",
    audience: str = "executive",
    db: AsyncSession = Depends(get_db)
):
    """Generate a report using AI"""
    try:
        report = await ai_copilot.generate_report(
            report_type=report_type,
            scope=scope,
            period=period,
            audience=audience,
            db=db
        )
        
        return {
            "report_type": report_type,
            "sections": report["sections"],
            "charts": report.get("charts", []),
            "citations": report.get("citations", []),
            "summary": report.get("summary"),
            "confidence": report.get("confidence", 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")


@router.post("/notify", response_model=Dict[str, Any])
async def notify_stakeholders(
    audience: List[str],
    message: str,
    channel: str = "email",
    db: AsyncSession = Depends(get_db)
):
    """Send notifications using AI"""
    try:
        notification = await ai_copilot.notify(
            audience=audience,
            message=message,
            channel=channel,
            db=db
        )
        
        return {
            "delivery_id": notification["delivery_id"],
            "status": notification["status"],
            "recipients": notification.get("recipients", []),
            "delivery_summary": notification.get("delivery_summary")
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=f"Notification error: {str(e)}")


@router.get("/tools", response_model=List[Dict[str, Any]])
async def list_available_tools():
    """List available AI tools and their schemas"""
    try:
        tools = ai_copilot.get_available_tools()
        return tools
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=f"Tool listing error: {str(e)}")


@router.get("/status", response_model=Dict[str, Any])
async def get_copilot_status():
    """Get AI Copilot system status"""
    try:
        status = await ai_copilot.get_status()
        return status
        
    except Exception as e:
        logger.error(f"Error getting copilot status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check error: {str(e)}")
