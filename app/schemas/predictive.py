#!/usr/bin/env python3
"""
Pydantic schemas for Predictive Analytics Service
"""

from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MitigationAction(str, Enum):
    """Types of mitigation actions"""
    SPLIT_TASK = "split_task"
    REASSIGN_RESOURCE = "reassign_resource"
    ESCALATE = "escalate"
    ADD_RESOURCE = "add_resource"
    REDUCE_SCOPE = "reduce_scope"
    EXTEND_TIMELINE = "extend_timeline"
    INCREASE_BUDGET = "increase_budget"


class RiskFactorInfo(BaseModel):
    """Risk factor information"""
    factor_name: str = Field(..., description="Name of the risk factor")
    factor_value: float = Field(..., description="Value of the risk factor (0-1)")
    weight: float = Field(..., description="Weight of the risk factor")
    contribution: float = Field(..., description="Contribution to overall risk score")
    description: str = Field(..., description="Human-readable description of the risk factor")


class MitigationActionInfo(BaseModel):
    """Mitigation action information"""
    action_type: str = Field(..., description="Type of mitigation action")
    description: str = Field(..., description="Description of the action")
    impact_score: float = Field(..., description="Impact score (0-100)")
    effort_score: float = Field(..., description="Effort score (0-100)")
    priority: str = Field(..., description="Priority level (high, medium, low)")


class PrescriptiveActionInfo(BaseModel):
    """Prescriptive action information"""
    action_type: MitigationAction = Field(..., description="Type of prescriptive action")
    description: str = Field(..., description="Description of the action")
    impact_score: float = Field(..., description="Impact score (0-100)")
    effort_score: float = Field(..., description="Effort score (0-100)")
    priority: str = Field(..., description="Priority level (high, medium, low)")
    estimated_effect: str = Field(..., description="Estimated effect of the action")
    human_in_the_loop: bool = Field(..., description="Whether human review is required")
    auto_apply: bool = Field(..., description="Whether action can be auto-applied")


class RiskAssessmentResponse(BaseModel):
    """Risk assessment response"""
    success: bool = Field(..., description="Whether the operation was successful")
    project_id: Optional[int] = Field(None, description="Project ID")
    task_id: Optional[int] = Field(None, description="Task ID")
    risk_score: float = Field(..., description="Overall risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level")
    risk_factors: List[RiskFactorInfo] = Field(..., description="List of risk factors")
    causal_explanation: str = Field(..., description="Human-readable causal explanation")
    mitigation_actions: List[MitigationActionInfo] = Field(..., description="List of mitigation actions")
    confidence: float = Field(..., description="Confidence in the assessment (0-1)")
    last_updated: str = Field(..., description="Last update timestamp")
    summary: Optional[Dict[str, Any]] = Field(None, description="Summary statistics")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class PrescriptivePlaybookResponse(BaseModel):
    """Prescriptive playbook response"""
    success: bool = Field(..., description="Whether the operation was successful")
    project_id: int = Field(..., description="Project ID")
    risk_level: RiskLevel = Field(..., description="Risk level")
    playbook: List[PrescriptiveActionInfo] = Field(..., description="List of prescriptive actions")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    message: Optional[str] = Field(None, description="Additional message")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class MitigationActionRequest(BaseModel):
    """Request to apply a mitigation action"""
    action_type: MitigationAction = Field(..., description="Type of action to apply")
    action_params: Dict[str, Any] = Field(..., description="Parameters for the action")


class MitigationActionResponse(BaseModel):
    """Response from applying a mitigation action"""
    success: bool = Field(..., description="Whether the operation was successful")
    action: str = Field(..., description="Type of action applied")
    message: str = Field(..., description="Result message")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class OutcomePrediction(BaseModel):
    """Project outcome prediction"""
    estimated_completion_date: str = Field(..., description="Estimated completion date")
    estimated_final_cost: float = Field(..., description="Estimated final cost")
    completion_probability: float = Field(..., description="Probability of completion (0-1)")
    quality_score: float = Field(..., description="Predicted quality score (0-1)")
    stakeholder_satisfaction: float = Field(..., description="Predicted stakeholder satisfaction (0-1)")


class ConfidenceInterval(BaseModel):
    """Confidence interval for predictions"""
    lower: Any = Field(..., description="Lower bound")
    upper: Any = Field(..., description="Upper bound")


class PredictionTrends(BaseModel):
    """Prediction trends"""
    schedule_trend: str = Field(..., description="Schedule trend (improving, declining, stable)")
    cost_trend: str = Field(..., description="Cost trend (improving, declining, stable)")
    quality_trend: str = Field(..., description="Quality trend (improving, declining, stable)")


class OutcomePredictionResponse(BaseModel):
    """Outcome prediction response"""
    success: bool = Field(..., description="Whether the operation was successful")
    project_id: int = Field(..., description="Project ID")
    predictions: OutcomePrediction = Field(..., description="Predicted outcomes")
    confidence_intervals: Dict[str, ConfidenceInterval] = Field(..., description="Confidence intervals")
    trends: PredictionTrends = Field(..., description="Prediction trends")
    risk_factors: List[str] = Field(..., description="List of risk factors")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class RiskCardInfo(BaseModel):
    """Risk card information for dashboard"""
    project_id: int = Field(..., description="Project ID")
    project_name: str = Field(..., description="Project name")
    risk_score: float = Field(..., description="Risk score (0-100)")
    risk_level: RiskLevel = Field(..., description="Risk level")
    critical_factors: int = Field(..., description="Number of critical risk factors")
    high_impact_actions: int = Field(..., description="Number of high-impact actions")
    last_updated: str = Field(..., description="Last update timestamp")
    trend: str = Field(..., description="Risk trend (increasing, decreasing, stable)")


class PortfolioRiskResponse(BaseModel):
    """Portfolio risk response"""
    success: bool = Field(..., description="Whether the operation was successful")
    total_projects: int = Field(..., description="Total number of projects")
    high_risk_projects: int = Field(..., description="Number of high-risk projects")
    critical_risk_projects: int = Field(..., description="Number of critical-risk projects")
    average_risk_score: float = Field(..., description="Average risk score across portfolio")
    risk_cards: List[RiskCardInfo] = Field(..., description="List of risk cards")
    error: Optional[str] = Field(None, description="Error message if operation failed")
