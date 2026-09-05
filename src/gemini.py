"""
ShelfIQ Gemini API Wrapper & Copilot Intelligence Engine
Provides natural-language understanding, intent classification, and grounded response synthesis.
Rely strictly on deterministic Python evidence from DataLoader, AnalyticsEngine, and AttentionEngine.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

# Centralized Model & System Configuration
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """You are ShelfIQ, a retail sales and inventory decision-support assistant.

STRICT OPERATIONAL GROUNDING RULES:
1. Use ONLY the supplied evidence payload.
2. Never invent sales numbers, stock quantities, days remaining, percentages, or metrics.
3. Never invent products, store names, suppliers, or dates.
4. Never claim a sales or stock trend without direct evidence in the payload.
5. If evidence is insufficient or missing, say so clearly by setting "data_sufficiency": "INSUFFICIENT".
6. Preserve numerical values exactly without alteration or rounding.
7. Explain calculations only when the calculation is supplied or directly derivable from supplied evidence.
8. Recommendations must be actionable decision-support suggestions for retail managers.
9. Do not claim that an action has been performed.
10. Do not place orders or perform external actions.
11. Clearly distinguish facts (derived from data) from assumptions.
12. Output ONLY valid JSON matching this exact structure:

{
    "answer": "<Concise executive summary response>",
    "key_points": ["<Key point 1>", "<Key point 2>"],
    "evidence": ["<Evidence item 1>", "<Evidence item 2>"],
    "recommendation": "<Actionable decision-support suggestion>",
    "assumptions": ["<Explicit assumption 1>"],
    "data_sufficiency": "SUFFICIENT" | "LIMITED" | "INSUFFICIENT"
}"""

# Keywords for Intent Classification
INTENT_PATTERNS = {
    "STOCK_OUT_RISK": [r"run out", r"stock-out", r"stockout", r"low stock", r"deplete", r"running out"],
    "SLOW_MOVING": [r"slow moving", r"not moving", r"dead stock", r"slow sales", r"low velocity", r"selling slowly"],
    "OVERSTOCK": [r"overstock", r"excess inventory", r"too much stock", r"overstocked"],
    "SALES_SPIKE": [r"sales spike", r"surge", r"sales increase", r"increased sales", r"spike"],
    "SALES_DROP": [r"sales drop", r"decline", r"sales decrease", r"decreased sales", r"drop"],
    "ATTENTION_SUMMARY": [r"review today", r"attention", r"priority", r"urgent", r"what needs attention", r"what to review"],
    "STORE_GROWTH": [r"strongest growth", r"store growth", r"top store", r"best store", r"store performance"],
    "PRODUCT_PERFORMANCE": [r"perform", r"performance", r"doing", r"sales for", r"how did"],
    "UNSUPPORTED_DATA": [r"supplier", r"lead time", r"employee", r"salary", r"weather", r"competitor", r"profit margin", r"warehouse", r"delivery time"]
}

class GeminiCopilot:
    """
    Gemini Copilot Service for ShelfIQ.
    Handles intent parsing, prompt construction, Gemini API calls, and structured fallback generation.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = DEFAULT_GEMINI_MODEL):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None

        if self.api_key and self.api_key.strip():
            self._init_client()

    def _init_client(self):
        """Initialize the Google Gemini SDK client safely."""
        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        except Exception:
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=self.api_key)
                self._client = genai_legacy.GenerativeModel(self.model_name)
            except Exception:
                self._client = None

    def is_available(self) -> bool:
        """Check if Gemini API key is configured and client initialized."""
        return bool(self.api_key and self.api_key.strip())

    def classify_question_intent(self, question: str) -> str:
        """Categorize natural-language user question into structured intent."""
        q_lower = question.lower().strip()

        # Check unsupported data intent first
        for pattern in INTENT_PATTERNS["UNSUPPORTED_DATA"]:
            if re.search(pattern, q_lower):
                return "UNSUPPORTED_DATA"

        for intent, patterns in INTENT_PATTERNS.items():
            if intent == "UNSUPPORTED_DATA":
                continue
            for pattern in patterns:
                if re.search(pattern, q_lower):
                    return intent

        return "GENERAL_QUERY"

    def generate_grounded_response(
        self,
        user_question: str,
        deterministic_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate grounded response from Gemini using supplied evidence payload.
        Falls back safely to deterministic Python analysis if Gemini API is unavailable or fails.
        """
        intent = self.classify_question_intent(user_question)

        # Handle explicit unsupported question intent
        if intent == "UNSUPPORTED_DATA":
            return {
                "question": user_question,
                "answer": "The current ShelfIQ dataset does not contain information to answer this question.",
                "key_points": [
                    "Requested metadata (e.g. supplier lead times, employee schedules, weather) is missing from sales/inventory records.",
                    "ShelfIQ strictly avoids unsupported assumptions or guessing."
                ],
                "evidence": [
                    "Data scope: local store sales.csv and inventory.csv schemas.",
                    "Attribute missing from deterministic dataset."
                ],
                "recommendation": "Consult external operational records for non-inventory master data.",
                "assumptions": ["Dataset scope is strictly limited to sales, inventory, stores, and products catalogs."],
                "data_sufficiency": "INSUFFICIENT"
            }

        # If Gemini API key is missing or client failed to initialize, return deterministic fallback
        if not self.is_available() or not self._client:
            return self._build_deterministic_fallback(
                user_question, intent, deterministic_context,
                "AI explanation is temporarily unavailable. The deterministic ShelfIQ analysis is still available."
            )

        # Construct prompt with strict system instructions and evidence
        prompt = f"""SYSTEM INSTRUCTIONS:
{SYSTEM_PROMPT}

USER QUESTION:
"{user_question}"

STRUCTURED DETERMINISTIC EVIDENCE PAYLOAD (TRUTH):
{json.dumps(deterministic_context, indent=2)}

Generate structured JSON response following the strict rules:"""

        try:
            raw_text = ""
            if hasattr(self._client, "models"):
                # google.genai SDK
                res = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                raw_text = res.text
            elif hasattr(self._client, "generate_content"):
                # google.generativeai SDK
                res = self._client.generate_content(prompt)
                raw_text = res.text
            else:
                return self._build_deterministic_fallback(
                    user_question, intent, deterministic_context,
                    "AI explanation is temporarily unavailable. The deterministic ShelfIQ analysis is still available."
                )

            if not raw_text or not raw_text.strip():
                return self._build_deterministic_fallback(
                    user_question, intent, deterministic_context,
                    "Empty model response received. Displaying deterministic ShelfIQ analysis."
                )

            # Parse JSON from response
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                parsed["question"] = user_question
                
                # Standardize required schema fields
                if "answer" not in parsed:
                    parsed["answer"] = "Analysis derived from deterministic ShelfIQ context."
                if "key_points" not in parsed:
                    parsed["key_points"] = []
                if "evidence" not in parsed:
                    parsed["evidence"] = []
                if "recommendation" not in parsed:
                    parsed["recommendation"] = "Review items indicated by deterministic rules."
                if "assumptions" not in parsed:
                    parsed["assumptions"] = []
                if "data_sufficiency" not in parsed:
                    parsed["data_sufficiency"] = deterministic_context.get("data_sufficiency", "SUFFICIENT")
                return parsed
            else:
                return self._build_deterministic_fallback(
                    user_question, intent, deterministic_context,
                    "Malformed model response received. Displaying deterministic ShelfIQ analysis."
                )

        except Exception as e:
            # Clean exception message to prevent secret leaks
            err_msg = str(e)
            if self.api_key and self.api_key in err_msg:
                err_msg = err_msg.replace(self.api_key, "[REDACTED_API_KEY]")
            return self._build_deterministic_fallback(
                user_question, intent, deterministic_context,
                f"Gemini API error: {err_msg}"
            )

    def _build_deterministic_fallback(
        self,
        question: str,
        intent: str,
        context: Dict[str, Any],
        fallback_reason: str
    ) -> Dict[str, Any]:
        """Build structured evidence response strictly from deterministic Python results."""
        findings = context.get("findings", [])
        sufficiency = context.get("data_sufficiency", "SUFFICIENT")

        if not findings and "sales_summary" not in context and "stores_summary" not in context and "product_performance" not in context:
            return {
                "question": question,
                "answer": f"Analysis complete. No critical issues detected for the query criteria. ({fallback_reason})",
                "key_points": ["All evaluated inventory items are within healthy operating parameters."],
                "evidence": ["Deterministic sales and inventory records analyzed across all active stores."],
                "recommendation": "Continue standard daily inventory monitoring.",
                "assumptions": ["Calculations derived strictly from deterministic Python analytics engine."],
                "data_sufficiency": sufficiency
            }

        key_points = []
        evidence_list = []

        if findings:
            for f in findings[:5]:
                p_name = f.get("product_name", f.get("product_id", "Product"))
                s_name = f.get("store_name", f.get("store_id", "Store"))
                summary = f.get("metric_summary", f.get("summary", ""))

                key_points.append(f"{p_name} ({s_name}): {summary}")
                ev_detail = f.get("evidence", {})
                ev_str = f"{p_name} @ {s_name} - Metric: {ev_detail.get('metric', 'value')}, Days Remaining: {ev_detail.get('days_remaining_display', 'N/A')}"
                evidence_list.append(ev_str)
            first_rec = findings[0].get("recommendation", "Review item replenishment.")
        elif "product_performance" in context:
            perf = context["product_performance"]
            for p in perf[:5]:
                p_name = p.get("product_name", "Product")
                key_points.append(f"{p_name}: Total Sales ${p.get('total_sales_amount', 0):,.2f}, Total Units {p.get('total_units_sold', 0)}")
                evidence_list.append(f"Product {p_name} ({p.get('product_id')}): trend {p.get('sales_trend', 'STABLE')}")
            first_rec = "Review top performing product category velocity."
        elif "stores_summary" in context:
            stores = context["stores_summary"]
            for st in stores:
                key_points.append(f"{st.get('store_name')}: Total Sales ${st.get('total_sales_amount', 0):,.2f}")
                evidence_list.append(f"Store {st.get('store_name')} ({st.get('store_id')}): {st.get('total_units_sold')} units sold")
            first_rec = "Compare store sales velocity against inventory allocations."
        else:
            key_points.append("Deterministic sales summary computed.")
            evidence_list.append("Sales and inventory data summarized across selected scope.")
            first_rec = "Review executive inventory dashboard."

        return {
            "question": question,
            "answer": f"Identified operational evidence matching your query. ({fallback_reason})",
            "key_points": key_points,
            "evidence": evidence_list,
            "recommendation": first_rec,
            "assumptions": ["Analysis based on factual historical daily sales velocity from Python backend."],
            "data_sufficiency": sufficiency
        }
