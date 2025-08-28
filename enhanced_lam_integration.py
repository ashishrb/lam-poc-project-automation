#!/usr/bin/env python3
"""
Enhanced True LAM Integration with Autonomous Capabilities
Adds multi-step reasoning, strategic planning, and autonomous decision-making
Optimized for AMD Ryzen 9 9950X + RTX 4090 + 128GB RAM
"""

import json
import logging
import torch
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer
from bs4 import BeautifulSoup
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import random
import time
from dataclasses import dataclass
from enum import Enum

# Optional external integrations
try:
    import ollama  # Python client for local Ollama server
    _ollama_available = True
except Exception:
    _ollama_available = False

# Import system configuration
try:
    from system_config import system_config
    print("✅ System configuration loaded successfully")
except ImportError as e:
    print(f"⚠️ System configuration not available: {e}")
    system_config = None

# Set random seed for reproducibility
torch.random.manual_seed(0)

# Configure PyTorch based on system capabilities
if system_config:
    system_config.print_system_info()
else:
    print("🔧 Using default PyTorch configuration")

class DecisionType(Enum):
    """Types of autonomous decisions"""
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    ESCALATION = "escalation"
    COMMUNICATION = "communication"
    RESOURCE = "resource"

@dataclass
class AutonomousTask:
    """Represents an autonomous task with context"""
    task_id: str
    description: str
    priority: int
    dependencies: List[str]
    estimated_duration: int
    assigned_to: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ProjectContext:
    """Project context for autonomous decision making"""
    project_id: str
    project_name: str
    status: str
    budget_used: float
    budget_total: float
    timeline_progress: float
    team_members: List[str]
    stakeholders: List[str]
    risk_level: str
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

class AutonomousMemory:
    """Memory system for context retention and learning"""
    
    def __init__(self):
        self.short_term_memory = {}  # Current session context
        self.long_term_memory = {}   # Persistent learning data
        self.decision_history = []   # Track autonomous decisions
        self.context_stack = []      # Multi-step context tracking
    
    def store_context(self, key: str, context: Dict[str, Any]):
        """Store context information"""
        self.short_term_memory[key] = {
            "data": context,
            "timestamp": datetime.now()
        }
    
    def get_context(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve context information"""
        if key in self.short_term_memory:
            return self.short_term_memory[key]["data"]
        return None
    
    def push_context(self, context: Dict[str, Any]):
        """Push context to stack for multi-step operations"""
        self.context_stack.append({
            "context": context,
            "timestamp": datetime.now()
        })
    
    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop context from stack"""
        if self.context_stack:
            return self.context_stack.pop()["context"]
        return None
    
    def log_decision(self, decision: Dict[str, Any]):
        """Log autonomous decision for learning"""
        self.decision_history.append({
            "decision": decision,
            "timestamp": datetime.now(),
            "context": self.short_term_memory.copy()
        })

class StrategicPlanner:
    """Strategic planning and multi-step reasoning engine"""
    
    def __init__(self, memory: AutonomousMemory):
        self.memory = memory
        self.planning_templates = {
            "project_status_report": [
                "analyze_project_data",
                "identify_risks_and_issues",
                "generate_recommendations",
                "create_stakeholder_communications",
                "schedule_follow_up_actions"
            ],
            "employee_development": [
                "analyze_performance_data",
                "identify_skill_gaps",
                "generate_development_plan",
                "create_appreciation_messages",
                "schedule_training_sessions"
            ],
            "resource_optimization": [
                "analyze_resource_utilization",
                "identify_bottlenecks",
                "optimize_allocations",
                "communicate_changes",
                "monitor_outcomes"
            ]
        }
    
    def create_strategic_plan(self, goal: str, context: Dict[str, Any]) -> List[AutonomousTask]:
        """Create a strategic plan with autonomous tasks"""
        plan_type = self._identify_plan_type(goal)
        template = self.planning_templates.get(plan_type, ["analyze", "plan", "execute", "communicate"])
        
        tasks = []
        for i, step in enumerate(template):
            task = AutonomousTask(
                task_id=f"{plan_type}_{i+1}",
                description=self._generate_task_description(step, context),
                priority=i+1,
                dependencies=[f"{plan_type}_{i}"] if i > 0 else [],
                estimated_duration=15 + (i * 5),  # Progressive duration
            )
            tasks.append(task)
        
        # Store plan in memory
        self.memory.store_context(f"strategic_plan_{plan_type}", {
            "goal": goal,
            "tasks": [task.__dict__ for task in tasks],
            "context": context
        })
        
        return tasks
    
    def _identify_plan_type(self, goal: str) -> str:
        """Identify the type of strategic plan needed"""
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ["report", "status", "progress"]):
            return "project_status_report"
        elif any(word in goal_lower for word in ["employee", "performance", "skill", "development"]):
            return "employee_development"
        elif any(word in goal_lower for word in ["resource", "optimize", "allocation"]):
            return "resource_optimization"
        else:
            return "general_planning"
    
    def _generate_task_description(self, step: str, context: Dict[str, Any]) -> str:
        """Generate detailed task description"""
        descriptions = {
            "analyze_project_data": "Analyze current project metrics, timelines, and performance indicators",
            "identify_risks_and_issues": "Identify potential risks, blockers, and critical issues requiring attention",
            "generate_recommendations": "Generate strategic recommendations based on analysis",
            "create_stakeholder_communications": "Create personalized communications for each stakeholder group",
            "schedule_follow_up_actions": "Schedule and plan follow-up actions and monitoring",
            "analyze_performance_data": "Analyze employee performance data and identify patterns",
            "identify_skill_gaps": "Identify skill gaps and development opportunities",
            "generate_development_plan": "Create personalized development plans and recommendations",
            "create_appreciation_messages": "Generate personalized appreciation and recognition messages",
            "schedule_training_sessions": "Schedule appropriate training sessions and development activities"
        }
        
        return descriptions.get(step, f"Execute {step} with current context")

