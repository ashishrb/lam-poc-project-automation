#!/usr/bin/env python3
"""
Financial Controls Service
Manages budget thresholds, cost tracking, and financial governance.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class BudgetStatus(str, Enum):
    """Budget status levels"""
    UNDER_BUDGET = "under_budget"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OVER_BUDGET = "over_budget"
    CRITICAL = "critical"


class AlertLevel(str, Enum):
    """Alert levels for budget monitoring"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"


@dataclass
class BudgetThreshold:
    """Budget threshold configuration"""
    threshold_id: str
    project_id: int
    threshold_type: str  # "percentage" or "amount"
    threshold_value: float
    alert_level: AlertLevel
    notification_emails: List[str]
    created_at: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class CostEntry:
    """Cost entry for tracking"""
    entry_id: str
    project_id: int
    category: str
    amount: float
    currency: Currency
    description: str
    date: datetime
    approved_by: Optional[int] = None
    invoice_number: Optional[str] = None
    vendor: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class BudgetSummary:
    """Budget summary for a project"""
    project_id: int
    project_name: str
    total_budget: float
    spent_amount: float
    remaining_amount: float
    utilization_percentage: float
    status: BudgetStatus
    currency: Currency
    last_updated: datetime
    alerts: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.alerts is None:
            self.alerts = []


