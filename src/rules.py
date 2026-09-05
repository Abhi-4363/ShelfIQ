"""
ShelfIQ Business Rules & Attention Engine
Transforms factual metrics from AnalyticsEngine into structured business attention items
and decision-support recommendations.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

# Deterministic Severity Priorities
SEVERITY_ORDER = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
    "INFO": 5
}

# Standard Decision-Support Recommendation Templates
RECOMMENDATIONS = {
    "STOCK_OUT_RISK": "Review replenishment for this product immediately to avoid stock-out.",
    "SLOW_MOVING": "Review inventory exposure and consider reducing future replenishment.",
    "OVERSTOCK": "Review excess inventory and consider reducing upcoming replenishment.",
    "SALES_SPIKE": "Review recent sales increase and check whether additional stock may be needed.",
    "SALES_DROP": "Review recent sales performance and investigate the decline."
}

@dataclass
class AttentionItem:
    """Structured representation of a retail operational attention alert."""
    attention_id: str
    attention_type: str        # STOCK_OUT_RISK | SLOW_MOVING | OVERSTOCK | SALES_SPIKE | SALES_DROP
    severity: str              # CRITICAL | HIGH | MEDIUM | LOW | INFO
    product_id: str
    product_name: str
    category: str
    store_id: str
    store_name: str
    metric_summary: str
    evidence: Dict[str, Any]
    recommendation: str
    assumptions: List[str]
    data_sufficiency: str      # SUFFICIENT | LIMITED | INSUFFICIENT

    def to_dict(self) -> Dict[str, Any]:
        """Convert AttentionItem to dictionary."""
        return asdict(self)

class AttentionEngine:
    """
    Business Rules & Attention Engine for ShelfIQ.
    Applies transparent, deterministic rules to AnalyticsEngine outputs.
    Produces prioritized, evidence-backed attention items.
    """
    def __init__(self, analytics_engine):
        self.analytics = analytics_engine

    def generate_stockout_attention_items(self, store_id: Optional[str] = None) -> List[AttentionItem]:
        """Generate attention items for products at stock-out risk."""
        risks = self.analytics.detect_stockout_risks(store_id=store_id)
        items = []

        for r in risks:
            pid = r["product_id"]
            sid = r["store_id"]
            days = r["days_remaining"]
            days_disp = r["days_remaining_display"]

            # Severity determination
            if days is not None and days <= 4.0:
                severity = "CRITICAL"
            elif days is not None and days <= 7.0:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            summary = f"Stock-out risk: {days_disp} days remaining (Stock: {r['current_stock']} units, Daily Sales: {r['average_daily_units_sold']} u/d)"
            
            evidence = {
                "metric": "days_remaining",
                "current_stock": r["current_stock"],
                "average_daily_units_sold": r["average_daily_units_sold"],
                "days_remaining": days,
                "days_remaining_display": days_disp,
                "threshold_used": r["threshold_used"],
                "calculation_period": "Historical 90-day window"
            }

            assumptions = [
                "Average daily sales calculated from historical daily sales data.",
                "Current stock level assumes no immediate unrecorded restocks."
            ]

            items.append(AttentionItem(
                attention_id=f"ATT_STOCKOUT_{sid}_{pid}",
                attention_type="STOCK_OUT_RISK",
                severity=severity,
                product_id=pid,
                product_name=r["product_name"],
                category=r["category"],
                store_id=sid,
                store_name=r["store_name"],
                metric_summary=summary,
                evidence=evidence,
                recommendation=RECOMMENDATIONS["STOCK_OUT_RISK"],
                assumptions=assumptions,
                data_sufficiency=r["data_sufficiency"]
            ))

        return items

    def generate_slow_moving_attention_items(self, store_id: Optional[str] = None) -> List[AttentionItem]:
        """Generate attention items for slow-moving products."""
        slow = self.analytics.detect_slow_moving_products(store_id=store_id)
        items = []

        for s in slow:
            pid = s["product_id"]
            sid = s["store_id"]
            vel = s["average_daily_units_sold"]

            severity = "HIGH" if vel < 0.1 else "MEDIUM"
            summary = f"Slow-moving inventory: velocity of {vel} units/day with {s['current_stock']} units in stock"

            evidence = {
                "metric": "average_daily_units_sold",
                "current_stock": s["current_stock"],
                "average_daily_units_sold": vel,
                "total_units_sold": s["total_units_sold"],
                "comparison_period": s["comparison_period"],
                "threshold_used": s["threshold_used"]
            }

            assumptions = [
                "Product has sufficient historical observation history (>= 14 days).",
                "Sales velocity calculated across the full historical period."
            ]

            items.append(AttentionItem(
                attention_id=f"ATT_SLOW_{sid}_{pid}",
                attention_type="SLOW_MOVING",
                severity=severity,
                product_id=pid,
                product_name=s["product_name"],
                category=s["category"],
                store_id=sid,
                store_name=s["store_name"],
                metric_summary=summary,
                evidence=evidence,
                recommendation=RECOMMENDATIONS["SLOW_MOVING"],
                assumptions=assumptions,
                data_sufficiency=s["data_sufficiency"]
            ))

        return items

    def generate_overstock_attention_items(self, store_id: Optional[str] = None) -> List[AttentionItem]:
        """Generate attention items for overstocked inventory."""
        overstock = self.analytics.detect_overstocked_products(store_id=store_id)
        items = []

        for o in overstock:
            pid = o["product_id"]
            sid = o["store_id"]
            days = o["estimated_days_of_inventory"]
            days_disp = o["estimated_days_display"]
            status = o["overstock_status"]

            if status == "ZERO_SALES_OVERSTOCK" or (days is not None and days > 120):
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            if status == "ZERO_SALES_OVERSTOCK":
                summary = f"Overstock alert: Zero sales history with {o['current_stock']} units in stock"
            else:
                summary = f"Overstock alert: Estimated {days_disp} of inventory remaining"

            evidence = {
                "metric": "estimated_days_of_inventory",
                "current_stock": o["current_stock"],
                "average_daily_units_sold": o["average_daily_units_sold"],
                "estimated_days": days,
                "estimated_days_of_inventory": days,
                "estimated_days_display": days_disp,
                "overstock_status": status,
                "threshold_used": o["threshold_used"]
            }

            assumptions = [
                "Sales velocity assumes continuation of current daily sales rate.",
                "Zero-sales overstock flagged due to high stock volume without recent sales activity."
            ]

            items.append(AttentionItem(
                attention_id=f"ATT_OVERSTOCK_{sid}_{pid}",
                attention_type="OVERSTOCK",
                severity=severity,
                product_id=pid,
                product_name=o["product_name"],
                category=o["category"],
                store_id=sid,
                store_name=o["store_name"],
                metric_summary=summary,
                evidence=evidence,
                recommendation=RECOMMENDATIONS["OVERSTOCK"],
                assumptions=assumptions,
                data_sufficiency=o["data_sufficiency"]
            ))

        return items

    def generate_spike_attention_items(self, store_id: Optional[str] = None) -> List[AttentionItem]:
        """Generate attention items for sales velocity spikes."""
        spikes = self.analytics.detect_sales_spikes(store_id=store_id)
        items = []

        for sp in spikes:
            pid = sp["product_id"]
            sid = sp["store_id"]
            pct = sp["percentage_change"]

            severity = "HIGH" if pct >= 150.0 else "MEDIUM"
            summary = f"Sales spike: Recent 7-day sales increased +{pct}% over baseline ({sp['baseline_daily_avg']} -> {sp['recent_daily_avg']} u/d)"

            evidence = {
                "metric": "sales_velocity_change",
                "recent_daily_avg": sp["recent_daily_avg"],
                "baseline_daily_avg": sp["baseline_daily_avg"],
                "percentage_change": pct,
                "threshold_used": sp["detection_threshold"],
                "calculation_period": "Last 7 days vs previous 83-day baseline"
            }

            assumptions = [
                "Spike is evaluated relative to historical baseline daily sales velocity.",
                "Recent period covers past 7 consecutive days."
            ]

            items.append(AttentionItem(
                attention_id=f"ATT_SPIKE_{sid}_{pid}",
                attention_type="SALES_SPIKE",
                severity=severity,
                product_id=pid,
                product_name=sp["product_name"],
                category=sp["category"],
                store_id=sid,
                store_name=sp["store_name"],
                metric_summary=summary,
                evidence=evidence,
                recommendation=RECOMMENDATIONS["SALES_SPIKE"],
                assumptions=assumptions,
                data_sufficiency=sp["data_sufficiency"]
            ))

        return items

    def generate_drop_attention_items(self, store_id: Optional[str] = None) -> List[AttentionItem]:
        """Generate attention items for sales velocity drops."""
        drops = self.analytics.detect_sales_drops(store_id=store_id)
        items = []

        for dr in drops:
            pid = dr["product_id"]
            sid = dr["store_id"]
            pct = dr["percentage_change"]

            severity = "HIGH" if pct <= -70.0 else "MEDIUM"
            summary = f"Sales drop: Recent 7-day sales dropped {pct}% under baseline ({dr['baseline_daily_avg']} -> {dr['recent_daily_avg']} u/d)"

            evidence = {
                "metric": "sales_velocity_change",
                "recent_daily_avg": dr["recent_daily_avg"],
                "baseline_daily_avg": dr["baseline_daily_avg"],
                "percentage_change": pct,
                "threshold_used": dr["detection_threshold"],
                "calculation_period": "Last 7 days vs previous 83-day baseline"
            }

            assumptions = [
                "Drop is evaluated relative to historical baseline daily sales velocity.",
                "Recent period covers past 7 consecutive days."
            ]

            items.append(AttentionItem(
                attention_id=f"ATT_DROP_{sid}_{pid}",
                attention_type="SALES_DROP",
                severity=severity,
                product_id=pid,
                product_name=dr["product_name"],
                category=dr["category"],
                store_id=sid,
                store_name=dr["store_name"],
                metric_summary=summary,
                evidence=evidence,
                recommendation=RECOMMENDATIONS["SALES_DROP"],
                assumptions=assumptions,
                data_sufficiency=dr["data_sufficiency"]
            ))

        return items

    def get_all_attention_items(
        self,
        store_id: Optional[str] = None,
        category: Optional[str] = None,
        attention_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate, deduplicate, filter, and prioritize all attention items across the 5 categories.
        """
        raw_items: List[AttentionItem] = []

        # Collect from all 5 categories
        if not attention_type or attention_type == "STOCK_OUT_RISK":
            raw_items.extend(self.generate_stockout_attention_items(store_id=store_id))
        if not attention_type or attention_type == "SLOW_MOVING":
            raw_items.extend(self.generate_slow_moving_attention_items(store_id=store_id))
        if not attention_type or attention_type == "OVERSTOCK":
            raw_items.extend(self.generate_overstock_attention_items(store_id=store_id))
        if not attention_type or attention_type == "SALES_SPIKE":
            raw_items.extend(self.generate_spike_attention_items(store_id=store_id))
        if not attention_type or attention_type == "SALES_DROP":
            raw_items.extend(self.generate_drop_attention_items(store_id=store_id))

        # Deduplication map: key = (product_id, store_id, attention_type)
        dedup_map: Dict[tuple, AttentionItem] = {}
        for item in raw_items:
            key = (item.product_id, item.store_id, item.attention_type)
            if key not in dedup_map:
                dedup_map[key] = item
            else:
                # Keep item with higher severity (lower numerical rank)
                existing_rank = SEVERITY_ORDER.get(dedup_map[key].severity, 99)
                new_rank = SEVERITY_ORDER.get(item.severity, 99)
                if new_rank < existing_rank:
                    dedup_map[key] = item

        # Filter by category and severity
        filtered_items = []
        for item in dedup_map.values():
            if category and item.category != category:
                continue
            if severity and item.severity != severity:
                continue
            filtered_items.append(item)

        # Sort deterministically by severity priority and product name
        filtered_items.sort(key=lambda x: (
            SEVERITY_ORDER.get(x.severity, 99),
            x.evidence.get("days_remaining", 999) if x.evidence.get("days_remaining") is not None else 999,
            x.product_name
        ))

        return [item.to_dict() for item in filtered_items]
