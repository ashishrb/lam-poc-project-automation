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
                    if "dates" in field_path:
                        # Extract task index from field path like "tasks[0].dates"
                        parts = field_path.split(".")
                        if len(parts) >= 2 and "[" in parts[0]:
                            task_part = parts[0]
                            task_idx = int(task_part[task_part.find("[")+1:task_part.find("]")])
                            if "tasks" in task_part and task_idx < len(repaired_data.get("tasks", [])):
                                task = repaired_data["tasks"][task_idx]
                                if "start_date" in task:
                                    try:
                                        start_dt = datetime.fromisoformat(task["start_date"])
                                        due_dt = start_dt + timedelta(days=1)
                                        repaired_data["tasks"][task_idx]["due_date"] = due_dt.strftime("%Y-%m-%d")
                                    except (ValueError, TypeError):
                                        pass
        
        return repaired_data
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set a nested value in a dictionary using dot notation with array support"""
        parts = field_path.split(".")
        current = data
        
        for part in parts[:-1]:
            if "[" in part and "]" in part:
                # Handle array notation like "tasks[0]"
                field_name = part[:part.find("[")]
                index = int(part[part.find("[")+1:part.find("]")])
                
                if field_name not in current:
                    current[field_name] = []
                if not isinstance(current[field_name], list):
                    current[field_name] = []
                
                # Ensure list is long enough
                while len(current[field_name]) <= index:
                    current[field_name].append({})
                
                current = current[field_name][index]
            else:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        last_part = parts[-1]
        if "[" in last_part and "]" in last_part:
            # Handle array notation in the last part
            field_name = last_part[:last_part.find("[")]
            index = int(last_part[last_part.find("[")+1:last_part.find("]")])
            
            if field_name not in current:
                current[field_name] = []
            if not isinstance(current[field_name], list):
                current[field_name] = []
            
            # Ensure list is long enough
            while len(current[field_name]) <= index:
                current[field_name].append({})
            
            current[field_name][index] = value
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

    async def validate_extracted_plan(
        self,
        extraction_result: Dict[str, Any],
        dependency_result: Dict[str, Any],
        risk_result: Dict[str, Any],
        effort_result: Dict[str, Any]
    ) -> ValidationResult:
        """Validate extracted plan from document AI extraction"""
        violations = []
        repair_suggestions = []
        
        try:
            # Validate extraction structure
            if not isinstance(extraction_result, dict):
                violations.append(GuardrailViolation(
                    rule_name="extraction_structure",
                    severity="error",
                    message="Extraction result must be a dictionary",
                    field_path="extraction",
                    current_value=type(extraction_result).__name__,
                    expected_value="dict"
                ))
                return ValidationResult(False, violations, repair_suggestions, 0.0)
            
            # Validate epics
            epics = extraction_result.get("epics", [])
            if isinstance(epics, list):
                for i, epic in enumerate(epics):
                    epic_violations = self._validate_epic(epic, f"epics[{i}]")
                    violations.extend(epic_violations)
            
            # Validate features
            features = extraction_result.get("features", [])
            if isinstance(features, list):
                for i, feature in enumerate(features):
                    feature_violations = self._validate_feature(feature, f"features[{i}]")
                    violations.extend(feature_violations)
            
            # Validate tasks
            tasks = extraction_result.get("tasks", [])
            if isinstance(tasks, list):
                for i, task in enumerate(tasks):
                    task_violations = self._validate_extracted_task(task, f"tasks[{i}]")
                    violations.extend(task_violations)
            
            # Validate dependencies
            dependencies = dependency_result.get("dependencies", [])
            if isinstance(dependencies, list):
                dep_violations = self._validate_dependencies(dependencies, tasks)
                violations.extend(dep_violations)
            
            # Validate risks
            risks = risk_result.get("risks", [])
            if isinstance(risks, list):
                for i, risk in enumerate(risks):
                    risk_violations = self._validate_risk(risk, f"risks[{i}]")
                    violations.extend(risk_violations)
            
            # Validate efforts
            task_efforts = effort_result.get("task_efforts", [])
            if isinstance(task_efforts, list):
                for i, effort in enumerate(task_efforts):
                    effort_violations = self._validate_effort(effort, f"task_efforts[{i}]")
                    violations.extend(effort_violations)
            
            # Generate repair suggestions
            repair_suggestions = self._generate_repair_suggestions(violations)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(violations, extraction_result)
            
            is_valid = not any(v.severity == "error" for v in violations)
            
            return ValidationResult(
                is_valid=is_valid,
                violations=violations,
                repair_suggestions=repair_suggestions,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error validating extracted plan: {e}")
            violations.append(GuardrailViolation(
                rule_name="validation_error",
                severity="error",
                message=f"Validation error: {str(e)}",
                field_path="root",
                current_value="error",
                expected_value="valid"
            ))
            return ValidationResult(False, violations, repair_suggestions, 0.0)
    
    async def repair_extracted_plan(
        self,
        extraction_result: Dict[str, Any],
        violations: List[GuardrailViolation]
    ) -> Dict[str, Any]:
        """Repair extracted plan based on violations"""
        try:
            repaired_extraction = extraction_result.copy()
            repaired_dependencies = {"dependencies": []}
            repaired_risks = {"risks": []}
            repaired_efforts = {"task_efforts": []}
            
            for violation in violations:
                if violation.severity == "error":
                    if "epics" in violation.field_path:
                        repaired_extraction = self._apply_epic_repair(repaired_extraction, violation)
                    elif "features" in violation.field_path:
                        repaired_extraction = self._apply_feature_repair(repaired_extraction, violation)
                    elif "tasks" in violation.field_path:
                        repaired_extraction = self._apply_task_repair(repaired_extraction, violation)
                    elif "dependencies" in violation.field_path:
                        repaired_dependencies = self._apply_dependency_repair(repaired_dependencies, violation)
                    elif "risks" in violation.field_path:
                        repaired_risks = self._apply_risk_repair(repaired_risks, violation)
                    elif "task_efforts" in violation.field_path:
                        repaired_efforts = self._apply_effort_repair(repaired_efforts, violation)
            
            return {
                "extraction": repaired_extraction,
                "dependencies": repaired_dependencies,
                "risks": repaired_risks,
                "efforts": repaired_efforts
            }
            
        except Exception as e:
            logger.error(f"Error repairing extracted plan: {e}")
            return {
                "extraction": extraction_result,
                "dependencies": {"dependencies": []},
                "risks": {"risks": []},
                "efforts": {"task_efforts": []}
            }
    
    def _validate_epic(self, epic: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual epic"""
        violations = []
        
        # Required fields
        required_fields = ["id", "name"]
        for field in required_fields:
            if field not in epic or not epic[field]:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Epic {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=epic.get(field),
                    expected_value="non_empty_value"
                ))
        
        # Priority validation
        if "priority" in epic:
            priority = epic["priority"]
            valid_priorities = ["high", "medium", "low"]
            if priority not in valid_priorities:
                violations.append(GuardrailViolation(
                    rule_name="priority_validation",
                    severity="warning",
                    message=f"Epic priority must be one of {valid_priorities}",
                    field_path=f"{field_path}.priority",
                    current_value=priority,
                    expected_value=valid_priorities
                ))
        
        return violations
    
    def _validate_feature(self, feature: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual feature"""
        violations = []
        
        # Required fields
        required_fields = ["id", "name", "epic_id"]
        for field in required_fields:
            if field not in feature or not feature[field]:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Feature {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=feature.get(field),
                    expected_value="non_empty_value"
                ))
        
        # Complexity validation
        if "complexity" in feature:
            complexity = feature["complexity"]
            valid_complexities = ["high", "medium", "low"]
            if complexity not in valid_complexities:
                violations.append(GuardrailViolation(
                    rule_name="complexity_validation",
                    severity="warning",
                    message=f"Feature complexity must be one of {valid_complexities}",
                    field_path=f"{field_path}.complexity",
                    current_value=complexity,
                    expected_value=valid_complexities
                ))
        
        return violations
    
    def _validate_extracted_task(self, task: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual extracted task"""
        violations = []
        
        # Required fields
        required_fields = ["id", "name"]
        for field in required_fields:
            if field not in task or not task[field]:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Task {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=task.get(field),
                    expected_value="non_empty_value"
                ))
        
        # Estimated hours validation
        if "estimated_hours" in task:
            hours = task["estimated_hours"]
            if not isinstance(hours, (int, float)) or hours <= 0:
                violations.append(GuardrailViolation(
                    rule_name="hours_validation",
                    severity="error",
                    message="Estimated hours must be a positive number",
                    field_path=f"{field_path}.estimated_hours",
                    current_value=hours,
                    expected_value="positive_number"
                ))
        
        # Type validation
        if "type" in task:
            task_type = task["type"]
            valid_types = ["development", "testing", "deployment", "documentation", "analysis"]
            if task_type not in valid_types:
                violations.append(GuardrailViolation(
                    rule_name="type_validation",
                    severity="warning",
                    message=f"Task type must be one of {valid_types}",
                    field_path=f"{field_path}.type",
                    current_value=task_type,
                    expected_value=valid_types
                ))
        
        return violations
    
    def _validate_risk(self, risk: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual risk"""
        violations = []
        
        # Required fields
        required_fields = ["id", "name", "description"]
        for field in required_fields:
            if field not in risk or not risk[field]:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Risk {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=risk.get(field),
                    expected_value="non_empty_value"
                ))
        
        # Severity validation
        if "severity" in risk:
            severity = risk["severity"]
            valid_severities = ["high", "medium", "low"]
            if severity not in valid_severities:
                violations.append(GuardrailViolation(
                    rule_name="severity_validation",
                    severity="warning",
                    message=f"Risk severity must be one of {valid_severities}",
                    field_path=f"{field_path}.severity",
                    current_value=severity,
                    expected_value=valid_severities
                ))
        
        return violations
    
    def _validate_effort(self, effort: Dict[str, Any], field_path: str) -> List[GuardrailViolation]:
        """Validate individual effort estimation"""
        violations = []
        
        # Required fields
        required_fields = ["task_id", "estimated_hours"]
        for field in required_fields:
            if field not in effort:
                violations.append(GuardrailViolation(
                    rule_name="required_field",
                    severity="error",
                    message=f"Effort {field} is required",
                    field_path=f"{field_path}.{field}",
                    current_value=effort.get(field),
                    expected_value="value"
                ))
        
        # Hours validation
        if "estimated_hours" in effort:
            hours = effort["estimated_hours"]
            if not isinstance(hours, (int, float)) or hours <= 0:
                violations.append(GuardrailViolation(
                    rule_name="hours_validation",
                    severity="error",
                    message="Estimated hours must be a positive number",
                    field_path=f"{field_path}.estimated_hours",
                    current_value=hours,
                    expected_value="positive_number"
                ))
        
        return violations
    
    def _apply_epic_repair(self, extraction: Dict[str, Any], violation: GuardrailViolation) -> Dict[str, Any]:
        """Apply repair to epic"""
        if "required_field" in violation.rule_name:
            field_path = violation.field_path
            if "name" in field_path:
                self._set_nested_value(extraction, field_path, "Unnamed Epic")
            elif "id" in field_path:
                self._set_nested_value(extraction, field_path, f"epic_{len(extraction.get('epics', []))}")
        return extraction
    
    def _apply_feature_repair(self, extraction: Dict[str, Any], violation: GuardrailViolation) -> Dict[str, Any]:
        """Apply repair to feature"""
        if "required_field" in violation.rule_name:
            field_path = violation.field_path
            if "name" in field_path:
                self._set_nested_value(extraction, field_path, "Unnamed Feature")
            elif "id" in field_path:
                self._set_nested_value(extraction, field_path, f"feature_{len(extraction.get('features', []))}")
        return extraction
    
    def _apply_task_repair(self, extraction: Dict[str, Any], violation: GuardrailViolation) -> Dict[str, Any]:
        """Apply repair to task"""
        if "required_field" in violation.rule_name:
            field_path = violation.field_path
            if "name" in field_path:
                self._set_nested_value(extraction, field_path, "Unnamed Task")
            elif "id" in field_path:
                self._set_nested_value(extraction, field_path, f"task_{len(extraction.get('tasks', []))}")
        elif "hours_validation" in violation.rule_name:
            field_path = violation.field_path
            self._set_nested_value(extraction, field_path, 8)  # Default 8 hours
        return extraction
    
    def _apply_dependency_repair(self, dependencies: Dict[str, Any], violation: GuardrailViolation) -> Dict[str, Any]:
        """Apply repair to dependencies"""
        # Remove invalid dependencies
        if "dependency_validation" in violation.rule_name:
            dependencies["dependencies"] = [d for d in dependencies.get("dependencies", []) 
                                          if d.get("from_id") and d.get("to_id")]
        return dependencies
    
    def _apply_risk_repair(self, risks: Dict[str, Any], violation: GuardrailViolation) -> Dict[str, Any]:
        """Apply repair to risks"""
        if "required_field" in violation.rule_name:
            field_path = violation.field_path
            if "name" in field_path:
                self._set_nested_value(risks, field_path, "Unnamed Risk")
            elif "id" in field_path:
                self._set_nested_value(risks, field_path, f"risk_{len(risks.get('risks', []))}")
        return risks
    
    def _apply_effort_repair(self, efforts: Dict[str, Any], violation: GuardrailViolation) -> Dict[str, Any]:
        """Apply repair to efforts"""
        if "hours_validation" in violation.rule_name:
            field_path = violation.field_path
            self._set_nested_value(efforts, field_path, 8)  # Default 8 hours
        return efforts
