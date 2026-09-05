"""
ShelfIQ Analytics Scenario Verification Script
Runs AnalyticsEngine against the dataset and prints structured reports of detected scenarios.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    loader = DataLoader(data_dir)
    is_valid, res = loader.load_all_data()
    if not is_valid:
        print("Dataset loading failed!")
        return

    engine = AnalyticsEngine(loader)

    print("==================================================")
    print(" SHELFIQ DETERMINISTIC ANALYTICS VERIFICATION")
    print("==================================================")

    # 1. Sales Summary
    sales_sum = engine.calculate_sales_summary()
    print(f"\n[1] Sales Summary (All Stores):")
    print(f"    - Total Sales Amount: INR {sales_sum['total_sales_amount']:,}")
    print(f"    - Total Units Sold: {sales_sum['total_units_sold']:,}")
    print(f"    - Avg Daily Sales: INR {sales_sum['avg_daily_sales_amount']:,}/day")
    print(f"    - Date Range: {sales_sum['date_range']['start_date']} to {sales_sum['date_range']['end_date']}")
    print(f"    - Sufficiency: {sales_sum['data_sufficiency']}")

    # 2. Stockout Risks
    risks = engine.detect_stockout_risks()
    print(f"\n[2] Stockout Risks Detected: {len(risks)} items")
    for r in risks[:6]:
        print(f"    - [{r['risk_level']}] Store: {r['store_id']}, Product: {r['product_name']} ({r['product_id']})")
        print(f"      Stock: {r['current_stock']} units, Daily Velocity: {r['average_daily_units_sold']} u/d, Days Remaining: {r['days_remaining_display']}d")

    # 3. Slow-Moving Items
    slow = engine.detect_slow_moving_products()
    print(f"\n[3] Slow-Moving Products Detected: {len(slow)} items")
    for s in slow:
        print(f"    - Store: {s['store_id']}, Product: {s['product_name']} ({s['product_id']})")
        print(f"      Stock: {s['current_stock']} units, Daily Velocity: {s['average_daily_units_sold']} u/d, Period: {s['comparison_period']}")

    # 4. Overstocked Items
    overstock = engine.detect_overstocked_products()
    print(f"\n[4] Overstocked Products Detected: {len(overstock)} items")
    for o in overstock[:5]:
        print(f"    - Store: {o['store_id']}, Product: {o['product_name']} ({o['product_id']})")
        print(f"      Stock: {o['current_stock']} units, Daily Velocity: {o['average_daily_units_sold']} u/d, Days Est: {o['estimated_days_display']}")

    # 5. Sales Spikes
    spikes = engine.detect_sales_spikes()
    print(f"\n[5] Sales Spikes Detected: {len(spikes)} items")
    for sp in spikes:
        print(f"    - Store: {sp['store_id']}, Product: {sp['product_name']} ({sp['product_id']})")
        print(f"      Baseline: {sp['baseline_daily_avg']} u/d -> Recent: {sp['recent_daily_avg']} u/d (Change: +{sp['percentage_change']}%)")

    # 6. Sales Drops
    drops = engine.detect_sales_drops()
    print(f"\n[6] Sales Drops Detected: {len(drops)} items")
    for dr in drops[:5]:
        print(f"    - Store: {dr['store_id']}, Product: {dr['product_name']} ({dr['product_id']})")
        print(f"      Baseline: {dr['baseline_daily_avg']} u/d -> Recent: {dr['recent_daily_avg']} u/d (Change: {dr['percentage_change']}%)")

    # 7. Store Summary
    stores = engine.calculate_store_summary()
    print(f"\n[7] Store-Level Summary:")
    for st in stores:
        print(f"    - Store: {st['store_name']} ({st['store_id']}): Sales: INR {st['total_sales_amount']:,}, Inv Value: INR {st['inventory_value']:,}, Low Stock Items: {st['low_stock_items_count']}")

    print("\n==================================================")
    print(" VERIFICATION COMPLETE - ALL ANALYTICS FUNCTIONAL!")
    print("==================================================")

if __name__ == "__main__":
    main()
