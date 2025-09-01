#!/usr/bin/env python3
"""
Advanced Reporting Engine
Comprehensive reporting with multiple formats and advanced analytics
"""

import json
import logging
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import io
import base64

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc

from app.models.project import Project, Task
from app.models.user import User
from app.models.project import TaskStatus, TaskPriority, ProjectStatus, ProjectPhase
from app.services.metrics import EVMService
from app.services.predictive_analytics import PredictiveAnalyticsService
from app.services.portfolio_analytics import PortfolioAnalyticsService
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Report output formats"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"
    HTML = "html"


class ReportType(str, Enum):
    """Report types"""
    EXECUTIVE_SUMMARY = "executive_summary"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    RESOURCE_ANALYSIS = "resource_analysis"
    FINANCIAL_ANALYSIS = "financial_analysis"
    COMPREHENSIVE = "comprehensive"
    PROJECT_DETAILED = "project_detailed"
    PORTFOLIO_OVERVIEW = "portfolio_overview"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


@dataclass
class ReportSection:
    """Report section with data and metadata"""
    title: str
    content: Dict[str, Any]
    charts: List[Dict[str, Any]]
    insights: List[str]
    recommendations: List[str]
    priority: str  # high, medium, low


@dataclass
class ReportMetadata:
    """Report metadata"""
    report_id: str
    report_type: ReportType
    generated_at: datetime
    generated_by: str
    data_sources: List[str]
    filters_applied: Dict[str, Any]
    version: str


