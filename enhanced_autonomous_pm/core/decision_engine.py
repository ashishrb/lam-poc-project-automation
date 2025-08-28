#!/usr/bin/env python3
"""Decision Engine wrapper to keep autonomous logic separate and reusable."""
from typing import Dict, Any

try:
    from enhanced_lam_integration import AutonomousDecisionEngine as LegacyDecisionEngine, DecisionType
    from enhanced_lam_integration import AutonomousMemory
except Exception:
    LegacyDecisionEngine = None
    DecisionType = None
    AutonomousMemory = None


class DecisionEngine:
    def __init__(self):
        self.memory = AutonomousMemory() if AutonomousMemory else None
        self.engine = LegacyDecisionEngine(self.memory) if LegacyDecisionEngine and self.memory else None

    def decide(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.engine or not DecisionType:
            return {"success": False, "error": "Decision engine unavailable"}
        dec = self.engine.make_autonomous_decision(context, DecisionType(decision_type))
        return {"success": True, "decision": dec}

