import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.project import Project, Task
from app.models.ai_draft import AIDraft, DraftType, DraftStatus
from app.models.status_update_policy import StatusUpdatePolicy, StatusUpdate
from app.models.resource import Resource, Skill
from app.services.ai_guardrails import AIGuardrails, ValidationResult
from app.services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class AIFirstService:
    """AI-First service for proactive project planning and management"""
    
    def __init__(self):
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=30.0
        )
        self.guardrails = AIGuardrails()
        self.rag_engine = RAGEngine()
        
        # Prompt templates for different AI operations
        self.prompts = {
            "wbs_generation": self._get_wbs_prompt(),
            "resource_allocation": self._get_allocation_prompt(),
            "status_update": self._get_status_update_prompt(),
            "risk_assessment": self._get_risk_assessment_prompt()
        }
    
    async def auto_plan_project(
        self,
        project_id: int,
        document_content: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Automatically plan a project using AI"""
        try:
            # Get project information
            if db:
                result = await db.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = result.scalar_one_or_none()
                if not project:
                    raise ValueError(f"Project {project_id} not found")
            else:
                project = None
            
            # Prepare context for AI
            context = {
                "project": {
                    "name": project.name if project else "New Project",
                    "description": project.description if project else "",
                    "start_date": project.start_date.isoformat() if project and project.start_date else None,
                    "end_date": project.end_date.isoformat() if project and project.end_date else None,
                    "client_name": project.client_name if project else None
                } if project else {},
                "document_content": document_content,
                "constraints": constraints or {},
                "ai_model": settings.AI_MODEL_NAME
            }
            
            # Generate WBS using AI
            wbs_result = await self._generate_wbs_with_ai(context)
            
            # Validate output using guardrails
            validation_result = await self.guardrails.validate_wbs_output(
                wbs_result["wbs"], 
                context["constraints"]
            )
            
            # If validation fails, attempt repair
            if not validation_result.is_valid:
                logger.warning(f"WBS validation failed for project {project_id}: {validation_result.violations}")
                
                if validation_result.repair_suggestions:
                    # Attempt to repair the output
                    repaired_wbs = await self.guardrails.repair_wbs_output(
                        wbs_result["wbs"], 
                        validation_result.violations
                    )
                    
                    # Re-validate repaired output
                    repair_validation = await self.guardrails.validate_wbs_output(
                        repaired_wbs, 
                        context["constraints"]
                    )
                    
                    if repair_validation.is_valid:
                        wbs_result["wbs"] = repaired_wbs
                        wbs_result["was_repaired"] = True
                        validation_result = repair_validation
                        logger.info(f"WBS repaired successfully for project {project_id}")
                    else:
                        logger.error(f"WBS repair failed for project {project_id}")
            
            # Create AI draft
            if db:
                ai_draft = await self._create_ai_draft(
                    project_id=project_id,
                    draft_type=DraftType.WBS,
                    payload=wbs_result["wbs"],
                    rationale={
                        "confidence": validation_result.confidence_score,
                        "validation_violations": [
                            {
                                "rule": v.rule_name,
                                "severity": v.severity,
                                "message": v.message,
                                "field_path": v.field_path
                            } for v in validation_result.violations
                        ],
                        "repair_suggestions": validation_result.repair_suggestions,
                        "was_repaired": wbs_result.get("was_repaired", False),
                        "ai_model": settings.AI_MODEL_NAME,
                        "prompt_tokens": wbs_result.get("prompt_tokens", 0),
                        "completion_tokens": wbs_result.get("completion_tokens", 0)
                    },
                    db=db
                )
                
                # Auto-publish if project policy allows
                if project and project.ai_autopublish and validation_result.is_valid:
                    await self._publish_wbs_from_draft(ai_draft.id, db)
                    wbs_result["auto_published"] = True
                    wbs_result["draft_id"] = ai_draft.id
                else:
                    wbs_result["draft_id"] = ai_draft.id
                    wbs_result["needs_review"] = True
            
            return {
                "success": True,
                "wbs": wbs_result["wbs"],
                "draft_id": wbs_result.get("draft_id"),
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "confidence": validation_result.confidence_score,
                    "violations": [
                        {
                            "rule": v.rule_name,
                            "severity": v.severity,
                            "message": v.message,
                            "field_path": v.field_path,
                            "suggestion": v.suggestion
                        } for v in validation_result.violations
                    ],
                    "repair_suggestions": validation_result.repair_suggestions
                },
                "auto_published": wbs_result.get("auto_published", False),
                "needs_review": wbs_result.get("needs_review", False)
            }
            
        except Exception as e:
            logger.error(f"Error in auto_plan_project: {e}")
            return {
                "success": False,
                "error": str(e),
                "wbs": None,
                "draft_id": None
            }
    
    async def auto_allocate_resources(
        self,
        project_id: int,
        task_ids: List[int],
        resource_constraints: Optional[Dict[str, Any]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Automatically allocate resources to tasks using AI"""
        try:
            # Get project and task information
            if db:
                result = await db.execute(
                    select(Project).where(Project.id == project_id)
                )
                project = result.scalar_one_or_none()
                if not project:
                    raise ValueError(f"Project {project_id} not found")
                
                # Get tasks
                result = await db.execute(
                    select(Task).where(Task.id.in_(task_ids))
                )
                tasks = result.scalars().all()
                
                # Get available resources
                result = await db.execute(
                    select(Resource).options(selectinload(Resource.skills))
                )
                resources = result.scalars().all()
            else:
                project = None
                tasks = []
                resources = []
            
            # Prepare context for AI
            context = {
                "project": {
                    "name": project.name if project else "Unknown Project",
                    "start_date": project.start_date.isoformat() if project and project.start_date else None,
                    "end_date": project.end_date.isoformat() if project and project.end_date else None
                } if project else {},
                "tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "description": task.description,
                        "estimated_hours": task.estimated_hours,
                        "start_date": task.start_date.isoformat() if task.start_date else None,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "priority": task.priority.value if task.priority else "medium"
                    } for task in tasks
                ],
                "resources": [
                    {
                        "id": resource.id,
                        "name": resource.name,
                        "skills": [skill.name for skill in resource.skills] if resource.skills else [],
                        "availability": resource.availability if hasattr(resource, 'availability') else 8.0,
                        "performance_score": resource.performance_score if hasattr(resource, 'performance_score') else 0.8
                    } for resource in resources
                ],
                "constraints": resource_constraints or {},
                "ai_model": settings.AI_MODEL_NAME
            }
            
            # Generate allocation using AI
            allocation_result = await self._generate_allocation_with_ai(context)
            
            # Validate output using guardrails
            validation_result = await self.guardrails.validate_allocation_output(
                allocation_result["allocation"], 
                context["constraints"]
            )
            
            # Create AI draft for allocation
            if db:
                ai_draft = await self._create_ai_draft(
                    project_id=project_id,
                    draft_type=DraftType.ALLOCATION,
                    payload=allocation_result["allocation"],
                    rationale={
                        "confidence": validation_result.confidence_score,
                        "validation_violations": [
                            {
                                "rule": v.rule_name,
                                "severity": v.severity,
                                "message": v.message,
                                "field_path": v.field_path
                            } for v in validation_result.violations
                        ],
                        "ai_model": settings.AI_MODEL_NAME,
                        "prompt_tokens": allocation_result.get("prompt_tokens", 0),
                        "completion_tokens": allocation_result.get("completion_tokens", 0)
                    },
                    db=db
                )
                
                allocation_result["draft_id"] = ai_draft.id
            
            return {
                "success": True,
                "allocation": allocation_result["allocation"],
                "draft_id": allocation_result.get("draft_id"),
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "confidence": validation_result.confidence_score,
                    "violations": [
                        {
                            "rule": v.rule_name,
                            "severity": v.severity,
                            "message": v.message,
                            "field_path": v.field_path,
                            "suggestion": v.suggestion
                        } for v in validation_result.violations
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error in auto_allocate_resources: {e}")
            return {
                "success": False,
                "error": str(e),
                "allocation": None,
                "draft_id": None
            }
    
    async def generate_status_update_draft(
        self,
        user_id: int,
        project_id: int,
        policy_id: int,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Generate AI draft for status update"""
        try:
            # Get status update policy and user context
            if db:
                result = await db.execute(
                    select(StatusUpdatePolicy).where(StatusUpdatePolicy.id == policy_id)
                )
                policy = result.scalar_one_or_none()
                if not policy:
                    raise ValueError(f"Status update policy {policy_id} not found")
                
                # Get user's recent work
                result = await db.execute(
                    select(Task).where(
                        Task.assigned_to_id == user_id,
                        Task.project_id == project_id
                    )
                )
                user_tasks = result.scalars().all()
            else:
                policy = None
                user_tasks = []
            
            # Prepare context for AI
            context = {
                "policy_requirements": {
                    "require_progress": policy.require_progress if policy else True,
                    "require_blockers": policy.require_blockers if policy else True,
                    "require_next_steps": policy.require_next_steps if policy else True,
                    "require_effort": policy.require_effort if policy else False,
                    "require_confidence": policy.require_confidence if policy else False
                } if policy else {},
                "user_tasks": [
                    {
                        "id": task.id,
                        "name": task.name,
                        "status": task.status.value if task.status else "todo",
                        "progress": self._calculate_task_progress(task),
                        "estimated_hours": task.estimated_hours,
                        "actual_hours": task.actual_hours
                    } for task in user_tasks
                ],
                "ai_model": settings.AI_MODEL_NAME
            }
            
            # Generate status update draft using AI
            draft_result = await self._generate_status_update_with_ai(context)
            
            # Create status update record
            if db:
                status_update = StatusUpdate(
                    policy_id=policy_id,
                    user_id=user_id,
                    project_id=project_id,
                    ai_draft=draft_result["draft"],
                    is_ai_generated=True,
                    ai_model_used=settings.AI_MODEL_NAME,
                    ai_confidence=draft_result.get("confidence", 0.8),
                    status="draft"
                )
                
                db.add(status_update)
                await db.commit()
                await db.refresh(status_update)
                
                draft_result["status_update_id"] = status_update.id
            
            return {
                "success": True,
                "draft": draft_result["draft"],
                "status_update_id": draft_result.get("status_update_id"),
                "confidence": draft_result.get("confidence", 0.8)
            }
            
        except Exception as e:
            logger.error(f"Error in generate_status_update_draft: {e}")
            return {
                "success": False,
                "error": str(e),
                "draft": None,
                "status_update_id": None
            }
    
    async def _generate_wbs_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate WBS using AI"""
        try:
            prompt = self.prompts["wbs_generation"].format(
                project_name=context["project"].get("name", "Project"),
                project_description=context["project"].get("description", ""),
                start_date=context["project"].get("start_date", "TBD"),
                end_date=context["project"].get("end_date", "TBD"),
                client_name=context["project"].get("client_name", "Client"),
                document_content=context.get("document_content", ""),
                constraints=json.dumps(context.get("constraints", {}), indent=2)
            )
            
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": settings.AI_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for more consistent output
                        "num_predict": 2048
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "{}")
                
                try:
                    wbs_data = json.loads(response_text)
                    return {
                        "wbs": wbs_data,
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0)
                    }
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse WBS JSON: {response_text}")
                    # Return a basic WBS structure as fallback
                    return {
                        "wbs": {
                            "tasks": [
                                {
                                    "id": 1,
                                    "name": "Project Planning",
                                    "description": "Initial project planning and setup",
                                    "estimated_hours": 40,
                                    "dependencies": []
                                }
                            ],
                            "dependencies": []
                        },
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0)
                    }
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating WBS with AI: {e}")
            raise
    
    async def _generate_allocation_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate resource allocation using AI"""
        try:
            prompt = self.prompts["resource_allocation"].format(
                project_name=context["project"].get("name", "Project"),
                tasks_json=json.dumps(context["tasks"], indent=2),
                resources_json=json.dumps(context["resources"], indent=2),
                constraints_json=json.dumps(context.get("constraints", {}), indent=2)
            )
            
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": settings.AI_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "num_predict": 1024
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "{}")
                
                try:
                    allocation_data = json.loads(response_text)
                    return {
                        "allocation": allocation_data,
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0)
                    }
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse allocation JSON: {response_text}")
                    raise Exception("Failed to generate valid allocation data")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating allocation with AI: {e}")
            raise
    
    async def _generate_status_update_with_ai(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate status update draft using AI"""
        try:
            prompt = self.prompts["status_update"].format(
                policy_requirements=json.dumps(context["policy_requirements"], indent=2),
                user_tasks_json=json.dumps(context["user_tasks"], indent=2)
            )
            
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": settings.AI_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 512
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                return {
                    "draft": response_text,
                    "confidence": 0.8,
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0)
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating status update with AI: {e}")
            raise
    
    async def _create_ai_draft(
        self,
        project_id: int,
        draft_type: DraftType,
        payload: Dict[str, Any],
        rationale: Dict[str, Any],
        db: AsyncSession
    ) -> AIDraft:
        """Create an AI draft record"""
        ai_draft = AIDraft(
            project_id=project_id,
            draft_type=draft_type,
            payload=payload,
            rationale=rationale,
            model_name=settings.AI_MODEL_NAME,
            prompt_tokens=rationale.get("prompt_tokens", 0),
            completion_tokens=rationale.get("completion_tokens", 0),
            total_tokens=rationale.get("prompt_tokens", 0) + rationale.get("completion_tokens", 0)
        )
        
        db.add(ai_draft)
        await db.commit()
        await db.refresh(ai_draft)
        
        return ai_draft
    
    async def _publish_wbs_from_draft(self, draft_id: int, db: AsyncSession) -> bool:
        """Publish WBS from AI draft to actual tasks"""
        try:
            # Get the AI draft
            result = await db.execute(
                select(AIDraft).where(AIDraft.id == draft_id)
            )
            draft = result.scalar_one_or_none()
            
            if not draft or draft.draft_type != DraftType.WBS:
                raise ValueError(f"Invalid WBS draft: {draft_id}")
            
            wbs_data = draft.payload
            
            # Create tasks from WBS
            for task_data in wbs_data.get("tasks", []):
                task = Task(
                    name=task_data.get("name", "Unnamed Task"),
                    description=task_data.get("description", ""),
                    project_id=draft.project_id,
                    estimated_hours=task_data.get("estimated_hours"),
                    start_date=datetime.fromisoformat(task_data["start_date"]) if task_data.get("start_date") else None,
                    due_date=datetime.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None,
                    confidence_score=draft.confidence_score,
                    reasoning=draft.rationale,
                    source="ai"
                )
                
                db.add(task)
            
            # Update draft status
            draft.status = DraftStatus.PUBLISHED
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error publishing WBS from draft: {e}")
            await db.rollback()
            return False
    
    def _calculate_task_progress(self, task: Task) -> float:
        """Calculate task progress percentage"""
        if task.status == TaskStatus.DONE:
            return 100.0
        elif task.status == TaskStatus.IN_PROGRESS:
            return 50.0
        elif task.status == TaskStatus.REVIEW:
            return 75.0
        elif task.status == TaskStatus.BLOCKED:
            return 25.0
        else:
            return 0.0
    
    def _get_wbs_prompt(self) -> str:
        """Get prompt template for WBS generation"""
        return """
        You are an expert project manager. Generate a Work Breakdown Structure (WBS) for the following project.
        
        Project: {project_name}
        Description: {project_description}
        Start Date: {start_date}
        End Date: {end_date}
        Client: {client_name}
        
        Document Content (if available):
        {document_content}
        
        Project Constraints:
        {constraints}
        
        Generate a comprehensive WBS with:
        1. Tasks with clear names, descriptions, and estimated hours
        2. Logical dependencies between tasks
        3. Realistic start and due dates within the project timeline
        4. Resource requirements and skill needs
        
        Return ONLY valid JSON in this exact format:
        {{
            "tasks": [
                {{
                    "id": 1,
                    "name": "Task Name",
                    "description": "Task description",
                    "estimated_hours": 40,
                    "start_date": "YYYY-MM-DD",
                    "due_date": "YYYY-MM-DD",
                    "dependencies": [],
                    "required_skills": ["skill1", "skill2"],
                    "priority": "high|medium|low"
                }}
            ],
            "dependencies": [
                {{
                    "from": 1,
                    "to": 2,
                    "type": "finish_to_start"
                }}
            ],
            "milestones": [
                {{
                    "name": "Milestone Name",
                    "due_date": "YYYY-MM-DD",
                    "tasks": [1, 2, 3]
                }}
            ]
        }}
        
        Ensure all dates are in YYYY-MM-DD format and dependencies reference valid task IDs.
        """
    
    def _get_allocation_prompt(self) -> str:
        """Get prompt template for resource allocation"""
        return """
        You are an expert resource manager. Allocate resources to tasks based on skills, availability, and constraints.
        
        Project: {project_name}
        
        Tasks:
        {tasks_json}
        
        Available Resources:
        {resources_json}
        
        Constraints:
        {constraints_json}
        
        Generate optimal resource allocation considering:
        1. Skill matching between tasks and resources
        2. Resource availability and workload limits
        3. Task priorities and deadlines
        4. Resource performance scores
        
        Return ONLY valid JSON in this exact format:
        {{
            "allocations": [
                {{
                    "resource_id": 1,
                    "task_id": 1,
                    "hours_per_day": 8.0,
                    "start_date": "YYYY-MM-DD",
                    "end_date": "YYYY-MM-DD",
                    "reasoning": "Why this resource was chosen"
                }}
            ],
            "resource_gaps": [
                {{
                    "task_id": 1,
                    "required_skills": ["skill1", "skill2"],
                    "gap_type": "missing_skill|insufficient_capacity"
                }}
            ]
        }}
        
        Ensure all allocations respect resource availability and workload limits.
        """
    
    def _get_status_update_prompt(self) -> str:
        """Get prompt template for status update generation"""
        return """
        You are an expert project team member. Generate a professional status update based on the user's recent work.
        
        Policy Requirements:
        {policy_requirements}
        
        User's Recent Work:
        {user_tasks_json}
        
        Generate a status update that includes:
        1. Progress summary of completed work
        2. Current blockers or challenges
        3. Next steps and planned work
        4. Effort tracking (if required)
        5. Confidence in estimates (if required)
        
        Write in a professional, concise tone suitable for project stakeholders.
        Focus on achievements, challenges, and next steps.
        """
    
    def _get_risk_assessment_prompt(self) -> str:
        """Get prompt template for risk assessment"""
        return """
        You are an expert risk manager. Assess project risks based on the provided information.
        
        Generate a comprehensive risk assessment including:
        1. Risk identification and categorization
        2. Probability and impact assessment
        3. Mitigation strategies
        4. Contingency plans
        
        Return the assessment in a structured format suitable for project stakeholders.
        """
    
    async def close(self):
        """Close the service and cleanup resources"""
        await self.ollama_client.aclose()
