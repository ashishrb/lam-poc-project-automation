#!/usr/bin/env python3
"""
Portfolio Analytics Service
Portfolio-level analytics, predictive resource allocation, and advanced reporting
"""

import json
import logging
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc

from app.models.project import Project, Task
from app.models.user import User
from app.models.project import TaskStatus, TaskPriority, ProjectStatus, ProjectPhase
from app.models.finance import Budget
from app.services.metrics import EVMService
from app.services.predictive_analytics import PredictiveAnalyticsService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AnalyticsPeriod(str, Enum):
    """Analytics time periods"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ResourceAllocationType(str, Enum):
    """Resource allocation types"""
    OPTIMAL = "optimal"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"


@dataclass
class PortfolioMetrics:
    """Portfolio-level metrics"""
    total_projects: int
    active_projects: int
    completed_projects: int
    total_budget: float
    spent_budget: float
    remaining_budget: float
    average_completion_rate: float
    average_schedule_variance: float
    average_cost_variance: float
    portfolio_health_score: float
    risk_distribution: Dict[str, int]
    phase_distribution: Dict[str, int]


@dataclass
class ResourceAllocationRecommendation:
    """Resource allocation recommendation"""
    resource_id: int
    resource_name: str
    current_utilization: float
    recommended_utilization: float
    allocation_change: float
    priority_projects: List[int]
    skill_gaps: List[str]
    training_recommendations: List[str]


@dataclass
class PortfolioTrend:
    """Portfolio trend data"""
    period: str
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # increasing, decreasing, stable


class PortfolioAnalyticsService:
    """Service for portfolio-level analytics and reporting"""
    
    def __init__(self):
        self.evm_service = EVMService()
        self.predictive_service = PredictiveAnalyticsService()
        
        # Portfolio health weights
        self.health_weights = {
            "completion_rate": 0.25,
            "schedule_performance": 0.25,
            "cost_performance": 0.20,
            "resource_utilization": 0.15,
            "risk_level": 0.15
        }
    
    async def calculate_portfolio_metrics(
        self, 
        db: AsyncSession,
        period: Optional[AnalyticsPeriod] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive portfolio metrics"""
        try:
            # Get all projects
            projects = await self._get_all_projects(db)
            
            # Calculate basic metrics
            total_projects = len(projects)
            active_projects = len([p for p in projects if p.status == ProjectStatus.ACTIVE])
            completed_projects = len([p for p in projects if p.status == ProjectStatus.COMPLETED])
            
            # Calculate budget metrics
            budget_metrics = await self._calculate_budget_metrics(projects)
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(projects, db)
            
            # Calculate risk distribution
            risk_distribution = await self._calculate_risk_distribution(projects, db)
            
            # Calculate phase distribution
            phase_distribution = await self._calculate_phase_distribution(projects)
            
            # Calculate portfolio health score
            health_score = await self._calculate_portfolio_health_score(
                performance_metrics, risk_distribution
            )
            
            # Create portfolio metrics object
            portfolio_metrics = PortfolioMetrics(
                total_projects=total_projects,
                active_projects=active_projects,
                completed_projects=completed_projects,
                total_budget=budget_metrics["total_budget"],
                spent_budget=budget_metrics["spent_budget"],
                remaining_budget=budget_metrics["remaining_budget"],
                average_completion_rate=performance_metrics["average_completion_rate"],
                average_schedule_variance=performance_metrics["average_schedule_variance"],
                average_cost_variance=performance_metrics["average_cost_variance"],
                portfolio_health_score=health_score,
                risk_distribution=risk_distribution,
                phase_distribution=phase_distribution
            )
            
            return {
                "success": True,
                "portfolio_metrics": {
                    "total_projects": portfolio_metrics.total_projects,
                    "active_projects": portfolio_metrics.active_projects,
                    "completed_projects": portfolio_metrics.completed_projects,
                    "total_budget": portfolio_metrics.total_budget,
                    "spent_budget": portfolio_metrics.spent_budget,
                    "remaining_budget": portfolio_metrics.remaining_budget,
                    "average_completion_rate": portfolio_metrics.average_completion_rate,
                    "average_schedule_variance": portfolio_metrics.average_schedule_variance,
                    "average_cost_variance": portfolio_metrics.average_cost_variance,
                    "portfolio_health_score": portfolio_metrics.portfolio_health_score,
                    "risk_distribution": portfolio_metrics.risk_distribution,
                    "phase_distribution": portfolio_metrics.phase_distribution
                },
                "summary": {
                    "budget_utilization": (portfolio_metrics.spent_budget / portfolio_metrics.total_budget * 100) if portfolio_metrics.total_budget > 0 else 0,
                    "completion_efficiency": portfolio_metrics.average_completion_rate * 100,
                    "health_status": self._get_health_status(portfolio_metrics.portfolio_health_score),
                    "top_risks": self._get_top_risks(risk_distribution)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def predict_resource_allocation(
        self, 
        allocation_type: ResourceAllocationType,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Predict optimal resource allocation for the portfolio"""
        try:
            # Get all resources and their current assignments
            resources = await self._get_all_resources(db)
            projects = await self._get_active_projects(db)
            
            # Calculate current resource utilization
            current_utilization = await self._calculate_current_utilization(resources, projects, db)
            
            # Generate allocation recommendations based on type
            if allocation_type == ResourceAllocationType.OPTIMAL:
                recommendations = await self._generate_optimal_allocation(resources, projects, current_utilization, db)
            elif allocation_type == ResourceAllocationType.BALANCED:
                recommendations = await self._generate_balanced_allocation(resources, projects, current_utilization, db)
            elif allocation_type == ResourceAllocationType.AGGRESSIVE:
                recommendations = await self._generate_aggressive_allocation(resources, projects, current_utilization, db)
            elif allocation_type == ResourceAllocationType.CONSERVATIVE:
                recommendations = await self._generate_conservative_allocation(resources, projects, current_utilization, db)
            else:
                return {
                    "success": False,
                    "error": f"Unknown allocation type: {allocation_type}"
                }
            
            # Calculate allocation impact
            impact_analysis = await self._analyze_allocation_impact(recommendations, projects, db)
            
            return {
                "success": True,
                "allocation_type": allocation_type.value,
                "recommendations": [
                    {
                        "resource_id": rec.resource_id,
                        "resource_name": rec.resource_name,
                        "current_utilization": rec.current_utilization,
                        "recommended_utilization": rec.recommended_utilization,
                        "allocation_change": rec.allocation_change,
                        "priority_projects": rec.priority_projects,
                        "skill_gaps": rec.skill_gaps,
                        "training_recommendations": rec.training_recommendations
                    }
                    for rec in recommendations
                ],
                "impact_analysis": impact_analysis,
                "summary": {
                    "total_resources": len(recommendations),
                    "resources_needing_reallocation": len([r for r in recommendations if abs(r.allocation_change) > 0.1]),
                    "average_utilization_change": sum(r.allocation_change for r in recommendations) / len(recommendations) if recommendations else 0,
                    "estimated_completion_improvement": impact_analysis.get("completion_improvement", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error predicting resource allocation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_portfolio_report(
        self, 
        report_type: str,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        try:
            # Get portfolio metrics
            metrics_result = await self.calculate_portfolio_metrics(db)
            if not metrics_result["success"]:
                return metrics_result
            
            metrics = metrics_result["portfolio_metrics"]
            
            # Generate report based on type
            if report_type == "executive_summary":
                report = await self._generate_executive_summary(metrics, db)
            elif report_type == "performance_analysis":
                report = await self._generate_performance_analysis(metrics, db)
            elif report_type == "risk_assessment":
                report = await self._generate_risk_assessment(metrics, db)
            elif report_type == "resource_analysis":
                report = await self._generate_resource_analysis(metrics, db)
            elif report_type == "financial_analysis":
                report = await self._generate_financial_analysis(metrics, db)
            elif report_type == "comprehensive":
                report = await self._generate_comprehensive_report(metrics, db)
            else:
                return {
                    "success": False,
                    "error": f"Unknown report type: {report_type}"
                }
            
            # Apply filters if provided
            if filters:
                report = await self._apply_report_filters(report, filters)
            
            return {
                "success": True,
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "report_data": report,
                "summary": {
                    "total_sections": len(report),
                    "key_insights": report.get("key_insights", []),
                    "recommendations": report.get("recommendations", [])
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating portfolio report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_portfolio_trends(
        self, 
        metric_name: str,
        period: AnalyticsPeriod,
        db: AsyncSession,
        lookback_periods: int = 12
    ) -> Dict[str, Any]:
        """Analyze trends for a specific metric over time"""
        try:
            trends = []
            current_date = date.today()
            
            # Calculate trends for each period
            for i in range(lookback_periods):
                period_date = self._get_period_date(current_date, period, i)
                period_value = await self._calculate_period_metric(metric_name, period_date, period, db)
                
                if i > 0:
                    previous_value = trends[-1]["current_value"]
                    change_percentage = ((period_value - previous_value) / previous_value * 100) if previous_value != 0 else 0
                    trend_direction = self._determine_trend_direction(change_percentage)
                else:
                    change_percentage = 0
                    trend_direction = "stable"
                
                trends.append({
                    "period": period_date.isoformat(),
                    "metric_name": metric_name,
                    "current_value": period_value,
                    "previous_value": trends[-1]["current_value"] if trends else period_value,
                    "change_percentage": change_percentage,
                    "trend_direction": trend_direction
                })
            
            # Calculate overall trend
            overall_trend = self._calculate_overall_trend(trends)
            
            return {
                "success": True,
                "metric_name": metric_name,
                "period": period.value,
                "lookback_periods": lookback_periods,
                "trends": trends,
                "overall_trend": overall_trend,
                "summary": {
                    "average_change": sum(t["change_percentage"] for t in trends[1:]) / (len(trends) - 1) if len(trends) > 1 else 0,
                    "trend_stability": self._calculate_trend_stability(trends),
                    "forecast": self._generate_forecast(trends)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio trends: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _get_all_projects(self, db: AsyncSession) -> List[Project]:
        """Get all projects"""
        result = await db.execute(select(Project))
        return result.scalars().all()
    
    async def _get_active_projects(self, db: AsyncSession) -> List[Project]:
        """Get active projects"""
        result = await db.execute(select(Project).where(Project.status == ProjectStatus.ACTIVE))
        return result.scalars().all()
    
    async def _get_all_resources(self, db: AsyncSession) -> List[User]:
        """Get all resources (users)"""
        result = await db.execute(select(User))
        return result.scalars().all()
    
    async def _calculate_budget_metrics(self, projects: List[Project]) -> Dict[str, float]:
        """Calculate budget-related metrics"""
        total_budget = sum(float(p.budget or 0) for p in projects)
        spent_budget = sum(float(p.actual_cost or 0) for p in projects)
        remaining_budget = total_budget - spent_budget
        
        return {
            "total_budget": total_budget,
            "spent_budget": spent_budget,
            "remaining_budget": remaining_budget
        }
    
    async def _calculate_performance_metrics(
        self, 
        projects: List[Project], 
        db: AsyncSession
    ) -> Dict[str, float]:
        """Calculate performance metrics"""
        completion_rates = []
        schedule_variances = []
        cost_variances = []
        
        for project in projects:
            if project.status == ProjectStatus.ACTIVE:
                # Calculate completion rate
                tasks = await self._get_project_tasks(project.id, db)
                if tasks:
                    completed_tasks = len([t for t in tasks if t.status == TaskStatus.DONE])
                    completion_rate = completed_tasks / len(tasks)
                    completion_rates.append(completion_rate)
                
                # Calculate EVM metrics
                evm_result = await self.evm_service.calculate_project_evm(project.id, db)
                if evm_result["success"]:
                    metrics = evm_result["metrics"]
                    schedule_variances.append(abs(metrics.get("schedule_variance", 0)))
                    cost_variances.append(abs(metrics.get("cost_variance", 0)))
        
        return {
            "average_completion_rate": sum(completion_rates) / len(completion_rates) if completion_rates else 0,
            "average_schedule_variance": sum(schedule_variances) / len(schedule_variances) if schedule_variances else 0,
            "average_cost_variance": sum(cost_variances) / len(cost_variances) if cost_variances else 0
        }
    
    async def _calculate_risk_distribution(
        self, 
        projects: List[Project], 
        db: AsyncSession
    ) -> Dict[str, int]:
        """Calculate risk distribution across projects"""
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for project in projects:
            if project.status == ProjectStatus.ACTIVE:
                risk_result = await self.predictive_service.calculate_project_risk_score(project.id, db)
                if risk_result["success"]:
                    risk_level = risk_result["risk_level"]
                    risk_distribution[risk_level] += 1
        
        return risk_distribution
    
    async def _calculate_phase_distribution(self, projects: List[Project]) -> Dict[str, int]:
        """Calculate phase distribution across projects"""
        phase_distribution = {}
        
        for project in projects:
            phase = project.phase.value if project.phase else "unknown"
            phase_distribution[phase] = phase_distribution.get(phase, 0) + 1
        
        return phase_distribution
    
    async def _calculate_portfolio_health_score(
        self, 
        performance_metrics: Dict[str, float], 
        risk_distribution: Dict[str, int]
    ) -> float:
        """Calculate overall portfolio health score"""
        # Normalize completion rate (0-1)
        completion_score = performance_metrics["average_completion_rate"]
        
        # Normalize schedule performance (invert variance)
        max_schedule_variance = 10000  # Assumed maximum
        schedule_score = 1 - (performance_metrics["average_schedule_variance"] / max_schedule_variance)
        
        # Normalize cost performance (invert variance)
        max_cost_variance = 50000  # Assumed maximum
        cost_score = 1 - (performance_metrics["average_cost_variance"] / max_cost_variance)
        
        # Calculate risk score (weighted by risk levels)
        total_projects = sum(risk_distribution.values())
        if total_projects > 0:
            risk_score = (
                risk_distribution["low"] * 1.0 +
                risk_distribution["medium"] * 0.7 +
                risk_distribution["high"] * 0.3 +
                risk_distribution["critical"] * 0.0
            ) / total_projects
        else:
            risk_score = 1.0
        
        # Calculate weighted health score
        health_score = (
            completion_score * self.health_weights["completion_rate"] +
            schedule_score * self.health_weights["schedule_performance"] +
            cost_score * self.health_weights["cost_performance"] +
            risk_score * self.health_weights["risk_level"]
        )
        
        return min(max(health_score, 0), 1)  # Ensure 0-1 range
    
    def _get_health_status(self, health_score: float) -> str:
        """Get health status based on score"""
        if health_score >= 0.8:
            return "excellent"
        elif health_score >= 0.6:
            return "good"
        elif health_score >= 0.4:
            return "fair"
        else:
            return "poor"
    
    def _get_top_risks(self, risk_distribution: Dict[str, int]) -> List[str]:
        """Get top risk categories"""
        sorted_risks = sorted(risk_distribution.items(), key=lambda x: x[1], reverse=True)
        return [risk[0] for risk in sorted_risks[:3]]
    
    async def _get_project_tasks(self, project_id: int, db: AsyncSession) -> List[Task]:
        """Get tasks for a project"""
        result = await db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        return result.scalars().all()
    
    async def _calculate_current_utilization(
        self, 
        resources: List[User], 
        projects: List[Project], 
        db: AsyncSession
    ) -> Dict[int, float]:
        """Calculate current resource utilization"""
        utilization = {}
        
        for resource in resources:
            # Count assigned tasks
            result = await db.execute(
                select(Task).where(Task.assigned_to_id == resource.id)
            )
            assigned_tasks = result.scalars().all()
            
            # Calculate utilization based on task hours
            total_hours = sum(float(t.estimated_hours or 0) for t in assigned_tasks)
            max_hours = 160  # Assumed monthly capacity
            utilization[resource.id] = min(total_hours / max_hours, 1.0) if max_hours > 0 else 0
        
        return utilization
    
    async def _generate_optimal_allocation(
        self, 
        resources: List[User], 
        projects: List[Project], 
        current_utilization: Dict[int, float], 
        db: AsyncSession
    ) -> List[ResourceAllocationRecommendation]:
        """Generate optimal resource allocation"""
        recommendations = []
        
        for resource in resources:
            current_util = current_utilization.get(resource.id, 0)
            
            # Calculate optimal utilization based on skills and project needs
            optimal_util = min(current_util * 1.2, 0.9)  # 20% increase, cap at 90%
            
            # Identify priority projects for this resource
            priority_projects = await self._identify_priority_projects(resource.id, projects, db)
            
            # Identify skill gaps
            skill_gaps = await self._identify_skill_gaps(resource.id, projects, db)
            
            # Generate training recommendations
            training_recommendations = await self._generate_training_recommendations(skill_gaps)
            
            recommendations.append(ResourceAllocationRecommendation(
                resource_id=resource.id,
                resource_name=resource.name,
                current_utilization=current_util,
                recommended_utilization=optimal_util,
                allocation_change=optimal_util - current_util,
                priority_projects=priority_projects,
                skill_gaps=skill_gaps,
                training_recommendations=training_recommendations
            ))
        
        return recommendations
    
    async def _generate_balanced_allocation(
        self, 
        resources: List[User], 
        projects: List[Project], 
        current_utilization: Dict[int, float], 
        db: AsyncSession
    ) -> List[ResourceAllocationRecommendation]:
        """Generate balanced resource allocation"""
        # Similar to optimal but with more conservative targets
        recommendations = []
        
        for resource in resources:
            current_util = current_utilization.get(resource.id, 0)
            balanced_util = min(current_util * 1.1, 0.8)  # 10% increase, cap at 80%
            
            priority_projects = await self._identify_priority_projects(resource.id, projects, db)
            skill_gaps = await self._identify_skill_gaps(resource.id, projects, db)
            training_recommendations = await self._generate_training_recommendations(skill_gaps)
            
            recommendations.append(ResourceAllocationRecommendation(
                resource_id=resource.id,
                resource_name=resource.name,
                current_utilization=current_util,
                recommended_utilization=balanced_util,
                allocation_change=balanced_util - current_util,
                priority_projects=priority_projects,
                skill_gaps=skill_gaps,
                training_recommendations=training_recommendations
            ))
        
        return recommendations
    
    async def _generate_aggressive_allocation(
        self, 
        resources: List[User], 
        projects: List[Project], 
        current_utilization: Dict[int, float], 
        db: AsyncSession
    ) -> List[ResourceAllocationRecommendation]:
        """Generate aggressive resource allocation"""
        # More aggressive targets for high-performance scenarios
        recommendations = []
        
        for resource in resources:
            current_util = current_utilization.get(resource.id, 0)
            aggressive_util = min(current_util * 1.4, 0.95)  # 40% increase, cap at 95%
            
            priority_projects = await self._identify_priority_projects(resource.id, projects, db)
            skill_gaps = await self._identify_skill_gaps(resource.id, projects, db)
            training_recommendations = await self._generate_training_recommendations(skill_gaps)
            
            recommendations.append(ResourceAllocationRecommendation(
                resource_id=resource.id,
                resource_name=resource.name,
                current_utilization=current_util,
                recommended_utilization=aggressive_util,
                allocation_change=aggressive_util - current_util,
                priority_projects=priority_projects,
                skill_gaps=skill_gaps,
                training_recommendations=training_recommendations
            ))
        
        return recommendations
    
    async def _generate_conservative_allocation(
        self, 
        resources: List[User], 
        projects: List[Project], 
        current_utilization: Dict[int, float], 
        db: AsyncSession
    ) -> List[ResourceAllocationRecommendation]:
        """Generate conservative resource allocation"""
        # Conservative targets for risk-averse scenarios
        recommendations = []
        
        for resource in resources:
            current_util = current_utilization.get(resource.id, 0)
            conservative_util = min(current_util * 1.05, 0.7)  # 5% increase, cap at 70%
            
            priority_projects = await self._identify_priority_projects(resource.id, projects, db)
            skill_gaps = await self._identify_skill_gaps(resource.id, projects, db)
            training_recommendations = await self._generate_training_recommendations(skill_gaps)
            
            recommendations.append(ResourceAllocationRecommendation(
                resource_id=resource.id,
                resource_name=resource.name,
                current_utilization=current_util,
                recommended_utilization=conservative_util,
                allocation_change=conservative_util - current_util,
                priority_projects=priority_projects,
                skill_gaps=skill_gaps,
                training_recommendations=training_recommendations
            ))
        
        return recommendations
    
    async def _identify_priority_projects(
        self, 
        resource_id: int, 
        projects: List[Project], 
        db: AsyncSession
    ) -> List[int]:
        """Identify priority projects for a resource"""
        # Simplified logic - would be more sophisticated in real implementation
        priority_projects = []
        
        for project in projects:
            if project.status == ProjectStatus.ACTIVE:
                # Check if resource has skills for this project
                # For now, just include first 3 active projects
                if len(priority_projects) < 3:
                    priority_projects.append(project.id)
        
        return priority_projects
    
    async def _identify_skill_gaps(
        self, 
        resource_id: int, 
        projects: List[Project], 
        db: AsyncSession
    ) -> List[str]:
        """Identify skill gaps for a resource"""
        # Simplified logic - would analyze actual skills vs requirements
        return ["project_management", "agile_methodologies", "risk_management"]
    
    async def _generate_training_recommendations(self, skill_gaps: List[str]) -> List[str]:
        """Generate training recommendations based on skill gaps"""
        training_map = {
            "project_management": "PMP Certification Course",
            "agile_methodologies": "Scrum Master Training",
            "risk_management": "Risk Management Workshop"
        }
        
        return [training_map.get(skill, f"{skill.title()} Training") for skill in skill_gaps]
    
    async def _analyze_allocation_impact(
        self, 
        recommendations: List[ResourceAllocationRecommendation], 
        projects: List[Project], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze the impact of resource allocation changes"""
        total_utilization_change = sum(r.allocation_change for r in recommendations)
        avg_utilization_change = total_utilization_change / len(recommendations) if recommendations else 0
        
        # Estimate completion improvement
        completion_improvement = min(avg_utilization_change * 0.15, 0.1)  # 15% of utilization change, max 10%
        
        return {
            "completion_improvement": completion_improvement,
            "resource_efficiency_gain": avg_utilization_change,
            "estimated_cost_savings": completion_improvement * 10000,  # Simplified calculation
            "risk_reduction": completion_improvement * 0.2  # 20% of completion improvement
        }
    
    async def _generate_executive_summary(
        self, 
        metrics: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate executive summary report"""
        return {
            "key_metrics": {
                "total_projects": metrics["total_projects"],
                "active_projects": metrics["active_projects"],
                "portfolio_health_score": metrics["portfolio_health_score"],
                "budget_utilization": (metrics["spent_budget"] / metrics["total_budget"] * 100) if metrics["total_budget"] > 0 else 0
            },
            "key_insights": [
                f"Portfolio health is {self._get_health_status(metrics['portfolio_health_score'])}",
                f"{metrics['active_projects']} projects are currently active",
                f"Budget utilization is at {((metrics['spent_budget'] / metrics['total_budget'] * 100) if metrics['total_budget'] > 0 else 0):.1f}%"
            ],
            "recommendations": [
                "Monitor high-risk projects closely",
                "Optimize resource allocation",
                "Review budget allocation"
            ]
        }
    
    async def _generate_performance_analysis(
        self, 
        metrics: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate performance analysis report"""
        return {
            "completion_rates": {
                "average": metrics["average_completion_rate"],
                "target": 0.8,
                "status": "on_track" if metrics["average_completion_rate"] >= 0.8 else "needs_attention"
            },
            "schedule_performance": {
                "average_variance": metrics["average_schedule_variance"],
                "target": 0,
                "status": "on_track" if metrics["average_schedule_variance"] <= 1000 else "needs_attention"
            },
            "cost_performance": {
                "average_variance": metrics["average_cost_variance"],
                "target": 0,
                "status": "on_track" if metrics["average_cost_variance"] <= 5000 else "needs_attention"
            }
        }
    
    async def _generate_risk_assessment(
        self, 
        metrics: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate risk assessment report"""
        return {
            "risk_distribution": metrics["risk_distribution"],
            "overall_risk_level": self._calculate_overall_risk_level(metrics["risk_distribution"]),
            "risk_trends": "stable",  # Would be calculated from historical data
            "mitigation_actions": [
                "Implement additional monitoring for high-risk projects",
                "Develop contingency plans for critical projects",
                "Increase stakeholder communication frequency"
            ]
        }
    
    async def _generate_resource_analysis(
        self, 
        metrics: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate resource analysis report"""
        return {
            "resource_utilization": "75%",  # Would be calculated from actual data
            "skill_gaps": ["project_management", "agile_methodologies"],
            "allocation_recommendations": [
                "Reallocate resources from low-priority to high-priority projects",
                "Provide training for identified skill gaps",
                "Consider hiring additional resources for critical projects"
            ]
        }
    
    async def _generate_financial_analysis(
        self, 
        metrics: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate financial analysis report"""
        return {
            "budget_overview": {
                "total_budget": metrics["total_budget"],
                "spent_budget": metrics["spent_budget"],
                "remaining_budget": metrics["remaining_budget"],
                "utilization_rate": (metrics["spent_budget"] / metrics["total_budget"] * 100) if metrics["total_budget"] > 0 else 0
            },
            "cost_performance": {
                "average_variance": metrics["average_cost_variance"],
                "trend": "stable",
                "forecast": "on_budget"
            }
        }
    
    async def _generate_comprehensive_report(
        self, 
        metrics: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        return {
            "executive_summary": await self._generate_executive_summary(metrics, db),
            "performance_analysis": await self._generate_performance_analysis(metrics, db),
            "risk_assessment": await self._generate_risk_assessment(metrics, db),
            "resource_analysis": await self._generate_resource_analysis(metrics, db),
            "financial_analysis": await self._generate_financial_analysis(metrics, db)
        }
    
    async def _apply_report_filters(
        self, 
        report: Dict[str, Any], 
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply filters to report data"""
        # Simplified filter application
        filtered_report = report.copy()
        
        if "project_status" in filters:
            # Filter by project status
            pass
        
        if "date_range" in filters:
            # Filter by date range
            pass
        
        return filtered_report
    
    def _get_period_date(self, current_date: date, period: AnalyticsPeriod, offset: int) -> date:
        """Get date for a specific period offset"""
        if period == AnalyticsPeriod.DAILY:
            return current_date - timedelta(days=offset)
        elif period == AnalyticsPeriod.WEEKLY:
            return current_date - timedelta(weeks=offset)
        elif period == AnalyticsPeriod.MONTHLY:
            # Simplified monthly calculation
            return current_date - timedelta(days=offset * 30)
        elif period == AnalyticsPeriod.QUARTERLY:
            return current_date - timedelta(days=offset * 90)
        elif period == AnalyticsPeriod.YEARLY:
            return current_date - timedelta(days=offset * 365)
        else:
            return current_date
    
    async def _calculate_period_metric(
        self, 
        metric_name: str, 
        period_date: date, 
        period: AnalyticsPeriod, 
        db: AsyncSession
    ) -> float:
        """Calculate metric value for a specific period"""
        # Simplified calculation - would use actual historical data
        return 0.75  # Placeholder value
    
    def _determine_trend_direction(self, change_percentage: float) -> str:
        """Determine trend direction based on change percentage"""
        if change_percentage > 5:
            return "increasing"
        elif change_percentage < -5:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_overall_trend(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall trend from trend data"""
        if len(trends) < 2:
            return {"direction": "stable", "strength": 0}
        
        changes = [t["change_percentage"] for t in trends[1:]]
        avg_change = sum(changes) / len(changes)
        
        if avg_change > 5:
            direction = "increasing"
        elif avg_change < -5:
            direction = "decreasing"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "strength": abs(avg_change),
            "consistency": self._calculate_trend_consistency(changes)
        }
    
    def _calculate_trend_stability(self, trends: List[Dict[str, Any]]) -> float:
        """Calculate trend stability (0-1)"""
        if len(trends) < 2:
            return 1.0
        
        changes = [t["change_percentage"] for t in trends[1:]]
        variance = np.var(changes) if len(changes) > 1 else 0
        max_variance = 100  # Assumed maximum variance
        
        return max(0, 1 - (variance / max_variance))
    
    def _calculate_trend_consistency(self, changes: List[float]) -> float:
        """Calculate trend consistency (0-1)"""
        if len(changes) < 2:
            return 1.0
        
        # Count how many changes are in the same direction as the average
        avg_change = sum(changes) / len(changes)
        consistent_changes = sum(1 for c in changes if (c > 0 and avg_change > 0) or (c < 0 and avg_change < 0))
        
        return consistent_changes / len(changes)
    
    def _generate_forecast(self, trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate forecast based on trends"""
        if len(trends) < 3:
            return {"next_period": 0, "confidence": 0}
        
        # Simple linear forecast
        recent_values = [t["current_value"] for t in trends[-3:]]
        if len(recent_values) >= 2:
            slope = (recent_values[-1] - recent_values[0]) / (len(recent_values) - 1)
            next_period = recent_values[-1] + slope
        else:
            next_period = recent_values[-1]
        
        return {
            "next_period": next_period,
            "confidence": 0.7,  # Placeholder confidence
            "range": [next_period * 0.9, next_period * 1.1]
        }
    
    def _calculate_overall_risk_level(self, risk_distribution: Dict[str, int]) -> str:
        """Calculate overall risk level from distribution"""
        total_projects = sum(risk_distribution.values())
        if total_projects == 0:
            return "low"
        
        # Weighted risk calculation
        weighted_risk = (
            risk_distribution["low"] * 0 +
            risk_distribution["medium"] * 1 +
            risk_distribution["high"] * 2 +
            risk_distribution["critical"] * 3
        ) / total_projects
        
        if weighted_risk >= 2.5:
            return "critical"
        elif weighted_risk >= 1.5:
            return "high"
        elif weighted_risk >= 0.5:
            return "medium"
        else:
            return "low"
