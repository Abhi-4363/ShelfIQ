"""
ShelfIQ Business Rules Scenario Verification Script
Runs AttentionEngine against the real dataset and prints structured attention items.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.rules import AttentionEngine

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    loader = DataLoader(data_dir)
    loader.load_all_data()

    analytics = AnalyticsEngine(loader)
    rules = AttentionEngine(analytics)

    items = rules.get_all_attention_items()

    print("==================================================")
    print(" SHELFIQ ATTENTION ENGINE VERIFICATION")
    print("==================================================")
    print(f"Total Attention Items Generated: {len(items)}")

    crit_count = sum(1 for i in items if i["severity"] == "CRITICAL")
    high_count = sum(1 for i in items if i["severity"] == "HIGH")
    med_count = sum(1 for i in items if i["severity"] == "MEDIUM")

    print(f"Severity Breakup: CRITICAL={crit_count}, HIGH={high_count}, MEDIUM={med_count}")

    print("\n--- SAMPLE CRITICAL STOCKOUT ATTENTION ITEMS ---")
    crit_items = [i for i in items if i["severity"] == "CRITICAL"]
    for ci in crit_items[:3]:
        print(f"\n[ATTENTION ID]: {ci['attention_id']}")
        print(f"Type: {ci['attention_type']} | Severity: {ci['severity']}")
        print(f"Product: {ci['product_name']} ({ci['product_id']}) @ {ci['store_name']}")
        print(f"Summary: {ci['metric_summary']}")
        print(f"Evidence: {ci['evidence']}")
        print(f"Recommendation: {ci['recommendation']}")

    print("\n--- SAMPLE SALES SPIKE ATTENTION ITEMS ---")
    spike_items = [i for i in items if i["attention_type"] == "SALES_SPIKE"]
    for si in spike_items[:2]:
        print(f"\n[ATTENTION ID]: {si['attention_id']}")
        print(f"Product: {si['product_name']} @ {si['store_name']}")
        print(f"Summary: {si['metric_summary']}")
        print(f"Recommendation: {si['recommendation']}")

    print("\n--- SAMPLE SALES DROP ATTENTION ITEMS ---")
    drop_items = [i for i in items if i["attention_type"] == "SALES_DROP"]
    for di in drop_items[:2]:
        print(f"\n[ATTENTION ID]: {di['attention_id']}")
        print(f"Product: {di['product_name']} @ {di['store_name']}")
        print(f"Summary: {di['metric_summary']}")
        print(f"Recommendation: {di['recommendation']}")

    print("\n==================================================")
    print(" ATTENTION ENGINE VERIFICATION COMPLETE!")
    print("==================================================")

if __name__ == "__main__":
    main()
