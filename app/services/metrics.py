#!/usr/bin/env python3
"""
EVM (Earned Value Management) Service
Calculates Schedule Variance (SV), Cost Variance (CV), SPI, CPI and other project metrics
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.project import Project, Task
from app.models.finance import Budget
from app.models.project import TaskStatus, ProjectStatus
from app.core.config import settings

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of EVM metrics"""
    SCHEDULE_VARIANCE = "schedule_variance"
    COST_VARIANCE = "cost_variance"
    SCHEDULE_PERFORMANCE_INDEX = "schedule_performance_index"
    COST_PERFORMANCE_INDEX = "cost_performance_index"
    BUDGET_AT_COMPLETION = "budget_at_completion"
    ESTIMATE_AT_COMPLETION = "estimate_at_completion"
    VARIANCE_AT_COMPLETION = "variance_at_completion"
    TO_COMPLETE_PERFORMANCE_INDEX = "to_complete_performance_index"


@dataclass
class EVMMetrics:
    """Earned Value Management metrics"""
    project_id: int
    calculation_date: date
    
    # Planned Value (PV) - Budgeted Cost of Work Scheduled
    planned_value: float
    
    # Earned Value (EV) - Budgeted Cost of Work Performed
    earned_value: float
    
    # Actual Cost (AC) - Actual Cost of Work Performed
    actual_cost: float
    
    # Schedule Variance (SV) = EV - PV
    schedule_variance: float
    
    # Cost Variance (CV) = EV - AC
    cost_variance: float
    
    # Schedule Performance Index (SPI) = EV / PV
    schedule_performance_index: float
    
    # Cost Performance Index (CPI) = EV / AC
    cost_performance_index: float
    
    # Budget at Completion (BAC)
    budget_at_completion: float
    
    # Estimate at Completion (EAC)
    estimate_at_completion: float
    
    # Variance at Completion (VAC) = BAC - EAC
    variance_at_completion: float
    
    # To Complete Performance Index (TCPI)
    to_complete_performance_index: float
    
    # Additional metrics
    completion_percentage: float
    schedule_percentage: float
    cost_percentage: float


@dataclass
class VarianceAnalysis:
    """Variance analysis results"""
    metric_type: MetricType
    current_value: float
    baseline_value: float
    variance_amount: float
    variance_percentage: float
    trend: str  # improving, declining, stable
    severity: str  # low, medium, high, critical
    recommendation: str


