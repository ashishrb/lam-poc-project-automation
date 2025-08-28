#!/usr/bin/env python3
"""Resource Optimizer - intelligent allocation strategies."""
from typing import Dict, Any


class ResourceOptimizer:
    def optimize(self, utilization: Dict[str, float]) -> Dict[str, Any]:
        over = [k for k, v in utilization.items() if v > 0.9]
        under = [k for k, v in utilization.items() if v < 0.6]
        plan = []
        for o in over:
            for u in under:
                plan.append({"from": o, "to": u, "action": "rebalance"})
        return {"success": True, "plan": plan, "overutilized": over, "underutilized": under}

