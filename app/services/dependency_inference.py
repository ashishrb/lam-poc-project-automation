#!/usr/bin/env python3
"""
Dependency Inference Service
Analyzes tasks for missing dependencies and prevents cycles
"""

import json
import logging
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.project import Project, Task
from app.models.project import TaskStatus, TaskPriority
from app.services.ai_guardrails import AIGuardrails
from app.core.config import settings

logger = logging.getLogger(__name__)


class DependencyType(str, Enum):
    """Types of task dependencies"""
    FINISH_TO_START = "finish_to_start"
    START_TO_START = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    START_TO_FINISH = "start_to_finish"


class DependencyConfidence(str, Enum):
    """Confidence levels for inferred dependencies"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class InferredDependency:
    """Inferred dependency information"""
    source_task_id: int
    target_task_id: int
    dependency_type: DependencyType
    confidence: DependencyConfidence
    reason: str
    suggested_guardrail: str


@dataclass
class DependencyCycle:
    """Dependency cycle information"""
    cycle_tasks: List[int]
    cycle_path: List[Tuple[int, int]]
    severity: str  # low, medium, high, critical
    impact: str
    suggested_fix: str


class DependencyInferenceService:
    """Service for inferring missing dependencies and detecting cycles"""
    
    def __init__(self):
        self.guardrails = AIGuardrails()
        self.dependency_patterns = {
            "prerequisites": [
                r"(?:requires|needs|depends on|after|following)\s+(.+?)(?:\.|$)",
                r"(?:must complete|should finish|need to finish)\s+(.+?)(?:\.|$)",
                r"(?:wait for|wait until)\s+(.+?)(?:\.|$)"
            ],
            "blockers": [
                r"(?:blocked by|blocking|waiting for)\s+(.+?)(?:\.|$)",
                r"(?:cannot start|cannot proceed|stuck on)\s+(.+?)(?:\.|$)",
                r"(?:delayed by|delaying)\s+(.+?)(?:\.|$)"
            ],
            "parallel_work": [
                r"(?:in parallel with|concurrently|simultaneously)\s+(.+?)(?:\.|$)",
                r"(?:can start together|can work together)\s+(.+?)(?:\.|$)"
            ]
        }
    
    async def infer_missing_dependencies(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Infer missing dependencies for a project"""
        try:
            # Get project tasks
            tasks = await self._get_project_tasks(project_id, db)
            if not tasks:
                return {
                    "success": False,
                    "error": "No tasks found for project"
                }
            
            # Analyze existing dependencies
            existing_deps = await self._analyze_existing_dependencies(tasks)
            
            # Infer missing dependencies using multiple methods
            inferred_deps = []
            
            # Method 1: Pattern-based inference
            pattern_deps = await self._infer_dependencies_by_patterns(tasks)
            inferred_deps.extend(pattern_deps)
            
            # Method 2: AI-based inference
            ai_deps = await self._infer_dependencies_by_ai(tasks)
            inferred_deps.extend(ai_deps)
            
            # Method 3: Temporal inference
            temporal_deps = await self._infer_dependencies_by_temporal_logic(tasks)
            inferred_deps.extend(temporal_deps)
            
            # Method 4: Resource-based inference
            resource_deps = await self._infer_dependencies_by_resources(tasks)
            inferred_deps.extend(resource_deps)
            
            # Filter out duplicates and existing dependencies
            unique_deps = await self._filter_unique_dependencies(
                inferred_deps, existing_deps
            )
            
            # Generate guardrails for each dependency
            enhanced_deps = await self._generate_dependency_guardrails(unique_deps)
            
            return {
                "success": True,
                "project_id": project_id,
                "total_tasks": len(tasks),
                "existing_dependencies": len(existing_deps),
                "inferred_dependencies": len(enhanced_deps),
                "dependencies": [
                    {
                        "source_task_id": dep.source_task_id,
                        "target_task_id": dep.target_task_id,
                        "dependency_type": dep.dependency_type.value,
                        "confidence": dep.confidence.value,
                        "reason": dep.reason,
                        "suggested_guardrail": dep.suggested_guardrail
                    }
                    for dep in enhanced_deps
                ],
                "summary": {
                    "high_confidence": len([d for d in enhanced_deps if d.confidence == DependencyConfidence.HIGH]),
                    "medium_confidence": len([d for d in enhanced_deps if d.confidence == DependencyConfidence.MEDIUM]),
                    "low_confidence": len([d for d in enhanced_deps if d.confidence == DependencyConfidence.LOW])
                }
            }
            
        except Exception as e:
            logger.error(f"Error inferring missing dependencies: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def detect_dependency_cycles(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Detect dependency cycles in a project"""
        try:
            # Get project tasks
            tasks = await self._get_project_tasks(project_id, db)
            if not tasks:
                return {
                    "success": False,
                    "error": "No tasks found for project"
                }
            
            # Build dependency graph
            dependency_graph = await self._build_dependency_graph(tasks)
            
            # Detect cycles
            cycles = await self._detect_cycles_in_graph(dependency_graph)
            
            # Analyze cycle impact
            analyzed_cycles = await self._analyze_cycle_impact(cycles, tasks)
            
            # Generate fixes
            cycles_with_fixes = await self._generate_cycle_fixes(analyzed_cycles)
            
            return {
                "success": True,
                "project_id": project_id,
                "total_tasks": len(tasks),
                "cycles_detected": len(cycles_with_fixes),
                "cycles": [
                    {
                        "cycle_tasks": cycle.cycle_tasks,
                        "cycle_path": cycle.cycle_path,
                        "severity": cycle.severity,
                        "impact": cycle.impact,
                        "suggested_fix": cycle.suggested_fix
                    }
                    for cycle in cycles_with_fixes
                ],
                "summary": {
                    "critical_cycles": len([c for c in cycles_with_fixes if c.severity == "critical"]),
                    "high_impact_cycles": len([c for c in cycles_with_fixes if c.severity == "high"]),
                    "medium_impact_cycles": len([c for c in cycles_with_fixes if c.severity == "medium"]),
                    "low_impact_cycles": len([c for c in cycles_with_fixes if c.severity == "low"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error detecting dependency cycles: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_dependencies(
        self, 
        project_id: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Validate existing dependencies and suggest improvements"""
        try:
            # Get project tasks
            tasks = await self._get_project_tasks(project_id, db)
            if not tasks:
                return {
                    "success": False,
                    "error": "No tasks found for project"
                }
            
            # Validate each task's dependencies
            validation_results = []
            
            for task in tasks:
                if not task.dependencies:
                    continue
                
                try:
                    deps = json.loads(task.dependencies)
                    if isinstance(deps, list):
                        dep_ids = deps
                    elif isinstance(deps, dict) and "dependencies" in deps:
                        dep_ids = deps["dependencies"]
                    else:
                        continue
                    
                    # Validate each dependency
                    for dep_id in dep_ids:
                        dep_task = next((t for t in tasks if t.id == dep_id), None)
                        if not dep_task:
                            validation_results.append({
                                "task_id": task.id,
                                "dependency_id": dep_id,
                                "issue": "Dependency task not found",
                                "severity": "high",
                                "suggestion": f"Remove dependency on non-existent task {dep_id}"
                            })
                        else:
                            # Check for logical issues
                            logical_issues = await self._check_logical_dependency_issues(
                                task, dep_task
                            )
                            validation_results.extend(logical_issues)
                
                except (json.JSONDecodeError, TypeError):
                    validation_results.append({
                        "task_id": task.id,
                        "dependency_id": None,
                        "issue": "Invalid dependency format",
                        "severity": "high",
                        "suggestion": "Fix dependency JSON format"
                    })
            
            return {
                "success": True,
                "project_id": project_id,
                "total_tasks": len(tasks),
                "validation_results": validation_results,
                "summary": {
                    "high_severity": len([r for r in validation_results if r["severity"] == "high"]),
                    "medium_severity": len([r for r in validation_results if r["severity"] == "medium"]),
                    "low_severity": len([r for r in validation_results if r["severity"] == "low"])
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating dependencies: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def apply_dependency_suggestions(
        self, 
        project_id: int, 
        suggestions: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Apply dependency suggestions to the project"""
        try:
            applied_count = 0
            failed_count = 0
            errors = []
            
            for suggestion in suggestions:
                try:
                    if suggestion["action"] == "add_dependency":
                        success = await self._add_dependency(
                            suggestion["source_task_id"],
                            suggestion["target_task_id"],
                            suggestion.get("dependency_type", "finish_to_start"),
                            db
                        )
                        if success:
                            applied_count += 1
                        else:
                            failed_count += 1
                            errors.append(f"Failed to add dependency: {suggestion}")
                    
                    elif suggestion["action"] == "remove_dependency":
                        success = await self._remove_dependency(
                            suggestion["source_task_id"],
                            suggestion["target_task_id"],
                            db
                        )
                        if success:
                            applied_count += 1
                        else:
                            failed_count += 1
                            errors.append(f"Failed to remove dependency: {suggestion}")
                    
                    elif suggestion["action"] == "fix_cycle":
                        success = await self._fix_dependency_cycle(
                            suggestion["cycle_tasks"],
                            suggestion["fix_strategy"],
                            db
                        )
                        if success:
                            applied_count += 1
                        else:
                            failed_count += 1
                            errors.append(f"Failed to fix cycle: {suggestion}")
                
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Error applying suggestion {suggestion}: {e}")
            
            return {
                "success": True,
                "project_id": project_id,
                "applied_suggestions": applied_count,
                "failed_suggestions": failed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error applying dependency suggestions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _get_project_tasks(self, project_id: int, db: AsyncSession) -> List[Task]:
        """Get all tasks for a project"""
        result = await db.execute(
            select(Task).where(Task.project_id == project_id).order_by(Task.start_date)
        )
        return result.scalars().all()
    
    async def _analyze_existing_dependencies(self, tasks: List[Task]) -> Set[Tuple[int, int]]:
        """Analyze existing dependencies in tasks"""
        existing_deps = set()
        
        for task in tasks:
            if not task.dependencies:
                continue
            
            try:
                deps = json.loads(task.dependencies)
                if isinstance(deps, list):
                    dep_ids = deps
                elif isinstance(deps, dict) and "dependencies" in deps:
                    dep_ids = deps["dependencies"]
                else:
                    continue
                
                for dep_id in dep_ids:
                    existing_deps.add((task.id, dep_id))
            
            except (json.JSONDecodeError, TypeError):
                continue
        
        return existing_deps
    
    async def _infer_dependencies_by_patterns(self, tasks: List[Task]) -> List[InferredDependency]:
        """Infer dependencies using pattern matching"""
        inferred_deps = []
        
        for task in tasks:
            if not task.description:
                continue
            
            # Check for prerequisite patterns
            for pattern in self.dependency_patterns["prerequisites"]:
                matches = re.finditer(pattern, task.description, re.IGNORECASE)
                for match in matches:
                    dependency_text = match.group(1).strip()
                    # Try to find matching task
                    target_task = await self._find_task_by_text(dependency_text, tasks)
                    if target_task and target_task.id != task.id:
                        inferred_deps.append(InferredDependency(
                            source_task_id=task.id,
                            target_task_id=target_task.id,
                            dependency_type=DependencyType.FINISH_TO_START,
                            confidence=DependencyConfidence.MEDIUM,
                            reason=f"Pattern match: '{match.group(0)}'",
                            suggested_guardrail="Verify prerequisite relationship"
                        ))
            
            # Check for blocker patterns
            for pattern in self.dependency_patterns["blockers"]:
                matches = re.finditer(pattern, task.description, re.IGNORECASE)
                for match in matches:
                    dependency_text = match.group(1).strip()
                    target_task = await self._find_task_by_text(dependency_text, tasks)
                    if target_task and target_task.id != task.id:
                        inferred_deps.append(InferredDependency(
                            source_task_id=task.id,
                            target_task_id=target_task.id,
                            dependency_type=DependencyType.FINISH_TO_START,
                            confidence=DependencyConfidence.HIGH,
                            reason=f"Blocker pattern: '{match.group(0)}'",
                            suggested_guardrail="Confirm blocking relationship"
                        ))
        
        return inferred_deps
    
    async def _infer_dependencies_by_ai(self, tasks: List[Task]) -> List[InferredDependency]:
        """Infer dependencies using AI analysis"""
        try:
            # Create prompt for AI analysis
            prompt = self._create_dependency_inference_prompt(tasks)
            
            # Call AI service
            ai_response = await self.guardrails.call_ai_model(prompt)
            
            # Parse AI response
            inferred_deps = await self._parse_ai_dependency_response(ai_response, tasks)
            
            return inferred_deps
            
        except Exception as e:
            logger.error(f"Error inferring dependencies by AI: {e}")
            return []
    
    def _create_dependency_inference_prompt(self, tasks: List[Task]) -> str:
        """Create prompt for AI dependency inference"""
        task_descriptions = []
        for task in tasks:
            task_descriptions.append(f"Task {task.id}: {task.title} - {task.description}")
        
        return f"""
Analyze the following tasks and identify missing dependencies between them.

Tasks:
{chr(10).join(task_descriptions)}

Please identify logical dependencies that should exist between these tasks. Consider:
1. Prerequisites (what must be completed before another task can start)
2. Blockers (what prevents a task from proceeding)
3. Resource dependencies (shared resources or skills)
4. Temporal dependencies (timing relationships)

Return the results as a JSON array with the following structure:
[
  {{
    "source_task_id": "ID of task that depends on another",
    "target_task_id": "ID of task that is depended upon",
    "dependency_type": "finish_to_start|start_to_start|finish_to_finish|start_to_finish",
    "confidence": "high|medium|low",
    "reason": "Explanation of why this dependency should exist"
  }}
]

Focus on logical relationships and avoid creating circular dependencies.
"""
    
    async def _parse_ai_dependency_response(
        self, 
        ai_response: str, 
        tasks: List[Task]
    ) -> List[InferredDependency]:
        """Parse AI response into InferredDependency objects"""
        inferred_deps = []
        
        try:
            # Extract JSON from AI response
            json_match = re.search(r'\[.*\]', ai_response, re.DOTALL)
            if not json_match:
                return inferred_deps
            
            dep_data = json.loads(json_match.group())
            
            for item in dep_data:
                # Parse dependency type
                dep_type = DependencyType.FINISH_TO_START
                if item.get("dependency_type") == "start_to_start":
                    dep_type = DependencyType.START_TO_START
                elif item.get("dependency_type") == "finish_to_finish":
                    dep_type = DependencyType.FINISH_TO_FINISH
                elif item.get("dependency_type") == "start_to_finish":
                    dep_type = DependencyType.START_TO_FINISH
                
                # Parse confidence
                confidence = DependencyConfidence.MEDIUM
                if item.get("confidence") == "high":
                    confidence = DependencyConfidence.HIGH
                elif item.get("confidence") == "low":
                    confidence = DependencyConfidence.LOW
                
                inferred_deps.append(InferredDependency(
                    source_task_id=int(item["source_task_id"]),
                    target_task_id=int(item["target_task_id"]),
                    dependency_type=dep_type,
                    confidence=confidence,
                    reason=item["reason"],
                    suggested_guardrail="Review AI-suggested dependency"
                ))
            
        except Exception as e:
            logger.error(f"Error parsing AI dependency response: {e}")
        
        return inferred_deps
    
    async def _infer_dependencies_by_temporal_logic(self, tasks: List[Task]) -> List[InferredDependency]:
        """Infer dependencies based on temporal logic"""
        inferred_deps = []
        
        # Sort tasks by start date
        sorted_tasks = sorted(tasks, key=lambda t: t.start_date or date.today())
        
        for i, task in enumerate(sorted_tasks):
            if not task.start_date:
                continue
            
            # Check if any later task should depend on this one
            for later_task in sorted_tasks[i+1:]:
                if not later_task.start_date:
                    continue
                
                # If later task starts before this one ends, there might be a dependency
                if later_task.start_date < (task.due_date or task.start_date + timedelta(days=1)):
                    # Check if they're related by title or description
                    if await self._are_tasks_related(task, later_task):
                        inferred_deps.append(InferredDependency(
                            source_task_id=later_task.id,
                            target_task_id=task.id,
                            dependency_type=DependencyType.FINISH_TO_START,
                            confidence=DependencyConfidence.LOW,
                            reason="Temporal overlap detected",
                            suggested_guardrail="Verify temporal dependency"
                        ))
        
        return inferred_deps
    
    async def _infer_dependencies_by_resources(self, tasks: List[Task]) -> List[InferredDependency]:
        """Infer dependencies based on resource constraints"""
        inferred_deps = []
        
        # Group tasks by assignee
        assignee_tasks = {}
        for task in tasks:
            if task.assigned_to_id:
                if task.assigned_to_id not in assignee_tasks:
                    assignee_tasks[task.assigned_to_id] = []
                assignee_tasks[task.assigned_to_id].append(task)
        
        # Check for resource conflicts
        for assignee_id, assignee_task_list in assignee_tasks.items():
            if len(assignee_task_list) > 1:
                # Sort by start date
                sorted_tasks = sorted(assignee_task_list, key=lambda t: t.start_date or date.today())
                
                for i, task in enumerate(sorted_tasks[:-1]):
                    next_task = sorted_tasks[i + 1]
                    
                    # If tasks overlap in time, suggest dependency
                    if (task.due_date and next_task.start_date and 
                        task.due_date > next_task.start_date):
                        inferred_deps.append(InferredDependency(
                            source_task_id=next_task.id,
                            target_task_id=task.id,
                            dependency_type=DependencyType.FINISH_TO_START,
                            confidence=DependencyConfidence.HIGH,
                            reason=f"Resource conflict: both tasks assigned to same person",
                            suggested_guardrail="Resolve resource allocation conflict"
                        ))
        
        return inferred_deps
    
    async def _filter_unique_dependencies(
        self, 
        inferred_deps: List[InferredDependency],
        existing_deps: Set[Tuple[int, int]]
    ) -> List[InferredDependency]:
        """Filter out duplicates and existing dependencies"""
        unique_deps = []
        seen_pairs = set()
        
        for dep in inferred_deps:
            dep_pair = (dep.source_task_id, dep.target_task_id)
            
            # Skip if already exists or already seen
            if dep_pair in existing_deps or dep_pair in seen_pairs:
                continue
            
            # Skip self-dependencies
            if dep.source_task_id == dep.target_task_id:
                continue
            
            seen_pairs.add(dep_pair)
            unique_deps.append(dep)
        
        return unique_deps
    
    async def _generate_dependency_guardrails(self, dependencies: List[InferredDependency]) -> List[InferredDependency]:
        """Generate guardrails for dependencies"""
        for dep in dependencies:
            if dep.confidence == DependencyConfidence.LOW:
                dep.suggested_guardrail = "Review and validate suggested dependency"
            elif dep.confidence == DependencyConfidence.MEDIUM:
                dep.suggested_guardrail = "Confirm dependency relationship with team"
            else:  # HIGH
                dep.suggested_guardrail = "Apply dependency and monitor impact"
        
        return dependencies
    
    async def _build_dependency_graph(self, tasks: List[Task]) -> Dict[int, List[int]]:
        """Build dependency graph from tasks"""
        graph = {task.id: [] for task in tasks}
        
        for task in tasks:
            if not task.dependencies:
                continue
            
            try:
                deps = json.loads(task.dependencies)
                if isinstance(deps, list):
                    dep_ids = deps
                elif isinstance(deps, dict) and "dependencies" in deps:
                    dep_ids = deps["dependencies"]
                else:
                    continue
                
                for dep_id in dep_ids:
                    if dep_id in graph:
                        graph[task.id].append(dep_id)
            
            except (json.JSONDecodeError, TypeError):
                continue
        
        return graph
    
    async def _detect_cycles_in_graph(self, graph: Dict[int, List[int]]) -> List[List[int]]:
        """Detect cycles in dependency graph using DFS"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: int, path: List[int]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Cycle detected
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for node in graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    async def _analyze_cycle_impact(self, cycles: List[List[int]], tasks: List[Task]) -> List[DependencyCycle]:
        """Analyze the impact of dependency cycles"""
        analyzed_cycles = []
        
        for cycle in cycles:
            # Calculate cycle severity based on number of tasks and their importance
            cycle_tasks = [t for t in tasks if t.id in cycle]
            
            # Determine severity
            if len(cycle) <= 2:
                severity = "low"
            elif len(cycle) <= 4:
                severity = "medium"
            elif len(cycle) <= 6:
                severity = "high"
            else:
                severity = "critical"
            
            # Create cycle path
            cycle_path = []
            for i in range(len(cycle) - 1):
                cycle_path.append((cycle[i], cycle[i + 1]))
            cycle_path.append((cycle[-1], cycle[0]))  # Close the cycle
            
            analyzed_cycles.append(DependencyCycle(
                cycle_tasks=cycle,
                cycle_path=cycle_path,
                severity=severity,
                impact=f"Cycle affects {len(cycle)} tasks",
                suggested_fix="Break cycle by removing one dependency"
            ))
        
        return analyzed_cycles
    
    async def _generate_cycle_fixes(self, cycles: List[DependencyCycle]) -> List[DependencyCycle]:
        """Generate fixes for dependency cycles"""
        for cycle in cycles:
            if cycle.severity == "critical":
                cycle.suggested_fix = "Immediately break cycle by removing least critical dependency"
            elif cycle.severity == "high":
                cycle.suggested_fix = "Break cycle by removing dependency with lowest impact"
            elif cycle.severity == "medium":
                cycle.suggested_fix = "Review cycle and remove one dependency"
            else:  # low
                cycle.suggested_fix = "Consider breaking cycle if it causes issues"
        
        return cycles
    
    async def _find_task_by_text(self, text: str, tasks: List[Task]) -> Optional[Task]:
        """Find task by matching text in title or description"""
        text_lower = text.lower()
        
        for task in tasks:
            if (text_lower in task.title.lower() or 
                (task.description and text_lower in task.description.lower())):
                return task
        
        return None
    
    async def _are_tasks_related(self, task1: Task, task2: Task) -> bool:
        """Check if two tasks are related"""
        # Simple similarity check
        title1 = task1.title.lower()
        title2 = task2.title.lower()
        
        # Check for common words
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        common_words = words1.intersection(words2)
        return len(common_words) >= 2  # At least 2 common words
    
    async def _check_logical_dependency_issues(
        self, 
        task: Task, 
        dep_task: Task
    ) -> List[Dict[str, Any]]:
        """Check for logical issues in dependencies"""
        issues = []
        
        # Check for self-dependency
        if task.id == dep_task.id:
            issues.append({
                "task_id": task.id,
                "dependency_id": dep_task.id,
                "issue": "Self-dependency detected",
                "severity": "high",
                "suggestion": "Remove self-dependency"
            })
        
        # Check for circular dependency (simplified)
        if task.dependencies:
            try:
                deps = json.loads(task.dependencies)
                if isinstance(deps, list) and task.id in deps:
                    issues.append({
                        "task_id": task.id,
                        "dependency_id": dep_task.id,
                        "issue": "Circular dependency detected",
                        "severity": "critical",
                        "suggestion": "Break circular dependency"
                    })
            except (json.JSONDecodeError, TypeError):
                pass
        
        return issues
    
    async def _add_dependency(
        self, 
        source_task_id: int, 
        target_task_id: int, 
        dependency_type: str, 
        db: AsyncSession
    ) -> bool:
        """Add a dependency to a task"""
        try:
            # Get source task
            result = await db.execute(select(Task).where(Task.id == source_task_id))
            source_task = result.scalar_one_or_none()
            
            if not source_task:
                return False
            
            # Parse existing dependencies
            current_deps = []
            if source_task.dependencies:
                try:
                    deps = json.loads(source_task.dependencies)
                    if isinstance(deps, list):
                        current_deps = deps
                    elif isinstance(deps, dict) and "dependencies" in deps:
                        current_deps = deps["dependencies"]
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Add new dependency
            if target_task_id not in current_deps:
                current_deps.append(target_task_id)
                source_task.dependencies = json.dumps(current_deps)
                await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding dependency: {e}")
            return False
    
    async def _remove_dependency(
        self, 
        source_task_id: int, 
        target_task_id: int, 
        db: AsyncSession
    ) -> bool:
        """Remove a dependency from a task"""
        try:
            # Get source task
            result = await db.execute(select(Task).where(Task.id == source_task_id))
            source_task = result.scalar_one_or_none()
            
            if not source_task:
                return False
            
            # Parse existing dependencies
            current_deps = []
            if source_task.dependencies:
                try:
                    deps = json.loads(source_task.dependencies)
                    if isinstance(deps, list):
                        current_deps = deps
                    elif isinstance(deps, dict) and "dependencies" in deps:
                        current_deps = deps["dependencies"]
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Remove dependency
            if target_task_id in current_deps:
                current_deps.remove(target_task_id)
                source_task.dependencies = json.dumps(current_deps)
                await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing dependency: {e}")
            return False
    
    async def _fix_dependency_cycle(
        self, 
        cycle_tasks: List[int], 
        fix_strategy: str, 
        db: AsyncSession
    ) -> bool:
        """Fix a dependency cycle"""
        try:
            # Simple strategy: remove the last dependency in the cycle
            if len(cycle_tasks) >= 2:
                source_task_id = cycle_tasks[-2]
                target_task_id = cycle_tasks[-1]
                return await self._remove_dependency(source_task_id, target_task_id, db)
            
            return False
            
        except Exception as e:
            logger.error(f"Error fixing dependency cycle: {e}")
            return False
