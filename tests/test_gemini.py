"""
ShelfIQ Gemini Integration & Query Engine Test Suite
Validates Gemini client initialization, intent parsing, prompt grounding, failure fallbacks, output schemas, and API endpoints.
Unit tests mock the Gemini SDK to run offline without requiring a live API key.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from src.gemini import GeminiCopilot
from src.query_engine import QueryEngine
from src.data_loader import DataLoader
from src.analytics import AnalyticsEngine
from src.rules import AttentionEngine


class TestGeminiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        cls.loader = DataLoader(cls.data_dir)
        cls.loader.load_all_data()
        cls.analytics = AnalyticsEngine(cls.loader)
        cls.attention = AttentionEngine(cls.analytics)
        cls.client = TestClient(app)

    def test_missing_api_key_handling(self):
        """Test behavior when GEMINI_API_KEY is not provided."""
        copilot = GeminiCopilot(api_key="")
        self.assertFalse(copilot.is_available())

        query_engine = QueryEngine(self.loader, self.analytics, self.attention, copilot)
        res = query_engine.process_query("Which products are running out of stock?")

        self.assertIn("answer", res)
        self.assertIn("key_points", res)
        self.assertIn("evidence", res)
        self.assertIn("recommendation", res)
        self.assertIn("data_sufficiency", res)
        self.assertIn("AI explanation is currently unavailable", res["answer"])

    def test_intent_classification(self):
        """Test natural language question intent parsing."""
        copilot = GeminiCopilot(api_key="")

        self.assertEqual(copilot.classify_question_intent("Which products are likely to run out?"), "INVENTORY_RISK")
        self.assertEqual(copilot.classify_question_intent("Which products are selling slowly?"), "SLOW_MOVING")
        self.assertEqual(copilot.classify_question_intent("Which products are overstocked?"), "OVERSTOCK")
        self.assertEqual(copilot.classify_question_intent("What should I review today?"), "GENERAL_ATTENTION")
        self.assertEqual(copilot.classify_question_intent("Which store has strongest growth?"), "STORE_SUMMARY")
        self.assertEqual(copilot.classify_question_intent("How did Amul Milk perform this month?"), "PRODUCT_PERFORMANCE")
        self.assertEqual(copilot.classify_question_intent("What is the supplier lead time for Rice?"), "UNSUPPORTED_DATA")

    def test_unsupported_data_intent_handling(self):
        """Test that questions requiring missing metadata return INSUFFICIENT data status."""
        copilot = GeminiCopilot(api_key="mock_key")
        res = copilot.generate_grounded_response("What is the supplier lead time?", {})

        self.assertEqual(res["data_sufficiency"], "INSUFFICIENT")
        self.assertIn("does not contain information", res["answer"])
        self.assertEqual(len(res["key_points"]), 2)

    def test_successful_structured_response_mocked(self):
        """Test Gemini SDK returning valid JSON output (mocked)."""
        mock_json_text = """{
            "answer": "Amul Fresh Milk PRD001 is facing stock depletion risk at STR001.",
            "key_points": ["PRD001 inventory will deplete in 2.5 days at STR001."],
            "evidence": ["STR001 stock = 50 units, daily velocity = 20.0 units/day."],
            "recommendation": "Reorder 100 units immediately.",
            "assumptions": ["Daily sales velocity remains constant."],
            "data_sufficiency": "SUFFICIENT"
        }"""

        copilot = GeminiCopilot(api_key="mock_key")
        copilot._client = MagicMock()

        # Mock genai client response
        mock_res = MagicMock()
        mock_res.text = mock_json_text
        copilot._client.models.generate_content.return_value = mock_res

        context = {"findings": [{"product_id": "PRD001", "store_id": "STR001"}]}
        res = copilot.generate_grounded_response("Which products are running out?", context)

        self.assertEqual(res["data_sufficiency"], "SUFFICIENT")
        self.assertIn("Amul Fresh Milk", res["answer"])
        self.assertEqual(len(res["key_points"]), 1)
        self.assertIn("Reorder", res["recommendation"])

    def test_malformed_response_handling(self):
        """Test Gemini SDK returning non-JSON malformed output."""
        copilot = GeminiCopilot(api_key="mock_key")
        copilot._client = MagicMock()

        mock_res = MagicMock()
        mock_res.text = "This is raw unformatted text without any JSON brackets."
        copilot._client.models.generate_content.return_value = mock_res

        context = {"findings": [{"product_name": "Rice", "store_name": "Store 1", "summary": "Low stock"}]}
        res = copilot.generate_grounded_response("Which items need review?", context)

        # Should fall back to deterministic response safely
        self.assertIn("Malformed model response", res["answer"])
        self.assertGreater(len(res["key_points"]), 0)

    def test_empty_response_handling(self):
        """Test Gemini SDK returning empty string response."""
        copilot = GeminiCopilot(api_key="mock_key")
        copilot._client = MagicMock()

        mock_res = MagicMock()
        mock_res.text = "   "
        copilot._client.models.generate_content.return_value = mock_res

        context = {"findings": [{"product_name": "Milk", "store_name": "Store 2"}]}
        res = copilot.generate_grounded_response("Any issues?", context)

        self.assertIn("Empty model response", res["answer"])

    def test_api_exception_handling(self):
        """Test Gemini SDK raising an exception (API error / timeout / rate limit)."""
        copilot = GeminiCopilot(api_key="mock_key_secret_12345")
        copilot._client = MagicMock()
        copilot._client.models.generate_content.side_effect = Exception("API rate limit exceeded for key mock_key_secret_12345")

        context = {"findings": [{"product_name": "Wheat", "store_name": "Store 3"}]}
        res = copilot.generate_grounded_response("Check wheat stock", context)

        self.assertIn("Gemini API error", res["answer"])
        # Ensure secret API key is sanitized and redacted from output text
        self.assertNotIn("mock_key_secret_12345", res["answer"])

    def test_deterministic_evidence_preserved_in_fallback(self):
        """Verify deterministic findings are preserved in fallback results."""
        copilot = GeminiCopilot(api_key="")
        query_engine = QueryEngine(self.loader, self.analytics, self.attention, copilot)

        res = query_engine.process_query("What should I review today?")
        self.assertIn("key_points", res)
        self.assertIn("evidence", res)
        self.assertGreater(len(res["key_points"]), 0)
        self.assertGreater(len(res["evidence"]), 0)

    def test_ai_analyze_api_endpoint(self):
        """Test POST /api/ai/analyze backend endpoint."""
        payload = {"question": "Which products are likely to run out?"}
        res = self.client.post("/api/ai/analyze", json=payload)

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("answer", data)
        self.assertIn("key_points", data)
        self.assertIn("evidence", data)
        self.assertIn("recommendation", data)
        self.assertIn("data_sufficiency", data)

    def test_ai_analyze_api_endpoint_validation(self):
        """Test validation for empty question and invalid store_id."""
        # Empty question -> 400
        res_empty = self.client.post("/api/ai/analyze", json={"question": "  "})
        self.assertEqual(res_empty.status_code, 400)
        self.assertIn("Question cannot be empty", res_empty.json()["detail"])

        # Invalid store_id -> 400
        res_invalid_store = self.client.post("/api/ai/analyze", json={"question": "Show sales", "store_id": "INVALID_STORE"})
        self.assertEqual(res_invalid_store.status_code, 400)
        self.assertIn("Invalid store_id", res_invalid_store.json()["detail"])

    @unittest.skipUnless(os.getenv("GEMINI_API_KEY"), "Real Gemini API integration test skipped because GEMINI_API_KEY is not set.")
    def test_real_gemini_integration(self):
        """Live Integration test using real GEMINI_API_KEY if present in environment."""
        copilot = GeminiCopilot()
        self.assertTrue(copilot.is_available())

        query_engine = QueryEngine(self.loader, self.analytics, self.attention, copilot)
        res = query_engine.process_query("Which products are running out of stock?")

        self.assertIn("answer", res)
        self.assertIn("key_points", res)
        self.assertIn(res["data_sufficiency"], ["SUFFICIENT", "LIMITED", "INSUFFICIENT"])


if __name__ == "__main__":
    unittest.main()
