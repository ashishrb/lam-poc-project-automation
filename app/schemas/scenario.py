#!/usr/bin/env python3
"""
Pydantic schemas for Scenario Simulation (Phase 2)
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.services.scenario_sim import ScenarioType, ImpactLevel


class ScenarioParameterInfo(BaseModel):
    """Scenario parameter information"""
    parameter_type: str
    current_value: Any
    proposed_value: Any
    unit: str
    description: str


class DurationImpact(BaseModel):
    """Duration impact information"""
    original_duration: int
    new_duration: int
    duration_change: int
    original_end_date: str
    new_end_date: str


class CostImpact(BaseModel):
    """Cost impact information"""
    original_cost: float
    new_cost: float
    cost_change: float


class RiskAssessment(BaseModel):
    """Risk assessment information"""
    risk_level: str
    risk_factors: List[str]


class ScenarioResultData(BaseModel):
    """Scenario result data"""
    scenario_name: str
    scenario_type: str
    parameters: List[ScenarioParameterInfo]
    duration_impact: DurationImpact
    cost_impact: CostImpact
    affected_tasks: List[int]
    new_critical_path: List[int]
    risk_assessment: RiskAssessment
    recommendations: List[str]
    feasibility_score: float


class ScenarioResponse(BaseModel):
    """Response for scenario simulation"""
    success: bool
    scenario_id: str
    result: ScenarioResultData


class ScenarioCreateRequest(BaseModel):
    """Request to create a scenario"""
    scenario_name: str
    scenario_type: ScenarioType
    parameters: Dict[str, Any]


class ComparisonMatrix(BaseModel):
    """Comparison matrix for scenarios"""
    duration_comparison: List[Dict[str, Any]]
    cost_comparison: List[Dict[str, Any]]
    risk_comparison: List[Dict[str, Any]]
    feasibility_comparison: List[Dict[str, Any]]


class ComparisonSummary(BaseModel):
    """Comparison summary"""
    total_scenarios: int
    scenarios_with_improvement: int
    scenarios_with_cost_savings: int


class ScenarioComparisonResponse(BaseModel):
    """Response for scenario comparison"""
    success: bool
    project_id: int
    scenarios: List[ScenarioResultData]
    comparison: ComparisonMatrix
    best_scenario: Dict[str, Any]
    summary: ComparisonSummary


class ScenarioApplyRequest(BaseModel):
    """Request to apply a scenario"""
    scenario_id: str
    confirm_application: bool = Field(True, description="Confirm that scenario should be applied")
