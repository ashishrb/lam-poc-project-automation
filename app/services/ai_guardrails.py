import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GuardrailViolation:
    """Represents a guardrail violation"""
    rule_name: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    field_path: str
    current_value: Any
    expected_value: Any
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of AI output validation"""
    is_valid: bool
    violations: List[GuardrailViolation]
    repair_suggestions: List[str]
    confidence_score: float


class AIGuardrails:
    """AI Guardrails service for validating AI outputs and enforcing business rules"""
    
    def __init__(self):
        self.max_project_duration = timedelta(days=settings.AI_MAX_PROJECT_DURATION_DAYS)
        self.max_task_duration = timedelta(days=settings.AI_MAX_TASK_DURATION_DAYS)
        self.max_workload_percent = settings.AI_MAX_WORKLOAD_PERCENT
    
    async def validate_wbs_output(self, wbs_data: Dict[str, Any], project_constraints: Dict[str, Any]) -> ValidationResult:
        """Validate Work Breakdown Structure output from AI"""
        violations = []
        repair_suggestions = []
        
        try:
            # Validate required structure
            if not isinstance(wbs_data, dict):
                violations.append(GuardrailViolation(
                    rule_name="structure",
                    severity="error",
                    message="WBS data must be a dictionary",
                    field_path="root",
                    current_value=type(wbs_data).__name__,
                    expected_value="dict"
                ))
                return ValidationResult(False, violations, repair_suggestions, 0.0)
            
            # Validate tasks array
            tasks = wbs_data.get("tasks", [])
            if not isinstance(tasks, list):
                violations.append(GuardrailViolation(
                    rule_name="tasks_structure",
                    severity="error",
                    message="Tasks must be an array",
                    field_path="tasks",
                    current_value=type(tasks).__name__,
                    expected_value="list"
                ))
            else:
                # Validate individual tasks
                for i, task in enumerate(tasks):
                    task_violations = self._validate_task(task, f"tasks[{i}]")
                    violations.extend(task_violations)
            
            # Validate dependencies
            dependencies = wbs_data.get("dependencies", [])
            if isinstance(dependencies, list):
                dep_violations = self._validate_dependencies(dependencies, tasks)
                violations.extend(dep_violations)
            
            # Validate project constraints
            constraint_violations = self._validate_project_constraints(wbs_data, project_constraints)
            violations.extend(constraint_violations)
            
            # Generate repair suggestions
            repair_suggestions = self._generate_repair_suggestions(violations)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(violations, wbs_data)
            
            is_valid = not any(v.severity == "error" for v in violations)
            
            return ValidationResult(
                is_valid=is_valid,
                violations=violations,
                repair_suggestions=repair_suggestions,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error validating WBS output: {e}")
            violations.append(GuardrailViolation(
                rule_name="validation_error",
                severity="error",
                message=f"Validation error: {str(e)}",
                field_path="root",
                current_value="error",
                expected_value="valid_data"
            ))
            return ValidationResult(False, violations, [], 0.0)
    
    def _validate_task(self, task: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual task structure and constraints"""
        violations = []
        
        # Required fields
        required_fields = ["name", "description"]
        for field in required_fields:
            if field not in task or not task[field]:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Task {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=None,
                    expected_value="non_empty_string"
                ))
        
        # Duration validation
        if "estimated_hours" in task:
            hours = task["estimated_hours"]
            if not isinstance(hours, (int, float)) or hours <= 0:
                violations.append(GuardrailViolation(
                    rule_name="duration_validation",
                    severity="error",
                    message="Estimated hours must be a positive number",
                    field_path=f"{field_path}.estimated_hours",
                    current_value=hours,
                    expected_value="positive_number"
                ))
            elif hours > 24 * self.max_task_duration.days:  # Convert to hours
                violations.append(GuardrailViolation(
                    rule_name="duration_limit",
                    severity="warning",
                    message=f"Task duration exceeds maximum allowed ({self.max_task_duration.days} days)",
                    field_path=f"{field_path}.estimated_hours",
                    current_value=hours,
                    expected_value=f"<={24 * self.max_task_duration.days}",
                    suggestion="Consider breaking this task into smaller subtasks"
                ))
        
        # Date validation
        if "start_date" in task and "due_date" in task:
            try:
                start_date = datetime.fromisoformat(task["start_date"])
                due_date = datetime.fromisoformat(task["due_date"])
                
                if due_date <= start_date:
                    violations.append(GuardrailViolation(
                        rule_name="date_logic",
                        severity="error",
                        message="Due date must be after start date",
                        field_path=f"{field_path}.dates",
                        current_value=f"start: {start_date}, due: {due_date}",
                        expected_value="due_date > start_date"
                    ))
                
                duration = due_date - start_date
                if duration > self.max_task_duration:
                    violations.append(GuardrailViolation(
                        rule_name="task_duration_limit",
                        severity="warning",
                        message=f"Task duration exceeds maximum allowed ({self.max_task_duration.days} days)",
                        field_path=f"{field_path}.duration",
                        current_value=duration.days,
                        expected_value=f"<={self.max_task_duration.days}",
                        suggestion="Consider breaking this task into smaller subtasks"
                    ))
                    
            except (ValueError, TypeError):
                violations.append(GuardrailViolation(
                    rule_name="date_format",
                    severity="error",
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    field_path=f"{field_path}.dates",
                    current_value=f"start: {task.get('start_date')}, due: {task.get('due_date')}",
                    expected_value="ISO_date_format"
                ))
        
        return violations
    
    def _validate_dependencies(self, dependencies: List[Dict[str, Any]], tasks: List[Dict[str, Any]]) -> List[GuardrailViolation]:
        """Validate task dependencies"""
        violations = []
        
        if not isinstance(dependencies, list):
            violations.append(GuardrailViolation(
                rule_name="dependencies_structure",
                severity="error",
                message="Dependencies must be an array",
                field_path="dependencies",
                current_value=type(dependencies).__name__,
                expected_value="list"
            ))
            return violations
        
        # Get valid task IDs
        valid_task_ids = [task.get("id") for task in tasks if task.get("id") is not None]
        
        for i, dep in enumerate(dependencies):
            if not isinstance(dep, dict):
                violations.append(GuardrailViolation(
                    rule_name="dependency_structure",
                    severity="error",
                    message="Each dependency must be an object",
                    field_path=f"dependencies[{i}]",
                    current_value=type(dep).__name__,
                    expected_value="dict"
                ))
                continue
            
            # Check required fields
            for field in ["from", "to"]:
                if field not in dep:
                    violations.append(GuardrailViolation(
                        rule_name="dependency_field",
                        severity="error",
                        message=f"Dependency {field} field is required",
                        field_path=f"dependencies[{i}].{field}",
                        current_value=None,
                        expected_value="task_id"
                    ))
                elif dep[field] not in valid_task_ids:
                    violations.append(GuardrailViolation(
                        rule_name="dependency_reference",
                        severity="error",
                        message=f"Dependency references non-existent task ID: {dep[field]}",
                        field_path=f"dependencies[{i}].{field}",
                        current_value=dep[field],
                        expected_value="valid_task_id"
                    ))
            
            # Check for self-dependencies
            if dep.get("from") == dep.get("to"):
                violations.append(GuardrailViolation(
                    rule_name="self_dependency",
                    severity="error",
                    message="Task cannot depend on itself",
                    field_path=f"dependencies[{i}]",
                    current_value=f"from: {dep.get('from')}, to: {dep.get('to')}",
                    expected_value="different_task_ids"
                ))
        
        return violations
    
    def _validate_project_constraints(self, wbs_data: Dict[str, Any], constraints: Dict[str, Any]) -> List[GuardrailViolation]:
        """Validate WBS against project constraints"""
        violations = []
        
        # Project duration constraint
        if "start_date" in constraints and "end_date" in constraints:
            try:
                project_start = datetime.fromisoformat(constraints["start_date"])
                project_end = datetime.fromisoformat(constraints["end_date"])
                
                if project_end <= project_start:
                    violations.append(GuardrailViolation(
                        rule_name="project_duration",
                        severity="error",
                        message="Project end date must be after start date",
                        field_path="project_constraints.dates",
                        current_value=f"start: {project_start}, end: {project_end}",
                        expected_value="end_date > start_date"
                    ))
                
                project_duration = project_end - project_start
                if project_duration > self.max_project_duration:
                    violations.append(GuardrailViolation(
                        rule_name="project_duration_limit",
                        severity="warning",
                        message=f"Project duration exceeds maximum allowed ({self.max_project_duration.days} days)",
                        field_path="project_constraints.duration",
                        current_value=project_duration.days,
                        expected_value=f"<={self.max_project_duration.days}",
                        suggestion="Consider breaking project into phases or reducing scope"
                    ))
                    
            except (ValueError, TypeError):
                violations.append(GuardrailViolation(
                    rule_name="project_date_format",
                    severity="error",
                    message="Invalid project date format. Use ISO format (YYYY-MM-DD)",
                    field_path="project_constraints.dates",
                    current_value=f"start: {constraints.get('start_date')}, end: {constraints.get('end_date')}",
                    expected_value="ISO_date_format"
                ))
        
        # Budget constraints
        if "budget_limit" in constraints:
            budget_limit = constraints["budget_limit"]
            if isinstance(budget_limit, (int, float)) and budget_limit > 0:
                # Calculate total estimated cost from WBS
                total_estimated = sum(
                    task.get("estimated_hours", 0) * constraints.get("hourly_rate", 100)
                    for task in wbs_data.get("tasks", [])
                )
                
                if total_estimated > budget_limit:
                    violations.append(GuardrailViolation(
                        rule_name="budget_limit",
                        severity="warning",
                        message=f"Total estimated cost (${total_estimated:,.2f}) exceeds budget limit (${budget_limit:,.2f})",
                        field_path="project_constraints.budget",
                        current_value=total_estimated,
                        expected_value=f"<={budget_limit}",
                        suggestion="Review task estimates or request budget increase"
                    ))
        
        return violations
    
    def _generate_repair_suggestions(self, violations: List[GuardrailViolation]) -> List[str]:
        """Generate suggestions for repairing validation violations"""
        suggestions = []
        
        for violation in violations:
            if violation.suggestion:
                suggestions.append(f"{violation.field_path}: {violation.suggestion}")
            elif violation.severity == "error":
                suggestions.append(f"Fix {violation.field_path}: {violation.message}")
            elif violation.severity == "warning":
                suggestions.append(f"Review {violation.field_path}: {violation.message}")
        
        return suggestions
    
    def _calculate_confidence_score(self, violations: List[GuardrailViolation], wbs_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on validation results"""
        if not violations:
            return 1.0
        
        # Count violations by severity
        error_count = len([v for v in violations if v.severity == "error"])
        warning_count = len([v for v in violations if v.severity == "warning"])
        info_count = len([v for v in violations if v.severity == "info"])
        
        # Calculate base score
        base_score = 1.0
        
        # Penalize errors heavily
        base_score -= error_count * 0.3
        
        # Penalize warnings moderately
        base_score -= warning_count * 0.1
        
        # Penalize info items slightly
        base_score -= info_count * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, base_score))
    
    async def repair_wbs_output(self, wbs_data: Dict[str, Any], violations: List[GuardrailViolation]) -> Dict[str, Any]:
        """Attempt to repair WBS output based on validation violations"""
        repaired_data = wbs_data.copy()
        
        for violation in violations:
            if violation.severity == "error":
                # Try to fix critical errors
                if "required_field" in violation.rule_name:
                    field_path = violation.field_path
                    if "name" in field_path:
                        self._set_nested_value(repaired_data, field_path, "Unnamed Task")
                    elif "description" in field_path:
                        self._set_nested_value(repaired_data, field_path, "No description provided")
                
                elif "date_logic" in violation.rule_name:
                    # Fix date logic issues
                    field_path = violation.field_path
                    if "start_date" in field_path and "due_date" in field_path:
                        # Set due date to start date + 1 day
                        start_date = repaired_data.get("start_date")
                        if start_date:
                            try:
                                start_dt = datetime.fromisoformat(start_date)
                                due_dt = start_dt + timedelta(days=1)
                                self._set_nested_value(repaired_data, field_path.replace("dates", "due_date"), due_dt.strftime("%Y-%m-%d"))
                            except (ValueError, TypeError):
                                pass
        
        return repaired_data
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set a nested value in a dictionary using dot notation"""
        parts = field_path.split(".")
        current = data
        
        for part in parts[:-1]:
            if part.isdigit():
                idx = int(part)
                if isinstance(current, list) and 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        last_part = parts[-1]
        if last_part.isdigit():
            idx = int(last_part)
            if isinstance(current, list) and 0 <= idx < len(current):
                current[idx] = value
        else:
            current[last_part] = value
    
    async def validate_allocation_output(self, allocation_data: Dict[str, Any], resource_constraints: Dict[str, Any]) -> ValidationResult:
        """Validate resource allocation output from AI"""
        violations = []
        repair_suggestions = []
        
        # Basic structure validation
        if not isinstance(allocation_data, dict):
            violations.append(GuardrailViolation(
                rule_name="structure",
                severity="error",
                message="Allocation data must be a dictionary",
                field_path="root",
                current_value=type(allocation_data).__name__,
                expected_value="dict"
            ))
            return ValidationResult(False, violations, repair_suggestions, 0.0)
        
        # Validate allocations array
        allocations = allocation_data.get("allocations", [])
        if not isinstance(allocations, list):
            violations.append(GuardrailViolation(
                rule_name="allocations_structure",
                severity="error",
                message="Allocations must be an array",
                field_path="allocations",
                current_value=type(allocations).__name__,
                expected_value="list"
            ))
        else:
            # Validate individual allocations
            for i, allocation in enumerate(allocations):
                alloc_violations = self._validate_allocation(allocation, f"allocations[{i}]")
                violations.extend(alloc_violations)
        
        # Validate workload constraints
        workload_violations = self._validate_workload_constraints(allocations, resource_constraints)
        violations.extend(workload_violations)
        
        # Generate repair suggestions
        repair_suggestions = self._generate_repair_suggestions(violations)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(violations, allocation_data)
        
        is_valid = not any(v.severity == "error" for v in violations)
        
        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            repair_suggestions=repair_suggestions,
            confidence_score=confidence_score
        )
    
    def _validate_allocation(self, allocation: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual resource allocation"""
        violations = []
        
        # Required fields
        required_fields = ["resource_id", "task_id", "hours_per_day"]
        for field in required_fields:
            if field not in allocation:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Allocation {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=None,
                    expected_value="value"
                ))
        
        # Hours validation
        if "hours_per_day" in allocation:
            hours = allocation["hours_per_day"]
            if not isinstance(hours, (int, float)) or hours <= 0:
                violations.append(GuardrailViolation(
                    rule_name="hours_validation",
                    severity="error",
                    message="Hours per day must be a positive number",
                    field_path=f"{field_path}.hours_per_day",
                    current_value=hours,
                    expected_value="positive_number"
                ))
            elif hours > 24:
                violations.append(GuardrailViolation(
                    rule_name="hours_limit",
                    severity="error",
                    message="Hours per day cannot exceed 24",
                    field_path=f"{field_path}.hours_per_day",
                    current_value=hours,
                    expected_value="<=24"
                ))
        
        return violations
    
    def _validate_workload_constraints(self, allocations: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[GuardrailViolation]:
        """Validate workload constraints"""
        violations = []
        
        # Group allocations by resource
        resource_workloads = {}
        for allocation in allocations:
            resource_id = allocation.get("resource_id")
            hours = allocation.get("hours_per_day", 0)
            
            if resource_id not in resource_workloads:
                resource_workloads[resource_id] = 0
            resource_workloads[resource_id] += hours
        
        # Check against max workload
        max_workload = constraints.get("max_hours_per_day", 8)
        for resource_id, total_hours in resource_workloads.items():
            if total_hours > max_workload:
                violations.append(GuardrailViolation(
                    rule_name="workload_limit",
                    severity="warning",
                    message=f"Resource {resource_id} workload ({total_hours}h/day) exceeds limit ({max_workload}h/day)",
                    field_path="resource_workloads",
                    current_value=total_hours,
                    expected_value=f"<={max_workload}",
                    suggestion="Reduce allocation or add more resources"
                ))
        
        return violations
