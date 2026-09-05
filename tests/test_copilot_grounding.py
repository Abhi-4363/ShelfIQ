"""
ShelfIQ Phase 9 Copilot Grounding & Evidence Test Suite
Validates natural-language query routing, evidence structure, supporting numbers,
ambiguous query resolution, refusal of non-retail/unsupported questions, follow-up intent resolution,
and API endpoint validation.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from src.gemini import GeminiCopilot
from src.query_engine import QueryEngine
from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.rules import AttentionEngine


class TestCopilotGrounding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        cls.loader = DataLoader(cls.data_dir)
        cls.loader.load_all_data()
        cls.analytics = AnalyticsEngine(cls.loader)
        cls.attention = AttentionEngine(cls.analytics)
        cls.client = TestClient(app)

    def test_01_inventory_risk_query(self):
        """Test 'Which products are likely to run out?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "Which products are likely to run out?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "INVENTORY_RISK")
        self.assertIn("answer", data)
        self.assertIn("key_points", data)
        self.assertIn("evidence", data)
        self.assertIn("recommendation", data)
        self.assertEqual(data["data_sufficiency"], "SUFFICIENT")

    def test_02_overstock_query(self):
        """Test 'Which products are overstocked?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "Which products are overstocked?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "OVERSTOCK")
        self.assertGreater(len(data["evidence"]), 0)

    def test_03_slow_moving_query(self):
        """Test 'Which products are selling slowly?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "Which products are selling slowly?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "SLOW_MOVING")

    def test_04_sales_spike_query(self):
        """Test 'Did sales spike anywhere?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "Did sales spike anywhere?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "SALES_SPIKE")
        sales_evidence = [ev for ev in data["evidence"] if ev.get("metric") == "sales_change"]
        self.assertGreater(len(sales_evidence), 0)
        self.assertIsNotNone(sales_evidence[0].get("recent_value"))
        self.assertIsNotNone(sales_evidence[0].get("baseline_value"))

    def test_05_sales_drop_query(self):
        """Test 'Did sales drop anywhere?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "Did sales drop anywhere?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "SALES_DROP")
        sales_evidence = [ev for ev in data["evidence"] if ev.get("metric") == "sales_change"]
        self.assertGreater(len(sales_evidence), 0)
        self.assertIsNotNone(sales_evidence[0].get("recent_value"))
        self.assertIsNotNone(sales_evidence[0].get("baseline_value"))

    def test_06_attention_review_query(self):
        """Test 'What should I review today?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "What should I review today?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "GENERAL_ATTENTION")
        self.assertGreater(len(data["key_points"]), 0)

    def test_07_valid_product_performance_query(self):
        """Test 'How did Toned Milk perform this month?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "How did Toned Milk perform this month?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "PRODUCT_PERFORMANCE")
        self.assertTrue(any(ev["product_id"] == "PRD047" for ev in data["evidence"]))

    def test_08_ambiguous_product_query(self):
        """Test ambiguous question 'How are biscuits doing?' matching multiple biscuit products."""
        res = self.client.post("/api/ai/analyze", json={"question": "How are biscuits doing?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "AMBIGUOUS")
        self.assertEqual(data["data_sufficiency"], "INSUFFICIENT")
        self.assertIn("Multiple matching products found", data["answer"])

    def test_09_unsupported_data_query(self):
        """Test question requiring missing metadata 'What is the supplier lead time?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "What is the supplier lead time?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "UNSUPPORTED_DATA")
        self.assertEqual(data["data_sufficiency"], "INSUFFICIENT")
        self.assertIn("does not contain information", data["answer"])

    def test_10_unknown_non_retail_query(self):
        """Test unrelated question 'What is the capital of France?'."""
        res = self.client.post("/api/ai/analyze", json={"question": "What is the capital of France?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "UNKNOWN")
        self.assertEqual(data["data_sufficiency"], "INSUFFICIENT")
        self.assertIn("I don't have data to answer that question", data["answer"])

    def test_11_empty_question_validation(self):
        """Test empty question returns 400 status."""
        res = self.client.post("/api/ai/analyze", json={"question": "   "})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Question cannot be empty", res.json()["detail"])

    def test_12_gemini_failure_fallback(self):
        """Test graceful fallback when Gemini SDK fails."""
        copilot = GeminiCopilot(api_key="mock_key")
        copilot._client = MagicMock()
        copilot._client.models.generate_content.side_effect = Exception("Network timeout connecting to Gemini API")

        query_engine = QueryEngine(self.loader, self.analytics, self.attention, copilot)
        res = query_engine.process_query("Which products are running out?")

        self.assertIn("answer", res)
        self.assertIn("evidence", res)
        self.assertIn("Gemini API error", res["answer"])
        self.assertGreater(len(res["evidence"]), 0)

    def test_13_malformed_gemini_response_fallback(self):
        """Test fallback when Gemini returns invalid non-JSON output."""
        copilot = GeminiCopilot(api_key="mock_key")
        copilot._client = MagicMock()

        mock_res = MagicMock()
        mock_res.text = "Here is an unformatted plain text explanation without any JSON tags."
        copilot._client.models.generate_content.return_value = mock_res

        query_engine = QueryEngine(self.loader, self.analytics, self.attention, copilot)
        res = query_engine.process_query("Which products are overstocked?")

        self.assertIn("Malformed model response", res["answer"])
        self.assertGreater(len(res["evidence"]), 0)

    def test_14_followup_query_resolution(self):
        """Test contextual follow-up query 'What about Hyderabad Central?'."""
        res = self.client.post("/api/ai/analyze", json={
            "question": "What about Hyderabad Central?",
            "previous_intent": "INVENTORY_RISK"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["intent"], "INVENTORY_RISK")
        self.assertTrue(all(ev.get("store_id") == "STR001" for ev in data["evidence"] if ev.get("store_id")))

    def test_15_store_filter_validation(self):
        """Test store filtering with invalid store_id."""
        res = self.client.post("/api/ai/analyze", json={
            "question": "Which products are selling slowly?",
            "store_id": "INVALID_STORE_CODE"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid store_id", res.json()["detail"])

    def test_16_frontend_copilot_error_and_escape_helpers(self):
        """Test frontend has inline error state and escapes dynamic copilot content."""
        app_js_path = os.path.join(os.path.dirname(__file__), "..", "static", "app.js")
        with open(app_js_path, "r", encoding="utf-8") as f:
            app_js = f.read()

        self.assertIn("renderCopilotErrorHTML()", app_js)
        self.assertIn("Copilot is temporarily unavailable", app_js)
        self.assertIn("function escapeHTML(value)", app_js)
        self.assertIn("escapeHTML(data.answer", app_js)
        self.assertNotIn("alert(\"Copilot Error:", app_js)

    @unittest.skipUnless(os.getenv("GEMINI_API_KEY"), "Real Gemini API test skipped because GEMINI_API_KEY is not set.")
    def test_17_real_gemini_integration(self):
        """Live End-to-End Gemini Integration Test."""
        copilot = GeminiCopilot()
        self.assertTrue(copilot.is_available())
        query_engine = QueryEngine(self.loader, self.analytics, self.attention, copilot)

        res = query_engine.process_query("Which products are likely to run out?")
        self.assertIn("answer", res)
        self.assertIn(res["data_sufficiency"], ["SUFFICIENT", "LIMITED", "INSUFFICIENT"])


if __name__ == "__main__":
    unittest.main()
