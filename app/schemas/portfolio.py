#!/usr/bin/env python3
"""
Pydantic schemas for Portfolio Analytics Service
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


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


class PortfolioMetricsData(BaseModel):
    """Portfolio metrics data"""
    total_projects: int = Field(..., description="Total number of projects")
    active_projects: int = Field(..., description="Number of active projects")
    completed_projects: int = Field(..., description="Number of completed projects")
    total_budget: float = Field(..., description="Total portfolio budget")
    spent_budget: float = Field(..., description="Total spent budget")
    remaining_budget: float = Field(..., description="Remaining budget")
    average_completion_rate: float = Field(..., description="Average completion rate")
    average_schedule_variance: float = Field(..., description="Average schedule variance")
    average_cost_variance: float = Field(..., description="Average cost variance")
    portfolio_health_score: float = Field(..., description="Portfolio health score (0-1)")
    risk_distribution: Dict[str, int] = Field(..., description="Risk distribution by level")
    phase_distribution: Dict[str, int] = Field(..., description="Phase distribution")


class PortfolioSummary(BaseModel):
    """Portfolio summary information"""
    budget_utilization: float = Field(..., description="Budget utilization percentage")
    completion_efficiency: float = Field(..., description="Completion efficiency percentage")
    health_status: str = Field(..., description="Portfolio health status")
    top_risks: List[str] = Field(..., description="Top risk categories")


class PortfolioMetricsResponse(BaseModel):
    """Portfolio metrics response"""
    success: bool = Field(..., description="Whether the operation was successful")
    portfolio_metrics: PortfolioMetricsData = Field(..., description="Portfolio metrics")
    summary: PortfolioSummary = Field(..., description="Portfolio summary")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ResourceAllocationRecommendation(BaseModel):
    """Resource allocation recommendation"""
    resource_id: int = Field(..., description="Resource ID")
    resource_name: str = Field(..., description="Resource name")
    current_utilization: float = Field(..., description="Current utilization (0-1)")
    recommended_utilization: float = Field(..., description="Recommended utilization (0-1)")
    allocation_change: float = Field(..., description="Allocation change")
    priority_projects: List[int] = Field(..., description="Priority project IDs")
    skill_gaps: List[str] = Field(..., description="Identified skill gaps")
    training_recommendations: List[str] = Field(..., description="Training recommendations")


class AllocationImpactAnalysis(BaseModel):
    """Resource allocation impact analysis"""
    completion_improvement: float = Field(..., description="Estimated completion improvement")
    resource_efficiency_gain: float = Field(..., description="Resource efficiency gain")
    estimated_cost_savings: float = Field(..., description="Estimated cost savings")
    risk_reduction: float = Field(..., description="Risk reduction")


class AllocationSummary(BaseModel):
    """Resource allocation summary"""
    total_resources: int = Field(..., description="Total number of resources")
    resources_needing_reallocation: int = Field(..., description="Resources needing reallocation")
    average_utilization_change: float = Field(..., description="Average utilization change")
    estimated_completion_improvement: float = Field(..., description="Estimated completion improvement")


class ResourceAllocationResponse(BaseModel):
    """Resource allocation response"""
    success: bool = Field(..., description="Whether the operation was successful")
    allocation_type: str = Field(..., description="Allocation type")
    recommendations: List[ResourceAllocationRecommendation] = Field(..., description="Allocation recommendations")
    impact_analysis: AllocationImpactAnalysis = Field(..., description="Impact analysis")
    summary: AllocationSummary = Field(..., description="Allocation summary")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class PortfolioTrend(BaseModel):
    """Portfolio trend data"""
    period: str = Field(..., description="Period identifier")
    metric_name: str = Field(..., description="Metric name")
    current_value: float = Field(..., description="Current value")
    previous_value: float = Field(..., description="Previous value")
    change_percentage: float = Field(..., description="Change percentage")
    trend_direction: str = Field(..., description="Trend direction")


class OverallTrend(BaseModel):
    """Overall trend information"""
    direction: str = Field(..., description="Trend direction")
    strength: float = Field(..., description="Trend strength")
    consistency: float = Field(..., description="Trend consistency")


class TrendForecast(BaseModel):
    """Trend forecast"""
    next_period: float = Field(..., description="Next period forecast")
    confidence: float = Field(..., description="Forecast confidence")
    range: List[float] = Field(..., description="Forecast range")


class TrendSummary(BaseModel):
    """Trend summary"""
    average_change: float = Field(..., description="Average change")
    trend_stability: float = Field(..., description="Trend stability")
    forecast: TrendForecast = Field(..., description="Forecast")


class PortfolioTrendsResponse(BaseModel):
    """Portfolio trends response"""
    success: bool = Field(..., description="Whether the operation was successful")
    metric_name: str = Field(..., description="Metric name")
    period: str = Field(..., description="Analytics period")
    lookback_periods: int = Field(..., description="Number of lookback periods")
    trends: List[PortfolioTrend] = Field(..., description="Trend data")
    overall_trend: OverallTrend = Field(..., description="Overall trend")
    summary: TrendSummary = Field(..., description="Trend summary")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ReportSection(BaseModel):
    """Report section"""
    section_name: str = Field(..., description="Section name")
    section_data: Dict[str, Any] = Field(..., description="Section data")
    insights: List[str] = Field(..., description="Key insights")
    recommendations: List[str] = Field(..., description="Recommendations")


class ReportSummary(BaseModel):
    """Report summary"""
    total_sections: int = Field(..., description="Total number of sections")
    key_insights: List[str] = Field(..., description="Key insights")
    recommendations: List[str] = Field(..., description="Recommendations")


class PortfolioReportResponse(BaseModel):
    """Portfolio report response"""
    success: bool = Field(..., description="Whether the operation was successful")
    report_type: str = Field(..., description="Report type")
    generated_at: str = Field(..., description="Report generation timestamp")
    report_data: Dict[str, Any] = Field(..., description="Report data")
    summary: ReportSummary = Field(..., description="Report summary")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class ReportFilters(BaseModel):
    """Report filters"""
    project_status: Optional[str] = Field(None, description="Filter by project status")
    date_range: Optional[Dict[str, str]] = Field(None, description="Filter by date range")
    risk_level: Optional[str] = Field(None, description="Filter by risk level")
    phase: Optional[str] = Field(None, description="Filter by project phase")


class ExecutiveSummary(BaseModel):
    """Executive summary"""
    key_metrics: Dict[str, Any] = Field(..., description="Key metrics")
    key_insights: List[str] = Field(..., description="Key insights")
    recommendations: List[str] = Field(..., description="Recommendations")


class PerformanceAnalysis(BaseModel):
    """Performance analysis"""
    completion_rates: Dict[str, Any] = Field(..., description="Completion rates")
    schedule_performance: Dict[str, Any] = Field(..., description="Schedule performance")
    cost_performance: Dict[str, Any] = Field(..., description="Cost performance")


class RiskAssessment(BaseModel):
    """Risk assessment"""
    risk_distribution: Dict[str, int] = Field(..., description="Risk distribution")
    overall_risk_level: str = Field(..., description="Overall risk level")
    risk_trends: str = Field(..., description="Risk trends")
    mitigation_actions: List[str] = Field(..., description="Mitigation actions")


class ResourceAnalysis(BaseModel):
    """Resource analysis"""
    resource_utilization: str = Field(..., description="Resource utilization")
    skill_gaps: List[str] = Field(..., description="Skill gaps")
    allocation_recommendations: List[str] = Field(..., description="Allocation recommendations")


class FinancialAnalysis(BaseModel):
    """Financial analysis"""
    budget_overview: Dict[str, Any] = Field(..., description="Budget overview")
    cost_performance: Dict[str, Any] = Field(..., description="Cost performance")


class ComprehensiveReport(BaseModel):
    """Comprehensive report"""
    executive_summary: ExecutiveSummary = Field(..., description="Executive summary")
    performance_analysis: PerformanceAnalysis = Field(..., description="Performance analysis")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    resource_analysis: ResourceAnalysis = Field(..., description="Resource analysis")
    financial_analysis: FinancialAnalysis = Field(..., description="Financial analysis")


class DashboardMetrics(BaseModel):
    """Dashboard metrics for real-time display"""
    portfolio_health: float = Field(..., description="Portfolio health score")
    active_projects: int = Field(..., description="Number of active projects")
    completion_rate: float = Field(..., description="Overall completion rate")
    budget_utilization: float = Field(..., description="Budget utilization percentage")
    risk_level: str = Field(..., description="Overall risk level")
    trend_direction: str = Field(..., description="Portfolio trend direction")


class DashboardResponse(BaseModel):
    """Dashboard response"""
    success: bool = Field(..., description="Whether the operation was successful")
    metrics: DashboardMetrics = Field(..., description="Dashboard metrics")
    last_updated: str = Field(..., description="Last update timestamp")
    error: Optional[str] = Field(None, description="Error message if operation failed")