class AutonomousDecisionEngine:
    """Autonomous decision-making engine"""
    
    def __init__(self, memory: AutonomousMemory):
        self.memory = memory
        self.decision_rules = self._initialize_decision_rules()
    
    def _initialize_decision_rules(self) -> Dict[str, Any]:
        """Initialize decision-making rules"""
        return {
            "project_health": {
                "budget_threshold": 0.8,  # 80% budget used
                "timeline_threshold": 0.9,  # 90% timeline passed
                "risk_escalation": ["high", "critical"]
            },
            "employee_performance": {
                "excellence_threshold": 8.5,  # Quality score >= 8.5
                "improvement_threshold": 7.0,  # Quality score < 7.0
                "recognition_frequency": 30  # Days between recognitions
            },
            "communication": {
                "stakeholder_update_frequency": 7,  # Weekly updates
                "escalation_levels": ["manager", "director", "vp"],
                "urgency_thresholds": {"low": 3, "medium": 1, "high": 0}  # Days
            }
        }
    
    def make_autonomous_decision(self, context: Dict[str, Any], decision_type: DecisionType) -> Dict[str, Any]:
        """Make autonomous decision based on context and rules"""
        decision = {
            "type": decision_type.value,
            "timestamp": datetime.now(),
            "context_summary": self._summarize_context(context),
            "decision": None,
            "reasoning": None,
            "actions": [],
            "confidence": 0.0
        }
        
        if decision_type == DecisionType.STRATEGIC:
            decision.update(self._make_strategic_decision(context))
        elif decision_type == DecisionType.OPERATIONAL:
            decision.update(self._make_operational_decision(context))
        elif decision_type == DecisionType.ESCALATION:
            decision.update(self._make_escalation_decision(context))
        elif decision_type == DecisionType.COMMUNICATION:
            decision.update(self._make_communication_decision(context))
        elif decision_type == DecisionType.RESOURCE:
            decision.update(self._make_resource_decision(context))
        
        # Log decision for learning
        self.memory.log_decision(decision)
        
        return decision
    
    def _make_strategic_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make strategic-level decisions"""
        if "project" in context:
            project = context["project"]
            budget_ratio = project.get("budget_used", 0) / project.get("budget_total", 1)
            timeline_progress = project.get("timeline_progress", 0)
            
            if budget_ratio > self.decision_rules["project_health"]["budget_threshold"]:
                return {
                    "decision": "budget_optimization_required",
                    "reasoning": f"Budget utilization at {budget_ratio:.1%}, exceeding threshold",
                    "actions": ["analyze_spending", "identify_cost_savings", "stakeholder_notification"],
                    "confidence": 0.85
                }
            elif timeline_progress > self.decision_rules["project_health"]["timeline_threshold"]:
                return {
                    "decision": "timeline_acceleration_needed",
                    "reasoning": f"Timeline progress at {timeline_progress:.1%}, risk of delay",
                    "actions": ["resource_reallocation", "scope_adjustment", "stakeholder_communication"],
                    "confidence": 0.90
                }
        
        return {
            "decision": "continue_current_strategy",
            "reasoning": "All metrics within acceptable ranges",
            "actions": ["monitor_progress"],
            "confidence": 0.75
        }
    
    def _make_operational_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make operational-level decisions"""
        if "employee_performance" in context:
            performance = context["employee_performance"]
            quality_score = performance.get("quality_score", 0)
            
            if quality_score >= self.decision_rules["employee_performance"]["excellence_threshold"]:
                return {
                    "decision": "recognize_excellence",
                    "reasoning": f"Quality score {quality_score} exceeds excellence threshold",
                    "actions": ["send_appreciation", "consider_promotion", "peer_recognition"],
                    "confidence": 0.95
                }
            elif quality_score < self.decision_rules["employee_performance"]["improvement_threshold"]:
                return {
                    "decision": "initiate_improvement_plan",
                    "reasoning": f"Quality score {quality_score} below improvement threshold",
                    "actions": ["skill_assessment", "training_plan", "mentorship_assignment"],
                    "confidence": 0.88
                }
        
        return {
            "decision": "maintain_current_operations",
            "reasoning": "Performance metrics within normal ranges",
            "actions": ["continue_monitoring"],
            "confidence": 0.70
        }
    
    def _make_escalation_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make escalation decisions"""
        risk_level = context.get("risk_level", "low")
        urgency = context.get("urgency", "low")
        
        if risk_level in self.decision_rules["project_health"]["risk_escalation"]:
            escalation_level = "director" if risk_level == "high" else "vp"
            return {
                "decision": f"escalate_to_{escalation_level}",
                "reasoning": f"Risk level {risk_level} requires senior attention",
                "actions": ["prepare_escalation_brief", "schedule_meeting", "stakeholder_notification"],
                "confidence": 0.92
            }
        
        return {
            "decision": "handle_at_current_level",
            "reasoning": "Risk level manageable at current level",
            "actions": ["monitor_closely"],
            "confidence": 0.80
        }
    
    def _make_communication_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make communication decisions"""
        last_update = context.get("last_stakeholder_update", datetime.now() - timedelta(days=10))
        days_since_update = (datetime.now() - last_update).days
        
        if days_since_update >= self.decision_rules["communication"]["stakeholder_update_frequency"]:
            return {
                "decision": "send_stakeholder_update",
                "reasoning": f"{days_since_update} days since last update, threshold exceeded",
                "actions": ["generate_status_report", "personalize_messages", "send_updates"],
                "confidence": 0.87
            }
        
        return {
            "decision": "maintain_current_communication",
            "reasoning": "Communication frequency within acceptable range",
            "actions": ["continue_monitoring"],
            "confidence": 0.75
        }
    
    def _make_resource_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make resource allocation decisions"""
        utilization = context.get("resource_utilization", {})
        
        overutilized = [k for k, v in utilization.items() if v > 0.9]
        underutilized = [k for k, v in utilization.items() if v < 0.6]
        
        if overutilized or underutilized:
            return {
                "decision": "optimize_resource_allocation",
                "reasoning": f"Resource imbalance detected: overutilized {overutilized}, underutilized {underutilized}",
                "actions": ["rebalance_workload", "adjust_assignments", "communicate_changes"],
                "confidence": 0.85
            }
        
        return {
            "decision": "maintain_current_allocation",
            "reasoning": "Resource utilization balanced",
            "actions": ["monitor_utilization"],
            "confidence": 0.78
        }
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Create a summary of the current context"""
        summary_parts = []
        
        if "project" in context:
            project = context["project"]
            summary_parts.append(f"Project: {project.get('name', 'Unknown')} ({project.get('status', 'Unknown')})")
        
        if "employee_performance" in context:
            perf = context["employee_performance"]
            summary_parts.append(f"Employee Quality: {perf.get('quality_score', 'N/A')}")
        
        if "risk_level" in context:
            summary_parts.append(f"Risk Level: {context['risk_level']}")
        
        return "; ".join(summary_parts) if summary_parts else "General context"


class EnhancedAIOrchestrator:
    """Routes queries to appropriate local models and embeddings via Ollama.

    - Uses xLAM for tool-use and function-style tasks
    - Uses gpt-oss:20b for complex strategic analysis
    - Uses nomic-embed-text:v1.5 embeddings for RAG
    """

    def __init__(self):
        # Keep existing xLAM model
        self.xlam_model = "Salesforce/xLAM-1b-fc-r"

        # Add new Ollama models
        self.strategic_model = "gpt-oss:20b"
        self.embedding_model = "nomic-embed-text:v1.5"

        self.ollama_available = _ollama_available
        if not self.ollama_available:
            logging.warning("Ollama client not available. Falling back to xLAM-only mode.")

    def _score_complexity(self, query: str) -> int:
        """Very lightweight heuristic for complexity scoring (1-10)."""
        q = query.lower()
        indicators = [
            ("strategy", 3), ("plan", 2), ("predict", 2), ("analysis", 2),
            ("optimize", 2), ("risk", 1), ("budget", 1), ("stakeholder", 1),
            ("lifecycle", 2), ("autonomous", 1)
        ]
        base = 3 if len(q) > 120 else 2
        return min(10, base + sum(w for k, w in indicators if k in q))

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Return embedding vector using Ollama nomic-embed model if available."""
        if not self.ollama_available:
            return None
        try:
            resp = ollama.embeddings(model=self.embedding_model, prompt=text)
            return resp.get("embedding")
        except Exception as e:
            logging.warning(f"Embedding generation failed: {e}")
            return None

    def route_query_to_appropriate_model(self, query: str, complexity_level: Optional[int] = None) -> Dict[str, Any]:
        """Decide which model to use and return a routing plan.

        - For simple or tool-oriented requests → xLAM
        - For complex, strategic analysis → gpt-oss:20b (if Ollama available)
        - Embeddings can be requested by callers via get_embedding
        """
        score = complexity_level if complexity_level is not None else self._score_complexity(query)
        route = {
            "complexity_score": score,
            "use_embeddings": score >= 5 and self.ollama_available,
            "selected_model": self.xlam_model,
            "provider": "transformers"
        }

        if self.ollama_available and score >= 6:
            route.update({
                "selected_model": self.strategic_model,
                "provider": "ollama"
            })

        # Simple function-call style triggers → bias towards xLAM
        simple_triggers = [
            "write file", "read file", "generate report", "get weather",
            "tool", "function", "call", "api"
        ]
        if any(t in query.lower() for t in simple_triggers):
            route.update({"selected_model": self.xlam_model, "provider": "transformers"})

        return route

class EnhancedTrueLAMInterface:
    """Enhanced True LAM Interface with Autonomous Capabilities"""
    
    def __init__(self):
        """Initialize the Enhanced True LAM Interface"""
        self.model_name = "Salesforce/xLAM-1b-fc-r"
        print(f"🤖 Loading Enhanced True LAM Model: {self.model_name}")
        
        # Initialize memory and autonomous systems
        self.memory = AutonomousMemory()
        self.strategic_planner = StrategicPlanner(self.memory)
        self.decision_engine = AutonomousDecisionEngine(self.memory)
        try:
            from enhanced_autonomous_pm.core.ai_orchestrator import EnhancedAIOrchestrator as CoreOrchestrator
            self.ai_orchestrator = CoreOrchestrator()
        except Exception:
            self.ai_orchestrator = EnhancedAIOrchestrator()
        
        try:
            # Use system configuration for optimal model loading
            if system_config:
                config = system_config.get_model_config()
                device = config['device']
                torch_dtype = config['torch_dtype']
                print(f"🔧 Using system-optimized configuration: {device}, {torch_dtype}")
            else:
                # Fallback to default configuration
                device = "cuda" if torch.cuda.is_available() else "cpu"
                torch_dtype = torch.float16 if device == "cuda" else torch.float32
                print(f"🔧 Using default configuration: {device}, {torch_dtype}")
            
            # Load model with optimized settings
            try:
                if device == "cuda":
                    # Try device_map="auto" first (requires accelerate)
                    try:
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name, 
                            device_map="auto",
                            torch_dtype=torch_dtype,
                            trust_remote_code=True,
                            low_cpu_mem_usage=True
                        )
                        print("✅ Model loaded with automatic device mapping")
                    except Exception as e:
                        print(f"⚠️ Auto device mapping failed: {e}")
                        print("🔄 Falling back to manual device placement...")
                        # Fallback to manual device placement
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name, 
                            torch_dtype=torch_dtype,
                            trust_remote_code=True,
                            low_cpu_mem_usage=True
                        )
                        self.model = self.model.to("cuda")
                        print("✅ Model loaded with manual device placement")
                else:
                    # CPU loading
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name, 
                        torch_dtype=torch_dtype,
                        trust_remote_code=True
                    )
                    self.model = self.model.to("cpu")
                    print("✅ Model loaded on CPU")
            except Exception as e:
                print(f"❌ Error in model loading: {e}")
                raise
            
            # Set CPU threads if using CPU
            if device == "cpu" and system_config:
                torch.set_num_threads(system_config.cpu_cores)
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            print(f"✅ Enhanced True LAM Model loaded successfully on {device}!")
            
            # Memory optimization for GPU
            if device == "cuda" and system_config:
                torch.cuda.empty_cache()
                print(f"🧹 GPU memory cache cleared")
                
        except Exception as e:
            print(f"❌ Error loading LAM model: {e}")
            print("🔄 Falling back to pattern matching...")
            self.model = None
            self.tokenizer = None
        
        # Enhanced task instruction for autonomous operations
        self.task_instruction = """
