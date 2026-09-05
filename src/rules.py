"""
ShelfIQ Business Rules & Thresholds
Centralized thresholds and recommendation engine for stock-out risks, slow-moving items, overstock, and sales spikes/drops.
"""

# Transparent Threshold Configuration
STOCKOUT_CRITICAL_DAYS = 4.0
STOCKOUT_HIGH_DAYS = 7.0
STOCKOUT_WATCH_DAYS = 14.0

SLOW_MOVING_VELOCITY_THRESHOLD = 0.5  # units/day
OVERSTOCK_DAYS_THRESHOLD = 60.0       # days of stock remaining

SALES_SPIKE_PERCENT_CHANGE = 50.0      # % increase over baseline
SALES_DROP_PERCENT_CHANGE = -30.0      # % decrease over baseline

def evaluate_stock_status(days_remaining: float, avg_daily_sales: float) -> str:
    """Evaluate inventory health status based on days remaining."""
    if days_remaining <= STOCKOUT_CRITICAL_DAYS:
        return "Critical"
    elif days_remaining <= STOCKOUT_HIGH_DAYS:
        return "Low Stock"
    elif days_remaining <= STOCKOUT_WATCH_DAYS:
        return "Watch"
    else:
        return "Healthy"

def generate_recommendation(issue_type: str, context: dict) -> str:
    """Generate deterministic recommendations for findings."""
    recommendations = {
        "STOCK_OUT": "Review replenishment quantity immediately and accelerate purchase order.",
        "SLOW_MOVING": "Review inventory allocation, consider promotional pricing or bundle offers.",
        "OVERSTOCK": "Review excess inventory and suspend upcoming replenishment orders.",
        "SALES_SPIKE": "Investigate whether increased demand is sustained to adjust reorder levels.",
        "SALES_DROP": "Review recent performance, check pricing, display, and availability."
    }
    return recommendations.get(issue_type, "Review item performance.")
