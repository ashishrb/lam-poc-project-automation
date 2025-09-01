#!/usr/bin/env python3
"""
Pydantic schemas for EVM Metrics (Phase 2)
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class EVMMetricsData(BaseModel):
    """EVM metrics data"""
    planned_value: float
    earned_value: float
    actual_cost: float
    schedule_variance: float
    cost_variance: float
    schedule_performance_index: float
    cost_performance_index: float
    budget_at_completion: float
    estimate_at_completion: float
    variance_at_completion: float
    to_complete_performance_index: float
    completion_percentage: float
    schedule_percentage: float
    cost_percentage: float


class VarianceAnalysisInfo(BaseModel):
    """Variance analysis information"""
    metric_type: str
    current_value: float
    baseline_value: float
    variance_amount: float
    variance_percentage: float
    trend: str
    severity: str
    recommendation: str


class EVMSummary(BaseModel):
    """EVM summary"""
    overall_health: str
    critical_issues: int
    high_risk_items: int
    on_track: int


class EVMMetricsResponse(BaseModel):
    """Response for EVM metrics"""
    success: bool
    project_id: int
    calculation_date: str
    metrics: EVMMetricsData
    variance_analysis: List[VarianceAnalysisInfo]
    summary: EVMSummary


class PortfolioMetricsData(BaseModel):
    """Portfolio metrics data"""
    total_projects: int
    total_planned_value: float
    total_earned_value: float
    total_actual_cost: float
    total_budget: float
    projects_on_track: int
    projects_at_risk: int
    projects_critical: int
    schedule_performance_index: float
    cost_performance_index: float
    schedule_variance: float
    cost_variance: float


class ProjectEVMResult(BaseModel):
    """Individual project EVM result"""
    project_id: int
    project_name: str
    metrics: EVMMetricsData
    health: str


class PortfolioSummary(BaseModel):
    """Portfolio summary"""
    overall_portfolio_health: str
    total_projects: int
    healthy_projects: int
    at_risk_projects: int
    critical_projects: int


class PortfolioEVMResponse(BaseModel):
    """Response for portfolio EVM"""
    success: bool
    calculation_date: str
    portfolio_metrics: PortfolioMetricsData
    project_results: List[ProjectEVMResult]
    summary: PortfolioSummary


class EVMTrends(BaseModel):
    """EVM trends"""
    spi_trend: str
    cpi_trend: str
    sv_trend: str
    cv_trend: str


class EVMReportResponse(BaseModel):
    """Response for EVM report"""
    success: bool
    project_id: int
    report_type: str
    generated_date: str
    current_metrics: EVMMetricsData
    variance_analysis: List[VarianceAnalysisInfo]
    trends: EVMTrends
    recommendations: List[str]
    summary: EVMSummary
