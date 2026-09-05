"""
ShelfIQ Analytics Engine Test Suite
Validates pure Python deterministic analytics against real synthetic dataset and edge cases.
"""

import os
import sys
import math
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import DataLoader
from src.analytics import (
    AnalyticsEngine,
    STOCKOUT_CRITICAL_DAYS,
    STOCKOUT_HIGH_DAYS,
    SLOW_MOVING_VELOCITY_THRESHOLD,
    OVERSTOCK_DAYS_THRESHOLD,
    SPIKE_PERCENT_THRESHOLD,
    DROP_PERCENT_THRESHOLD
)

class TestAnalyticsEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        cls.loader = DataLoader(data_dir)
        is_valid, result = cls.loader.load_all_data()
        assert is_valid, f"Dataset loading failed in setUpClass: {[e.message for e in result.errors]}"
        cls.engine = AnalyticsEngine(cls.loader)

    def test_sales_summary(self):
        """Test overall and filtered sales summary calculations."""
        summary = self.engine.calculate_sales_summary()
        self.assertGreater(summary["total_sales_amount"], 0)
        self.assertGreater(summary["total_units_sold"], 0)
        self.assertEqual(summary["unique_days_count"], 90)
        self.assertEqual(summary["data_sufficiency"], "SUFFICIENT")

        # Test store filtering
        hyd_summary = self.engine.calculate_sales_summary(store_id="STR001")
        self.assertGreater(hyd_summary["total_sales_amount"], 0)
        self.assertLess(hyd_summary["total_sales_amount"], summary["total_sales_amount"])

        # Test category filtering
        dairy_summary = self.engine.calculate_sales_summary(category="Dairy")
        self.assertGreater(dairy_summary["total_sales_amount"], 0)
        self.assertLess(dairy_summary["total_sales_amount"], summary["total_sales_amount"])

    def test_product_performance(self):
        """Test product-level sales performance calculations."""
        perf = self.engine.calculate_product_performance()
        self.assertEqual(len(perf), 55)

        for p in perf:
            self.assertIn("product_id", p)
            self.assertIn("avg_daily_units", p)
            self.assertIn("data_sufficiency", p)
            self.assertFalse(math.isnan(p["total_sales_amount"]))
            self.assertFalse(math.isinf(p["total_sales_amount"]))

    def test_inventory_metrics_and_zero_sales(self):
        """Test inventory metrics and zero-sales division safety."""
        inv_metrics = self.engine.calculate_inventory_metrics()
        self.assertEqual(len(inv_metrics), 220)

        for item in inv_metrics:
            # Check zero division safety
            if item["average_daily_units_sold"] == 0:
                self.assertIsNone(item["days_remaining"])
                self.assertEqual(item["days_remaining_display"], "UNAVAILABLE")
                self.assertEqual(item["status"], "ZERO_SALES")
            else:
                self.assertIsNotNone(item["days_remaining"])
                self.assertFalse(math.isnan(item["days_remaining"]))
                self.assertFalse(math.isinf(item["days_remaining"]))

    def test_stockout_risk_detection(self):
        """Test detection of stock-out risks against Phase 2 known scenarios."""
        risks = self.engine.detect_stockout_risks()
        self.assertGreater(len(risks), 0)

        critical_risks = [r for r in risks if r["risk_level"] == "CRITICAL"]
        high_risks = [r for r in risks if r["risk_level"] == "HIGH"]

        self.assertGreaterEqual(len(critical_risks), 3, "Expected at least 3 CRITICAL stock-out scenarios")
        self.assertGreaterEqual(len(high_risks), 4, "Expected at least 4 HIGH stock-out scenarios")

        # Verify evidence fields
        for r in risks:
            self.assertIn("product_id", r)
            self.assertIn("product_name", r)
            self.assertIn("store_id", r)
            self.assertIn("current_stock", r)
            self.assertIn("days_remaining", r)
            self.assertIn("risk_level", r)
            self.assertIn("threshold_used", r)

    def test_slow_moving_detection(self):
        """Test detection of slow-moving items."""
        slow = self.engine.detect_slow_moving_products()
        self.assertGreaterEqual(len(slow), 4, "Expected at least 4 slow-moving products")

        for item in slow:
            self.assertLess(item["average_daily_units_sold"], SLOW_MOVING_VELOCITY_THRESHOLD)
            self.assertGreaterEqual(item["current_stock"], 30)
            self.assertIn("comparison_period", item)
            self.assertIn("threshold_used", item)

    def test_overstock_detection(self):
        """Test detection of overstocked items."""
        overstocked = self.engine.detect_overstocked_products()
        self.assertGreaterEqual(len(overstocked), 4, "Expected at least 4 overstocked products")

        for item in overstocked:
            self.assertIn(item["overstock_status"], ["OVERSTOCKED", "ZERO_SALES_OVERSTOCK"])
            self.assertIn("threshold_used", item)

    def test_sales_spikes_detection(self):
        """Test detection of sales velocity spikes."""
        spikes = self.engine.detect_sales_spikes()
        self.assertGreaterEqual(len(spikes), 3, "Expected at least 3 sales spikes")

        for s in spikes:
            self.assertGreaterEqual(s["percentage_change"], SPIKE_PERCENT_THRESHOLD)
            self.assertIn("recent_daily_avg", s)
            self.assertIn("baseline_daily_avg", s)

    def test_sales_drops_detection(self):
        """Test detection of sales velocity drops."""
        drops = self.engine.detect_sales_drops()
        self.assertGreaterEqual(len(drops), 3, "Expected at least 3 sales drops")

        for d in drops:
            self.assertLessEqual(d["percentage_change"], DROP_PERCENT_THRESHOLD)
            self.assertIn("recent_daily_avg", d)
            self.assertIn("baseline_daily_avg", d)

    def test_category_and_store_summaries(self):
        """Test category and store level aggregation analytics."""
        cat_summary = self.engine.calculate_category_summary()
        self.assertEqual(len(cat_summary), 6)

        store_summary = self.engine.calculate_store_summary()
        self.assertEqual(len(store_summary), 4)

        for st in store_summary:
            self.assertGreater(st["total_sales_amount"], 0)
            self.assertGreater(st["inventory_value"], 0)

if __name__ == "__main__":
    unittest.main()