class EVMService:
    """Service for Earned Value Management calculations"""
    
    def __init__(self):
        self.performance_thresholds = {
            "spi_critical": 0.8,  # SPI below 0.8 is critical
            "spi_high": 0.9,      # SPI below 0.9 is high risk
            "cpi_critical": 0.8,  # CPI below 0.8 is critical
            "cpi_high": 0.9,      # CPI below 0.9 is high risk
            "sv_critical": -0.2,  # SV below -20% is critical
            "cv_critical": -0.2   # CV below -20% is critical
        }
    
    async def calculate_project_evm(
        self, 
        project_id: int, 
        db: AsyncSession,
        calculation_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate EVM metrics for a project"""
        try:
            # Get project
            project = await self._get_project(project_id, db)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Use current date if not specified
            if not calculation_date:
                calculation_date = date.today()
            
            # Get project tasks
            tasks = await self._get_project_tasks(project_id, db)
            
            # Get project budget
            budget = await self._get_project_budget(project_id, db)
            
            # Calculate EVM components
            planned_value = await self._calculate_planned_value(tasks, calculation_date)
            earned_value = await self._calculate_earned_value(tasks, calculation_date)
            actual_cost = await self._calculate_actual_cost(tasks, calculation_date)
            budget_at_completion = await self._calculate_bac(tasks, budget)
            
            # Calculate derived metrics
            schedule_variance = earned_value - planned_value
            cost_variance = earned_value - actual_cost
            
            schedule_performance_index = earned_value / planned_value if planned_value > 0 else 0
            cost_performance_index = earned_value / actual_cost if actual_cost > 0 else 0
            
            # Calculate completion percentages
            completion_percentage = await self._calculate_completion_percentage(tasks)
            schedule_percentage = await self._calculate_schedule_percentage(tasks, calculation_date)
            cost_percentage = actual_cost / budget_at_completion if budget_at_completion > 0 else 0
            
            # Calculate EAC and VAC
            estimate_at_completion = await self._calculate_eac(
                budget_at_completion, cost_performance_index
            )
            variance_at_completion = budget_at_completion - estimate_at_completion
            
            # Calculate TCPI
            to_complete_performance_index = await self._calculate_tcpi(
                budget_at_completion, earned_value, estimate_at_completion
            )
            
            # Create EVM metrics object
            evm_metrics = EVMMetrics(
                project_id=project_id,
                calculation_date=calculation_date,
                planned_value=planned_value,
                earned_value=earned_value,
                actual_cost=actual_cost,
                schedule_variance=schedule_variance,
                cost_variance=cost_variance,
                schedule_performance_index=schedule_performance_index,
                cost_performance_index=cost_performance_index,
                budget_at_completion=budget_at_completion,
                estimate_at_completion=estimate_at_completion,
                variance_at_completion=variance_at_completion,
                to_complete_performance_index=to_complete_performance_index,
                completion_percentage=completion_percentage,
                schedule_percentage=schedule_percentage,
                cost_percentage=cost_percentage
            )
            
            # Generate variance analysis
            variance_analysis = await self._generate_variance_analysis(evm_metrics)
            
            return {
                "success": True,
                "project_id": project_id,
                "calculation_date": calculation_date.isoformat(),
                "metrics": {
                    "planned_value": evm_metrics.planned_value,
                    "earned_value": evm_metrics.earned_value,
                    "actual_cost": evm_metrics.actual_cost,
                    "schedule_variance": evm_metrics.schedule_variance,
                    "cost_variance": evm_metrics.cost_variance,
                    "schedule_performance_index": evm_metrics.schedule_performance_index,
                    "cost_performance_index": evm_metrics.cost_performance_index,
                    "budget_at_completion": evm_metrics.budget_at_completion,
                    "estimate_at_completion": evm_metrics.estimate_at_completion,
                    "variance_at_completion": evm_metrics.variance_at_completion,
                    "to_complete_performance_index": evm_metrics.to_complete_performance_index,
                    "completion_percentage": evm_metrics.completion_percentage,
                    "schedule_percentage": evm_metrics.schedule_percentage,
                    "cost_percentage": evm_metrics.cost_percentage
                },
                "variance_analysis": [
                    {
                        "metric_type": v.metric_type.value,
                        "current_value": v.current_value,
                        "baseline_value": v.baseline_value,
                        "variance_amount": v.variance_amount,
                        "variance_percentage": v.variance_percentage,
                        "trend": v.trend,
                        "severity": v.severity,
                        "recommendation": v.recommendation
                    }
                    for v in variance_analysis
                ],
                "summary": {
                    "overall_health": self._calculate_overall_health(evm_metrics),
                    "critical_issues": len([v for v in variance_analysis if v.severity == "critical"]),
                    "high_risk_items": len([v for v in variance_analysis if v.severity == "high"]),
                    "on_track": len([v for v in variance_analysis if v.severity == "low"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating EVM metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def calculate_portfolio_evm(
        self, 
        db: AsyncSession,
        calculation_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Calculate EVM metrics for entire portfolio"""
        try:
            if not calculation_date:
                calculation_date = date.today()
            
            # Get all active projects
            projects = await self._get_active_projects(db)
            
            portfolio_metrics = {
                "total_projects": len(projects),
                "total_planned_value": 0,
                "total_earned_value": 0,
                "total_actual_cost": 0,
                "total_budget": 0,
                "projects_on_track": 0,
                "projects_at_risk": 0,
                "projects_critical": 0
            }
            
            project_evm_results = []
            
            for project in projects:
                evm_result = await self.calculate_project_evm(project.id, db, calculation_date)
                if evm_result["success"]:
                    metrics = evm_result["metrics"]
                    portfolio_metrics["total_planned_value"] += metrics["planned_value"]
                    portfolio_metrics["total_earned_value"] += metrics["earned_value"]
                    portfolio_metrics["total_actual_cost"] += metrics["actual_cost"]
                    portfolio_metrics["total_budget"] += metrics["budget_at_completion"]
                    
                    # Categorize project health
                    if evm_result["summary"]["overall_health"] == "healthy":
                        portfolio_metrics["projects_on_track"] += 1
                    elif evm_result["summary"]["overall_health"] == "at_risk":
                        portfolio_metrics["projects_at_risk"] += 1
                    else:
                        portfolio_metrics["projects_critical"] += 1
                    
                    project_evm_results.append({
                        "project_id": project.id,
                        "project_name": project.name,
                        "metrics": metrics,
                        "health": evm_result["summary"]["overall_health"]
                    })
            
            # Calculate portfolio-level metrics
            portfolio_spi = (portfolio_metrics["total_earned_value"] / 
                           portfolio_metrics["total_planned_value"] 
                           if portfolio_metrics["total_planned_value"] > 0 else 0)
            
            portfolio_cpi = (portfolio_metrics["total_earned_value"] / 
                           portfolio_metrics["total_actual_cost"] 
                           if portfolio_metrics["total_actual_cost"] > 0 else 0)
            
            return {
                "success": True,
                "calculation_date": calculation_date.isoformat(),
                "portfolio_metrics": {
                    **portfolio_metrics,
                    "schedule_performance_index": portfolio_spi,
                    "cost_performance_index": portfolio_cpi,
                    "schedule_variance": portfolio_metrics["total_earned_value"] - portfolio_metrics["total_planned_value"],
                    "cost_variance": portfolio_metrics["total_earned_value"] - portfolio_metrics["total_actual_cost"]
                },
                "project_results": project_evm_results,
                "summary": {
                    "overall_portfolio_health": self._calculate_portfolio_health(portfolio_spi, portfolio_cpi),
                    "total_projects": len(projects),
                    "healthy_projects": portfolio_metrics["projects_on_track"],
                    "at_risk_projects": portfolio_metrics["projects_at_risk"],
                    "critical_projects": portfolio_metrics["projects_critical"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio EVM: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_evm_report(
        self, 
        project_id: int, 
        db: AsyncSession,
        report_type: str = "weekly"
    ) -> Dict[str, Any]:
        """Generate EVM report for a project"""
        try:
            # Calculate current EVM metrics
            current_evm = await self.calculate_project_evm(project_id, db)
            if not current_evm["success"]:
                return current_evm
            
            # Get historical data if available
            historical_data = await self._get_historical_evm_data(project_id, db, report_type)
            
            # Generate trends
            trends = await self._calculate_evm_trends(historical_data, current_evm["metrics"])
            
            # Generate recommendations
            recommendations = await self._generate_evm_recommendations(current_evm)
            
            return {
                "success": True,
                "project_id": project_id,
                "report_type": report_type,
                "generated_date": date.today().isoformat(),
                "current_metrics": current_evm["metrics"],
                "variance_analysis": current_evm["variance_analysis"],
                "trends": trends,
                "recommendations": recommendations,
                "summary": current_evm["summary"]
            }
            
        except Exception as e:
            logger.error(f"Error generating EVM report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _get_project(self, project_id: int, db: AsyncSession) -> Optional[Project]:
        """Get project by ID"""
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()
    
    async def _get_project_tasks(self, project_id: int, db: AsyncSession) -> List[Task]:
        """Get all tasks for a project"""
        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.start_date)
        )
        return result.scalars().all()
    
    async def _get_project_budget(self, project_id: int, db: AsyncSession) -> Optional[Budget]:
        """Get project budget"""
        result = await db.execute(select(Budget).where(Budget.project_id == project_id))
        return result.scalar_one_or_none()
    
    async def _get_active_projects(self, db: AsyncSession) -> List[Project]:
        """Get all active projects"""
        result = await db.execute(
            select(Project).where(Project.status.in_([ProjectStatus.ACTIVE, ProjectStatus.PLANNING]))
        )
        return result.scalars().all()
    
    async def _calculate_planned_value(self, tasks: List[Task], calculation_date: date) -> float:
        """Calculate Planned Value (PV) - Budgeted Cost of Work Scheduled"""
        pv = 0.0
        
        for task in tasks:
            if not task.start_date or not task.due_date or not task.estimated_hours:
                continue
            
            # Check if task should be completed by calculation date
            if task.due_date <= calculation_date:
                # Task should be completed, include full budget
                pv += task.estimated_hours * self._get_hourly_rate(task)
            elif task.start_date <= calculation_date <= task.due_date:
                # Task is in progress, calculate partial budget
                total_days = (task.due_date - task.start_date).days + 1
                completed_days = (calculation_date - task.start_date).days + 1
                completion_ratio = min(completed_days / total_days, 1.0)
                pv += (task.estimated_hours * completion_ratio) * self._get_hourly_rate(task)
        
        return pv
    
    async def _calculate_earned_value(self, tasks: List[Task], calculation_date: date) -> float:
        """Calculate Earned Value (EV) - Budgeted Cost of Work Performed"""
        ev = 0.0
        
        for task in tasks:
            if not task.estimated_hours:
                continue
            
            # Calculate based on task status and progress
            if task.status == TaskStatus.DONE:
                # Task completed, full earned value
                ev += task.estimated_hours * self._get_hourly_rate(task)
            elif task.status == TaskStatus.IN_PROGRESS:
                # Task in progress, calculate based on actual hours vs estimated
                if task.actual_hours and task.estimated_hours:
                    progress_ratio = min(task.actual_hours / task.estimated_hours, 1.0)
                    ev += (task.estimated_hours * progress_ratio) * self._get_hourly_rate(task)
                else:
                    # Default 50% progress for in-progress tasks
                    ev += (task.estimated_hours * 0.5) * self._get_hourly_rate(task)
            elif task.status == TaskStatus.REVIEW:
                # Task in review, assume 90% complete
                ev += (task.estimated_hours * 0.9) * self._get_hourly_rate(task)
        
        return ev
    
    async def _calculate_actual_cost(self, tasks: List[Task], calculation_date: date) -> float:
        """Calculate Actual Cost (AC) - Actual Cost of Work Performed"""
        ac = 0.0
        
        for task in tasks:
            if task.actual_hours:
                ac += task.actual_hours * self._get_hourly_rate(task)
        
        return ac
    
    async def _calculate_bac(self, tasks: List[Task], budget: Optional[Budget]) -> float:
        """Calculate Budget at Completion (BAC)"""
        if budget and budget.total_amount:
            return budget.total_amount
        
        # Calculate from task estimates
        bac = 0.0
        for task in tasks:
            if task.estimated_hours:
                bac += task.estimated_hours * self._get_hourly_rate(task)
        
        return bac
    
    async def _calculate_completion_percentage(self, tasks: List[Task]) -> float:
        """Calculate project completion percentage"""
        if not tasks:
            return 0.0
        
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
        return (completed_tasks / len(tasks)) * 100
    
    async def _calculate_schedule_percentage(self, tasks: List[Task], calculation_date: date) -> float:
        """Calculate schedule completion percentage"""
        if not tasks:
            return 0.0
        
        total_days = 0
        completed_days = 0
        
        for task in tasks:
            if not task.start_date or not task.due_date:
                continue
            
            task_days = (task.due_date - task.start_date).days + 1
            total_days += task_days
            
            if task.due_date <= calculation_date:
                completed_days += task_days
            elif task.start_date <= calculation_date <= task.due_date:
                completed_days += (calculation_date - task.start_date).days + 1
        
        return (completed_days / total_days * 100) if total_days > 0 else 0.0
    
    async def _calculate_eac(self, bac: float, cpi: float) -> float:
        """Calculate Estimate at Completion (EAC)"""
        if cpi > 0:
            return bac / cpi
        return bac
    
    async def _calculate_tcpi(self, bac: float, ev: float, eac: float) -> float:
        """Calculate To Complete Performance Index (TCPI)"""
        remaining_work = bac - ev
        remaining_budget = eac - ev
        
        if remaining_budget > 0:
            return remaining_work / remaining_budget
        return 1.0
    
    def _get_hourly_rate(self, task: Task) -> float:
        """Get hourly rate for task (simplified calculation)"""
        # In a real system, this would come from user profiles or project settings
        return 100.0  # Default hourly rate
    
    async def _generate_variance_analysis(self, evm_metrics: EVMMetrics) -> List[VarianceAnalysis]:
        """Generate variance analysis for EVM metrics"""
        analysis = []
        
        # Schedule Variance Analysis
        sv_percentage = (evm_metrics.schedule_variance / evm_metrics.planned_value * 100 
                        if evm_metrics.planned_value > 0 else 0)
        
        sv_severity = self._determine_severity(sv_percentage, "sv")
        analysis.append(VarianceAnalysis(
            metric_type=MetricType.SCHEDULE_VARIANCE,
            current_value=evm_metrics.schedule_variance,
            baseline_value=0,
            variance_amount=evm_metrics.schedule_variance,
            variance_percentage=sv_percentage,
            trend="improving" if evm_metrics.schedule_variance >= 0 else "declining",
            severity=sv_severity,
            recommendation=self._get_sv_recommendation(sv_percentage)
        ))
        
        # Cost Variance Analysis
        cv_percentage = (evm_metrics.cost_variance / evm_metrics.earned_value * 100 
                        if evm_metrics.earned_value > 0 else 0)
        
        cv_severity = self._determine_severity(cv_percentage, "cv")
        analysis.append(VarianceAnalysis(
            metric_type=MetricType.COST_VARIANCE,
            current_value=evm_metrics.cost_variance,
            baseline_value=0,
            variance_amount=evm_metrics.cost_variance,
            variance_percentage=cv_percentage,
            trend="improving" if evm_metrics.cost_variance >= 0 else "declining",
            severity=cv_severity,
            recommendation=self._get_cv_recommendation(cv_percentage)
        ))
        
        # SPI Analysis
        spi_severity = self._determine_severity(evm_metrics.schedule_performance_index, "spi")
        analysis.append(VarianceAnalysis(
            metric_type=MetricType.SCHEDULE_PERFORMANCE_INDEX,
            current_value=evm_metrics.schedule_performance_index,
            baseline_value=1.0,
            variance_amount=evm_metrics.schedule_performance_index - 1.0,
            variance_percentage=(evm_metrics.schedule_performance_index - 1.0) * 100,
            trend="improving" if evm_metrics.schedule_performance_index >= 1.0 else "declining",
            severity=spi_severity,
            recommendation=self._get_spi_recommendation(evm_metrics.schedule_performance_index)
        ))
        
        # CPI Analysis
        cpi_severity = self._determine_severity(evm_metrics.cost_performance_index, "cpi")
        analysis.append(VarianceAnalysis(
            metric_type=MetricType.COST_PERFORMANCE_INDEX,
            current_value=evm_metrics.cost_performance_index,
            baseline_value=1.0,
            variance_amount=evm_metrics.cost_performance_index - 1.0,
            variance_percentage=(evm_metrics.cost_performance_index - 1.0) * 100,
            trend="improving" if evm_metrics.cost_performance_index >= 1.0 else "declining",
            severity=cpi_severity,
            recommendation=self._get_cpi_recommendation(evm_metrics.cost_performance_index)
        ))
        
        return analysis
    
    def _determine_severity(self, value: float, metric_type: str) -> str:
        """Determine severity level based on metric value"""
        if metric_type in ["spi", "cpi"]:
            if value < self.performance_thresholds[f"{metric_type}_critical"]:
                return "critical"
            elif value < self.performance_thresholds[f"{metric_type}_high"]:
                return "high"
            elif value < 1.0:
                return "medium"
            else:
                return "low"
        elif metric_type in ["sv", "cv"]:
            if value < self.performance_thresholds[f"{metric_type}_critical"]:
                return "critical"
            elif value < -0.1:
                return "high"
            elif value < 0:
                return "medium"
            else:
                return "low"
        
        return "low"
    
    def _get_sv_recommendation(self, sv_percentage: float) -> str:
        """Get recommendation for Schedule Variance"""
        if sv_percentage < -20:
            return "Critical schedule delay. Consider adding resources or reducing scope."
        elif sv_percentage < -10:
            return "Significant schedule delay. Review task dependencies and resource allocation."
        elif sv_percentage < 0:
            return "Minor schedule delay. Monitor progress closely."
        else:
            return "Schedule is on track or ahead of plan."
    
    def _get_cv_recommendation(self, cv_percentage: float) -> str:
        """Get recommendation for Cost Variance"""
        if cv_percentage < -20:
            return "Critical cost overrun. Review budget and consider cost-cutting measures."
        elif cv_percentage < -10:
            return "Significant cost overrun. Analyze cost drivers and optimize processes."
        elif cv_percentage < 0:
            return "Minor cost overrun. Monitor spending closely."
        else:
            return "Cost is under control or under budget."
    
    def _get_spi_recommendation(self, spi: float) -> str:
        """Get recommendation for Schedule Performance Index"""
        if spi < 0.8:
            return "Critical schedule performance. Immediate intervention required."
        elif spi < 0.9:
            return "Poor schedule performance. Review project plan and resource allocation."
        elif spi < 1.0:
            return "Below target schedule performance. Monitor and adjust as needed."
        else:
            return "Schedule performance is on target or better."
    
    def _get_cpi_recommendation(self, cpi: float) -> str:
        """Get recommendation for Cost Performance Index"""
        if cpi < 0.8:
            return "Critical cost performance. Immediate cost control measures needed."
        elif cpi < 0.9:
            return "Poor cost performance. Review cost management processes."
        elif cpi < 1.0:
            return "Below target cost performance. Monitor costs closely."
        else:
            return "Cost performance is on target or better."
    
    def _calculate_overall_health(self, evm_metrics: EVMMetrics) -> str:
        """Calculate overall project health based on EVM metrics"""
        critical_count = 0
        high_count = 0
        
        # Check SPI
        if evm_metrics.schedule_performance_index < self.performance_thresholds["spi_critical"]:
            critical_count += 1
        elif evm_metrics.schedule_performance_index < self.performance_thresholds["spi_high"]:
            high_count += 1
        
        # Check CPI
        if evm_metrics.cost_performance_index < self.performance_thresholds["cpi_critical"]:
            critical_count += 1
        elif evm_metrics.cost_performance_index < self.performance_thresholds["cpi_high"]:
            high_count += 1
        
        if critical_count > 0:
            return "critical"
        elif high_count > 0:
            return "at_risk"
        else:
            return "healthy"
    
    def _calculate_portfolio_health(self, spi: float, cpi: float) -> str:
        """Calculate overall portfolio health"""
        if spi < 0.8 or cpi < 0.8:
            return "critical"
        elif spi < 0.9 or cpi < 0.9:
            return "at_risk"
        else:
            return "healthy"
    
    async def _get_historical_evm_data(self, project_id: int, db: AsyncSession, report_type: str) -> List[Dict]:
        """Get historical EVM data for trend analysis"""
        # This would typically query a historical metrics table
        # For now, return empty list
        return []
    
    async def _calculate_evm_trends(self, historical_data: List[Dict], current_metrics: Dict) -> Dict[str, Any]:
        """Calculate EVM trends over time"""
        # Simplified trend calculation
        return {
            "spi_trend": "stable",
            "cpi_trend": "stable",
            "sv_trend": "stable",
            "cv_trend": "stable"
        }
    
    async def _generate_evm_recommendations(self, evm_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on EVM analysis"""
        recommendations = []
        
        metrics = evm_result["metrics"]
        
        if metrics["schedule_performance_index"] < 0.9:
            recommendations.append("Consider adding resources to improve schedule performance")
        
        if metrics["cost_performance_index"] < 0.9:
            recommendations.append("Review cost management processes and identify cost drivers")
        
        if metrics["schedule_variance"] < 0:
            recommendations.append("Analyze critical path and consider schedule compression techniques")
        
        if metrics["cost_variance"] < 0:
            recommendations.append("Implement cost control measures and review resource allocation")
        
        if not recommendations:
            recommendations.append("Project is performing well. Continue current management approach.")
        
        return recommendations