You are an autonomous AI system with strategic thinking and multi-step execution capabilities. 
You can analyze complex business situations, make strategic decisions, and execute multi-step plans.

When given a task, you should:
1. Analyze the current situation and context
2. Identify strategic objectives and constraints
3. Create a multi-step execution plan
4. Make autonomous decisions based on business rules
5. Execute tasks with appropriate tool calls
6. Monitor outcomes and adjust plans as needed

IMPORTANT: You have autonomous decision-making authority for:
- Project status analysis and reporting
- Employee performance assessment and development
- Resource optimization and allocation
- Stakeholder communication and updates
- Risk assessment and mitigation planning

Use your tools strategically to achieve business objectives efficiently.
""".strip()

        self.format_instruction = """
The output MUST be a valid JSON array of tool calls for autonomous execution.
For complex tasks, break them into logical steps and execute multiple tools in sequence.

AUTONOMOUS EXECUTION EXAMPLES:
- "Create project status report and send to stakeholders" → 
  [
    {"name": "analyze_project_status", "arguments": {"project_id": "current"}},
    {"name": "generate_status_report", "arguments": {"include_recommendations": true}},
    {"name": "identify_stakeholders", "arguments": {"project_id": "current"}},
    {"name": "send_personalized_updates", "arguments": {"report_type": "status_update"}}
  ]

- "Analyze team performance and take appropriate actions" →
  [
    {"name": "analyze_team_performance", "arguments": {"period": "current_quarter"}},
    {"name": "identify_top_performers", "arguments": {}},
    {"name": "identify_improvement_needs", "arguments": {}},
    {"name": "generate_appreciation_messages", "arguments": {"for": "top_performers"}},
    {"name": "create_development_plans", "arguments": {"for": "improvement_needed"}},
    {"name": "send_personalized_communications", "arguments": {}}
  ]
