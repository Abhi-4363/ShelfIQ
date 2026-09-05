"""
ShelfIQ FastAPI REST API Test Suite
Validates all backend API endpoints, query parameters, error responses, and JSON schemas.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        """Test GET / endpoint."""
        res = self.client.get("/", headers={"accept": "application/json"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["name"], "ShelfIQ")
        self.assertEqual(data["status"], "running")
        self.assertEqual(data["version"], "1.0.0")

    def test_health_endpoint(self):
        """Test GET /api/health endpoint."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["data_loaded"])
        self.assertTrue(data["data_valid"])

    def test_summary_endpoint(self):
        """Test GET /api/summary endpoint."""
        res = self.client.get("/api/summary")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["total_sales"], 0)
        self.assertGreater(data["total_units_sold"], 0)
        self.assertEqual(data["total_products"], 55)
        self.assertEqual(data["total_stores"], 4)
        self.assertEqual(len(data["stores_summary"]), 4)
        self.assertEqual(len(data["category_summary"]), 6)
        self.assertIn("sales_growth", data)
        self.assertIn("percentage_change", data["sales_growth"])

    def test_inventory_endpoint_and_filters(self):
        """Test GET /api/inventory with store, status, category, and search filters."""
        res = self.client.get("/api/inventory")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 220)

        # Store filter
        res_hyd = self.client.get("/api/inventory?store_id=STR001")
        self.assertEqual(res_hyd.status_code, 200)
        self.assertEqual(res_hyd.json()["count"], 55)

        # Search filter
        res_search = self.client.get("/api/inventory?search=Rice")
        self.assertEqual(res_search.status_code, 200)
        self.assertGreater(res_search.json()["count"], 0)

        # Status filter
        res_critical = self.client.get("/api/inventory?status=CRITICAL")
        self.assertEqual(res_critical.status_code, 200)
        self.assertGreater(res_critical.json()["count"], 0)

    def test_sales_endpoint_and_date_filtering(self):
        """Test GET /api/sales with store and date range filtering."""
        res = self.client.get("/api/sales")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("summary", data)
        self.assertEqual(data["product_performance_count"], 55)

        # Date range filter
        res_date = self.client.get("/api/sales?start_date=2026-08-01&end_date=2026-08-15")
        self.assertEqual(res_date.status_code, 200)
        date_data = res_date.json()
        self.assertEqual(date_data["summary"]["date_range"]["start_date"], "2026-08-01")
        self.assertIn("daily_trend", date_data)
        self.assertIn("sales_growth", date_data)
        self.assertEqual(date_data["daily_trend"][0]["date"], "2026-08-01")
        self.assertEqual(date_data["daily_trend"][-1]["date"], "2026-08-15")

    def test_attention_endpoint_and_filters(self):
        """Test GET /api/attention with store_id, attention_type, and severity filters."""
        res = self.client.get("/api/attention")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data["count"], 0)
        self.assertIn("severity_counts", data)

        # Filter by severity CRITICAL
        res_crit = self.client.get("/api/attention?severity=CRITICAL")
        self.assertEqual(res_crit.status_code, 200)
        self.assertTrue(all(item["severity"] == "CRITICAL" for item in res_crit.json()["attention_items"]))

        # Filter by attention_type STOCK_OUT_RISK
        res_type = self.client.get("/api/attention?attention_type=STOCK_OUT_RISK")
        self.assertEqual(res_type.status_code, 200)
        self.assertTrue(all(item["attention_type"] == "STOCK_OUT_RISK" for item in res_type.json()["attention_items"]))

    def test_products_endpoints(self):
        """Test GET /api/products and GET /api/products/{id}."""
        res_list = self.client.get("/api/products")
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(res_list.json()["count"], 55)

        # Valid product
        res_detail = self.client.get("/api/products/PRD001")
        self.assertEqual(res_detail.status_code, 200)
        data = res_detail.json()
        self.assertEqual(data["product_id"], "PRD001")
        self.assertIn("sales_performance", data)
        self.assertIn("inventory_metrics", data)
        self.assertIn("attention_items", data)

        # Invalid product -> 404
        res_invalid = self.client.get("/api/products/PRD9999")
        self.assertEqual(res_invalid.status_code, 404)
        self.assertIn("Product not found", res_invalid.json()["detail"])

    def test_stores_endpoints(self):
        """Test GET /api/stores and GET /api/stores/{id}."""
        res_stores = self.client.get("/api/stores")
        self.assertEqual(res_stores.status_code, 200)
        self.assertEqual(len(res_stores.json()["stores"]), 4)

        # Valid store
        res_detail = self.client.get("/api/stores/STR001")
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.json()["store"]["store_id"], "STR001")

        # Invalid store -> 400
        res_invalid = self.client.get("/api/stores/STR9999")
        self.assertEqual(res_invalid.status_code, 400)
        self.assertIn("Invalid store_id", res_invalid.json()["detail"])

    def test_invalid_parameters_error_handling(self):
        """Test error responses for malformed query parameters."""
        # Invalid date format
        res_bad_date = self.client.get("/api/sales?start_date=bad-date-format")
        self.assertEqual(res_bad_date.status_code, 400)
        self.assertIn("Invalid ISO date format", res_bad_date.json()["detail"])

        # Invalid store_id in inventory
        res_bad_store = self.client.get("/api/inventory?store_id=NON_EXISTENT_STORE")
        self.assertEqual(res_bad_store.status_code, 400)

    def test_docs_endpoint(self):
        """Test OpenAPI documentation endpoint GET /docs."""
        res = self.client.get("/openapi.json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["info"]["title"], "ShelfIQ")

    def test_static_frontend_has_no_credentials(self):
        """Test frontend assets do not contain backend credentials."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        frontend_paths = [
            os.path.join(repo_root, "static", "app.js"),
            os.path.join(repo_root, "static", "index.html"),
        ]

        for path in frontend_paths:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertNotIn("GEMINI_API_KEY", content)
            self.assertNotIn("AIza", content)
            self.assertNotIn("secret-value", content)

    def test_static_frontend_uses_friendly_error_copy(self):
        """Test frontend avoids raw technical API errors for common failure states."""
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        app_js_path = os.path.join(repo_root, "static", "app.js")
        with open(app_js_path, "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("Unable to connect to ShelfIQ. Please try again.", app_js)
        self.assertIn("Copilot is temporarily unavailable", app_js)
        self.assertIn("No products match", app_js)
        self.assertIn("buildSalesQueryParams", app_js)
        self.assertNotIn("sample simulation", app_js)
        self.assertNotIn("alert(\"Copilot Error:", app_js)

if __name__ == "__main__":
    unittest.main()
