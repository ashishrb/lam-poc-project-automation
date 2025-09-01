#!/usr/bin/env python3
"""
Document AI Extraction Service
Parse HLD/BRD/SRS to Epics → Features → Stories/Tasks + dependencies, estimates, risks.
"""

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
from app.models.project import Project, Task, TaskStatus, TaskPriority
from app.models.document import Document, DocumentChunk
from app.services.rag_engine import RAGEngine
from app.services.ai_guardrails import AIGuardrails, ValidationResult

logger = logging.getLogger(__name__)


class PlanBuilderService:
    """AI-powered document to plan conversion service"""
    
    def __init__(self):
        self.ollama_client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=60.0
        )
        self.rag_engine = RAGEngine()
        self.guardrails = AIGuardrails()
        
        # Document type detection patterns
        self.doc_patterns = {
            "hld": ["high level design", "hld", "architecture", "system design", "technical design"],
            "brd": ["business requirements document", "business case", "business objectives"],
            "srs": ["software requirements specification", "srs", "functional requirements", "specification"]
        }
        
        # Prompt templates for different document types
        self.prompts = {
            "hld_extraction": self._get_hld_extraction_prompt(),
            "brd_extraction": self._get_brd_extraction_prompt(),
            "srs_extraction": self._get_srs_extraction_prompt(),
            "dependency_analysis": self._get_dependency_analysis_prompt(),
            "risk_assessment": self._get_risk_assessment_prompt(),
            "effort_estimation": self._get_effort_estimation_prompt()
        }
    
    async def extract_plan_from_document(
        self,
        document_content: str,
        document_metadata: Dict[str, Any],
        project_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Extract project plan from document content
        Returns: WBS with Epics → Features → Stories/Tasks + dependencies, estimates, risks
        """
        try:
            # Detect document type
            doc_type = self._detect_document_type(document_content, document_metadata)
            logger.info(f"Detected document type: {doc_type}")
            
            # Extract structured plan based on document type
            extraction_result = await self._extract_structured_plan(
                document_content, 
                doc_type, 
                document_metadata
            )
            
            # Analyze dependencies
            dependency_result = await self._analyze_dependencies(
                extraction_result["epics"],
                extraction_result["features"],
                extraction_result["tasks"]
            )
            
            # Assess risks
            risk_result = await self._assess_risks(
                extraction_result["epics"],
                extraction_result["features"],
                extraction_result["tasks"],
                dependency_result["dependencies"]
            )
            
            # Estimate efforts
            effort_result = await self._estimate_efforts(
                extraction_result["tasks"],
                dependency_result["dependencies"]
            )
            
            # Validate extracted plan
            validation_result = await self.guardrails.validate_extracted_plan(
                extraction_result,
                dependency_result,
                risk_result,
                effort_result
            )
            
            # If validation fails, attempt repair
            if not validation_result.is_valid:
                logger.warning(f"Plan validation failed: {validation_result.violations}")
                
                if validation_result.repair_suggestions:
                    repaired_plan = await self.guardrails.repair_extracted_plan(
                        extraction_result,
                        validation_result.violations
                    )
                    
                    # Re-validate repaired plan
                    repair_validation = await self.guardrails.validate_extracted_plan(
                        repaired_plan["extraction"],
                        repaired_plan["dependencies"],
                        repaired_plan["risks"],
                        repaired_plan["efforts"]
                    )
                    
                    if repair_validation.is_valid:
                        extraction_result = repaired_plan["extraction"]
                        dependency_result = repaired_plan["dependencies"]
                        risk_result = repaired_plan["risks"]
                        effort_result = repaired_plan["efforts"]
                        logger.info("Plan repaired successfully")
                    else:
                        logger.error("Plan repair failed")
            
            # Persist to database if project_id provided
            if project_id and db:
                await self._persist_extracted_plan(
                    project_id,
                    extraction_result,
                    dependency_result,
                    risk_result,
                    effort_result,
                    document_metadata,
                    db
                )
            
            return {
                "success": True,
                "document_type": doc_type,
                "extraction": extraction_result,
                "dependencies": dependency_result,
                "risks": risk_result,
                "efforts": effort_result,
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "violations": validation_result.violations,
                    "warnings": getattr(validation_result, 'warnings', [])
                },
                "metadata": {
                    "extraction_date": datetime.now().isoformat(),
                    "document_source": document_metadata.get("source", "unknown"),
                    "ai_model_used": settings.AI_MODEL_NAME
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting plan from document: {e}")
            return {
                "success": False,
                "error": str(e),
                "document_type": "unknown"
            }
    
    def _detect_document_type(self, content: str, metadata: Dict[str, Any]) -> str:
        """Detect document type based on content and metadata"""
        content_lower = content.lower()
        
        # Check filename patterns first (higher priority)
        filename = metadata.get("file_name", "").lower()
        for doc_type, patterns in self.doc_patterns.items():
            if any(pattern in filename for pattern in patterns):
                return doc_type
        
        # Check content patterns with priority order
        # BRD patterns (check first to avoid conflicts with SRS)
        brd_patterns = self.doc_patterns["brd"]
        for pattern in brd_patterns:
            if pattern in content_lower:
                return "brd"
        
        # SRS patterns (check after BRD to avoid conflicts)
        srs_patterns = self.doc_patterns["srs"]
        for pattern in srs_patterns:
            if pattern in content_lower:
                return "srs"
        
        # HLD patterns (most generic, check last)
        hld_patterns = self.doc_patterns["hld"]
        for pattern in hld_patterns:
            if pattern in content_lower:
                return "hld"
        
        # Default to SRS if no clear pattern
        return "srs"
    
    async def _extract_structured_plan(
        self,
        content: str,
        doc_type: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract structured plan using AI based on document type"""
        try:
            # Get appropriate prompt for document type
            prompt_template = self.prompts.get(f"{doc_type}_extraction")
            if not prompt_template:
                prompt_template = self.prompts["srs_extraction"]  # Default fallback
            
            # Prepare prompt with document content
            prompt = prompt_template.format(
                document_content=content[:8000],  # Limit content length
                document_metadata=json.dumps(metadata, indent=2),
                ai_model=settings.AI_MODEL_NAME
            )
            
            # Call AI model
            response = await self._call_ai_model(prompt)
            
            # Parse AI response
            parsed_result = self._parse_extraction_response(response)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error in structured plan extraction: {e}")
            raise
    
    async def _analyze_dependencies(
        self,
        epics: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze dependencies between epics, features, and tasks"""
        try:
            prompt = self.prompts["dependency_analysis"].format(
                epics=json.dumps(epics, indent=2),
                features=json.dumps(features, indent=2),
                tasks=json.dumps(tasks, indent=2),
                ai_model=settings.AI_MODEL_NAME
            )
            
            response = await self._call_ai_model(prompt)
            parsed_dependencies = self._parse_dependency_response(response)
            
            return {
                "dependencies": parsed_dependencies["dependencies"],
                "critical_path": parsed_dependencies.get("critical_path", []),
                "dependency_graph": parsed_dependencies.get("dependency_graph", {})
            }
            
        except Exception as e:
            logger.error(f"Error in dependency analysis: {e}")
            return {
                "dependencies": [],
                "critical_path": [],
                "dependency_graph": {}
            }
    
    async def _assess_risks(
        self,
        epics: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        tasks: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess risks based on plan components and dependencies"""
        try:
            prompt = self.prompts["risk_assessment"].format(
                epics=json.dumps(epics, indent=2),
                features=json.dumps(features, indent=2),
                tasks=json.dumps(tasks, indent=2),
                dependencies=json.dumps(dependencies, indent=2),
                ai_model=settings.AI_MODEL_NAME
            )
            
            response = await self._call_ai_model(prompt)
            parsed_risks = self._parse_risk_response(response)
            
            return {
                "risks": parsed_risks["risks"],
                "risk_summary": parsed_risks.get("risk_summary", {}),
                "mitigation_suggestions": parsed_risks.get("mitigation_suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {e}")
            return {
                "risks": [],
                "risk_summary": {},
                "mitigation_suggestions": []
            }
    
    async def _estimate_efforts(
        self,
        tasks: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Estimate efforts for tasks considering dependencies"""
        try:
            prompt = self.prompts["effort_estimation"].format(
                tasks=json.dumps(tasks, indent=2),
                dependencies=json.dumps(dependencies, indent=2),
                ai_model=settings.AI_MODEL_NAME
            )
            
            response = await self._call_ai_model(prompt)
            parsed_efforts = self._parse_effort_response(response)
            
            return {
                "task_efforts": parsed_efforts["task_efforts"],
                "total_effort": parsed_efforts.get("total_effort", 0),
                "effort_distribution": parsed_efforts.get("effort_distribution", {})
            }
            
        except Exception as e:
            logger.error(f"Error in effort estimation: {e}")
            return {
                "task_efforts": [],
                "total_effort": 0,
                "effort_distribution": {}
            }
    
    async def _call_ai_model(self, prompt: str) -> str:
        """Call AI model with prompt"""
        try:
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": settings.AI_MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_tokens": 4000
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"AI model call failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error calling AI model: {e}")
            raise
    
    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for plan extraction"""
        try:
            # Try to extract JSON from response
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # Try to find JSON object
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            
            parsed = json.loads(json_str)
            
            return {
                "epics": parsed.get("epics", []),
                "features": parsed.get("features", []),
                "tasks": parsed.get("tasks", []),
                "summary": parsed.get("summary", "")
            }
            
        except Exception as e:
            logger.error(f"Error parsing extraction response: {e}")
            # Return fallback structure
            return {
                "epics": [],
                "features": [],
                "tasks": [],
                "summary": "Failed to parse AI response"
            }
    
    def _parse_dependency_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for dependency analysis"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error parsing dependency response: {e}")
            return {"dependencies": []}
    
    def _parse_risk_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for risk assessment"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error parsing risk response: {e}")
            return {"risks": []}
    
    def _parse_effort_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for effort estimation"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                json_str = response[start:end]
            
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Error parsing effort response: {e}")
            return {"task_efforts": []}
    
    async def _persist_extracted_plan(
        self,
        project_id: int,
        extraction_result: Dict[str, Any],
        dependency_result: Dict[str, Any],
        risk_result: Dict[str, Any],
        effort_result: Dict[str, Any],
        document_metadata: Dict[str, Any],
        db: AsyncSession
    ):
        """Persist extracted plan to database"""
        try:
            # Create tasks from extracted plan
            for task_data in extraction_result.get("tasks", []):
                task = Task(
                    project_id=project_id,
                    name=task_data.get("name", "Unnamed Task"),
                    description=task_data.get("description", ""),
                    status=TaskStatus.PLANNED,
                    priority=TaskPriority.MEDIUM,
                    estimated_hours=task_data.get("estimated_hours", 0),
                    actual_hours=0,
                    start_date=None,
                    due_date=None,
                    assigned_to=None,
                    epic_id=task_data.get("epic_id"),
                    feature_id=task_data.get("feature_id"),
                    dependencies=json.dumps(task_data.get("dependencies", [])),
                    risks=json.dumps(task_data.get("risks", [])),
                    metadata=json.dumps({
                        "extracted_from_document": True,
                        "document_source": document_metadata.get("source", "unknown"),
                        "extraction_date": datetime.now().isoformat(),
                        "ai_generated": True
                    })
                )
                db.add(task)
            
            await db.commit()
            logger.info(f"Persisted extracted plan for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error persisting extracted plan: {e}")
            await db.rollback()
            raise
    
    def _get_hld_extraction_prompt(self) -> str:
        """Get prompt template for HLD extraction"""
        return """
You are an expert project manager and technical architect. Extract a structured project plan from the following High-Level Design (HLD) document.

Document Content:
{document_content}

Document Metadata:
{document_metadata}

Please extract and structure the information into the following JSON format:

{{
    "epics": [
        {{
            "id": "epic_1",
            "name": "Epic Name",
            "description": "Epic description",
            "priority": "high|medium|low",
            "business_value": "high|medium|low"
        }}
    ],
    "features": [
        {{
            "id": "feature_1",
            "epic_id": "epic_1",
            "name": "Feature Name",
            "description": "Feature description",
            "priority": "high|medium|low",
            "complexity": "high|medium|low"
        }}
    ],
    "tasks": [
        {{
            "id": "task_1",
            "feature_id": "feature_1",
            "name": "Task Name",
            "description": "Task description",
            "type": "development|testing|deployment|documentation",
            "estimated_hours": 8,
            "priority": "high|medium|low",
            "complexity": "high|medium|low"
        }}
    ],
    "summary": "Brief summary of the extracted plan"
}}

Focus on:
1. Identifying major system components as epics
2. Breaking down components into features
3. Creating specific tasks for implementation
4. Estimating effort based on complexity
5. Identifying technical dependencies

Use the {ai_model} model for analysis.
"""
    
    def _get_brd_extraction_prompt(self) -> str:
        """Get prompt template for BRD extraction"""
        return """
You are an expert business analyst and project manager. Extract a structured project plan from the following Business Requirements Document (BRD).

Document Content:
{document_content}

Document Metadata:
{document_metadata}

Please extract and structure the information into the following JSON format:

{{
    "epics": [
        {{
            "id": "epic_1",
            "name": "Epic Name",
            "description": "Epic description",
            "priority": "high|medium|low",
            "business_value": "high|medium|low"
        }}
    ],
    "features": [
        {{
            "id": "feature_1",
            "epic_id": "epic_1",
            "name": "Feature Name",
            "description": "Feature description",
            "priority": "high|medium|low",
            "complexity": "high|medium|low"
        }}
    ],
    "tasks": [
        {{
            "id": "task_1",
            "feature_id": "feature_1",
            "name": "Task Name",
            "description": "Task description",
            "type": "analysis|development|testing|deployment|documentation",
            "estimated_hours": 8,
            "priority": "high|medium|low",
            "complexity": "high|medium|low"
        }}
    ],
    "summary": "Brief summary of the extracted plan"
}}

Focus on:
1. Identifying business capabilities as epics
2. Breaking down capabilities into features
3. Creating tasks for business analysis and implementation
4. Estimating effort based on business complexity
5. Identifying business dependencies

Use the {ai_model} model for analysis.
"""
    
    def _get_srs_extraction_prompt(self) -> str:
        """Get prompt template for SRS extraction"""
        return """
You are an expert software requirements analyst and project manager. Extract a structured project plan from the following Software Requirements Specification (SRS).

Document Content:
{document_content}

Document Metadata:
{document_metadata}

Please extract and structure the information into the following JSON format:

{{
    "epics": [
        {{
            "id": "epic_1",
            "name": "Epic Name",
            "description": "Epic description",
            "priority": "high|medium|low",
            "business_value": "high|medium|low"
        }}
    ],
    "features": [
        {{
            "id": "feature_1",
            "epic_id": "epic_1",
            "name": "Feature Name",
            "description": "Feature description",
            "priority": "high|medium|low",
            "complexity": "high|medium|low"
        }}
    ],
    "tasks": [
        {{
            "id": "task_1",
            "feature_id": "feature_1",
            "name": "Task Name",
            "description": "Task description",
            "type": "development|testing|deployment|documentation",
            "estimated_hours": 8,
            "priority": "high|medium|low",
            "complexity": "high|medium|low"
        }}
    ],
    "summary": "Brief summary of the extracted plan"
}}

Focus on:
1. Identifying functional requirements as epics
2. Breaking down requirements into features
3. Creating specific development tasks
4. Estimating effort based on technical complexity
5. Identifying technical dependencies

Use the {ai_model} model for analysis.
"""
    
    def _get_dependency_analysis_prompt(self) -> str:
        """Get prompt template for dependency analysis"""
        return """
You are an expert project manager specializing in dependency analysis. Analyze the dependencies between the following project components.

Epics:
{epics}

Features:
{features}

Tasks:
{tasks}

Please analyze and return the dependencies in the following JSON format:

{{
    "dependencies": [
        {{
            "from_id": "task_1",
            "to_id": "task_2",
            "type": "finish_to_start|start_to_start|finish_to_finish|start_to_finish",
            "lag": 0,
            "description": "Dependency description"
        }}
    ],
    "critical_path": ["task_1", "task_2", "task_3"],
    "dependency_graph": {{
        "task_1": ["task_2", "task_3"],
        "task_2": ["task_4"]
    }}
}}

Focus on:
1. Identifying logical dependencies between tasks
2. Determining the critical path
3. Understanding feature dependencies
4. Identifying epic-level dependencies
5. Creating a dependency graph

Use the {ai_model} model for analysis.
"""
    
    def _get_risk_assessment_prompt(self) -> str:
        """Get prompt template for risk assessment"""
        return """
You are an expert risk analyst and project manager. Assess the risks associated with the following project plan.

Epics:
{epics}

Features:
{features}

Tasks:
{tasks}

Dependencies:
{dependencies}

Please assess and return the risks in the following JSON format:

{{
    "risks": [
        {{
            "id": "risk_1",
            "name": "Risk Name",
            "description": "Risk description",
            "probability": "high|medium|low",
            "impact": "high|medium|low",
            "severity": "high|medium|low",
            "affected_tasks": ["task_1", "task_2"],
            "mitigation_strategy": "Mitigation strategy"
        }}
    ],
    "risk_summary": {{
        "high_risks": 3,
        "medium_risks": 5,
        "low_risks": 2,
        "total_risks": 10
    }},
    "mitigation_suggestions": [
        "Suggestion 1",
        "Suggestion 2"
    ]
}}

Focus on:
1. Identifying technical risks
2. Assessing business risks
3. Evaluating dependency risks
4. Analyzing resource risks
5. Providing mitigation strategies

Use the {ai_model} model for analysis.
"""
    
    def _get_effort_estimation_prompt(self) -> str:
        """Get prompt template for effort estimation"""
        return """
You are an expert project manager specializing in effort estimation. Estimate the effort required for the following tasks considering their dependencies.

Tasks:
{tasks}

Dependencies:
{dependencies}

Please estimate and return the efforts in the following JSON format:

{{
    "task_efforts": [
        {{
            "task_id": "task_1",
            "estimated_hours": 8,
            "confidence": "high|medium|low",
            "assumptions": ["Assumption 1", "Assumption 2"],
            "complexity_factors": ["Factor 1", "Factor 2"]
        }}
    ],
    "total_effort": 120,
    "effort_distribution": {{
        "development": 60,
        "testing": 30,
        "deployment": 15,
        "documentation": 15
    }}
}}

Focus on:
1. Estimating effort based on task complexity
2. Considering dependency impacts
3. Accounting for uncertainty
4. Providing confidence levels
5. Identifying effort distribution

Use the {ai_model} model for analysis.
"""