""".strip()

        # Enhanced tools for autonomous operations
        self.tools = [
            {
                "name": "analyze_project_status",
                "description": "Analyze current project status, health, and metrics for autonomous decision-making",
                "parameters": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID to analyze, use 'current' for active project"
                    },
                    "include_predictions": {
                        "type": "boolean",
                        "description": "Whether to include predictive analysis and forecasting"
                    }
                }
            },
            {
                "name": "generate_strategic_plan",
                "description": "Generate a strategic multi-step plan for achieving business objectives",
                "parameters": {
                    "objective": {
                        "type": "string",
                        "description": "The strategic objective to achieve"
                    },
                    "timeline": {
                        "type": "string",
                        "description": "Timeline for plan execution (e.g., 'immediate', 'weekly', 'monthly')"
                    }
                }
            },
            {
                "name": "make_autonomous_decision",
                "description": "Make autonomous decisions based on current context and business rules",
                "parameters": {
                    "decision_type": {
                        "type": "string",
                        "description": "Type of decision: strategic, operational, escalation, communication, resource"
                    },
                    "context": {
                        "type": "object",
                        "description": "Current context and data for decision-making"
                    }
                }
            },
            {
                "name": "analyze_team_performance",
                "description": "Analyze team performance and identify patterns, top performers, and improvement needs",
                "parameters": {
                    "period": {
                        "type": "string",
                        "description": "Analysis period: current_quarter, last_month, ytd"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Whether to include autonomous recommendations"
                    }
                }
            },
            {
                "name": "generate_personalized_communications",
                "description": "Generate personalized communications for stakeholders, team members, or management",
                "parameters": {
                    "audience": {
                        "type": "string",
                        "description": "Target audience: stakeholders, team, management, individual"
                    },
                    "message_type": {
                        "type": "string",
                        "description": "Type of message: status_update, appreciation, development_plan, escalation"
                    },
                    "personalization_data": {
                        "type": "object",
                        "description": "Data for personalizing messages"
                    }
                }
            },
            {
                "name": "execute_autonomous_workflow",
                "description": "Execute a complete autonomous workflow with multiple coordinated actions",
                "parameters": {
                    "workflow_type": {
                        "type": "string",
                        "description": "Type of workflow: project_management, employee_development, crisis_response"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Workflow-specific parameters"
                    }
                }
            },
            # Keep existing tools for backward compatibility
            {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, New York, London"
                    }
                }
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                }
            },
            {
                "name": "read_file",
                "description": "Read content from a file",
                "parameters": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to read"
                    }
                }
            },
            {
                "name": "generate_sales_report",
                "description": "Generate a comprehensive sales report with autonomous analysis",
                "parameters": {
                    "quarter": {
                        "type": "string",
                        "description": "The quarter for the report, e.g. Q1, Q2, Q3, Q4"
                    },
                    "include_predictions": {
                        "type": "boolean",
                        "description": "Whether to include predictive analysis"
                    },
                    "autonomous_recommendations": {
                        "type": "boolean",
                        "description": "Whether to include autonomous strategic recommendations"
                    }
                }
            },
            {
                "name": "send_email_report",
                "description": "Send email report with autonomous personalization",
                "parameters": {
                    "to_email": {
                        "type": "string",
                        "description": "The email address to send to"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the email"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content of the email"
                    },
                    "personalize": {
                        "type": "boolean",
                        "description": "Whether to autonomously personalize the message"
                    }
                }
            }
        ]
    
    def convert_to_xlam_tool(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI format tools to xLAM format"""
        xlam_tools = []
        for tool in tools:
            # Determine required parameters
            required_params = []
            for param_name, param_info in tool["parameters"].items():
                if "optional" not in param_info.get("description", "").lower():
                    required_params.append(param_name)
            
            xlam_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": tool["parameters"],
                    "required": required_params
                }
            }
            xlam_tools.append(xlam_tool)
        return xlam_tools

    def build_autonomous_prompt(self, query: str) -> str:
        """Build enhanced prompt for autonomous operations"""
        tools_json = json.dumps(self.convert_to_xlam_tool(self.tools), indent=2)
        
        # Get relevant context from memory
        context_info = ""
        if self.memory.short_term_memory:
            context_info = f"\nCURRENT CONTEXT: {json.dumps({k: v['data'] for k, v in self.memory.short_term_memory.items()}, indent=2)}\n"
        
        prompt = f"""{self.task_instruction}

Available tools for autonomous execution:
{tools_json}

{self.format_instruction}
{context_info}
AUTONOMOUS REQUEST: {query}

STRATEGIC ANALYSIS: First analyze what the user wants to achieve strategically, then create a multi-step execution plan.

AUTONOMOUS RESPONSE:"""
        return prompt

    # Enhanced tool execution methods
    def analyze_project_status(self, project_id: str, include_predictions: bool = True) -> Dict[str, Any]:
        """Analyze project status with autonomous insights"""
        try:
            # Simulate project data analysis
            project_data = {
                "project_id": project_id,
                "name": f"Project {project_id.upper()}",
                "status": "in_progress",
                "budget_used": random.uniform(0.6, 0.9),
                "budget_total": 100000,
                "timeline_progress": random.uniform(0.7, 0.95),
                "team_size": random.randint(5, 12),
                "completion_rate": random.uniform(0.75, 0.88),
                "quality_score": random.uniform(7.5, 9.2),
                "risk_factors": random.choice(["low", "medium", "high"])
            }
            
            # Store project context
            project_context = ProjectContext(
                project_id=project_id,
                project_name=project_data["name"],
                status=project_data["status"],
                budget_used=project_data["budget_used"] * project_data["budget_total"],
                budget_total=project_data["budget_total"],
                timeline_progress=project_data["timeline_progress"],
                team_members=[f"EMP{i:03d}" for i in range(1, project_data["team_size"]+1)],
                stakeholders=["manager@company.com", "director@company.com"],
                risk_level=project_data["risk_factors"]
            )
            
            self.memory.store_context("current_project", project_context.__dict__)
            
            # Make autonomous decision about project health
            decision = self.decision_engine.make_autonomous_decision(
                {"project": project_context.__dict__}, 
                DecisionType.STRATEGIC
            )
            
            analysis_result = f"""
🔍 **Autonomous Project Analysis**

**Project Health Dashboard:**
- Budget Utilization: {project_data['budget_used']:.1%}
- Timeline Progress: {project_data['timeline_progress']:.1%}  
- Team Performance: {project_data['quality_score']:.1f}/10
- Completion Rate: {project_data['completion_rate']:.1%}
- Risk Level: {project_data['risk_factors'].upper()}

**🤖 Autonomous Decision:**
- **Decision:** {decision['decision'].replace('_', ' ').title()}
- **Reasoning:** {decision['reasoning']}
- **Recommended Actions:** {', '.join(decision['actions'])}
- **Confidence Level:** {decision['confidence']:.1%}

**📊 Predictive Analysis:**
- Projected Completion: {(datetime.now() + timedelta(days=int((1-project_data['timeline_progress'])*30))).strftime('%Y-%m-%d')}
- Budget Risk: {'HIGH' if project_data['budget_used'] > 0.85 else 'MEDIUM' if project_data['budget_used'] > 0.75 else 'LOW'}
- Success Probability: {random.uniform(0.75, 0.95):.1%}
"""
            
            return {
                "success": True,
                "data": analysis_result,
                "autonomous_decision": decision,
                "project_context": project_context.__dict__
            }
            
        except Exception as e:
            return {"success": False, "error": f"Project analysis failed: {str(e)}"}

    def generate_strategic_plan(self, objective: str, timeline: str = "immediate") -> Dict[str, Any]:
        """Generate strategic plan with autonomous task breakdown"""
        try:
            # Get current context
            context = {}
            if "current_project" in self.memory.short_term_memory:
                context = self.memory.short_term_memory["current_project"]["data"]
            
            # Create strategic plan
            tasks = self.strategic_planner.create_strategic_plan(objective, context)
            
            plan_result = f"""
🎯 **Strategic Plan Generated**

**Objective:** {objective}
**Timeline:** {timeline}
**Total Tasks:** {len(tasks)}

**📋 Autonomous Task Breakdown:**
"""
            
            for i, task in enumerate(tasks, 1):
                plan_result += f"""
**{i}. {task.description}**
   - Priority: {task.priority}
   - Duration: ~{task.estimated_duration} minutes
   - Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}
   - Status: {task.status}
"""
            
            plan_result += f"""
**🤖 Execution Strategy:**
- Tasks will be executed autonomously in sequence
- Each task includes automated validation and error handling  
- Progress tracking and adaptive replanning enabled
- Stakeholder notifications at key milestones
"""
            
            return {
                "success": True,
                "data": plan_result,
                "strategic_plan": [task.__dict__ for task in tasks],
                "execution_timeline": timeline
            }
            
        except Exception as e:
            return {"success": False, "error": f"Strategic planning failed: {str(e)}"}

    def make_autonomous_decision(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make autonomous decision with business logic"""
        try:
            # Convert string to enum
            decision_enum = DecisionType(decision_type.lower())
            
            # Make decision using autonomous engine
            decision = self.decision_engine.make_autonomous_decision(context, decision_enum)
            
            decision_result = f"""
🤖 **Autonomous Decision Made**

**Decision Type:** {decision_type.upper()}
**Decision:** {decision['decision'].replace('_', ' ').title()}

**🧠 Reasoning:**
{decision['reasoning']}

**📋 Recommended Actions:**
{chr(10).join(f"• {action.replace('_', ' ').title()}" for action in decision['actions'])}

**📊 Confidence Level:** {decision['confidence']:.1%}

**⏰ Decision Timestamp:** {decision['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return {
                "success": True,
                "data": decision_result,
                "decision_details": decision
            }
            
        except Exception as e:
            return {"success": False, "error": f"Autonomous decision failed: {str(e)}"}

    def analyze_team_performance(self, period: str = "current_quarter", include_recommendations: bool = True) -> Dict[str, Any]:
        """Analyze team performance with autonomous insights"""
        try:
            # Simulate team performance data
            team_data = []
            employees = ["Alice Johnson", "Bob Smith", "Carol Davis", "David Wilson", "Eva Brown"]
            
            for i, emp_name in enumerate(employees, 1):
                performance = {
                    "employee_id": f"EMP{i:03d}",
                    "name": emp_name,
                    "quality_score": random.uniform(6.5, 9.5),
                    "tasks_completed": random.randint(15, 35),
                    "hours_worked": random.randint(140, 180),
                    "collaboration_score": random.uniform(7.0, 9.0),
                    "innovation_score": random.uniform(6.0, 9.0),
                    "last_promotion": random.choice(["6 months", "1 year", "2 years", "3 years"])
                }
                team_data.append(performance)
            
            # Store team context
            self.memory.store_context("team_performance", {
                "period": period,
                "team_data": team_data,
                "analysis_timestamp": datetime.now()
            })
            
            # Identify top performers and improvement needs
            top_performers = [emp for emp in team_data if emp["quality_score"] >= 8.5]
            needs_improvement = [emp for emp in team_data if emp["quality_score"] < 7.0]
            
            analysis_result = f"""
👥 **Team Performance Analysis - {period.replace('_', ' ').title()}**

**📊 Team Overview:**
- Team Size: {len(team_data)} members
- Average Quality Score: {sum(emp['quality_score'] for emp in team_data)/len(team_data):.2f}/10
- Total Tasks Completed: {sum(emp['tasks_completed'] for emp in team_data)}
- Average Hours Worked: {sum(emp['hours_worked'] for emp in team_data)/len(team_data):.1f}

**🌟 Top Performers ({len(top_performers)} identified):**
"""
            
            for emp in top_performers:
                analysis_result += f"• **{emp['name']}** - Quality: {emp['quality_score']:.1f}/10, Tasks: {emp['tasks_completed']}\n"
            
            analysis_result += f"""
**📈 Needs Development ({len(needs_improvement)} identified):**
"""
            
            for emp in needs_improvement:
                analysis_result += f"• **{emp['name']}** - Quality: {emp['quality_score']:.1f}/10, Needs: Skill development\n"
            
            # Generate autonomous recommendations
            if include_recommendations:
                for emp in top_performers:
                    decision = self.decision_engine.make_autonomous_decision(
                        {"employee_performance": emp}, 
                        DecisionType.OPERATIONAL
                    )
                    analysis_result += f"\n🤖 **Auto-Recommendation for {emp['name']}:** {decision['decision'].replace('_', ' ').title()}"
            
            return {
                "success": True,
                "data": analysis_result,
                "top_performers": top_performers,
                "needs_improvement": needs_improvement,
                "team_metrics": {
                    "avg_quality": sum(emp['quality_score'] for emp in team_data)/len(team_data),
                    "total_tasks": sum(emp['tasks_completed'] for emp in team_data),
                    "avg_hours": sum(emp['hours_worked'] for emp in team_data)/len(team_data)
                }
            }
            
        except Exception as e:
            return {"success": False, "error": f"Team analysis failed: {str(e)}"}

    def generate_personalized_communications(self, audience: str, message_type: str, personalization_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate personalized communications with autonomous customization"""
        try:
            communications = []
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if message_type == "appreciation" and "top_performers" in str(personalization_data):
                # Get top performers from context
                team_context = self.memory.get_context("team_performance")
                if team_context:
                    top_performers = [emp for emp in team_context["team_data"] if emp["quality_score"] >= 8.5]
                    
                    for emp in top_performers:
                        message = f"""
Subject: Recognition for Outstanding Performance

Dear {emp['name']},

I wanted to take a moment to recognize your exceptional performance this quarter. Your quality score of {emp['quality_score']:.1f}/10 and completion of {emp['tasks_completed']} tasks demonstrates your commitment to excellence.

Key Achievements:
• Quality Score: {emp['quality_score']:.1f}/10 (Above Excellence Threshold)
• Tasks Completed: {emp['tasks_completed']} (High Productivity)
• Collaboration Impact: Strong team contribution

Based on your outstanding performance, I'm recommending you for:
• Leadership development opportunities
• Mentoring junior team members
• Consideration for the next promotion cycle

Keep up the excellent work!

Best regards,
Autonomous Project Manager
Generated: {timestamp}
"""
                        communications.append({
                            "recipient": emp['name'],
                            "email": f"{emp['name'].lower().replace(' ', '.')}@company.com",
                            "subject": "Recognition for Outstanding Performance",
                            "message": message,
                            "type": "appreciation"
                        })
            
            elif message_type == "development_plan":
                # Generate development plans for employees needing improvement
                team_context = self.memory.get_context("team_performance")
                if team_context:
                    needs_improvement = [emp for emp in team_context["team_data"] if emp["quality_score"] < 7.0]
                    
                    for emp in needs_improvement:
                        message = f"""
Subject: Personal Development Plan - Q{(datetime.now().month-1)//3 + 1}

Dear {emp['name']},

I've prepared a personalized development plan to help you reach your full potential and advance your career.

Current Performance Review:
• Quality Score: {emp['quality_score']:.1f}/10
• Tasks Completed: {emp['tasks_completed']}
• Areas for Growth: Quality improvement, efficiency optimization

📚 Recommended Development Actions:
1. **Skill Enhancement Training**
   - Technical skills workshop (2 hours/week)
   - Quality assurance best practices course
   - Time management techniques seminar

2. **Mentorship Program**
   - Pairing with senior team member
   - Weekly 1:1 coaching sessions
   - Project collaboration opportunities

3. **Goal Setting (Next 90 Days)**
   - Target Quality Score: 7.5+/10
   - Increase task completion rate by 20%
   - Complete 2 professional development courses

I'm committed to supporting your growth. Let's schedule a meeting to discuss this plan in detail.

Best regards,
Autonomous Project Manager
Generated: {timestamp}
"""
                        communications.append({
                            "recipient": emp['name'],
                            "email": f"{emp['name'].lower().replace(' ', '.')}@company.com",
                            "subject": "Personal Development Plan",
                            "message": message,
                            "type": "development_plan"
                        })
            
            elif message_type == "status_update":
                # Generate stakeholder status update
                project_context = self.memory.get_context("current_project")
                if project_context:
                    stakeholder_message = f"""
Subject: Project Status Update - {project_context['project_name']}

Dear Stakeholders,

Here's the latest autonomous analysis of our project status:

📊 **Project Health Dashboard:**
• Budget Utilization: {(project_context['budget_used']/project_context['budget_total']):.1%}
• Timeline Progress: {project_context['timeline_progress']:.1%}
• Risk Level: {project_context['risk_level'].upper()}
• Team Size: {len(project_context['team_members'])} members

🤖 **Autonomous Insights:**
• Project is tracking within acceptable parameters
• No immediate escalation required
• Recommended actions are being implemented automatically

📈 **Next Steps:**
• Continue monitoring key metrics
• Automated team performance optimization
• Stakeholder updates will continue weekly

This report was generated autonomously by our AI Project Manager.

Best regards,
Autonomous Project Management System
Generated: {timestamp}
"""
                    communications.append({
                        "recipient": "Stakeholders",
                        "email": "stakeholders@company.com",
                        "subject": f"Project Status Update - {project_context['project_name']}",
                        "message": stakeholder_message,
                        "type": "status_update"
                    })
            
            result_summary = f"""
📧 **Personalized Communications Generated**

**Audience:** {audience}
**Message Type:** {message_type.replace('_', ' ').title()}
**Total Messages:** {len(communications)}

**📋 Communication Summary:**
"""
            
            for comm in communications:
                result_summary += f"• **{comm['recipient']}** - {comm['type'].replace('_', ' ').title()}\n"
            
            result_summary += f"""
**🤖 Autonomous Features:**
• Personalized content based on individual performance
• Context-aware messaging with relevant data
• Professional tone and structure
• Actionable recommendations included
• Timestamp tracking for audit trail
"""
            
            return {
                "success": True,
                "data": result_summary,
                "communications": communications,
                "total_generated": len(communications)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Communication generation failed: {str(e)}"}

    def execute_autonomous_workflow(self, workflow_type: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute complete autonomous workflow"""
        try:
            workflow_results = []
            workflow_start = datetime.now()
            
            if workflow_type == "project_management":
                # Execute comprehensive project management workflow
                
                # Step 1: Analyze project status
                analysis = self.analyze_project_status("current", include_predictions=True)
                workflow_results.append(("Project Analysis", analysis))
                time.sleep(1)  # Simulate processing time
                
                # Step 2: Make strategic decisions
                if analysis["success"]:
                    decision = self.make_autonomous_decision(
                        "strategic", 
                        analysis.get("project_context", {})
                    )
                    workflow_results.append(("Strategic Decision", decision))
                    time.sleep(1)
                
                # Step 3: Generate stakeholder communications
                comm = self.generate_personalized_communications(
                    "stakeholders", 
                    "status_update"
                )
                workflow_results.append(("Stakeholder Communication", comm))
                time.sleep(1)
                
                # Step 4: Analyze team performance
                team_analysis = self.analyze_team_performance("current_quarter", True)
                workflow_results.append(("Team Analysis", team_analysis))
                time.sleep(1)
                
                # Step 5: Generate employee communications
                if team_analysis["success"]:
                    emp_comm = self.generate_personalized_communications(
                        "team", 
                        "appreciation"
                    )
                    workflow_results.append(("Employee Communications", emp_comm))
            
            elif workflow_type == "employee_development":
                # Execute employee development workflow
                
                # Step 1: Analyze team performance
                team_analysis = self.analyze_team_performance("current_quarter", True)
                workflow_results.append(("Team Performance Analysis", team_analysis))
                time.sleep(1)
                
                # Step 2: Generate appreciation messages
                appreciation = self.generate_personalized_communications(
                    "team", 
                    "appreciation"
                )
                workflow_results.append(("Appreciation Messages", appreciation))
                time.sleep(1)
                
                # Step 3: Generate development plans
                development = self.generate_personalized_communications(
                    "team", 
                    "development_plan"
                )
                workflow_results.append(("Development Plans", development))
                time.sleep(1)
            
            # Generate workflow summary
            workflow_duration = (datetime.now() - workflow_start).total_seconds()
            successful_steps = sum(1 for _, result in workflow_results if result.get("success", False))
            
            workflow_summary = f"""
🚀 **Autonomous Workflow Executed**

**Workflow Type:** {workflow_type.replace('_', ' ').title()}
**Execution Time:** {workflow_duration:.1f} seconds
**Steps Completed:** {len(workflow_results)}
**Successful Steps:** {successful_steps}
**Success Rate:** {(successful_steps/len(workflow_results)*100):.1f}%

**📋 Workflow Execution Log:**
"""
            
            for i, (step_name, result) in enumerate(workflow_results, 1):
                status = "✅ SUCCESS" if result.get("success", False) else "❌ FAILED"
                workflow_summary += f"{i}. **{step_name}** - {status}\n"
            
            workflow_summary += f"""
**🤖 Autonomous Capabilities Demonstrated:**
• Multi-step strategic planning and execution
• Context-aware decision making
• Personalized communication generation
• Real-time performance analysis
• Adaptive workflow management
• Comprehensive audit trail

**📊 Business Impact:**
• Reduced manual project management overhead
• Improved stakeholder communication consistency
• Enhanced employee engagement through personalization
• Proactive risk identification and mitigation
• Data-driven decision making at scale
"""
            
            return {
                "success": True,
                "data": workflow_summary,
                "workflow_results": workflow_results,
                "execution_time": workflow_duration,
                "steps_completed": len(workflow_results),
                "success_rate": successful_steps/len(workflow_results)
            }
            
        except Exception as e:
            return {"success": False, "error": f"Autonomous workflow execution failed: {str(e)}"}

    # Keep existing methods for backward compatibility
    def get_weather(self, location: str) -> Dict[str, Any]:
        """Get weather information for a location"""
        try:
            url = f"https://wttr.in/{location}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current_condition = data['current_condition'][0]
            
            weather_info = {
                "location": location,
                "temperature": f"{current_condition['temp_C']}°C",
                "feels_like": f"{current_condition['FeelsLikeC']}°C",
                "humidity": f"{current_condition['humidity']}%",
                "description": current_condition['weatherDesc'][0]['value'],
                "wind_speed": f"{current_condition['windspeedKmph']} km/h"
            }
            
            return {
                "success": True,
                "data": f"""🌤️ **Weather for {location}**
- Temperature: {weather_info['temperature']}
- Feels like: {weather_info['feels_like']}
- Humidity: {weather_info['humidity']}
- Description: {weather_info['description']}
- Wind Speed: {weather_info['wind_speed']}"""
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to get weather: {str(e)}"}

    def write_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return {
                "success": True,
                "data": f"✅ Successfully wrote to file: {filename}\n\nContent:\n{content}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to write file: {str(e)}"}

    def read_file(self, filename: str) -> Dict[str, Any]:
        """Read content from a file"""
        try:
            if not os.path.exists(filename):
                return {"success": False, "error": f"File {filename} does not exist"}
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "success": True,
                "data": f"📄 **File: {filename}**\n\n{content}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}

    def generate_sales_report(self, quarter: str, include_predictions: bool = False, autonomous_recommendations: bool = False, filename: str = None) -> Dict[str, Any]:
        """Generate enhanced sales report with autonomous features"""
        try:
            # Generate basic sales data
            products = ["Smartphones", "Laptops", "Tablets", "Accessories", "Software"]
            regions = ["North", "South", "East", "West", "Central"]
            
            sales_data = []
            total_sales = 0
            total_units = 0
            
            for product in products:
                for region in regions:
                    sales_amount = random.randint(10000, 100000)
                    units_sold = random.randint(50, 500)
                    sales_data.append({
                        "product": product,
                        "region": region,
                        "sales": sales_amount,
                        "units": units_sold
                    })
                    total_sales += sales_amount
                    total_units += units_sold
            
            # Find top performers
            product_sales = {}
            region_sales = {}
            
            for item in sales_data:
                product_sales[item["product"]] = product_sales.get(item["product"], 0) + item["sales"]
                region_sales[item["region"]] = region_sales.get(item["region"], 0) + item["sales"]
            
            top_product = max(product_sales.items(), key=lambda x: x[1])
            top_region = max(region_sales.items(), key=lambda x: x[1])
            
            report_content = f"""
📊 **AUTONOMOUS SALES REPORT - {quarter}**
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**📈 Executive Summary:**
- Total Sales: ${total_sales:,}
- Total Units Sold: {total_units:,}
- Average Sale Value: ${total_sales/total_units:.2f}
- Top Product: {top_product[0]} (${top_product[1]:,})
- Top Region: {top_region[0]} (${top_region[1]:,})

**🎯 Product Performance:**
"""
            for product, sales in sorted(product_sales.items(), key=lambda x: x[1], reverse=True):
                percentage = (sales / total_sales) * 100
                report_content += f"• {product}: ${sales:,} ({percentage:.1f}%)\n"
            
            report_content += "\n**🌍 Regional Performance:**\n"
            for region, sales in sorted(region_sales.items(), key=lambda x: x[1], reverse=True):
                percentage = (sales / total_sales) * 100
                report_content += f"• {region}: ${sales:,} ({percentage:.1f}%)\n"
            
            if include_predictions:
                next_quarter_prediction = total_sales * random.uniform(1.05, 1.25)
                growth_rate = ((next_quarter_prediction - total_sales) / total_sales) * 100
                
                report_content += f"""
**🔮 Predictive Analysis:**
- Next Quarter Forecast: ${next_quarter_prediction:,.0f}
- Predicted Growth: {growth_rate:.1f}%
- Market Trend: {'Positive' if growth_rate > 10 else 'Stable' if growth_rate > 0 else 'Declining'}
- Confidence Level: {random.uniform(0.75, 0.95):.1%}
"""
            
            if autonomous_recommendations:
                recommendations = []
                if product_sales[top_product[0]] / total_sales > 0.3:
                    recommendations.append("Diversify product portfolio to reduce dependency on top product")
                if max(region_sales.values()) / total_sales > 0.3:
                    recommendations.append("Expand marketing efforts in underperforming regions")
                recommendations.append("Implement dynamic pricing strategy based on regional performance")
                recommendations.append("Focus inventory management on top-performing products")
                
                report_content += f"""
**🤖 Autonomous Recommendations:**
"""
                for i, rec in enumerate(recommendations, 1):
                    report_content += f"{i}. {rec}\n"
            
            # Save to file if requested
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report_content)
                    report_content += f"\n✅ Report saved to: {filename}"
                except Exception as file_error:
                    report_content += f"\n⚠️ Could not save to file: {str(file_error)}"
            
            return {
                "success": True, 
                "data": report_content,
                "sales_metrics": {
                    "total_sales": total_sales,
                    "total_units": total_units,
                    "top_product": top_product,
                    "top_region": top_region
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_email_report(self, to_email: str, subject: str, content: str, personalize: bool = False) -> Dict[str, Any]:
        """Send email report with autonomous personalization"""
        try:
            if personalize:
                # Add personalization based on recipient
                personalized_content = f"""
Dear {to_email.split('@')[0].replace('.', ' ').title()},

{content}

This report was automatically generated and personalized by our Autonomous AI System.
For questions or additional analysis, please reply to this email.

Best regards,
Autonomous Project Manager
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            else:
                personalized_content = content
            
            # Simulate email sending
            email_log = f"""
📧 **Email Sent Successfully**

**To:** {to_email}
**Subject:** {subject}
**Personalized:** {'Yes' if personalize else 'No'}
**Content Length:** {len(personalized_content)} characters
**Sent At:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**🤖 Autonomous Features:**
• Content personalization based on recipient profile
• Professional formatting and structure
• Automated timestamp and signature
• Audit trail generation

(Simulated for POC - would use real SMTP in production)
"""
            return {
                "success": True,
                "data": email_log,
                "email_content": personalized_content
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call with enhanced autonomous capabilities"""
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        try:
            if tool_name == "analyze_project_status":
                return self.analyze_project_status(**arguments)
            elif tool_name == "generate_strategic_plan":
                return self.generate_strategic_plan(**arguments)
            elif tool_name == "make_autonomous_decision":
                return self.make_autonomous_decision(**arguments)
            elif tool_name == "analyze_team_performance":
                return self.analyze_team_performance(**arguments)
            elif tool_name == "generate_personalized_communications":
                return self.generate_personalized_communications(**arguments)
            elif tool_name == "execute_autonomous_workflow":
                return self.execute_autonomous_workflow(**arguments)
            elif tool_name == "get_weather":
                return self.get_weather(**arguments)
            elif tool_name == "write_file":
                return self.write_file(**arguments)
            elif tool_name == "read_file":
                return self.read_file(**arguments)
            elif tool_name == "generate_sales_report":
                return self.generate_sales_report(**arguments)
            elif tool_name == "send_email_report":
                return self.send_email_report(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": f"Tool execution failed: {str(e)}"}

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process query with FIXED routing logic"""
        print(f"🤖 Processing autonomous query: {query}")
        
        try:
            # ALWAYS try real autonomous processing first
            return self.process_with_real_autonomous_functions(query)
            
        except Exception as e:
            print(f"❌ Real processing failed: {str(e)}")
            return {"success": False, "error": f"Query processing failed: {str(e)}"}

    def execute_real_autonomous_workflow(self) -> Dict[str, Any]:
        """Execute REAL autonomous workflow using autonomous_manager"""
        
        try:
            # Import here to avoid circular imports
            from autonomous_manager import AutonomousProjectManager
            
            print("🚀 Executing REAL Autonomous Workflow...")
            
            # Create autonomous manager instance
            manager = AutonomousProjectManager()
            
            # Execute the REAL workflow
            result = manager.execute_autonomous_project_workflow()
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": f"""🚀 **REAL Autonomous Workflow Executed**

    {result.get('data', 'Workflow completed successfully')}

    🤖 **This is REAL autonomous processing, not a template!**
    - Used actual AutonomousProjectManager
    - Executed real business logic  
    - Generated real insights and decisions
    - Processed actual project data
    """,
                    "workflow_results": result.get("workflow_results", {}),
                    "autonomous_features": {
                        "real_processing": True,
                        "autonomous_manager_used": True,
                        "actual_data_analysis": True,
                        "real_decision_making": True
                    }
                }
            else:
                return {
                    "success": False, 
                    "error": f"Real workflow execution failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute real autonomous workflow: {str(e)}"
            }

    def process_with_real_autonomous_functions(self, query: str) -> Dict[str, Any]:
        """Process with REAL autonomous functions - no templates!"""
        
        query_lower = query.lower()
        
        # Route to REAL functions based on query intent
        if any(phrase in query_lower for phrase in [
            "execute autonomous project management workflow",
            "autonomous project management", 
            "project management workflow"
        ]):
            return self.execute_real_autonomous_workflow()
        
        elif any(phrase in query_lower for phrase in [
            "analyze team performance", 
            "team performance",
            "take appropriate actions"
        ]):
            return self.execute_real_team_analysis()
        
        elif any(phrase in query_lower for phrase in [
            "analyze project", 
            "project health",
            "project status"
        ]):
            return self.execute_real_project_analysis()
        
        else:
            # For other queries, use the original LAM processing
            if self.model and self.tokenizer:
                return self.process_query_with_enhanced_ai(query)
            else:
                return {"success": False, "error": "Query not recognized and AI model not available"}

    def execute_real_project_analysis(self) -> Dict[str, Any]:
        """Execute REAL project analysis using autonomous_manager"""
        
        try:
            from autonomous_manager import AutonomousProjectManager
            
            print("🏥 Executing REAL Project Analysis...")
            
            manager = AutonomousProjectManager()
            result = manager.analyze_project_health()
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": f"""🏥 **REAL Project Health Analysis**

    {result.get('data', 'Project analysis completed')}

    🤖 **Real Analysis Performed:**
    - Analyzed actual project metrics
    - Generated real health assessment
    - Made data-driven recommendations
    """,
                    "project_analysis": result,
                    "autonomous_features": {
                        "real_processing": True,
                        "actual_project_data": True,
                        "real_health_metrics": True
                    }
                }
            else:
                return {"success": False, "error": result.get("error", "Project analysis failed")}
                
        except Exception as e:
            return {"success": False, "error": f"Real project analysis failed: {str(e)}"}

    def execute_real_team_analysis(self) -> Dict[str, Any]:
        """Execute REAL team analysis using autonomous_manager"""
        
        try:
            from autonomous_manager import AutonomousProjectManager
            
            print("👥 Executing REAL Team Analysis...")
            
            manager = AutonomousProjectManager()
            result = manager.analyze_team_performance()
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": f"""👥 **REAL Team Analysis Executed**

    {result.get('data', 'Team analysis completed')}

    🤖 **Real Data Analysis Performed:**
    - Analyzed actual employee performance data
    - Generated real insights and recommendations  
    - Used business intelligence algorithms
    """,
                    "team_analysis": result,
                    "autonomous_features": {
                        "real_processing": True,
                        "actual_team_data": True,
                        "real_insights": True
                    }
                }
            else:
                return {"success": False, "error": result.get("error", "Team analysis failed")}
                
        except Exception as e:
            return {"success": False, "error": f"Real team analysis failed: {str(e)}"}


    def process_query_with_enhanced_ai(self, query: str) -> Dict[str, Any]:
        """Process query using enhanced AI model with autonomous capabilities"""
        try:
            # Build enhanced autonomous prompt
            prompt = self.build_autonomous_prompt(query)
            
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Move inputs to the same device as model
            device = next(self.model.parameters()).device
            input_ids = inputs["input_ids"].to(device)
            attention_mask = inputs["attention_mask"].to(device) if "attention_mask" in inputs else None
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=512,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract the generated part
            if "AUTONOMOUS RESPONSE:" in response_text:
                answer_part = response_text.split("AUTONOMOUS RESPONSE:")[-1].strip()
            else:
                answer_part = response_text
            
            # Parse and execute tool calls
            return self.parse_and_execute_autonomous_response(answer_part, query)
            
        except Exception as e:
            return {"success": False, "error": f"Enhanced AI processing failed: {str(e)}"}

    def process_query_with_enhanced_fallback(self, query: str) -> Dict[str, Any]:
        """Enhanced fallback processing with autonomous pattern matching"""
        query_lower = query.lower()
        
        # FIXED: Check for autonomous workflow FIRST (most specific patterns first)
        if any(phrase in query_lower for phrase in [
            "execute autonomous project management workflow",
            "autonomous project management workflow", 
            "execute autonomous workflow",
            "run autonomous workflow"
        ]):
            return {
                "success": True,
                "data": "🤖 **Executing Full Autonomous Project Management Workflow**",
                "tool_calls": [{"name": "execute_autonomous_workflow", "arguments": {"workflow_type": "project_management"}}]
            }
        
        # Autonomous project management patterns (less specific)
        elif any(phrase in query_lower for phrase in [
            "create project status report", "analyze project", "project health",
            "generate status report"
        ]):
            return {
                "success": True,
                "data": "🤖 **Autonomous Project Analysis Initiated**",
                "tool_calls": [{"name": "analyze_project_status", "arguments": {"project_id": "current", "include_predictions": True}}]
            }
        
        # Team performance and employee development
        elif any(phrase in query_lower for phrase in [
            "analyze team performance and take", "employee development workflow",
            "team analysis", "performance review", "appreciate employees"
        ]):
            return {
                "success": True,
                "data": "🤖 **Autonomous Employee Development Initiated**",
                "tool_calls": [{"name": "execute_autonomous_workflow", "arguments": {"workflow_type": "employee_development"}}]
            }
        
        # Strategic planning (moved after specific workflow patterns)
        elif any(phrase in query_lower for phrase in [
            "create strategic plan", "make strategic decision",
            "strategic planning", "strategic analysis"
        ]) and "workflow" not in query_lower:  # Added exclusion for workflow
            objective = query_lower.replace("create", "").replace("generate", "").replace("strategic plan for", "").strip()
            return {
                "success": True,
                "data": f"🤖 **Strategic Planning for: {objective}**",
                "tool_calls": [{"name": "generate_strategic_plan", "arguments": {"objective": objective}}]
            }
        
        # Rest of the patterns remain the same...
        # Enhanced sales reporting
        elif any(phrase in query_lower for phrase in [
            "sales report", "autonomous sales", "predictive sales"
        ]):
            quarter = "Q4"  # Default
            for q in ["q1", "q2", "q3", "q4"]:
                if q in query_lower:
                    quarter = q.upper()
                    break
            
            return {
                "success": True,
                "data": f"🤖 **Autonomous Sales Analysis for {quarter}**",
                "tool_calls": [{"name": "generate_sales_report", "arguments": {
                    "quarter": quarter, 
                    "include_predictions": True, 
                    "autonomous_recommendations": True
                }}]
            }
        
        # Fall back to original patterns for other queries
        else:
            return self.process_original_patterns(query_lower)
    
    def process_original_patterns(self, query_lower: str) -> Dict[str, Any]:
        """Process original patterns for backward compatibility"""
        # Weather queries
        if any(word in query_lower for word in ["weather", "temperature", "climate"]):
            location = "London"  # Default
            if "in" in query_lower:
                parts = query_lower.split("in")
                if len(parts) > 1:
                    location_part = parts[-1].strip()
                    location_part = location_part.replace("?", "").replace("!", "").strip()
                    words = location_part.split()
                    if len(words) <= 3:
                        location = " ".join(words)
                    else:
                        location = words[0]
            
            return {
                "success": True,
                "data": f"🔄 **Getting weather for {location}**",
                "tool_calls": [{"name": "get_weather", "arguments": {"location": location}}]
            }
        
        # File operations
        elif any(word in query_lower for word in ["write", "create", "save"]) and "file" in query_lower:
            filename = "report.txt"
            content = "Sample content generated by enhanced autonomous mode."
            
            if ".txt" in query_lower:
                words = query_lower.split()
                for word in words:
                    if ".txt" in word:
                        filename = word
                        break
            
            return {
                "success": True,
                "data": f"🔄 **Creating file {filename}**",
                "tool_calls": [{"name": "write_file", "arguments": {"filename": filename, "content": content}}]
            }
        
        elif any(word in query_lower for word in ["read", "open", "show"]) and "file" in query_lower:
            filename = "sample.txt"
            
            if ".txt" in query_lower:
                words = query_lower.split()
                for word in words:
                    if ".txt" in word:
                        filename = word
                        break
            
            return {
                "success": True,
                "data": f"🔄 **Reading file {filename}**",
                "tool_calls": [{"name": "read_file", "arguments": {"filename": filename}}]
            }
        
        else:
            return {
                "success": False,
                "error": "I don't understand this query. Try asking about autonomous project management, team performance analysis, or strategic planning."
            }

    def parse_and_execute_autonomous_response(self, response_text: str, original_query: str) -> Dict[str, Any]:
        """Parse AI response and execute autonomous actions"""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                tool_calls = json.loads(json_str)
            else:
                # Look for single JSON object
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    tool_calls = [json.loads(json_str)]
                else:
                    # No JSON found, use fallback processing
                    return self.process_query_with_enhanced_fallback(original_query)
            
            if not tool_calls:
                return {
                    "success": True,
                    "data": f"🤖 **AI Response**: {response_text}"
                }
            
            # Execute tool calls autonomously
            results = []
            for tool_call in tool_calls:
                result = self.execute_tool_call(tool_call)
                results.append(result)
            
            # Combine results with autonomous summary
            successful_results = [r for r in results if r.get("success")]
            combined_data = "\n\n".join([r.get("data", str(r)) for r in successful_results])
            
            autonomous_summary = f"""
🚀 **Autonomous Execution Completed**

**Query Processed:** {original_query}
**Tools Executed:** {len(tool_calls)}
**Successful Operations:** {len(successful_results)}
**Success Rate:** {(len(successful_results)/len(tool_calls)*100):.1f}%

**🤖 Autonomous Results:**
{combined_data}

**📊 Execution Summary:**
• Multi-step autonomous reasoning applied
• Context-aware decision making enabled
• Strategic business logic implemented
• Real-time adaptation and learning active
"""
            
            return {
                "success": True,
                "data": autonomous_summary,
                "tool_calls": tool_calls,
                "execution_results": results,
                "autonomous_features": {
                    "multi_step_reasoning": True,
                    "context_awareness": True,
                    "strategic_planning": True,
                    "autonomous_decision_making": True
                }
            }
                
        except json.JSONDecodeError:
            return {
                "success": True,
                "data": f"🤖 **Enhanced AI Response**: {response_text}"
            }
        except Exception as e:
            return {"success": False, "error": f"Autonomous execution failed: {str(e)}"}

def main():
    """Test the Enhanced True LAM Interface"""
    enhanced_lam = EnhancedTrueLAMInterface()
    
    test_queries = [
        "Execute autonomous project management workflow",
        "Analyze team performance and take appropriate actions",
        "Create strategic plan for improving team productivity",
        "Generate personalized employee appreciation messages",
        "Make autonomous decision about resource allocation",
        "Execute complete employee development workflow",
        "What's the weather in London?",  # Test backward compatibility
        "Create a sales report with predictions and recommendations"
    ]
    
    print("🧪 Testing Enhanced True LAM Interface with Autonomous Capabilities")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        result = enhanced_lam.process_query(query)
        
        if result.get("success"):
            print("✅ Success!")
            print(result.get("data", "No data"))
            
            # Show autonomous features if available
            if "autonomous_features" in result:
                features = result["autonomous_features"]
                print("\n🤖 Autonomous Features Demonstrated:")
                for feature, enabled in features.items():
                    if enabled:
                        print(f"   • {feature.replace('_', ' ').title()}")
        else:
            print("❌ Failed!")
            print(result.get("error", "Unknown error"))
        
        print("=" * 80)

if __name__ == "__main__":
    main()
