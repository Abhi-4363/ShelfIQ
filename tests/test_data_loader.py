"""
ShelfIQ Data Loader & Validation Test Suite
Tests loading and validation logic against the real dataset and against synthetic error conditions.
"""

import os
import sys
import tempfile
import csv
import unittest

# Ensure src module is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import DataLoader, ValidationError, ValidationResult

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self.loader = DataLoader(self.data_dir)

    def _create_minimal_valid_csvs(self, tmp_dir):
        """Helper to create minimal valid CSV files for isolated test scenarios."""
        with open(os.path.join(tmp_dir, "stores.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["store_id", "store_name", "city"])
            writer.writerow(["STR001", "Hyderabad Central", "Hyderabad"])

        with open(os.path.join(tmp_dir, "products.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["product_id", "product_name", "category", "unit_price", "cost_price"])
            writer.writerow(["PRD001", "Basmati Rice 5kg", "Groceries", "550.0", "420.0"])

        with open(os.path.join(tmp_dir, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["store_id", "product_id", "current_stock", "last_updated"])
            writer.writerow(["STR001", "PRD001", "50", "2026-08-29"])

        with open(os.path.join(tmp_dir, "sales.csv"), "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "store_id", "product_id", "units_sold", "sales_amount"])
            writer.writerow(["2026-08-01", "STR001", "PRD001", "2", "1100.0"])

    def test_load_real_dataset(self):
        """Test loading and validating the actual generated dataset in data/."""
        is_valid, result = self.loader.load_all_data()
        
        self.assertTrue(is_valid, f"Expected dataset to be valid, but got errors: {[e.message for e in result.errors]}")
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(result.summary_stats["stores_count"], 4)
        self.assertEqual(result.summary_stats["products_count"], 55)
        self.assertEqual(result.summary_stats["inventory_count"], 220)
        self.assertEqual(result.summary_stats["sales_count"], 19064)

        # Test getter methods
        self.assertEqual(len(self.loader.get_stores()), 4)
        self.assertEqual(len(self.loader.get_products()), 55)
        self.assertEqual(len(self.loader.get_inventory()), 220)
        self.assertEqual(len(self.loader.get_sales()), 19064)

    def test_missing_required_column(self):
        """Test detection of missing required column."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            # Overwrite stores.csv with missing column 'city'
            with open(os.path.join(tmp_dir, "stores.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["store_id", "store_name"])  # Missing 'city'
                writer.writerow(["STR001", "Hyderabad Central"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Missing required columns" in e.message for e in result.errors))

    def test_duplicate_store_id(self):
        """Test detection of duplicate store_id."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            # Overwrite stores.csv with duplicate store_id
            with open(os.path.join(tmp_dir, "stores.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["store_id", "store_name", "city"])
                writer.writerow(["STR001", "Hyderabad Central", "Hyderabad"])
                writer.writerow(["STR001", "Duplicate Store", "Hyderabad"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Duplicate store_id" in e.message for e in result.errors))

    def test_invalid_foreign_key_reference(self):
        """Test detection of invalid store_id reference in inventory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            # Overwrite inventory referencing invalid store 'STR999'
            with open(os.path.join(tmp_dir, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["store_id", "product_id", "current_stock", "last_updated"])
                writer.writerow(["STR999", "PRD001", "50", "2026-08-29"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Invalid store_id reference" in e.message for e in result.errors))

    def test_missing_csv_file(self):
        """Test detection of a missing required CSV file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)
            os.remove(os.path.join(tmp_dir, "sales.csv"))

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Required data file missing" in e.message for e in result.errors))

    def test_invalid_product_reference(self):
        """Test detection of invalid product_id reference in sales."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            with open(os.path.join(tmp_dir, "sales.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "store_id", "product_id", "units_sold", "sales_amount"])
                writer.writerow(["2026-08-01", "STR001", "PRD999", "2", "1100.0"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Invalid product_id reference" in e.message for e in result.errors))

    def test_invalid_dates_and_missing_values(self):
        """Test clear validation errors for invalid dates and required missing values."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            with open(os.path.join(tmp_dir, "stores.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["store_id", "store_name", "city"])
                writer.writerow(["", "Missing ID Store", "Hyderabad"])

            with open(os.path.join(tmp_dir, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["store_id", "product_id", "current_stock", "last_updated"])
                writer.writerow(["STR001", "PRD001", "50", "bad-date"])

            with open(os.path.join(tmp_dir, "sales.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "store_id", "product_id", "units_sold", "sales_amount"])
                writer.writerow(["bad-date", "STR001", "PRD001", "2", "1100.0"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Missing required field" in e.message for e in result.errors))
            self.assertTrue(any("Invalid ISO date format" in e.message for e in result.errors))

    def test_mathematical_mismatch(self):
        """Test detection of mathematical inconsistency in sales_amount."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            # Sales amount mismatch: 2 units * 550 = 1100, but sales_amount = 9999
            with open(os.path.join(tmp_dir, "sales.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "store_id", "product_id", "units_sold", "sales_amount"])
                writer.writerow(["2026-08-01", "STR001", "PRD001", "2", "9999.0"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("Mathematical mismatch" in e.message for e in result.errors))

    def test_negative_stock(self):
        """Test detection of negative inventory stock."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._create_minimal_valid_csvs(tmp_dir)

            # Overwrite inventory with negative stock
            with open(os.path.join(tmp_dir, "inventory.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["store_id", "product_id", "current_stock", "last_updated"])
                writer.writerow(["STR001", "PRD001", "-10", "2026-08-29"])

            loader = DataLoader(tmp_dir)
            is_valid, result = loader.load_all_data()
            self.assertFalse(is_valid)
            self.assertTrue(any("cannot be negative" in e.message for e in result.errors))

if __name__ == "__main__":
    unittest.main()
