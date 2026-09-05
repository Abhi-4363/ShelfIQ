"""
ShelfIQ Business Rules & Attention Engine Test Suite
Validates attention generation, severity mapping, evidence structures, deduplication, and filtering.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.rules import AttentionEngine, SEVERITY_ORDER

class TestAttentionEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        cls.loader = DataLoader(data_dir)
        is_valid, result = cls.loader.load_all_data()
        assert is_valid, f"Dataset loading failed: {[e.message for e in result.errors]}"
        
        cls.analytics = AnalyticsEngine(cls.loader)
        cls.rules = AttentionEngine(cls.analytics)

    def test_stockout_attention_items(self):
        """Test generation of stock-out risk attention items."""
        items = self.rules.generate_stockout_attention_items()
        self.assertGreater(len(items), 0)

        for item in items:
            self.assertEqual(item.attention_type, "STOCK_OUT_RISK")
            self.assertIn(item.severity, ["CRITICAL", "HIGH", "MEDIUM"])
            self.assertIn("days_remaining", item.evidence)
            self.assertIn("Review replenishment", item.recommendation)
            self.assertGreater(len(item.assumptions), 0)
            self.assertEqual(item.data_sufficiency, "SUFFICIENT")

    def test_slow_moving_attention_items(self):
        """Test generation of slow-moving attention items."""
        items = self.rules.generate_slow_moving_attention_items()
        self.assertGreaterEqual(len(items), 4)

        for item in items:
            self.assertEqual(item.attention_type, "SLOW_MOVING")
            self.assertIn(item.severity, ["HIGH", "MEDIUM"])
            self.assertIn("average_daily_units_sold", item.evidence)
            self.assertIn("Review inventory exposure", item.recommendation)

    def test_overstock_attention_items(self):
        """Test generation of overstock attention items."""
        items = self.rules.generate_overstock_attention_items()
        self.assertGreaterEqual(len(items), 4)

        for item in items:
            self.assertEqual(item.attention_type, "OVERSTOCK")
            self.assertIn(item.severity, ["HIGH", "MEDIUM"])
            self.assertIn("estimated_days_of_inventory", item.evidence)
            self.assertIn("Review excess inventory", item.recommendation)

    def test_spike_and_drop_attention_items(self):
        """Test generation of sales spike and sales drop attention items."""
        spikes = self.rules.generate_spike_attention_items()
        drops = self.rules.generate_drop_attention_items()

        self.assertGreaterEqual(len(spikes), 3)
        self.assertGreaterEqual(len(drops), 3)

        for sp in spikes:
            self.assertEqual(sp.attention_type, "SALES_SPIKE")
            self.assertGreaterEqual(sp.evidence["percentage_change"], 50.0)

        for dr in drops:
            self.assertEqual(dr.attention_type, "SALES_DROP")
            self.assertLessEqual(dr.evidence["percentage_change"], -30.0)

    def test_all_attention_items_aggregation_and_deduplication(self):
        """Test get_all_attention_items aggregation, deduplication, and sorting."""
        all_items = self.rules.get_all_attention_items()
        self.assertGreater(len(all_items), 0)

        # Check deduplication by (product_id, store_id, attention_type)
        seen_keys = set()
        for item in all_items:
            key = (item["product_id"], item["store_id"], item["attention_type"])
            self.assertNotIn(key, seen_keys, f"Duplicate attention item found for key {key}")
            seen_keys.add(key)

        # Check deterministic sorting by severity priority
        severities = [item["severity"] for item in all_items]
        severity_ranks = [SEVERITY_ORDER[s] for s in severities]
        self.assertEqual(severity_ranks, sorted(severity_ranks), "Attention items must be sorted by severity rank")

    def test_filtering(self):
        """Test filtering by store_id, category, attention_type, and severity."""
        store_items = self.rules.get_all_attention_items(store_id="STR001")
        self.assertGreater(len(store_items), 0)
        self.assertTrue(all(i["store_id"] == "STR001" for i in store_items))

        critical_items = self.rules.get_all_attention_items(severity="CRITICAL")
        self.assertGreater(len(critical_items), 0)
        self.assertTrue(all(i["severity"] == "CRITICAL" for i in critical_items))

        spike_items = self.rules.get_all_attention_items(attention_type="SALES_SPIKE")
        self.assertGreater(len(spike_items), 0)
        self.assertTrue(all(i["attention_type"] == "SALES_SPIKE" for i in spike_items))

if __name__ == "__main__":
    unittest.main()