class FinancialControls:
    """Financial controls and budget management service"""
    
    def __init__(self):
        self.budgets = {}
        self.thresholds = {}
        self.cost_entries = {}
        self.alert_history = []
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 0.85,
            "GBP": 0.73,
            "INR": 74.5,
            "CAD": 1.25
        }
    
    async def create_budget(
        self,
        project_id: int,
        project_name: str,
        total_budget: float,
        currency: Currency = Currency.USD,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create a new budget for a project"""
        try:
            budget_id = f"budget_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            budget = {
                "budget_id": budget_id,
                "project_id": project_id,
                "project_name": project_name,
                "total_budget": float(total_budget),
                "spent_amount": 0.0,
                "currency": currency,
                "start_date": start_date or datetime.now(),
                "end_date": end_date,
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "status": BudgetStatus.UNDER_BUDGET
            }
            
            self.budgets[project_id] = budget
            
            logger.info(f"Created budget for project {project_name}: {total_budget} {currency.value}")
            
            # Convert budget dict to ensure all values are JSON serializable
            budget_dict = {
                "budget_id": budget["budget_id"],
                "project_id": budget["project_id"],
                "project_name": budget["project_name"],
                "total_budget": float(budget["total_budget"]),
                "spent_amount": float(budget["spent_amount"]),
                "currency": budget["currency"].value,
                "start_date": budget["start_date"].isoformat(),
                "end_date": budget["end_date"].isoformat() if budget["end_date"] else None,
                "created_at": budget["created_at"].isoformat(),
                "last_updated": budget["last_updated"].isoformat(),
                "status": budget["status"].value
            }
            
            return {
                "success": True,
                "budget_id": budget_id,
                "project_id": project_id,
                "budget": budget_dict
            }
            
        except Exception as e:
            logger.error(f"Error creating budget for project {project_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def add_cost_entry(
        self,
        project_id: int,
        category: str,
        amount: float,
        description: str,
        currency: Currency = Currency.USD,
        approved_by: Optional[int] = None,
        invoice_number: Optional[str] = None,
        vendor: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Add a cost entry to a project"""
        try:
            if project_id not in self.budgets:
                return {
                    "success": False,
                    "error": f"Budget not found for project {project_id}"
                }
            
            entry_id = f"cost_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            cost_entry = CostEntry(
                entry_id=entry_id,
                project_id=project_id,
                category=category,
                amount=float(amount),
                currency=currency,
                description=description,
                date=datetime.now(),
                approved_by=approved_by,
                invoice_number=invoice_number,
                vendor=vendor,
                tags=tags or []
            )
            
            # Convert to USD if different currency
            usd_amount = self._convert_to_usd(amount, currency)
            
            # Add to cost entries
            if project_id not in self.cost_entries:
                self.cost_entries[project_id] = []
            self.cost_entries[project_id].append(cost_entry)
            
            # Update budget
            budget = self.budgets[project_id]
            budget["spent_amount"] += usd_amount
            budget["last_updated"] = datetime.now()
            
            # Update budget status
            await self._update_budget_status(project_id)
            
            # Check thresholds
            await self._check_thresholds(project_id)
            
            logger.info(f"Added cost entry {entry_id} for project {project_id}: {amount} {currency.value}")
            
            # Convert cost entry to JSON serializable format
            cost_entry_dict = {
                "entry_id": cost_entry.entry_id,
                "project_id": cost_entry.project_id,
                "category": cost_entry.category,
                "amount": float(cost_entry.amount),
                "currency": cost_entry.currency.value,
                "description": cost_entry.description,
                "date": cost_entry.date.isoformat(),
                "approved_by": cost_entry.approved_by,
                "invoice_number": cost_entry.invoice_number,
                "vendor": cost_entry.vendor,
                "tags": cost_entry.tags
            }
            
            return {
                "success": True,
                "entry_id": entry_id,
                "cost_entry": cost_entry_dict,
                "budget_impact": {
                    "spent_amount": float(budget["spent_amount"]),
                    "remaining_amount": float(budget["total_budget"] - budget["spent_amount"]),
                    "utilization_percentage": float((budget["spent_amount"] / budget["total_budget"]) * 100)
                }
            }
            
        except Exception as e:
            logger.error(f"Error adding cost entry for project {project_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def set_budget_threshold(
        self,
        project_id: int,
        threshold_type: str,
        threshold_value: float,
        alert_level: AlertLevel,
        notification_emails: List[str]
    ) -> Dict[str, Any]:
        """Set a budget threshold for monitoring"""
        try:
            if project_id not in self.budgets:
                return {
                    "success": False,
                    "error": f"Budget not found for project {project_id}"
                }
            
            threshold_id = f"threshold_{project_id}_{threshold_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            threshold = BudgetThreshold(
                threshold_id=threshold_id,
                project_id=project_id,
                threshold_type=threshold_type,
                threshold_value=threshold_value,
                alert_level=alert_level,
                notification_emails=notification_emails
            )
            
            if project_id not in self.thresholds:
                self.thresholds[project_id] = []
            self.thresholds[project_id].append(threshold)
            
            logger.info(f"Set budget threshold for project {project_id}: {threshold_type} at {threshold_value}")
            
            return {
                "success": True,
                "threshold_id": threshold_id,
                "threshold": threshold.__dict__
            }
            
        except Exception as e:
            logger.error(f"Error setting budget threshold for project {project_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_budget_summary(self, project_id: int) -> Dict[str, Any]:
        """Get budget summary for a project"""
        try:
            if project_id not in self.budgets:
                return {
                    "success": False,
                    "error": f"Budget not found for project {project_id}"
                }
            
            budget = self.budgets[project_id]
            spent_amount = budget["spent_amount"]
            total_budget = budget["total_budget"]
            remaining_amount = total_budget - spent_amount
            utilization_percentage = float((spent_amount / total_budget) * 100)
            
            # Get alerts
            alerts = []
            if project_id in self.thresholds:
                for threshold in self.thresholds[project_id]:
                    if threshold.is_active:
                        if threshold.threshold_type == "percentage":
                            if utilization_percentage >= threshold.threshold_value:
                                alerts.append({
                                    "threshold_id": threshold.threshold_id,
                                    "alert_level": threshold.alert_level.value,
                                    "message": f"Budget utilization {utilization_percentage:.1f}% exceeds threshold {threshold.threshold_value}%",
                                    "threshold_value": threshold.threshold_value,
                                    "current_value": utilization_percentage
                                })
                        elif threshold.threshold_type == "amount":
                            if spent_amount >= Decimal(str(threshold.threshold_value)):
                                alerts.append({
                                    "threshold_id": threshold.threshold_id,
                                    "alert_level": threshold.alert_level.value,
                                    "message": f"Spent amount ${float(spent_amount):,.2f} exceeds threshold ${threshold.threshold_value:,.2f}",
                                    "threshold_value": threshold.threshold_value,
                                    "current_value": float(spent_amount)
                                })
            
            summary = BudgetSummary(
                project_id=project_id,
                project_name=budget["project_name"],
                total_budget=total_budget,
                spent_amount=spent_amount,
                remaining_amount=remaining_amount,
                utilization_percentage=utilization_percentage,
                status=budget["status"],
                currency=budget["currency"],
                last_updated=budget["last_updated"],
                alerts=alerts
            )
            
            return {
                "success": True,
                "budget_summary": summary.__dict__
            }
            
        except Exception as e:
            logger.error(f"Error getting budget summary for project {project_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio-wide budget summary"""
        try:
            portfolio_stats = {
                "total_projects": len(self.budgets),
                "total_budget": 0.0,
                "total_spent": 0.0,
                "total_remaining": 0.0,
                "average_utilization": 0.0,
                "projects_at_risk": 0,
                "projects_over_budget": 0,
                "currency_breakdown": {},
                "status_breakdown": {}
            }
            
            total_utilization = 0.0
            
            for project_id, budget in self.budgets.items():
                total_budget = float(budget["total_budget"])
                spent_amount = float(budget["spent_amount"])
                utilization = float((spent_amount / total_budget) * 100)
                
                portfolio_stats["total_budget"] += total_budget
                portfolio_stats["total_spent"] += spent_amount
                total_utilization += utilization
                
                # Status breakdown
                status = budget["status"].value
                portfolio_stats["status_breakdown"][status] = portfolio_stats["status_breakdown"].get(status, 0) + 1
                
                if status in ["at_risk", "over_budget", "critical"]:
                    portfolio_stats["projects_at_risk"] += 1
                
                if status in ["over_budget", "critical"]:
                    portfolio_stats["projects_over_budget"] += 1
                
                # Currency breakdown
                currency = budget["currency"].value
                if currency not in portfolio_stats["currency_breakdown"]:
                    portfolio_stats["currency_breakdown"][currency] = {
                        "total_budget": 0.0,
                        "total_spent": 0.0
                    }
                portfolio_stats["currency_breakdown"][currency]["total_budget"] += total_budget
                portfolio_stats["currency_breakdown"][currency]["total_spent"] += spent_amount
            
            portfolio_stats["total_remaining"] = portfolio_stats["total_budget"] - portfolio_stats["total_spent"]
            portfolio_stats["average_utilization"] = total_utilization / len(self.budgets) if self.budgets else 0.0
            
            return {
                "success": True,
                "portfolio_summary": portfolio_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cost_analysis(
        self,
        project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cost analysis with filtering options"""
        try:
            analysis = {
                "total_cost": 0.0,
                "cost_by_category": {},
                "cost_by_month": {},
                "cost_by_vendor": {},
                "top_expenses": [],
                "currency_breakdown": {}
            }
            
            all_entries = []
            
            # Collect entries based on filters
            if project_id:
                if project_id in self.cost_entries:
                    all_entries.extend(self.cost_entries[project_id])
            else:
                for project_entries in self.cost_entries.values():
                    all_entries.extend(project_entries)
            
            # Apply date filters
            if start_date:
                all_entries = [entry for entry in all_entries if entry.date >= start_date]
            if end_date:
                all_entries = [entry for entry in all_entries if entry.date <= end_date]
            
            # Apply category filter
            if category:
                all_entries = [entry for entry in all_entries if entry.category == category]
            
            # Analyze entries
            for entry in all_entries:
                usd_amount = self._convert_to_usd(float(entry.amount), entry.currency)
                analysis["total_cost"] += usd_amount
                
                # Category breakdown
                if entry.category not in analysis["cost_by_category"]:
                    analysis["cost_by_category"][entry.category] = 0.0
                analysis["cost_by_category"][entry.category] += float(usd_amount)
                
                # Monthly breakdown
                month_key = entry.date.strftime("%Y-%m")
                if month_key not in analysis["cost_by_month"]:
                    analysis["cost_by_month"][month_key] = 0.0
                analysis["cost_by_month"][month_key] += float(usd_amount)
                
                # Vendor breakdown
                if entry.vendor:
                    if entry.vendor not in analysis["cost_by_vendor"]:
                        analysis["cost_by_vendor"][entry.vendor] = 0.0
                    analysis["cost_by_vendor"][entry.vendor] += float(usd_amount)
                
                # Currency breakdown
                currency = entry.currency.value
                if currency not in analysis["currency_breakdown"]:
                    analysis["currency_breakdown"][currency] = 0.0
                analysis["currency_breakdown"][currency] += float(entry.amount)
                
                # Top expenses
                analysis["top_expenses"].append({
                    "entry_id": entry.entry_id,
                    "project_id": entry.project_id,
                    "category": entry.category,
                    "amount": float(entry.amount),
                    "currency": entry.currency.value,
                    "description": entry.description,
                    "date": entry.date.isoformat(),
                    "vendor": entry.vendor
                })
            
            # Sort top expenses by amount
            analysis["top_expenses"].sort(key=lambda x: x["amount"], reverse=True)
            analysis["top_expenses"] = analysis["top_expenses"][:10]  # Top 10
            
            return {
                "success": True,
                "cost_analysis": analysis,
                "filters_applied": {
                    "project_id": project_id,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "category": category
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cost analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_budget_status(self, project_id: int):
        """Update budget status based on utilization"""
        try:
            budget = self.budgets[project_id]
            utilization_percentage = float((budget["spent_amount"] / budget["total_budget"]) * 100)
            
            if utilization_percentage < 50:
                budget["status"] = BudgetStatus.UNDER_BUDGET
            elif utilization_percentage < 75:
                budget["status"] = BudgetStatus.ON_TRACK
            elif utilization_percentage < 90:
                budget["status"] = BudgetStatus.AT_RISK
            elif utilization_percentage < 100:
                budget["status"] = BudgetStatus.OVER_BUDGET
            else:
                budget["status"] = BudgetStatus.CRITICAL
            
        except Exception as e:
            logger.error(f"Error updating budget status for project {project_id}: {str(e)}")
    
    async def _check_thresholds(self, project_id: int):
        """Check if any thresholds have been exceeded"""
        try:
            if project_id not in self.thresholds:
                return
            
            budget = self.budgets[project_id]
            spent_amount = budget["spent_amount"]
            total_budget = budget["total_budget"]
            utilization_percentage = float((spent_amount / total_budget) * 100)
            
            for threshold in self.thresholds[project_id]:
                if not threshold.is_active:
                    continue
                
                triggered = False
                if threshold.threshold_type == "percentage":
                    if utilization_percentage >= threshold.threshold_value:
                        triggered = True
                elif threshold.threshold_type == "amount":
                    if spent_amount >= threshold.threshold_value:
                        triggered = True
                
                if triggered:
                    alert = {
                        "alert_id": f"alert_{threshold.threshold_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "project_id": project_id,
                        "threshold_id": threshold.threshold_id,
                        "alert_level": threshold.alert_level.value,
                        "message": f"Budget threshold exceeded for project {budget['project_name']}",
                        "threshold_value": threshold.threshold_value,
                        "current_value": utilization_percentage if threshold.threshold_type == "percentage" else float(spent_amount),
                        "created_at": datetime.now(),
                        "notification_emails": threshold.notification_emails
                    }
                    
                    self.alert_history.append(alert)
                    logger.warning(f"Budget threshold exceeded: {alert['message']}")
            
        except Exception as e:
            logger.error(f"Error checking thresholds for project {project_id}: {str(e)}")
    
    def _convert_to_usd(self, amount: float, currency: Currency) -> float:
        """Convert amount to USD using exchange rates"""
        if currency == Currency.USD:
            return amount
        
        exchange_rate = self.exchange_rates.get(currency.value, 1.0)
        return round(amount / exchange_rate, 2)
    
    async def get_alert_history(
        self,
        project_id: Optional[int] = None,
        alert_level: Optional[AlertLevel] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get alert history with filtering"""
        try:
            filtered_alerts = self.alert_history.copy()
            
            if project_id:
                filtered_alerts = [alert for alert in filtered_alerts if alert["project_id"] == project_id]
            
            if alert_level:
                filtered_alerts = [alert for alert in filtered_alerts if alert["alert_level"] == alert_level.value]
            
            if start_date:
                filtered_alerts = [alert for alert in filtered_alerts if alert["created_at"] >= start_date]
            
            if end_date:
                filtered_alerts = [alert for alert in filtered_alerts if alert["created_at"] <= end_date]
            
            # Sort by creation date (newest first)
            filtered_alerts.sort(key=lambda x: x["created_at"], reverse=True)
            
            return {
                "success": True,
                "alerts": filtered_alerts,
                "total_alerts": len(filtered_alerts),
                "filters_applied": {
                    "project_id": project_id,
                    "alert_level": alert_level.value if alert_level else None,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting alert history: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global instance and getter function
_financial_controls = None

def get_financial_controls() -> FinancialControls:
    """Get the global financial controls instance"""
    global _financial_controls
    if _financial_controls is None:
        _financial_controls = FinancialControls()
    return _financial_controls
