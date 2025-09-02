#!/usr/bin/env python3
"""
Plan Analysis and Modification Service
Provides comprehensive analysis, modification, and versioning capabilities for project plans.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from app.models.project import Project, ProjectPlan, PlanTask, PlanMilestone, Task, Milestone
from app.models.resource import Resource, ResourceSkill
from app.core.database import get_db

logger = logging.getLogger(__name__)


class PlanAnalysisService:
    """Service for analyzing and modifying project plans"""
    
    def __init__(self):
        self.analysis_metrics = {
            "completeness": self._analyze_completeness,
            "consistency": self._analyze_consistency,
            "feasibility": self._analyze_feasibility,
            "resource_optimization": self._analyze_resource_optimization,
            "risk_assessment": self._analyze_risk_assessment,
            "timeline_analysis": self._analyze_timeline
        }
    
    async def analyze_plan(
        self,
        plan_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Comprehensive plan analysis
        """
        try:
            # Get plan details
            plan_query = select(ProjectPlan).where(ProjectPlan.id == plan_id)
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()
            
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Get plan tasks and milestones
            tasks_query = select(PlanTask).where(PlanTask.plan_id == plan_id)
            tasks_result = await db.execute(tasks_query)
            plan_tasks = tasks_result.scalars().all()
            
            milestones_query = select(PlanMilestone).where(PlanMilestone.plan_id == plan_id)
            milestones_result = await db.execute(milestones_query)
            plan_milestones = milestones_result.scalars().all()
            
            # Perform comprehensive analysis
            analysis_results = {}
            
            for metric_name, analysis_func in self.analysis_metrics.items():
                analysis_results[metric_name] = await analysis_func(plan, plan_tasks, plan_milestones, db)
            
            # Calculate overall plan health score
            overall_score = self._calculate_overall_score(analysis_results)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(analysis_results, plan, plan_tasks)
            
            return {
                "plan_id": plan_id,
                "plan_name": plan.name,
                "analysis_timestamp": datetime.now().isoformat(),
                "overall_health_score": overall_score,
                "detailed_analysis": analysis_results,
                "recommendations": recommendations,
                "summary": {
                    "total_tasks": len(plan_tasks),
                    "total_milestones": len(plan_milestones),
                    "estimated_duration": plan.estimated_duration_days,
                    "estimated_hours": plan.estimated_hours,
                    "required_resources": plan.required_resources
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing plan {plan_id}: {str(e)}")
            raise
    
    async def _analyze_completeness(
        self,
        plan: ProjectPlan,
        plan_tasks: List[PlanTask],
        plan_milestones: List[PlanMilestone],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze plan completeness
        """
        completeness_score = 0
        missing_elements = []
        
        # Check required elements
        required_elements = {
            "project_name": plan.name,
            "project_description": plan.description,
            "tasks": len(plan_tasks) > 0,
            "milestones": len(plan_milestones) > 0,
            "timeline": plan.estimated_duration_days > 0,
            "resource_requirements": plan.required_resources > 0
        }
        
        # Check task completeness
        task_completeness = 0
        for task in plan_tasks:
            task_score = 0
            if task.name:
                task_score += 20
            if task.description:
                task_score += 20
            if task.estimated_hours:
                task_score += 20
            if task.start_date and task.due_date:
                task_score += 20
            if task.skill_requirements:
                task_score += 20
            task_completeness += task_score
        
        task_completeness = task_completeness / len(plan_tasks) if plan_tasks else 0
        
        # Calculate overall completeness
        element_score = sum(required_elements.values()) / len(required_elements) * 100
        completeness_score = (element_score * 0.6) + (task_completeness * 0.4)
        
        # Identify missing elements
        for element, present in required_elements.items():
            if not present:
                missing_elements.append(element)
        
        return {
            "score": completeness_score,
            "missing_elements": missing_elements,
            "task_completeness": task_completeness,
            "element_coverage": element_score
        }
    
    async def _analyze_consistency(
        self,
        plan: ProjectPlan,
        plan_tasks: List[PlanTask],
        plan_milestones: List[PlanMilestone],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze plan consistency
        """
        consistency_score = 100
        inconsistencies = []
        
        # Check date consistency
        for task in plan_tasks:
            if task.start_date and task.due_date:
                if task.start_date > task.due_date:
                    inconsistencies.append(f"Task '{task.name}' has start date after due date")
                    consistency_score -= 10
        
        # Check dependency consistency
        task_ids = {task.id for task in plan_tasks}
        for task in plan_tasks:
            if task.dependencies:
                for dep_id in task.dependencies:
                    if dep_id not in task_ids:
                        inconsistencies.append(f"Task '{task.name}' has invalid dependency ID {dep_id}")
                        consistency_score -= 5
        
        # Check milestone consistency
        for milestone in plan_milestones:
            if milestone.associated_tasks:
                for task_id in milestone.associated_tasks:
                    if task_id not in task_ids:
                        inconsistencies.append(f"Milestone '{milestone.name}' has invalid task ID {task_id}")
                        consistency_score -= 5
        
        # Check resource assignment consistency
        assigned_resources = set()
        for task in plan_tasks:
            if task.assigned_resource_id:
                assigned_resources.add(task.assigned_resource_id)
        
        if len(assigned_resources) > plan.required_resources:
            inconsistencies.append(f"More resources assigned ({len(assigned_resources)}) than required ({plan.required_resources})")
            consistency_score -= 10
        
        return {
            "score": max(0, consistency_score),
            "inconsistencies": inconsistencies,
            "total_issues": len(inconsistencies)
        }
    
    async def _analyze_feasibility(
        self,
        plan: ProjectPlan,
        plan_tasks: List[PlanTask],
        plan_milestones: List[PlanMilestone],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze plan feasibility
        """
        feasibility_score = 100
        feasibility_issues = []
        
        # Check timeline feasibility
        total_hours = sum(task.estimated_hours or 0 for task in plan_tasks)
        if plan.estimated_duration_days > 0:
            daily_hours = total_hours / plan.estimated_duration_days
            if daily_hours > 40:  # Assuming 40 hours per day is maximum
                feasibility_issues.append(f"Daily workload ({daily_hours:.1f} hours) exceeds reasonable capacity")
                feasibility_score -= 20
        
        # Check resource availability
        if plan.required_resources > 0:
            # Get available resources
            resources_query = select(Resource).where(Resource.is_active == True)
            resources_result = await db.execute(resources_query)
            available_resources = resources_result.scalars().all()
            
            if len(available_resources) < plan.required_resources:
                feasibility_issues.append(f"Insufficient resources: {len(available_resources)} available vs {plan.required_resources} required")
                feasibility_score -= 30
        
        # Check skill requirements feasibility
        skill_requirements = set()
        for task in plan_tasks:
            if task.skill_requirements:
                skill_requirements.update(task.skill_requirements)
        
        if skill_requirements:
            # Check if skills are available
            skills_query = select(ResourceSkill).where(ResourceSkill.skill_id.in_(skill_requirements))
            skills_result = await db.execute(skills_query)
            available_skills = skills_result.scalars().all()
            
            if len(available_skills) < len(skill_requirements):
                feasibility_issues.append(f"Some required skills are not available")
                feasibility_score -= 15
        
        return {
            "score": max(0, feasibility_score),
            "issues": feasibility_issues,
            "total_hours": total_hours,
            "daily_workload": total_hours / plan.estimated_duration_days if plan.estimated_duration_days > 0 else 0
        }
    
    async def _analyze_resource_optimization(
        self,
        plan: ProjectPlan,
        plan_tasks: List[PlanTask],
        plan_milestones: List[PlanMilestone],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze resource optimization
        """
        optimization_score = 100
        optimization_issues = []
        
        # Analyze resource utilization
        resource_assignments = {}
        for task in plan_tasks:
            if task.assigned_resource_id:
                if task.assigned_resource_id not in resource_assignments:
                    resource_assignments[task.assigned_resource_id] = {
                        "total_hours": 0,
                        "tasks": [],
                        "skill_matches": []
                    }
                
                resource_assignments[task.assigned_resource_id]["total_hours"] += task.estimated_hours or 0
                resource_assignments[task.assigned_resource_id]["tasks"].append(task.name)
                resource_assignments[task.assigned_resource_id]["skill_matches"].append(task.skill_match_score or 0)
        
        # Check for over-allocation
        for resource_id, data in resource_assignments.items():
            if data["total_hours"] > 160:  # Assuming 160 hours per month
                optimization_issues.append(f"Resource {resource_id} is over-allocated ({data['total_hours']} hours)")
                optimization_score -= 15
            
            # Check skill match quality
            avg_skill_match = sum(data["skill_matches"]) / len(data["skill_matches"])
            if avg_skill_match < 0.6:
                optimization_issues.append(f"Resource {resource_id} has low skill match ({avg_skill_match:.2f})")
                optimization_score -= 10
        
        # Check for unassigned tasks
        unassigned_tasks = [task.name for task in plan_tasks if not task.assigned_resource_id]
        if unassigned_tasks:
            optimization_issues.append(f"{len(unassigned_tasks)} tasks are unassigned")
            optimization_score -= len(unassigned_tasks) * 5
        
        return {
            "score": max(0, optimization_score),
            "issues": optimization_issues,
            "resource_assignments": resource_assignments,
            "unassigned_tasks": unassigned_tasks,
            "utilization_rate": len(resource_assignments) / plan.required_resources if plan.required_resources > 0 else 0
        }
    
    async def _analyze_risk_assessment(
        self,
        plan: ProjectPlan,
        plan_tasks: List[PlanTask],
        plan_milestones: List[PlanMilestone],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze plan risks
        """
        risk_score = 100
        identified_risks = []
        
        # Check for high-risk tasks
        high_risk_tasks = []
        for task in plan_tasks:
            task_risk = 0
            
            # High estimated hours
            if task.estimated_hours and task.estimated_hours > 40:
                task_risk += 20
                identified_risks.append(f"Task '{task.name}' has high estimated hours ({task.estimated_hours})")
            
            # No skill requirements
            if not task.skill_requirements:
                task_risk += 15
                identified_risks.append(f"Task '{task.name}' has no skill requirements defined")
            
            # No resource assignment
            if not task.assigned_resource_id:
                task_risk += 10
                identified_risks.append(f"Task '{task.name}' has no resource assignment")
            
            # Long duration
            if task.start_date and task.due_date:
                duration = (task.due_date - task.start_date).days
                if duration > 30:
                    task_risk += 15
                    identified_risks.append(f"Task '{task.name}' has long duration ({duration} days)")
            
            if task_risk > 30:
                high_risk_tasks.append({
                    "task_name": task.name,
                    "risk_score": task_risk,
                    "risk_factors": identified_risks[-3:]  # Last 3 risks for this task
                })
        
        # Check for critical path risks
        critical_milestones = [m for m in plan_milestones if m.is_critical]
        if len(critical_milestones) > 3:
            identified_risks.append(f"Too many critical milestones ({len(critical_milestones)})")
            risk_score -= 10
        
        # Calculate overall risk score
        risk_score -= len(high_risk_tasks) * 5
        risk_score -= len(identified_risks) * 2
        
        return {
            "score": max(0, risk_score),
            "identified_risks": identified_risks,
            "high_risk_tasks": high_risk_tasks,
            "critical_milestones": len(critical_milestones),
            "total_risks": len(identified_risks)
        }
    
    async def _analyze_timeline(
        self,
        plan: ProjectPlan,
        plan_tasks: List[PlanTask],
        plan_milestones: List[PlanMilestone],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Analyze timeline and scheduling
        """
        timeline_score = 100
        timeline_issues = []
        
        # Check for overlapping tasks
        task_periods = []
        for task in plan_tasks:
            if task.start_date and task.due_date:
                task_periods.append({
                    "task_name": task.name,
                    "start": task.start_date,
                    "end": task.due_date,
                    "resource_id": task.assigned_resource_id
                })
        
        # Check for resource conflicts
        resource_conflicts = []
        for i, period1 in enumerate(task_periods):
            for j, period2 in enumerate(task_periods[i+1:], i+1):
                if (period1["resource_id"] and period2["resource_id"] and 
                    period1["resource_id"] == period2["resource_id"]):
                    # Check for overlap
                    if (period1["start"] <= period2["end"] and 
                        period1["end"] >= period2["start"]):
                        resource_conflicts.append({
                            "resource_id": period1["resource_id"],
                            "task1": period1["task_name"],
                            "task2": period2["task_name"],
                            "overlap_days": (min(period1["end"], period2["end"]) - 
                                           max(period1["start"], period2["start"])).days
                        })
        
        if resource_conflicts:
            timeline_issues.extend([f"Resource conflict: {conflict['task1']} and {conflict['task2']}" 
                                  for conflict in resource_conflicts])
            timeline_score -= len(resource_conflicts) * 10
        
        # Check milestone feasibility
        for milestone in plan_milestones:
            if milestone.associated_tasks:
                # Check if all associated tasks can be completed before milestone
                milestone_date = milestone.due_date
                for task_id in milestone.associated_tasks:
                    task = next((t for t in plan_tasks if t.id == task_id), None)
                    if task and task.due_date and task.due_date > milestone_date:
                        timeline_issues.append(f"Task '{task.name}' ends after milestone '{milestone.name}'")
                        timeline_score -= 5
        
        return {
            "score": max(0, timeline_score),
            "issues": timeline_issues,
            "resource_conflicts": resource_conflicts,
            "total_conflicts": len(resource_conflicts)
        }
    
    def _calculate_overall_score(self, analysis_results: Dict[str, Any]) -> float:
        """
        Calculate overall plan health score
        """
        weights = {
            "completeness": 0.25,
            "consistency": 0.20,
            "feasibility": 0.25,
            "resource_optimization": 0.15,
            "risk_assessment": 0.10,
            "timeline_analysis": 0.05
        }
        
        overall_score = 0
        for metric, weight in weights.items():
            if metric in analysis_results:
                overall_score += analysis_results[metric]["score"] * weight
        
        return overall_score
    
    async def _generate_recommendations(
        self,
        analysis_results: Dict[str, Any],
        plan: ProjectPlan,
        plan_tasks: List[PlanTask]
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement recommendations
        """
        recommendations = []
        
        # Completeness recommendations
        completeness = analysis_results.get("completeness", {})
        if completeness.get("score", 0) < 80:
            recommendations.append({
                "category": "completeness",
                "priority": "high",
                "title": "Improve Plan Completeness",
                "description": f"Plan completeness score is {completeness.get('score', 0):.1f}%. Add missing elements.",
                "actions": [
                    "Add missing project description",
                    "Define skill requirements for all tasks",
                    "Add resource assignments for unassigned tasks"
                ]
            })
        
        # Consistency recommendations
        consistency = analysis_results.get("consistency", {})
        if consistency.get("total_issues", 0) > 0:
            recommendations.append({
                "category": "consistency",
                "priority": "high",
                "title": "Fix Plan Inconsistencies",
                "description": f"Found {consistency.get('total_issues', 0)} consistency issues.",
                "actions": [
                    "Fix date inconsistencies",
                    "Resolve invalid dependencies",
                    "Correct resource assignments"
                ]
            })
        
        # Feasibility recommendations
        feasibility = analysis_results.get("feasibility", {})
        if feasibility.get("score", 0) < 70:
            recommendations.append({
                "category": "feasibility",
                "priority": "critical",
                "title": "Address Feasibility Issues",
                "description": f"Plan feasibility score is {feasibility.get('score', 0):.1f}%.",
                "actions": [
                    "Reduce daily workload",
                    "Increase available resources",
                    "Extend project timeline"
                ]
            })
        
        # Resource optimization recommendations
        resource_opt = analysis_results.get("resource_optimization", {})
        if resource_opt.get("score", 0) < 80:
            recommendations.append({
                "category": "resource_optimization",
                "priority": "medium",
                "title": "Optimize Resource Allocation",
                "description": f"Resource optimization score is {resource_opt.get('score', 0):.1f}%.",
                "actions": [
                    "Reassign over-allocated resources",
                    "Improve skill matches",
                    "Assign unassigned tasks"
                ]
            })
        
        return recommendations
    
    async def create_plan_version(
        self,
        plan_id: int,
        version_name: str,
        changes: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Create a new version of an existing plan
        """
        try:
            # Get current plan
            plan_query = select(ProjectPlan).where(ProjectPlan.id == plan_id)
            plan_result = await db.execute(plan_query)
            current_plan = plan_result.scalar_one_or_none()
            
            if not current_plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Create new version
            new_version = ProjectPlan(
                project_id=current_plan.project_id,
                name=version_name,
                description=current_plan.description,
                version=self._increment_version(current_plan.version),
                status="draft",
                plan_type=current_plan.plan_type,
                creation_method="version",
                source_documents=current_plan.source_documents,
                extraction_confidence=current_plan.extraction_confidence,
                
                # Apply changes
                epics=changes.get("epics", current_plan.epics),
                features=changes.get("features", current_plan.features),
                tasks=changes.get("tasks", current_plan.tasks),
                milestones=changes.get("milestones", current_plan.milestones),
                dependencies=changes.get("dependencies", current_plan.dependencies),
                risks=changes.get("risks", current_plan.risks),
                resource_requirements=changes.get("resource_requirements", current_plan.resource_requirements),
                
                # Recalculate metrics
                total_tasks=len(changes.get("tasks", current_plan.tasks or [])),
                total_milestones=len(changes.get("milestones", current_plan.milestones or [])),
                estimated_duration_days=changes.get("estimated_duration_days", current_plan.estimated_duration_days),
                estimated_hours=changes.get("estimated_hours", current_plan.estimated_hours),
                required_resources=changes.get("required_resources", current_plan.required_resources),
                total_budget=changes.get("total_budget", current_plan.total_budget),
                
                # Metadata
                created_by_id=current_plan.created_by_id,
                approved_by_id=None
            )
            
            db.add(new_version)
            await db.flush()
            
            return {
                "success": True,
                "new_plan_id": new_version.id,
                "version": new_version.version,
                "message": f"Plan version {new_version.version} created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating plan version: {str(e)}")
            raise
    
    def _increment_version(self, current_version: str) -> str:
        """
        Increment version number
        """
        try:
            major, minor = current_version.split(".")
            return f"{major}.{int(minor) + 1}"
        except:
            return "1.1"
