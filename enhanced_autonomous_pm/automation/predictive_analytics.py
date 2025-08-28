#!/usr/bin/env python3
"""
Predictive Analytics
Provides simple forecasting stubs for success probability and resource needs.
"""

from typing import Dict, Any, List
import math
import random

try:
    import numpy as np
except Exception:
    np = None


class PredictiveAnalytics:
    def project_success_modeling(self, features: Dict[str, float] = None) -> Dict[str, Any]:
        f = features or {}
        budget_util = max(0.0, min(1.0, f.get('budget_utilization', 0.75)))
        schedule_progress = max(0.0, min(1.0, f.get('schedule_progress', 0.6)))
        quality = max(0.0, min(1.0, (f.get('avg_quality', 8.0) / 10.0)))
        risk = 1.0 - max(0.0, min(1.0, f.get('risk_level', 0.5)))
        score = 0.25 * (1 - abs(budget_util - 0.7)) + 0.25 * schedule_progress + 0.25 * quality + 0.25 * risk
        prob = max(0.0, min(1.0, score))
        return {"success": True, "success_probability": prob, "score": score}

    def resource_optimization(self, demand_forecast: List[int] = None, capacity: int = 10) -> Dict[str, Any]:
        df = demand_forecast or [random.randint(6, 12) for _ in range(6)]
        shortages = [max(0, d - capacity) for d in df]
        surplus = [max(0, capacity - d) for d in df]
        return {
            "success": True,
            "demand_forecast": df,
            "capacity": capacity,
            "shortage_weeks": sum(1 for s in shortages if s > 0),
            "total_shortage": sum(shortages),
            "total_surplus": sum(surplus)
        }

