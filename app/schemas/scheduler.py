#!/usr/bin/env python3
"""
Pydantic schemas for Dynamic Re-planning & Scenario Simulation (Phase 2)
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.services.scheduler import ConstraintType, RescheduleReason
from app.services.scenario_sim import ScenarioType, ImpactLevel


# Scheduler Schemas
class ConstraintInfo(BaseModel):
    """Constraint information"""
    type: str
    task_id: int
    description: str
    severity: str
    is_violated: bool
    current_value: Any
    required_value: Any


class ConstraintSummary(BaseModel):
    """Constraint summary"""
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int


class ConstraintAnalysisResponse(BaseModel):
    """Response for constraint analysis"""
    success: bool
    project_id: int
    total_constraints: int
    violated_constraints: int
    constraint_score: float
    constraints: List[ConstraintInfo]
    summary: ConstraintSummary


class RescheduleProposalInfo(BaseModel):
    """Reschedule proposal information"""
    task_id: int
    current_start_date: str
    current_end_date: str
    proposed_start_date: str
    proposed_end_date: str
    current_assignee_id: Optional[int]
    proposed_assignee_id: Optional[int]
    reason: str
    impact_level: str
    rationale: str
    affected_tasks: List[int]
    estimated_delay: int


class ProposalSummary(BaseModel):
    """Proposal summary"""
    total_proposals: int
    high_impact: int
    medium_impact: int
    low_impact: int


class RescheduleProposalResponse(BaseModel):
    """Response for reschedule proposals"""
    success: bool
    project_id: int
    task_id: Optional[int]
    proposals: List[RescheduleProposalInfo]
    summary: ProposalSummary


class ProposalApplyRequest(BaseModel):
    """Request to apply a reschedule proposal"""
    task_id: int
    proposed_start_date: Optional[str] = None
    proposed_end_date: Optional[str] = None
    proposed_assignee_id: Optional[int] = None


class OptimizationSuggestion(BaseModel):
    """Resource optimization suggestion"""
    type: str
    resource_id: Optional[int] = None
    resource_name: Optional[str] = None
    description: str
    impact: str
    estimated_improvement: str


class OptimizationSummary(BaseModel):
    """Optimization summary"""
    total_suggestions: int
    resource_utilization_improvement: float
    estimated_cost_savings: float


class ResourceOptimizationResponse(BaseModel):
    """Response for resource optimization"""
    success: bool
    project_id: int
    current_allocation: Dict[str, Any]
    optimizations: List[OptimizationSuggestion]
    summary: OptimizationSummary
