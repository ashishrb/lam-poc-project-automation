#!/usr/bin/env python3
"""
Intelligent Communication Engine
Generates role-specific updates and manages escalations.
"""

from typing import List, Dict, Any
from datetime import datetime

try:
    from enhanced_autonomous_pm.core.rag_engine import RAGKnowledgeEngine
except Exception:
    RAGKnowledgeEngine = None


class IntelligentCommunicationEngine:
    def __init__(self):
        self.rag_engine = RAGKnowledgeEngine() if RAGKnowledgeEngine else None

    def generate_personalized_updates(self, audience: str = "stakeholders") -> Dict[str, Any]:
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        base_context = []
        if self.rag_engine:
            ctx = self.rag_engine.enhance_query_with_context("best practices for stakeholder communications", top_k=3)
            if ctx.get("success"):
                base_context = ctx["contexts"]

        def mk(recipient, subject, body, role):
            return {
                "recipient": recipient,
                "subject": subject,
                "message": body + f"\n\nGenerated: {now}",
                "role": role
            }

        docs_hint = "\n\nGuidance: " + " | ".join(c["metadata"].get("type", "doc") for c in base_context) if base_context else ""

        messages = []
        if audience == "stakeholders":
            messages.append(mk("project_manager@company.com", "Weekly Status Update",
                               "Project is on track. Budget and schedule under control." + docs_hint, "project_manager"))
            messages.append(mk("director@company.com", "Executive Summary",
                               "Portfolio risk remains medium. No escalations required." + docs_hint, "director"))
        else:
            messages.append(mk("team@company.com", "Team Appreciation",
                               "Thank you for your efforts. Keep quality high and communicate blockers early." + docs_hint, "team"))

        return {"success": True, "generated": messages, "count": len(messages)}

    def escalation_management(self, risk_level: str = "low", last_update_days: int = 7) -> Dict[str, Any]:
        should_escalate = (risk_level in ["high", "critical"]) or (last_update_days >= 14)
        target = "director" if risk_level == "high" else ("vp" if risk_level == "critical" else "manager")
        plan = []
        if should_escalate:
            plan = [
                {"action": "prepare_brief", "due": "immediate"},
                {"action": "notify_" + target, "due": "immediate"},
                {"action": "schedule_review_meeting", "due": "24h"}
            ]
        return {"success": True, "escalate": should_escalate, "route": target, "plan": plan}