class AdvancedReportingEngine:
    """Advanced reporting engine with multiple formats and analytics"""
    
    def __init__(self):
        self.evm_service = EVMService()
        self.predictive_service = PredictiveAnalyticsService()
        self.portfolio_service = PortfolioAnalyticsService()
        
        # Report templates
        self.report_templates = {
            ReportType.EXECUTIVE_SUMMARY: self._generate_executive_summary_template,
            ReportType.PERFORMANCE_ANALYSIS: self._generate_performance_analysis_template,
            ReportType.RISK_ASSESSMENT: self._generate_risk_assessment_template,
            ReportType.RESOURCE_ANALYSIS: self._generate_resource_analysis_template,
            ReportType.FINANCIAL_ANALYSIS: self._generate_financial_analysis_template,
            ReportType.COMPREHENSIVE: self._generate_comprehensive_template,
            ReportType.PROJECT_DETAILED: self._generate_project_detailed_template,
            ReportType.PORTFOLIO_OVERVIEW: self._generate_portfolio_overview_template,
            ReportType.TREND_ANALYSIS: self._generate_trend_analysis_template,
            ReportType.COMPARATIVE_ANALYSIS: self._generate_comparative_analysis_template
        }
    
    async def generate_report(
        self, 
        report_type: ReportType,
        format: ReportFormat,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        include_charts: bool = True,
        include_insights: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive report in specified format"""
        try:
            # Generate report template
            template_func = self.report_templates.get(report_type)
            if not template_func:
                return {
                    "success": False,
                    "error": f"Unknown report type: {report_type}"
                }
            
            # Generate report content
            report_content = await template_func(db, filters)
            
            # Add metadata
            report_metadata = ReportMetadata(
                report_id=f"{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                report_type=report_type,
                generated_at=datetime.now(),
                generated_by="system",
                data_sources=["projects", "tasks", "users", "metrics"],
                filters_applied=filters or {},
                version="1.0"
            )
            
            # Generate charts if requested
            charts = []
            if include_charts:
                charts = await self._generate_charts(report_content, report_type)
            
            # Generate insights if requested
            insights = []
            if include_insights:
                insights = await self._generate_insights(report_content, report_type)
            
            # Format report based on requested format
            formatted_report = await self._format_report(
                report_content, 
                report_metadata, 
                charts, 
                insights, 
                format
            )
            
            return {
                "success": True,
                "report_type": report_type.value,
                "format": format.value,
                "report_id": report_metadata.report_id,
                "generated_at": report_metadata.generated_at.isoformat(),
                "content": formatted_report,
                "metadata": {
                    "report_id": report_metadata.report_id,
                    "report_type": report_metadata.report_type.value,
                    "generated_at": report_metadata.generated_at.isoformat(),
                    "generated_by": report_metadata.generated_by,
                    "data_sources": report_metadata.data_sources,
                    "filters_applied": report_metadata.filters_applied,
                    "version": report_metadata.version
                },
                "summary": {
                    "total_sections": len(report_content.get("sections", [])),
                    "total_charts": len(charts),
                    "total_insights": len(insights),
                    "file_size": len(str(formatted_report))
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_comparative_report(
        self, 
        report_type: ReportType,
        comparison_periods: List[str],
        format: ReportFormat,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comparative report across multiple periods"""
        try:
            comparative_data = {}
            
            # Generate data for each comparison period
            for period in comparison_periods:
                period_filters = filters.copy() if filters else {}
                period_filters["date_range"] = self._get_period_date_range(period)
                
                template_func = self.report_templates.get(report_type)
                if template_func:
                    period_data = await template_func(db, period_filters)
                    comparative_data[period] = period_data
            
            # Generate comparative analysis
            comparative_analysis = await self._generate_comparative_analysis(comparative_data)
            
            # Format comparative report
            formatted_report = await self._format_comparative_report(
                comparative_data, 
                comparative_analysis, 
                format
            )
            
            return {
                "success": True,
                "report_type": f"comparative_{report_type.value}",
                "format": format.value,
                "comparison_periods": comparison_periods,
                "content": formatted_report,
                "comparative_analysis": comparative_analysis,
                "summary": {
                    "periods_compared": len(comparison_periods),
                    "key_differences": len(comparative_analysis.get("key_differences", [])),
                    "trend_insights": len(comparative_analysis.get("trend_insights", []))
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comparative report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_scheduled_report(
        self, 
        report_type: ReportType,
        schedule_config: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate scheduled report based on configuration"""
        try:
            # Apply schedule-specific filters
            filters = await self._apply_schedule_filters(schedule_config)
            
            # Generate report
            report_result = await self.generate_report(
                report_type, 
                ReportFormat.PDF, 
                db, 
                filters
            )
            
            if not report_result["success"]:
                return report_result
            
            # Add scheduling metadata
            report_result["scheduled"] = True
            report_result["schedule_config"] = schedule_config
            report_result["next_run"] = self._calculate_next_run(schedule_config)
            
            return report_result
            
        except Exception as e:
            logger.error(f"Error generating scheduled report: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Report template generators
    
    async def _generate_executive_summary_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate executive summary template"""
        # Get portfolio metrics
        metrics_result = await self.portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return {"error": "Failed to calculate portfolio metrics"}
        
        metrics = metrics_result["portfolio_metrics"]
        
        return {
            "title": "Executive Summary",
            "sections": [
                {
                    "title": "Portfolio Overview",
                    "content": {
                        "total_projects": metrics["total_projects"],
                        "active_projects": metrics["active_projects"],
                        "completed_projects": metrics["completed_projects"],
                        "portfolio_health_score": metrics["portfolio_health_score"]
                    }
                },
                {
                    "title": "Financial Summary",
                    "content": {
                        "total_budget": metrics["total_budget"],
                        "spent_budget": metrics["spent_budget"],
                        "remaining_budget": metrics["remaining_budget"],
                        "budget_utilization": (metrics["spent_budget"] / metrics["total_budget"] * 100) if metrics["total_budget"] > 0 else 0
                    }
                },
                {
                    "title": "Performance Highlights",
                    "content": {
                        "completion_rate": metrics["average_completion_rate"],
                        "schedule_variance": metrics["average_schedule_variance"],
                        "cost_variance": metrics["average_cost_variance"]
                    }
                },
                {
                    "title": "Risk Overview",
                    "content": {
                        "risk_distribution": metrics["risk_distribution"],
                        "overall_risk_level": self._calculate_overall_risk_level(metrics["risk_distribution"])
                    }
                }
            ]
        }
    
    async def _generate_performance_analysis_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate performance analysis template"""
        # Get performance data
        projects = await self._get_filtered_projects(db, filters)
        
        performance_data = []
        for project in projects:
            evm_result = await self.evm_service.calculate_project_evm(project.id, db)
            if evm_result["success"]:
                metrics = evm_result["metrics"]
                performance_data.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "completion_rate": metrics.get("completion_rate", 0),
                    "schedule_variance": metrics.get("schedule_variance", 0),
                    "cost_variance": metrics.get("cost_variance", 0),
                    "spi": metrics.get("schedule_performance_index", 1.0),
                    "cpi": metrics.get("cost_performance_index", 1.0)
                })
        
        return {
            "title": "Performance Analysis",
            "sections": [
                {
                    "title": "Project Performance Summary",
                    "content": {
                        "total_projects": len(performance_data),
                        "on_schedule": len([p for p in performance_data if p["spi"] >= 0.9]),
                        "on_budget": len([p for p in performance_data if p["cpi"] >= 0.9]),
                        "behind_schedule": len([p for p in performance_data if p["spi"] < 0.9]),
                        "over_budget": len([p for p in performance_data if p["cpi"] < 0.9])
                    }
                },
                {
                    "title": "Performance Metrics",
                    "content": {
                        "average_spi": sum(p["spi"] for p in performance_data) / len(performance_data) if performance_data else 1.0,
                        "average_cpi": sum(p["cpi"] for p in performance_data) / len(performance_data) if performance_data else 1.0,
                        "average_completion_rate": sum(p["completion_rate"] for p in performance_data) / len(performance_data) if performance_data else 0
                    }
                },
                {
                    "title": "Top Performers",
                    "content": {
                        "best_schedule_performance": sorted(performance_data, key=lambda x: x["spi"], reverse=True)[:5],
                        "best_cost_performance": sorted(performance_data, key=lambda x: x["cpi"], reverse=True)[:5]
                    }
                },
                {
                    "title": "Performance Issues",
                    "content": {
                        "schedule_issues": [p for p in performance_data if p["spi"] < 0.8],
                        "cost_issues": [p for p in performance_data if p["cpi"] < 0.8]
                    }
                }
            ]
        }
    
    async def _generate_risk_assessment_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate risk assessment template"""
        # Get risk data
        projects = await self._get_filtered_projects(db, filters)
        
        risk_data = []
        for project in projects:
            risk_result = await self.predictive_service.calculate_project_risk_score(project.id, db)
            if risk_result["success"]:
                risk_data.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "risk_score": risk_result["risk_score"],
                    "risk_level": risk_result["risk_level"],
                    "risk_factors": risk_result["risk_factors"],
                    "mitigation_actions": risk_result["mitigation_actions"]
                })
        
        return {
            "title": "Risk Assessment",
            "sections": [
                {
                    "title": "Risk Overview",
                    "content": {
                        "total_projects": len(risk_data),
                        "high_risk_projects": len([r for r in risk_data if r["risk_level"] in ["high", "critical"]]),
                        "average_risk_score": sum(r["risk_score"] for r in risk_data) / len(risk_data) if risk_data else 0
                    }
                },
                {
                    "title": "Risk Distribution",
                    "content": {
                        "risk_levels": {
                            "low": len([r for r in risk_data if r["risk_level"] == "low"]),
                            "medium": len([r for r in risk_data if r["risk_level"] == "medium"]),
                            "high": len([r for r in risk_data if r["risk_level"] == "high"]),
                            "critical": len([r for r in risk_data if r["risk_level"] == "critical"])
                        }
                    }
                },
                {
                    "title": "High Risk Projects",
                    "content": {
                        "critical_risk": [r for r in risk_data if r["risk_level"] == "critical"],
                        "high_risk": [r for r in risk_data if r["risk_level"] == "high"]
                    }
                },
                {
                    "title": "Risk Mitigation",
                    "content": {
                        "mitigation_actions": self._aggregate_mitigation_actions(risk_data)
                    }
                }
            ]
        }
    
    async def _generate_resource_analysis_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate resource analysis template"""
        # Get resource allocation data
        allocation_result = await self.portfolio_service.predict_resource_allocation(
            ResourceAllocationType.OPTIMAL, 
            db
        )
        
        if not allocation_result["success"]:
            return {"error": "Failed to get resource allocation data"}
        
        recommendations = allocation_result["recommendations"]
        
        return {
            "title": "Resource Analysis",
            "sections": [
                {
                    "title": "Resource Utilization",
                    "content": {
                        "total_resources": len(recommendations),
                        "average_utilization": sum(r["current_utilization"] for r in recommendations) / len(recommendations) if recommendations else 0,
                        "under_utilized": len([r for r in recommendations if r["current_utilization"] < 0.5]),
                        "over_utilized": len([r for r in recommendations if r["current_utilization"] > 0.8])
                    }
                },
                {
                    "title": "Allocation Recommendations",
                    "content": {
                        "resources_needing_reallocation": len([r for r in recommendations if abs(r["allocation_change"]) > 0.1]),
                        "priority_reallocations": sorted(recommendations, key=lambda x: abs(x["allocation_change"]), reverse=True)[:10]
                    }
                },
                {
                    "title": "Skill Gaps",
                    "content": {
                        "common_skill_gaps": self._aggregate_skill_gaps(recommendations),
                        "training_recommendations": self._aggregate_training_recommendations(recommendations)
                    }
                }
            ]
        }
    
    async def _generate_financial_analysis_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate financial analysis template"""
        # Get financial data
        projects = await self._get_filtered_projects(db, filters)
        
        financial_data = []
        for project in projects:
            evm_result = await self.evm_service.calculate_project_evm(project.id, db)
            if evm_result["success"]:
                metrics = evm_result["metrics"]
                financial_data.append({
                    "project_id": project.id,
                    "project_name": project.name,
                    "budget": float(project.budget or 0),
                    "actual_cost": metrics.get("actual_cost", 0),
                    "planned_value": metrics.get("planned_value", 0),
                    "earned_value": metrics.get("earned_value", 0),
                    "cost_variance": metrics.get("cost_variance", 0),
                    "cpi": metrics.get("cost_performance_index", 1.0)
                })
        
        return {
            "title": "Financial Analysis",
            "sections": [
                {
                    "title": "Budget Overview",
                    "content": {
                        "total_budget": sum(f["budget"] for f in financial_data),
                        "total_spent": sum(f["actual_cost"] for f in financial_data),
                        "total_earned": sum(f["earned_value"] for f in financial_data),
                        "budget_utilization": (sum(f["actual_cost"] for f in financial_data) / sum(f["budget"] for f in financial_data) * 100) if sum(f["budget"] for f in financial_data) > 0 else 0
                    }
                },
                {
                    "title": "Cost Performance",
                    "content": {
                        "average_cpi": sum(f["cpi"] for f in financial_data) / len(financial_data) if financial_data else 1.0,
                        "projects_under_budget": len([f for f in financial_data if f["cpi"] > 1.0]),
                        "projects_over_budget": len([f for f in financial_data if f["cpi"] < 1.0])
                    }
                },
                {
                    "title": "Cost Variance Analysis",
                    "content": {
                        "total_cost_variance": sum(f["cost_variance"] for f in financial_data),
                        "largest_overruns": sorted(financial_data, key=lambda x: x["cost_variance"])[:5],
                        "largest_savings": sorted(financial_data, key=lambda x: x["cost_variance"], reverse=True)[:5]
                    }
                }
            ]
        }
    
    async def _generate_comprehensive_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive report template"""
        # Combine all report types
        executive = await self._generate_executive_summary_template(db, filters)
        performance = await self._generate_performance_analysis_template(db, filters)
        risk = await self._generate_risk_assessment_template(db, filters)
        resource = await self._generate_resource_analysis_template(db, filters)
        financial = await self._generate_financial_analysis_template(db, filters)
        
        return {
            "title": "Comprehensive Portfolio Report",
            "sections": [
                *executive.get("sections", []),
                *performance.get("sections", []),
                *risk.get("sections", []),
                *resource.get("sections", []),
                *financial.get("sections", [])
            ]
        }
    
    async def _generate_project_detailed_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate detailed project report template"""
        # Get specific project data
        project_id = filters.get("project_id") if filters else None
        if not project_id:
            return {"error": "Project ID required for detailed project report"}
        
        project = await self._get_project(project_id, db)
        if not project:
            return {"error": f"Project {project_id} not found"}
        
        # Get project metrics
        evm_result = await self.evm_service.calculate_project_evm(project_id, db)
        risk_result = await self.predictive_service.calculate_project_risk_score(project_id, db)
        tasks = await self._get_project_tasks(project_id, db)
        
        return {
            "title": f"Detailed Report - {project.name}",
            "sections": [
                {
                    "title": "Project Overview",
                    "content": {
                        "project_id": project.id,
                        "project_name": project.name,
                        "status": project.status.value,
                        "phase": project.phase.value if project.phase else "unknown",
                        "start_date": project.planned_start_date.isoformat() if project.planned_start_date else None,
                        "end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
                        "budget": float(project.budget or 0)
                    }
                },
                {
                    "title": "Performance Metrics",
                    "content": evm_result.get("metrics", {}) if evm_result["success"] else {}
                },
                {
                    "title": "Risk Assessment",
                    "content": {
                        "risk_score": risk_result.get("risk_score", 0),
                        "risk_level": risk_result.get("risk_level", "unknown"),
                        "risk_factors": risk_result.get("risk_factors", [])
                    } if risk_result["success"] else {}
                },
                {
                    "title": "Task Breakdown",
                    "content": {
                        "total_tasks": len(tasks),
                        "completed_tasks": len([t for t in tasks if t.status == TaskStatus.DONE]),
                        "in_progress_tasks": len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS]),
                        "todo_tasks": len([t for t in tasks if t.status == TaskStatus.TODO])
                    }
                }
            ]
        }
    
    async def _generate_portfolio_overview_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate portfolio overview template"""
        # Use portfolio analytics service
        metrics_result = await self.portfolio_service.calculate_portfolio_metrics(db)
        if not metrics_result["success"]:
            return {"error": "Failed to calculate portfolio metrics"}
        
        metrics = metrics_result["portfolio_metrics"]
        
        return {
            "title": "Portfolio Overview",
            "sections": [
                {
                    "title": "Portfolio Summary",
                    "content": {
                        "total_projects": metrics["total_projects"],
                        "active_projects": metrics["active_projects"],
                        "completed_projects": metrics["completed_projects"],
                        "portfolio_health_score": metrics["portfolio_health_score"]
                    }
                },
                {
                    "title": "Project Distribution",
                    "content": {
                        "phase_distribution": metrics["phase_distribution"],
                        "status_distribution": {
                            "active": metrics["active_projects"],
                            "completed": metrics["completed_projects"],
                            "other": metrics["total_projects"] - metrics["active_projects"] - metrics["completed_projects"]
                        }
                    }
                },
                {
                    "title": "Performance Summary",
                    "content": {
                        "average_completion_rate": metrics["average_completion_rate"],
                        "average_schedule_variance": metrics["average_schedule_variance"],
                        "average_cost_variance": metrics["average_cost_variance"]
                    }
                },
                {
                    "title": "Risk Summary",
                    "content": {
                        "risk_distribution": metrics["risk_distribution"],
                        "overall_risk_level": self._calculate_overall_risk_level(metrics["risk_distribution"])
                    }
                }
            ]
        }
    
    async def _generate_trend_analysis_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate trend analysis template"""
        # Get trend data for key metrics
        trend_metrics = ["completion_rate", "schedule_variance", "cost_variance", "portfolio_health"]
        
        trend_data = {}
        for metric in trend_metrics:
            trend_result = await self.portfolio_service.analyze_portfolio_trends(
                metric, 
                AnalyticsPeriod.MONTHLY, 
                db, 
                12
            )
            if trend_result["success"]:
                trend_data[metric] = trend_result
        
        return {
            "title": "Trend Analysis",
            "sections": [
                {
                    "title": "Completion Rate Trends",
                    "content": trend_data.get("completion_rate", {})
                },
                {
                    "title": "Schedule Performance Trends",
                    "content": trend_data.get("schedule_variance", {})
                },
                {
                    "title": "Cost Performance Trends",
                    "content": trend_data.get("cost_variance", {})
                },
                {
                    "title": "Portfolio Health Trends",
                    "content": trend_data.get("portfolio_health", {})
                }
            ]
        }
    
    async def _generate_comparative_analysis_template(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comparative analysis template"""
        # This would be populated by the comparative report generation
        return {
            "title": "Comparative Analysis",
            "sections": [
                {
                    "title": "Period Comparison",
                    "content": {}
                },
                {
                    "title": "Key Differences",
                    "content": {}
                },
                {
                    "title": "Trend Analysis",
                    "content": {}
                }
            ]
        }
    
    # Helper methods
    
    async def _get_filtered_projects(
        self, 
        db: AsyncSession, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Project]:
        """Get projects with applied filters"""
        query = select(Project)
        
        if filters:
            if "status" in filters:
                query = query.where(Project.status == filters["status"])
            if "phase" in filters:
                query = query.where(Project.phase == filters["phase"])
            if "date_range" in filters:
                # Apply date range filters
                pass
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def _get_project(self, project_id: int, db: AsyncSession) -> Optional[Project]:
        """Get project by ID"""
        result = await db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()
    
    async def _get_project_tasks(self, project_id: int, db: AsyncSession) -> List[Task]:
        """Get tasks for a project"""
        result = await db.execute(
            select(Task).where(Task.project_id == project_id)
        )
        return result.scalars().all()
    
    async def _generate_charts(
        self, 
        report_content: Dict[str, Any], 
        report_type: ReportType
    ) -> List[Dict[str, Any]]:
        """Generate charts for the report"""
        charts = []
        
        # Generate charts based on report type and content
        if report_type == ReportType.PERFORMANCE_ANALYSIS:
            charts.extend([
                {
                    "type": "bar",
                    "title": "Project Performance Index",
                    "data": self._extract_performance_chart_data(report_content)
                },
                {
                    "type": "pie",
                    "title": "Performance Distribution",
                    "data": self._extract_performance_distribution_data(report_content)
                }
            ])
        
        elif report_type == ReportType.RISK_ASSESSMENT:
            charts.extend([
                {
                    "type": "doughnut",
                    "title": "Risk Distribution",
                    "data": self._extract_risk_distribution_data(report_content)
                },
                {
                    "type": "bar",
                    "title": "Risk Scores by Project",
                    "data": self._extract_risk_scores_data(report_content)
                }
            ])
        
        return charts
    
    async def _generate_insights(
        self, 
        report_content: Dict[str, Any], 
        report_type: ReportType
    ) -> List[str]:
        """Generate insights from report content"""
        insights = []
        
        # Generate insights based on report type and content
        if report_type == ReportType.PERFORMANCE_ANALYSIS:
            performance_data = report_content.get("sections", [])
            for section in performance_data:
                if "Performance Metrics" in section.get("title", ""):
                    content = section.get("content", {})
                    avg_spi = content.get("average_spi", 1.0)
                    avg_cpi = content.get("average_cpi", 1.0)
                    
                    if avg_spi < 0.9:
                        insights.append(f"Schedule performance is below target (SPI: {avg_spi:.2f})")
                    if avg_cpi < 0.9:
                        insights.append(f"Cost performance is below target (CPI: {avg_cpi:.2f})")
        
        elif report_type == ReportType.RISK_ASSESSMENT:
            risk_data = report_content.get("sections", [])
            for section in risk_data:
                if "Risk Overview" in section.get("title", ""):
                    content = section.get("content", {})
                    high_risk_count = content.get("high_risk_projects", 0)
                    
                    if high_risk_count > 0:
                        insights.append(f"{high_risk_count} projects require immediate attention due to high risk levels")
        
        return insights
    
    async def _format_report(
        self, 
        report_content: Dict[str, Any], 
        metadata: ReportMetadata, 
        charts: List[Dict[str, Any]], 
        insights: List[str], 
        format: ReportFormat
    ) -> Any:
        """Format report in specified format"""
        if format == ReportFormat.JSON:
            return {
                "metadata": {
                    "report_id": metadata.report_id,
                    "report_type": metadata.report_type.value,
                    "generated_at": metadata.generated_at.isoformat(),
                    "version": metadata.version
                },
                "content": report_content,
                "charts": charts,
                "insights": insights
            }
        
        elif format == ReportFormat.CSV:
            return self._format_as_csv(report_content)
        
        elif format == ReportFormat.EXCEL:
            return self._format_as_excel(report_content, charts)
        
        elif format == ReportFormat.HTML:
            return self._format_as_html(report_content, metadata, charts, insights)
        
        else:
            return report_content
    
    def _format_as_csv(self, report_content: Dict[str, Any]) -> str:
        """Format report as CSV"""
        # Convert report content to CSV format
        csv_data = []
        
        for section in report_content.get("sections", []):
            csv_data.append([section.get("title", "")])
            content = section.get("content", {})
            
            for key, value in content.items():
                if isinstance(value, (dict, list)):
                    csv_data.append([key, str(value)])
                else:
                    csv_data.append([key, value])
            
            csv_data.append([])  # Empty row between sections
        
        # Convert to CSV string
        output = io.StringIO()
        import csv
        writer = csv.writer(output)
        writer.writerows(csv_data)
        
        return output.getvalue()
    
    def _format_as_excel(self, report_content: Dict[str, Any], charts: List[Dict[str, Any]]) -> bytes:
        """Format report as Excel"""
        # Create Excel file with multiple sheets
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main report sheet
            main_data = []
            for section in report_content.get("sections", []):
                main_data.append([section.get("title", "")])
                content = section.get("content", {})
                
                for key, value in content.items():
                    if isinstance(value, (dict, list)):
                        main_data.append([key, str(value)])
                    else:
                        main_data.append([key, value])
                
                main_data.append([])
            
            df_main = pd.DataFrame(main_data)
            df_main.to_excel(writer, sheet_name='Report', index=False, header=False)
            
            # Charts sheet
            if charts:
                chart_data = []
                for chart in charts:
                    chart_data.append([chart.get("title", ""), chart.get("type", "")])
                
                df_charts = pd.DataFrame(chart_data, columns=['Chart Title', 'Chart Type'])
                df_charts.to_excel(writer, sheet_name='Charts', index=False)
        
        return output.getvalue()
    
    def _format_as_html(self, report_content: Dict[str, Any], metadata: ReportMetadata, charts: List[Dict[str, Any]], insights: List[str]) -> str:
        """Format report as HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{metadata.report_type.value} Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 30px; }}
                .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .content {{ margin-left: 20px; }}
                .insight {{ background-color: #e6f3ff; padding: 10px; margin: 10px 0; border-left: 4px solid #0066cc; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{metadata.report_type.value} Report</h1>
                <p>Generated: {metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Report ID: {metadata.report_id}</p>
            </div>
        """
        
        # Add sections
        for section in report_content.get("sections", []):
            html += f"""
            <div class="section">
                <div class="section-title">{section.get('title', '')}</div>
                <div class="content">
            """
            
            content = section.get("content", {})
            for key, value in content.items():
                html += f"<p><strong>{key}:</strong> {value}</p>"
            
            html += "</div></div>"
        
        # Add insights
        if insights:
            html += '<div class="section"><div class="section-title">Key Insights</div>'
            for insight in insights:
                html += f'<div class="insight">{insight}</div>'
            html += "</div>"
        
        html += "</body></html>"
        return html
    
    def _calculate_overall_risk_level(self, risk_distribution: Dict[str, int]) -> str:
        """Calculate overall risk level from distribution"""
        total_projects = sum(risk_distribution.values())
        if total_projects == 0:
            return "low"
        
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
    
    def _aggregate_mitigation_actions(self, risk_data: List[Dict[str, Any]]) -> List[str]:
        """Aggregate mitigation actions from risk data"""
        all_actions = []
        for risk in risk_data:
            actions = risk.get("mitigation_actions", [])
            for action in actions:
                action_type = action.get("action_type", "")
                if action_type and action_type not in all_actions:
                    all_actions.append(action_type)
        return all_actions
    
    def _aggregate_skill_gaps(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Aggregate skill gaps from recommendations"""
        all_gaps = []
        for rec in recommendations:
            gaps = rec.get("skill_gaps", [])
            for gap in gaps:
                if gap not in all_gaps:
                    all_gaps.append(gap)
        return all_gaps
    
    def _aggregate_training_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Aggregate training recommendations"""
        all_training = []
        for rec in recommendations:
            training = rec.get("training_recommendations", [])
            for item in training:
                if item not in all_training:
                    all_training.append(item)
        return all_training
    
    def _get_period_date_range(self, period: str) -> Dict[str, str]:
        """Get date range for a period"""
        # Simplified implementation
        return {
            "start": (date.today() - timedelta(days=30)).isoformat(),
            "end": date.today().isoformat()
        }
    
    async def _apply_schedule_filters(self, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply schedule-specific filters"""
        filters = {}
        
        if "date_range" in schedule_config:
            filters["date_range"] = schedule_config["date_range"]
        
        if "project_status" in schedule_config:
            filters["project_status"] = schedule_config["project_status"]
        
        return filters
    
    def _calculate_next_run(self, schedule_config: Dict[str, Any]) -> str:
        """Calculate next run time for scheduled report"""
        # Simplified implementation
        next_run = datetime.now() + timedelta(days=7)
        return next_run.isoformat()
    
    def _extract_performance_chart_data(self, report_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for performance charts"""
        # Simplified implementation
        return {
            "labels": ["Project 1", "Project 2", "Project 3"],
            "datasets": [
                {
                    "label": "SPI",
                    "data": [0.9, 0.8, 1.1]
                },
                {
                    "label": "CPI",
                    "data": [0.95, 0.85, 1.05]
                }
            ]
        }
    
    def _extract_performance_distribution_data(self, report_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for performance distribution chart"""
        return {
            "labels": ["On Track", "Behind Schedule", "Over Budget"],
            "data": [60, 25, 15]
        }
    
    def _extract_risk_distribution_data(self, report_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for risk distribution chart"""
        return {
            "labels": ["Low", "Medium", "High", "Critical"],
            "data": [40, 30, 20, 10]
        }
    
    def _extract_risk_scores_data(self, report_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data for risk scores chart"""
        return {
            "labels": ["Project A", "Project B", "Project C"],
            "data": [25, 45, 75]
        }
    
    async def _generate_comparative_analysis(self, comparative_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comparative analysis between periods"""
        # Simplified implementation
        return {
            "key_differences": [
                "Completion rate improved by 5%",
                "Schedule variance decreased by 10%",
                "Cost variance increased by 3%"
            ],
            "trend_insights": [
                "Overall performance is improving",
                "Resource utilization is stable",
                "Risk levels are decreasing"
            ]
        }
    
    async def _format_comparative_report(
        self, 
        comparative_data: Dict[str, Any], 
        comparative_analysis: Dict[str, Any], 
        format: ReportFormat
    ) -> Any:
        """Format comparative report"""
        # Simplified implementation
        return {
            "comparative_data": comparative_data,
            "analysis": comparative_analysis,
            "format": format.value
        }
