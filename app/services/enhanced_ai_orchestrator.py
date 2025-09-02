#!/usr/bin/env python3
"""
Enhanced AI Orchestrator
Routes queries to appropriate models based on task complexity and type.
Uses available models: nomic-embed-text:v1.5, gpt-oss:20B, qwen3:latest, qwen2.5-coder:1.5b, llama3.2:1b-instruct-q4_K_M, llama3.2:3b-instruct-q4_K_M, codellama:7b-instruct-q4_K_M
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

try:
    import ollama
    _ollama_available = True
except ImportError:
    _ollama_available = False

logger = logging.getLogger(__name__)


class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    STRATEGIC = "strategic"


class TaskType(str, Enum):
    """Types of AI tasks"""
    SECURITY_ANALYSIS = "security_analysis"
    BUSINESS_ANALYSIS = "business_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    DECISION_MAKING = "decision_making"
    STRATEGIC_PLANNING = "strategic_planning"
    RISK_ASSESSMENT = "risk_assessment"
    DOCUMENT_ANALYSIS = "document_analysis"
    FAST_REASONING = "fast_reasoning"
    EMBEDDINGS = "embeddings"


@dataclass
class ModelConfig:
    """Configuration for AI models"""
    name: str
    provider: str  # "ollama" or "transformers"
    task_types: List[TaskType]
    complexity_range: Tuple[TaskComplexity, TaskComplexity]
    response_time_ms: int
    memory_usage_gb: float
    max_tokens: int
    temperature: float = 0.7
    top_p: float = 0.9


class EnhancedAIOrchestrator:
    """Enhanced AI orchestrator with model routing based on available models"""
    
    def __init__(self):
        self.ollama_available = _ollama_available
        
        # Model configurations based on your available models
        self.models = {
            # Embeddings
            "nomic-embed-text:v1.5": ModelConfig(
                name="nomic-embed-text:v1.5",
                provider="ollama",
                task_types=[TaskType.EMBEDDINGS],
                complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.SIMPLE),
                response_time_ms=100,
                memory_usage_gb=0.3,
                max_tokens=512
            ),
            
            # Strategic reasoning and complex analysis
            "gpt-oss:20B": ModelConfig(
                name="gpt-oss:20B",
                provider="ollama",
                task_types=[
                    TaskType.STRATEGIC_PLANNING,
                    TaskType.DECISION_MAKING,
                    TaskType.BUSINESS_ANALYSIS,
                    TaskType.RISK_ASSESSMENT
                ],
                complexity_range=(TaskComplexity.COMPLEX, TaskComplexity.STRATEGIC),
                response_time_ms=5000,
                memory_usage_gb=13.0,
                max_tokens=4096,
                temperature=0.8
            ),
            
            # General tasks and conversation
            "qwen3:latest": ModelConfig(
                name="qwen3:latest",
                provider="ollama",
                task_types=[
                    TaskType.BUSINESS_ANALYSIS,
                    TaskType.DOCUMENT_ANALYSIS,
                    TaskType.DECISION_MAKING
                ],
                complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
                response_time_ms=2000,
                memory_usage_gb=5.2,
                max_tokens=2048,
                temperature=0.7
            ),
            
            # Code generation and technical tasks
            "qwen2.5-coder:1.5b": ModelConfig(
                name="qwen2.5-coder:1.5b",
                provider="ollama",
                task_types=[
                    TaskType.CODE_GENERATION,
                    TaskType.CODE_REVIEW
                ],
                complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.MODERATE),
                response_time_ms=1000,
                memory_usage_gb=1.0,
                max_tokens=1024,
                temperature=0.3
            ),
            
            # Fast decisions and lightweight tasks
            "llama3.2:1b-instruct-q4_K_M": ModelConfig(
                name="llama3.2:1b-instruct-q4_K_M",
                provider="ollama",
                task_types=[
                    TaskType.FAST_REASONING,
                    TaskType.DECISION_MAKING
                ],
                complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.SIMPLE),
                response_time_ms=500,
                memory_usage_gb=0.8,
                max_tokens=512,
                temperature=0.5
            ),
            
            # Security analysis and validation
            "llama3.2:3b-instruct-q4_K_M": ModelConfig(
                name="llama3.2:3b-instruct-q4_K_M",
                provider="ollama",
                task_types=[
                    TaskType.SECURITY_ANALYSIS,
                    TaskType.RISK_ASSESSMENT
                ],
                complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.MODERATE),
                response_time_ms=1000,
                memory_usage_gb=2.0,
                max_tokens=1024,
                temperature=0.6
            ),
            
            # Code security and development
            "codellama:7b-instruct-q4_K_M": ModelConfig(
                name="codellama:7b-instruct-q4_K_M",
                provider="ollama",
                task_types=[
                    TaskType.CODE_GENERATION,
                    TaskType.CODE_REVIEW,
                    TaskType.SECURITY_ANALYSIS
                ],
                complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
                response_time_ms=2000,
                memory_usage_gb=4.1,
                max_tokens=2048,
                temperature=0.4
            )
        }
        
        # Task complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                "simple", "basic", "quick", "fast", "lightweight", "routine", "standard"
            ],
            TaskComplexity.MODERATE: [
                "moderate", "medium", "analysis", "review", "assessment", "evaluation"
            ],
            TaskComplexity.COMPLEX: [
                "complex", "advanced", "detailed", "comprehensive", "thorough", "strategic"
            ],
            TaskComplexity.STRATEGIC: [
                "strategic", "planning", "long-term", "vision", "roadmap", "architecture"
            ]
        }
        
        # Task type indicators
        self.task_indicators = {
            TaskType.SECURITY_ANALYSIS: [
                "security", "vulnerability", "threat", "risk", "compliance", "audit", "penetration"
            ],
            TaskType.BUSINESS_ANALYSIS: [
                "business", "analysis", "market", "competitor", "strategy", "performance", "metrics"
            ],
            TaskType.CODE_GENERATION: [
                "code", "programming", "development", "implementation", "function", "class", "api"
            ],
            TaskType.CODE_REVIEW: [
                "review", "code review", "quality", "best practices", "refactoring", "optimization"
            ],
            TaskType.DECISION_MAKING: [
                "decision", "choose", "select", "recommend", "suggest", "option", "alternative"
            ],
            TaskType.STRATEGIC_PLANNING: [
                "strategic", "planning", "roadmap", "vision", "long-term", "architecture", "design"
            ],
            TaskType.RISK_ASSESSMENT: [
                "risk", "assessment", "mitigation", "threat", "vulnerability", "probability", "impact"
            ],
            TaskType.DOCUMENT_ANALYSIS: [
                "document", "analysis", "extract", "parse", "understand", "interpret", "summarize"
            ],
            TaskType.FAST_REASONING: [
                "quick", "fast", "immediate", "urgent", "real-time", "instant", "rapid"
            ]
        }
    
    def _analyze_query(self, query: str) -> Tuple[TaskType, TaskComplexity]:
        """
        Analyze query to determine task type and complexity
        """
        query_lower = query.lower()
        
        # Determine task type
        task_type_scores = {}
        for task_type, indicators in self.task_indicators.items():
            score = sum(1 for indicator in indicators if indicator in query_lower)
            task_type_scores[task_type] = score
        
        # Get the task type with highest score
        task_type = max(task_type_scores.items(), key=lambda x: x[1])[0]
        
        # Determine complexity
        complexity_scores = {}
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in query_lower)
            complexity_scores[complexity] = score
        
        # Get the complexity with highest score
        complexity = max(complexity_scores.items(), key=lambda x: x[1])[0]
        
        # Adjust based on query length and keywords
        if len(query) > 200:
            complexity = TaskComplexity.COMPLEX
        elif len(query) > 100:
            complexity = TaskComplexity.MODERATE
        
        return task_type, complexity
    
    def route_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route query to appropriate model based on analysis
        """
        task_type, complexity = self._analyze_query(query)
        
        # Find suitable models
        suitable_models = []
        for model_name, config in self.models.items():
            if (task_type in config.task_types and
                complexity >= config.complexity_range[0] and
                complexity <= config.complexity_range[1]):
                suitable_models.append((model_name, config))
        
        if not suitable_models:
            # Fallback to general purpose model
            suitable_models = [("qwen3:latest", self.models["qwen3:latest"])]
        
        # Select best model based on response time and complexity match
        best_model = min(suitable_models, key=lambda x: x[1].response_time_ms)
        
        return {
            "selected_model": best_model[0],
            "model_config": asdict(best_model[1]),
            "task_type": task_type.value,
            "complexity": complexity.value,
            "reasoning": f"Selected {best_model[0]} for {task_type.value} task with {complexity.value} complexity"
        }
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embeddings using nomic-embed-text:v1.5
        """
        if not self.ollama_available:
            logger.warning("Ollama not available for embeddings")
            return None
        
        try:
            response = ollama.embeddings(model="nomic-embed-text:v1.5", prompt=text)
            return response.get("embedding")
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            return None
    
    async def generate_response(
        self,
        query: str,
        context: Dict[str, Any] = None,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate response using appropriate model
        """
        if not self.ollama_available:
            return {
                "success": False,
                "error": "Ollama not available",
                "fallback_response": "AI service temporarily unavailable"
            }
        
        try:
            # Route query to appropriate model
            if model_override:
                selected_model = model_override
                model_config = self.models.get(selected_model)
                if not model_config:
                    return {
                        "success": False,
                        "error": f"Model {model_override} not found"
                    }
            else:
                routing_result = self.route_query(query, context)
                selected_model = routing_result["selected_model"]
                model_config = self.models[selected_model]
            
            # Generate response
            start_time = datetime.now()
            
            response = ollama.generate(
                model=selected_model,
                prompt=query,
                options={
                    "temperature": model_config.temperature,
                    "top_p": model_config.top_p,
                    "num_predict": min(model_config.max_tokens, 2048)
                }
            )
            
            end_time = datetime.now()
            response_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return {
                "success": True,
                "model": selected_model,
                "response": response.get("response", ""),
                "response_time_ms": response_time_ms,
                "tokens_used": response.get("eval_count", 0),
                "model_config": asdict(model_config),
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model": selected_model if 'selected_model' in locals() else "unknown"
            }
    
    async def analyze_project_health(
        self,
        project_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze project health using strategic model
        """
        query = f"""
        Analyze the following project data and provide a comprehensive health assessment:
        
        Project: {project_data.get('name', 'Unknown')}
        Status: {project_data.get('status', 'Unknown')}
        Progress: {project_data.get('completion_percentage', 0)}%
        Budget Used: {project_data.get('budget_used', 0)} / {project_data.get('budget_allocated', 0)}
        Timeline: {project_data.get('days_remaining', 0)} days remaining
        Team Size: {project_data.get('team_size', 0)} members
        Risk Level: {project_data.get('risk_level', 'Unknown')}
        
        Please provide:
        1. Overall health score (0-100)
        2. Key risk factors
        3. Recommendations for improvement
        4. Priority actions needed
        """
        
        return await self.generate_response(
            query,
            context,
            model_override="gpt-oss:20B"
        )
    
    async def assess_security_risks(
        self,
        action_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Assess security risks using security-focused model
        """
        query = f"""
        Perform a security risk assessment for the following autonomous action:
        
        Action Type: {action_data.get('action_type', 'Unknown')}
        Action Data: {json.dumps(action_data.get('action_data', {}), indent=2)}
        User Context: {context.get('user_id', 'Unknown')}
        
        Please assess:
        1. Security vulnerabilities
        2. Data privacy risks
        3. Access control issues
        4. Compliance concerns
        5. Risk mitigation recommendations
        """
        
        return await self.generate_response(
            query,
            context,
            model_override="llama3.2:3b-instruct-q4_K_M"
        )
    
    async def generate_code(
        self,
        requirements: str,
        language: str = "python",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate code using code-focused model
        """
        query = f"""
        Generate {language} code based on the following requirements:
        
        {requirements}
        
        Please provide:
        1. Complete, working code
        2. Comments explaining the logic
        3. Error handling
        4. Best practices implementation
        """
        
        return await self.generate_response(
            query,
            context,
            model_override="qwen2.5-coder:1.5b"
        )
    
    async def make_quick_decision(
        self,
        decision_context: Dict[str, Any],
        options: List[str],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make quick decision using fast reasoning model
        """
        query = f"""
        Make a quick decision based on the following context:
        
        Context: {json.dumps(decision_context, indent=2)}
        Options: {', '.join(options)}
        
        Please provide:
        1. Selected option
        2. Brief reasoning
        3. Confidence level (0-100%)
        """
        
        return await self.generate_response(
            query,
            context,
            model_override="llama3.2:1b-instruct-q4_K_M"
        )
    
    async def analyze_business_metrics(
        self,
        metrics_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze business metrics using business analysis model
        """
        query = f"""
        Analyze the following business metrics and provide insights:
        
        {json.dumps(metrics_data, indent=2)}
        
        Please provide:
        1. Key trends and patterns
        2. Performance insights
        3. Areas of concern
        4. Recommendations for improvement
        5. Strategic implications
        """
        
        return await self.generate_response(
            query,
            context,
            model_override="qwen3:latest"
        )
    
    def get_model_status(self) -> Dict[str, Any]:
        """
        Get status of all available models
        """
        model_status = {}
        
        for model_name, config in self.models.items():
            model_status[model_name] = {
                "available": True,
                "provider": config.provider,
                "task_types": [t.value for t in config.task_types],
                "complexity_range": [c.value for c in config.complexity_range],
                "response_time_ms": config.response_time_ms,
                "memory_usage_gb": config.memory_usage_gb,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature
            }
        
        return {
            "ollama_available": self.ollama_available,
            "total_models": len(self.models),
            "models": model_status
        }
    
    async def test_model_availability(self) -> Dict[str, Any]:
        """
        Test availability of all models
        """
        if not self.ollama_available:
            return {
                "success": False,
                "error": "Ollama not available",
                "models": {}
            }
        
        test_results = {}
        
        for model_name in self.models.keys():
            try:
                # Simple test query
                test_query = "Hello, this is a test."
                start_time = datetime.now()
                
                response = ollama.generate(
                    model=model_name,
                    prompt=test_query,
                    options={"num_predict": 10}
                )
                
                end_time = datetime.now()
                response_time_ms = (end_time - start_time).total_seconds() * 1000
                
                test_results[model_name] = {
                    "available": True,
                    "response_time_ms": response_time_ms,
                    "test_response": response.get("response", "")[:50] + "..."
                }
                
            except Exception as e:
                test_results[model_name] = {
                    "available": False,
                    "error": str(e)
                }
        
        return {
            "success": True,
            "models": test_results
        }


# Global instance and getter function
_ai_orchestrator_instance = None

def get_ai_orchestrator() -> EnhancedAIOrchestrator:
    """Get the global AI orchestrator instance"""
    global _ai_orchestrator_instance
    if _ai_orchestrator_instance is None:
        _ai_orchestrator_instance = EnhancedAIOrchestrator()
    return _ai_orchestrator_instance
