#!/usr/bin/env python3
"""Decision-making engine facade wrapping existing planners/engines."""
from typing import Dict, Any

try:
    from enhanced_lam_integration import AutonomousDecisionEngine, StrategicPlanner, AutonomousMemory
except Exception:
    AutonomousDecisionEngine = None
    StrategicPlanner = None
    AutonomousMemory = None


class AutonomousAgent:
    def __init__(self):
        self.memory = AutonomousMemory() if AutonomousMemory else None
        self.planner = StrategicPlanner(self.memory) if StrategicPlanner and self.memory else None
        self.engine = AutonomousDecisionEngine(self.memory) if AutonomousDecisionEngine and self.memory else None

    def strategic_plan(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.planner:
            return {"success": False, "error": "Planner not available"}
        tasks = self.planner.create_strategic_plan(goal, context)
        return {"success": True, "tasks": [t.__dict__ for t in tasks]}

    def decide(self, context: Dict[str, Any], decision_type: str) -> Dict[str, Any]:
        if not self.engine:
            return {"success": False, "error": "Decision engine not available"}
        from enhanced_lam_integration import DecisionType
        return self.engine.make_autonomous_decision(context, DecisionType(decision_type))

