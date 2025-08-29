import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.project import Project, Task, Risk
from app.models.resource import Resource, Evaluation
from app.models.finance import Budget, Actual, Forecast
from app.services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class AICopilotService:
    """AI Copilot service for orchestrating agent interactions and tool calling"""
    
    def __init__(self):
        self.rag_engine = RAGEngine()
        self.ollama_client = httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL)
        self.tools_registry = self._initialize_tools_registry()
    
    def _initialize_tools_registry(self) -> Dict[str, Dict[str, Any]]:
        """Initialize the registry of available tools"""
        return {
            "search_docs": {
                "name": "search_docs",
                "description": "Search documents and knowledge base",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "filters": {"type": "object", "description": "Search filters"},
                    "k": {"type": "integer", "description": "Number of results"}
                },
                "returns": {
                    "items": {"type": "array", "description": "Search results"},
                    "citations": {"type": "array", "description": "Document citations"}
                }
            },
            "generate_wbs": {
                "name": "generate_wbs",
                "description": "Generate Work Breakdown Structure",
                "parameters": {
                    "project_id": {"type": "integer", "description": "Project ID"},
                    "constraints": {"type": "object", "description": "Project constraints"}
                },
                "returns": {
                    "tasks": {"type": "array", "description": "Generated tasks"},
                    "dependencies": {"type": "array", "description": "Task dependencies"}
                }
            },
            "forecast_budget": {
                "name": "forecast_budget",
                "description": "Forecast project budget",
                "parameters": {
                    "project_id": {"type": "integer", "description": "Project ID"},
                    "horizon": {"type": "string", "description": "Forecast horizon"},
                    "drivers": {"type": "object", "description": "Forecast drivers"}
                },
                "returns": {
                    "forecast": {"type": "array", "description": "Budget forecast"},
                    "variance_explained": {"type": "string", "description": "Variance explanation"}
                }
            },
            "explain_variance": {
                "name": "explain_variance",
                "description": "Explain budget/schedule variance",
                "parameters": {
                    "project_id": {"type": "integer", "description": "Project ID"},
                    "period": {"type": "string", "description": "Analysis period"}
                },
                "returns": {
                    "narrative": {"type": "string", "description": "Variance narrative"},
                    "drivers": {"type": "array", "description": "Variance drivers"},
                    "actions": {"type": "array", "description": "Recommended actions"}
                }
            },
            "plan_staffing": {
                "name": "plan_staffing",
                "description": "Plan project staffing",
                "parameters": {
                    "project_id": {"type": "integer", "description": "Project ID"},
                    "sprint_range": {"type": "string", "description": "Sprint range"},
                    "constraints": {"type": "object", "description": "Staffing constraints"}
                },
                "returns": {
                    "allocations": {"type": "array", "description": "Resource allocations"},
                    "gaps": {"type": "array", "description": "Resource gaps"},
                    "alternatives": {"type": "array", "description": "Alternative solutions"}
                }
            },
            "evaluate_resource": {
                "name": "evaluate_resource",
                "description": "Evaluate resource performance",
                "parameters": {
                    "resource_id": {"type": "integer", "description": "Resource ID"},
                    "rubric_id": {"type": "integer", "description": "Evaluation rubric"},
                    "evidence": {"type": "object", "description": "Evaluation evidence"}
                },
                "returns": {
                    "scores": {"type": "object", "description": "Evaluation scores"},
                    "summary": {"type": "string", "description": "Evaluation summary"}
                }
            },
            "create_risk": {
                "name": "create_risk",
                "description": "Create risk assessment",
                "parameters": {
                    "project_id": {"type": "integer", "description": "Project ID"},
                    "risk_data": {"type": "object", "description": "Risk information"}
                },
                "returns": {
                    "risk_id": {"type": "integer", "description": "Created risk ID"},
                    "status": {"type": "string", "description": "Risk status"}
                }
            },
            "generate_report": {
                "name": "generate_report",
                "description": "Generate project report",
                "parameters": {
                    "report_type": {"type": "string", "description": "Report type"},
                    "scope": {"type": "object", "description": "Report scope"},
                    "period": {"type": "string", "description": "Report period"},
                    "audience": {"type": "string", "description": "Target audience"}
                },
                "returns": {
                    "sections": {"type": "array", "description": "Report sections"},
                    "charts": {"type": "array", "description": "Report charts"},
                    "citations": {"type": "array", "description": "Report citations"}
                }
            },
            "notify": {
                "name": "notify",
                "description": "Send notifications",
                "parameters": {
                    "audience": {"type": "array", "description": "Target audience"},
                    "message": {"type": "string", "description": "Notification message"},
                    "channel": {"type": "string", "description": "Communication channel"}
                },
                "returns": {
                    "delivery_id": {"type": "string", "description": "Delivery ID"},
                    "status": {"type": "string", "description": "Delivery status"}
                }
            }
        }
    
    async def process_message(
        self,
        message: str,
        context: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Process a user message and return AI response with actions"""
        try:
            # Analyze message intent
            intent = await self._analyze_intent(message, context)
            
            # Select appropriate tools
            selected_tools = await self._select_tools(intent, context)
            
            # Execute tools and gather results
            tool_results = await self._execute_tools(selected_tools, context, db)
            
            # Generate response using reasoning model
            response = await self._generate_response(message, intent, tool_results, context)
            
            return {
                "response": response["text"],
                "actions": response.get("actions", []),
                "citations": response.get("citations", []),
                "confidence": response.get("confidence", 0.8),
                "tools_used": [tool["name"] for tool in selected_tools]
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "actions": [],
                "citations": [],
                "confidence": 0.0,
                "tools_used": []
            }
    
    async def _analyze_intent(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user intent using Ollama"""
        try:
            prompt = f"""
            Analyze the user's intent from this message: "{message}"
            
            Context: {json.dumps(context, default=str)}
            
            Return a JSON response with:
            - intent: the main intent (search, create, analyze, report, etc.)
            - entities: relevant entities mentioned
            - urgency: low/medium/high
            - complexity: simple/moderate/complex
            """
            
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": settings.OLLAMA_REASONER_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                # Parse the response to extract JSON
                response_text = result.get("response", "{}")
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # Fallback to simple intent detection
                    return self._fallback_intent_analysis(message)
            else:
                return self._fallback_intent_analysis(message)
                
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            return self._fallback_intent_analysis(message)
    
    def _fallback_intent_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback intent analysis using simple keyword matching"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["search", "find", "look"]):
            intent = "search"
        elif any(word in message_lower for word in ["create", "generate", "make"]):
            intent = "create"
        elif any(word in message_lower for word in ["analyze", "explain", "why"]):
            intent = "analyze"
        elif any(word in message_lower for word in ["report", "summary", "overview"]):
            intent = "report"
        else:
            intent = "general"
        
        return {
            "intent": intent,
            "entities": [],
            "urgency": "medium",
            "complexity": "simple"
        }
    
    async def _select_tools(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Select appropriate tools based on intent"""
        selected_tools = []
        
        intent_type = intent.get("intent", "general")
        
        if intent_type == "search":
            selected_tools.append(self.tools_registry["search_docs"])
        elif intent_type == "create":
            if "wbs" in context.get("request", "").lower():
                selected_tools.append(self.tools_registry["generate_wbs"])
            elif "risk" in context.get("request", "").lower():
                selected_tools.append(self.tools_registry["create_risk"])
        elif intent_type == "analyze":
            if "variance" in context.get("request", "").lower():
                selected_tools.append(self.tools_registry["explain_variance"])
            elif "budget" in context.get("request", "").lower():
                selected_tools.append(self.tools_registry["forecast_budget"])
        elif intent_type == "report":
            selected_tools.append(self.tools_registry["generate_report"])
        
        # Always include search for context
        if not any(tool["name"] == "search_docs" for tool in selected_tools):
            selected_tools.append(self.tools_registry["search_docs"])
        
        return selected_tools
    
    async def _execute_tools(
        self,
        tools: List[Dict[str, Any]],
        context: Dict[str, Any],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """Execute selected tools and return results"""
        results = []
        
        for tool in tools:
            try:
                if tool["name"] == "search_docs":
                    result = await self.rag_engine.search(
                        query=context.get("message", ""),
                        filters=context.get("filters", {}),
                        k=5
                    )
                    results.append({
                        "tool": tool["name"],
                        "result": result,
                        "success": True
                    })
                elif tool["name"] == "generate_wbs":
                    result = await self.generate_wbs(
                        project_id=context.get("project_id"),
                        constraints=context.get("constraints", {}),
                        db=db
                    )
                    results.append({
                        "tool": tool["name"],
                        "result": result,
                        "success": True
                    })
                # Add more tool executions as needed
                
            except Exception as e:
                logger.error(f"Error executing tool {tool['name']}: {e}")
                results.append({
                    "tool": tool["name"],
                    "result": None,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _generate_response(
        self,
        message: str,
        intent: Dict[str, Any],
        tool_results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI response using reasoning model"""
        try:
            # Build context for the AI
            context_summary = {
                "user_message": message,
                "intent": intent,
                "tool_results": tool_results,
                "available_context": context
            }
            
            prompt = f"""
            Based on the user's message and the available context, provide a helpful response.
            
            User Message: {message}
            Intent: {json.dumps(intent, default=str)}
            Tool Results: {json.dumps(tool_results, default=str)}
            Context: {json.dumps(context, default=str)}
            
            Provide a response that:
            1. Addresses the user's question directly
            2. References relevant information from tool results
            3. Suggests next steps or actions if appropriate
            4. Maintains a helpful and professional tone
            
            Return a JSON response with:
            - text: the main response text
            - actions: any suggested actions
            - citations: references to sources
            """
            
            response = await self.ollama_client.post(
                "/api/generate",
                json={
                    "model": settings.OLLAMA_REASONER_MODEL,
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "{}")
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return self._generate_fallback_response(message, tool_results)
            else:
                return self._generate_fallback_response(message, tool_results)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(message, tool_results)
    
    def _generate_fallback_response(
        self,
        message: str,
        tool_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a fallback response when AI generation fails"""
        successful_tools = [r for r in tool_results if r.get("success")]
        
        if successful_tools:
            return {
                "text": f"I found some relevant information for your request: '{message}'. Let me help you with that.",
                "actions": [],
                "citations": [],
                "confidence": 0.6
            }
        else:
            return {
                "text": f"I understand you're asking about '{message}'. Let me search for relevant information to help you.",
                "actions": [],
                "citations": [],
                "confidence": 0.4
            }
    
    # Tool implementations
    async def generate_wbs(
        self,
        project_id: int,
        constraints: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Generate Work Breakdown Structure"""
        try:
            # Get project information
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Simple WBS generation logic
            tasks = [
                {
                    "id": 1,
                    "name": "Project Planning",
                    "description": "Initial project planning and setup",
                    "estimated_hours": 40,
                    "dependencies": []
                },
                {
                    "id": 2,
                    "name": "Requirements Analysis",
                    "description": "Gather and analyze project requirements",
                    "estimated_hours": 60,
                    "dependencies": [1]
                },
                {
                    "id": 3,
                    "name": "Design",
                    "description": "Create project design and architecture",
                    "estimated_hours": 80,
                    "dependencies": [2]
                }
            ]
            
            return {
                "tasks": tasks,
                "dependencies": [
                    {"from": 1, "to": 2},
                    {"from": 2, "to": 3}
                ],
                "estimated_duration": "3 weeks",
                "confidence": 0.8
            }
            
        except Exception as e:
            logger.error(f"Error generating WBS: {e}")
            raise
    
    async def forecast_budget(
        self,
        project_id: int,
        horizon: str,
        drivers: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Forecast project budget"""
        try:
            # Get budget information
            result = await db.execute(select(Budget).where(Budget.project_id == project_id))
            budget = result.scalar_one_or_none()
            
            if not budget:
                raise ValueError(f"Budget for project {project_id} not found")
            
            # Simple forecasting logic
            base_amount = budget.total_amount
            forecast = []
            
            if horizon == "3months":
                for month in range(1, 4):
                    forecast.append({
                        "month": month,
                        "amount": base_amount * (0.3 + month * 0.2),
                        "confidence": 0.8 - (month * 0.1)
                    })
            
            return {
                "forecast": forecast,
                "variance_explained": "Based on historical spending patterns and project phase",
                "recommendations": [
                    "Monitor spending closely in month 2",
                    "Review resource allocation for cost optimization"
                ],
                "confidence": 0.75
            }
            
        except Exception as e:
            logger.error(f"Error forecasting budget: {e}")
            raise
    
    async def explain_variance(
        self,
        project_id: int,
        period: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Explain budget/schedule variance"""
        try:
            # Get project and budget data
            result = await db.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Simple variance explanation
            narrative = f"Project {project.name} shows moderate variance in {period}. "
            narrative += "This is primarily due to resource allocation changes and scope adjustments."
            
            return {
                "narrative": narrative,
                "drivers": [
                    "Resource reallocation to higher priority tasks",
                    "Scope changes approved by stakeholders",
                    "Vendor delivery delays"
                ],
                "actions": [
                    "Review resource allocation weekly",
                    "Implement change control process",
                    "Establish vendor performance metrics"
                ],
                "confidence": 0.7
            }
            
        except Exception as e:
            logger.error(f"Error explaining variance: {e}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return list(self.tools_registry.values())
    
    async def get_status(self) -> Dict[str, Any]:
        """Get AI Copilot system status"""
        try:
            # Check Ollama connection
            ollama_status = "healthy"
            try:
                response = await self.ollama_client.get("/api/tags")
                if response.status_code != 200:
                    ollama_status = "unhealthy"
            except Exception:
                ollama_status = "unreachable"
            
            return {
                "status": "operational",
                "ollama": ollama_status,
                "tools_count": len(self.tools_registry),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
