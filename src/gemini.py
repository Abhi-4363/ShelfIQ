"""
ShelfIQ Gemini API Wrapper & Copilot Intelligence Engine
Provides natural-language understanding, intent classification, and grounded response synthesis.
Relies strictly on deterministic Python evidence from DataLoader, AnalyticsEngine, and AttentionEngine.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

# Centralized Model & System Configuration
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

SYSTEM_PROMPT = """You are ShelfIQ, a retail sales and inventory decision-support assistant.

STRICT OPERATIONAL GROUNDING RULES:
1. Use ONLY supplied ShelfIQ evidence. Never use your own training data for retail facts.
2. Never invent numbers.
3. Never invent products.
4. Never invent stores.
5. Never invent dates.
6. Never invent trends.
7. Never invent inventory quantities.
8. Never invent percentages.
9. Do not turn assumptions into facts.
10. If evidence is insufficient, explicitly say so.
11. If the question cannot be answered from available data, say so clearly.
12. Preserve exact numerical values from the evidence payload.
13. Recommendations must be directly supported by evidence.
14. Never claim an action was performed.
15. Never place an order or perform an external action.

RESPONSE FORMAT — Output ONLY valid JSON matching this exact structure (no markdown, no extra text):
{
    "intent": "<INTENT_NAME>",
    "answer": "<Concise executive summary response, 1-3 sentences>",
    "key_points": ["<Key point 1>", "<Key point 2>"],
    "supporting_numbers": [
        {"product_name": "...", "store_name": "...", "metric": "...", "value": "..."}
    ],
    "evidence": [
        {
            "source": "Inventory analysis | Sales analysis | Attention engine | Product performance | Store analysis",
            "product_id": "...",
            "product_name": "...",
            "store_id": "...",
            "store_name": "...",
            "metric": "...",
            "value": "...",
            "supporting_values": {},
            "period": "Last 90 days"
        }
    ],
    "recommendation": "<Actionable decision-support suggestion>",
    "assumptions": ["<Explicit assumption 1>"],
    "data_sufficiency": "SUFFICIENT"
}

The data_sufficiency field must be exactly one of: SUFFICIENT, LIMITED, INSUFFICIENT."""

# Keywords for Intent Classification — ordered from most specific to least specific
INTENT_PATTERNS = {
    "INVENTORY_RISK": [
        r"run out", r"stock.?out", r"stockout", r"low stock", r"deplete",
        r"running out", r"finish soon", r"going to finish", r"what is going to finish",
        r"less than \d+ days", r"stock left", r"stock remaining",
        r"likely to run out", r"which products.*run out", r"products.*finish",
        r"about to.*run", r"almost out", r"nearly out", r"days of stock",
        r"days remaining", r"days left", r"out of stock risk",
    ],
    "SLOW_MOVING": [
        r"slow.?moving", r"not moving", r"dead stock", r"slow sales",
        r"low velocity", r"selling slowly", r"slowest selling", r"slowest moving",
        r"slow velocity", r"poor velocity", r"low turnover",
    ],
    "OVERSTOCK": [
        r"overstock", r"excess inventory", r"too much stock", r"overstocked",
        r"surplus", r"excess stock", r"too many units", r"high stock",
    ],
    "SALES_SPIKE": [
        r"sales spike", r"surge", r"sales increase", r"increased sales",
        r"spike", r"unusual spike", r"highest growth", r"unusual.*sales",
        r"did anything unusual", r"anything unusual.*sales", r"unusual happen",
        r"sales.*unusual", r"sales jumped", r"sales soar", r"sales surged",
    ],
    "SALES_DROP": [
        r"sales drop", r"decline", r"sales decrease", r"decreased sales",
        r"drop in sales", r"unusual drop", r"sales fell", r"sales fallen",
        r"sales declined", r"sales slowed", r"fall in sales",
    ],
    "GENERAL_ATTENTION": [
        r"review today", r"what should i review", r"what to review",
        r"attention", r"priority", r"urgent", r"what needs attention",
        r"need attention", r"products that need attention",
        r"show me.*attention", r"what should i look at",
        r"look at today", r"needs.*review", r"check today",
        r"what is important", r"what is critical", r"anything to review",
        r"items to review", r"operational issues",
    ],
    "STORE_SUMMARY": [
        r"store performing", r"my store", r"store performance",
        r"best store", r"store summary", r"how is my store",
        r"strongest growth", r"store growth", r"top store",
        r"all stores", r"across stores", r"store comparison",
        r"how are.*stores", r"store.*doing",
    ],
    "PRODUCT_PERFORMANCE": [
        r"how did .+ perform", r"how is .+ performing", r"how did .+ do",
        r"how are .+ doing",
        r"performance of .+", r"sales for .+", r".+ this month",
        r".+ this week", r"how is .+ doing", r"show me .+ performance",
    ],
    "UNSUPPORTED_DATA": [
        r"supplier", r"lead time", r"employee", r"salary", r"weather",
        r"competitor", r"profit margin", r"warehouse", r"delivery time",
        r"shipping cost", r"discount", r"promotion", r"marketing",
    ],
}

# Domain vocabulary to check relevance for unknown non-retail questions
RETAIL_DOMAIN_KEYWORDS = [
    "stock", "sale", "sales", "inventory", "product", "store", "item", "category",
    "velocity", "run out", "finish", "deplete", "overstock", "slow", "spike", "drop",
    "review", "attention", "perform", "performance", "amul", "milk", "rice", "oil",
    "biscuit", "biscuits", "soap", "tea", "dal", "chips", "juice", "hyderabad", "banjara",
    "kukatpally", "secunderabad", "str001", "str002", "str003", "str004", "prd",
    "issue", "issues", "problem", "anything", "check", "health", "toned", "packaged",
    "pepsi", "nimyle", "colgate", "horlicks", "maggi", "aashirvaad", "lifebuoy",
    "parachute", "britannia", "parle",
]


class GeminiCopilot:
    """
    Gemini Copilot Service for ShelfIQ.
    Handles intent parsing, prompt construction, Gemini API calls, and structured fallback generation.
    Gemini ONLY explains supplied evidence — it never generates retail facts.
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
        """Check if Gemini API key is configured."""
        return bool(self.api_key and self.api_key.strip())

    def classify_question_intent(self, question: str) -> str:
        """
        Classify natural-language user question into a structured intent.
        Uses deterministic regex patterns — no Gemini call needed for routing.
        """
        q_lower = question.lower().strip()

        # Check unsupported data intent first (highest priority rejection)
        for pattern in INTENT_PATTERNS["UNSUPPORTED_DATA"]:
            if re.search(pattern, q_lower):
                return "UNSUPPORTED_DATA"

        # Check domain-specific intents in priority order
        intent_order = [
            "INVENTORY_RISK",
            "SLOW_MOVING",
            "OVERSTOCK",
            "SALES_SPIKE",
            "SALES_DROP",
            "STORE_SUMMARY",
            "PRODUCT_PERFORMANCE",
            "GENERAL_ATTENTION",
        ]

        for intent in intent_order:
            patterns = INTENT_PATTERNS.get(intent, [])
            for pattern in patterns:
                if re.search(pattern, q_lower):
                    return intent

        # Check domain relevance for unknown non-retail queries
        words = re.findall(r"\w+", q_lower)
        is_retail_relevant = any(w in RETAIL_DOMAIN_KEYWORDS for w in words)
        if not is_retail_relevant:
            return "UNKNOWN"

        return "GENERAL_ATTENTION"

    def generate_grounded_response(
        self,
        user_question: str,
        deterministic_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a grounded response using supplied evidence from the deterministic backend.
        Falls back safely to deterministic Python analysis if Gemini API is unavailable or fails.
        Gemini explains evidence — it never generates retail facts.
        """
        intent = deterministic_context.get("intent") or self.classify_question_intent(user_question)

        # Handle explicit ambiguity intent
        if intent == "AMBIGUOUS":
            candidates = deterministic_context.get("candidates", [])
            cand_names = [
                f"{c['product_name']} ({c['product_id']})" for c in candidates[:4]
            ]
            return {
                "intent": "AMBIGUOUS",
                "question": user_question,
                "answer": (
                    f"Multiple matching products found. Please specify which product or store "
                    f"you would like me to analyze: {', '.join(cand_names)}."
                ),
                "key_points": [
                    f"Found {len(candidates)} matching products for your search query.",
                    "Please provide the exact product name or ID for a focused analysis.",
                ],
                "supporting_numbers": [],
                "evidence": [
                    {
                        "source": "Catalogue analysis",
                        "metric": "matched_products",
                        "value": len(candidates),
                        "supporting_values": {"candidate_products": cand_names},
                        "period": "Current Catalog",
                    }
                ],
                "recommendation": "Specify the exact product name or ID for detailed analysis.",
                "assumptions": ["Ambiguous query resolved by requesting entity clarification."],
                "data_sufficiency": "INSUFFICIENT",
            }

        # Handle unsupported data scope
        if intent == "UNSUPPORTED_DATA":
            return {
                "intent": "UNSUPPORTED_DATA",
                "question": user_question,
                "answer": "The current ShelfIQ dataset does not contain information to answer this question.",
                "key_points": [
                    "Requested metadata (e.g. supplier lead times, employee schedules, weather) is missing from sales/inventory records.",
                    "ShelfIQ strictly avoids unsupported assumptions or guessing.",
                ],
                "supporting_numbers": [],
                "evidence": [
                    {
                        "source": "Scope Validation",
                        "metric": "dataset_schema",
                        "value": "Missing field",
                        "supporting_values": {},
                        "period": "Current Dataset Scope",
                    }
                ],
                "recommendation": "Consult external operational records for non-inventory master data.",
                "assumptions": [
                    "Dataset scope is strictly limited to sales, inventory, stores, and products catalogs."
                ],
                "data_sufficiency": "INSUFFICIENT",
            }

        # Handle unknown non-retail intent
        if intent == "UNKNOWN":
            return {
                "intent": "UNKNOWN",
                "question": user_question,
                "answer": (
                    "I can help with ShelfIQ's sales, inventory, product performance and "
                    "attention insights, but I don't have data to answer that question."
                ),
                "key_points": [
                    "Question is outside the scope of retail sales and inventory data.",
                    "Try asking about stock levels, sales velocity, product performance, or store summaries.",
                ],
                "supporting_numbers": [],
                "evidence": [
                    {
                        "source": "Scope Validation",
                        "metric": "domain_relevance",
                        "value": "Non-retail query",
                        "supporting_values": {},
                        "period": "N/A",
                    }
                ],
                "recommendation": (
                    "Ask a question related to store inventory, sales velocity, "
                    "product performance, or attention alerts."
                ),
                "assumptions": [
                    "ShelfIQ dataset strictly contains local store sales and inventory data."
                ],
                "data_sufficiency": "INSUFFICIENT",
            }

        # If Gemini API key is missing or client failed to initialize, return deterministic fallback
        if not self.is_available() or not self._client:
            return self._build_deterministic_fallback(
                user_question,
                intent,
                deterministic_context,
                "AI explanation is currently unavailable. Showing deterministic evidence.",
            )

        # Build prompt with strict system instructions and deterministic evidence
        prompt = f"""SYSTEM INSTRUCTIONS:
{SYSTEM_PROMPT}

USER QUESTION:
"{user_question}"

STRUCTURED DETERMINISTIC EVIDENCE PAYLOAD (THIS IS THE ONLY SOURCE OF TRUTH):
{json.dumps(deterministic_context, indent=2)}

IMPORTANT: Your response must use ONLY the numbers, products, stores, and metrics from the evidence payload above.
Output ONLY the JSON object — no markdown code blocks, no extra explanation text."""

        try:
            raw_text = ""
            if hasattr(self._client, "models"):
                # google-genai SDK
                res = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                raw_text = res.text
            elif hasattr(self._client, "generate_content"):
                # google-generativeai legacy SDK
                res = self._client.generate_content(prompt)
                raw_text = res.text
            else:
                return self._build_deterministic_fallback(
                    user_question,
                    intent,
                    deterministic_context,
                    "AI explanation is currently unavailable.",
                )

            if not raw_text or not raw_text.strip():
                return self._build_deterministic_fallback(
                    user_question,
                    intent,
                    deterministic_context,
                    "Empty model response received.",
                )

            # Strip markdown fences if model wraps response in ```json ... ```
            cleaned_text = re.sub(r"```(?:json)?\s*", "", raw_text).strip().rstrip("`").strip()

            # Extract JSON object from response
            json_match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))

                # Enforce intent from deterministic classifier — never trust model's intent
                parsed["intent"] = intent
                parsed["question"] = user_question

                # Fill any missing required fields from deterministic context
                if "answer" not in parsed or not parsed["answer"]:
                    parsed["answer"] = "Analysis derived from deterministic ShelfIQ context."
                if "key_points" not in parsed:
                    parsed["key_points"] = []
                if "supporting_numbers" not in parsed:
                    parsed["supporting_numbers"] = deterministic_context.get("supporting_numbers", [])
                if "evidence" not in parsed or not parsed["evidence"]:
                    parsed["evidence"] = deterministic_context.get("evidence", [])
                if "recommendation" not in parsed or not parsed["recommendation"]:
                    parsed["recommendation"] = "Review items indicated by deterministic rules."
                if "assumptions" not in parsed:
                    parsed["assumptions"] = []
                if "data_sufficiency" not in parsed:
                    parsed["data_sufficiency"] = deterministic_context.get("data_sufficiency", "SUFFICIENT")

                # Validate data_sufficiency value
                valid_sufficiency = {"SUFFICIENT", "LIMITED", "INSUFFICIENT"}
                if parsed.get("data_sufficiency") not in valid_sufficiency:
                    parsed["data_sufficiency"] = deterministic_context.get("data_sufficiency", "SUFFICIENT")

                return parsed
            else:
                return self._build_deterministic_fallback(
                    user_question,
                    intent,
                    deterministic_context,
                    "Malformed model response received.",
                )

        except json.JSONDecodeError:
            return self._build_deterministic_fallback(
                user_question,
                intent,
                deterministic_context,
                "Malformed model response received.",
            )
        except Exception as e:
            # Sanitize exception message to prevent API key leaks
            err_msg = str(e)
            if self.api_key and self.api_key in err_msg:
                err_msg = err_msg.replace(self.api_key, "[REDACTED_API_KEY]")
            return self._build_deterministic_fallback(
                user_question,
                intent,
                deterministic_context,
                f"Gemini API error: {err_msg}",
            )

    def _build_deterministic_fallback(
        self,
        question: str,
        intent: str,
        context: Dict[str, Any],
        fallback_reason: str,
    ) -> Dict[str, Any]:
        """
        Build a structured evidence response strictly from deterministic Python results.
        Called when Gemini is unavailable, fails, or returns an unparse-able response.
        """
        findings = context.get("findings", [])
        sufficiency = context.get("data_sufficiency", "SUFFICIENT")
        evidence_objects = context.get("evidence", [])
        supporting_numbers = context.get("supporting_numbers", [])

        # No data available for this query at all
        if (
            not findings
            and "sales_summary" not in context
            and "stores_summary" not in context
            and "product_performance" not in context
            and not evidence_objects
        ):
            return {
                "intent": intent,
                "question": question,
                "answer": f"Analysis complete. No critical issues detected for the query criteria. ({fallback_reason})",
                "key_points": [
                    "All evaluated inventory items are within healthy operating parameters."
                ],
                "supporting_numbers": [],
                "evidence": [
                    {
                        "source": "Inventory analysis",
                        "metric": "inventory_status",
                        "value": "Healthy",
                        "supporting_values": {},
                        "period": "Last 90 days",
                    }
                ],
                "recommendation": "Continue standard daily inventory monitoring.",
                "assumptions": [
                    "Calculations derived strictly from deterministic Python analytics engine."
                ],
                "data_sufficiency": sufficiency,
            }

        # Build key points from available findings
        key_points = []
        first_rec = "Review items indicated by the deterministic rules engine."

        if findings:
            for f in findings[:5]:
                p_name = f.get("product_name", f.get("product_id", "Product"))
                s_name = f.get("store_name", f.get("store_id", "Store"))
                summary = f.get("metric_summary", f.get("summary", ""))
                key_points.append(f"{p_name} ({s_name}): {summary}")
            first_rec = findings[0].get("recommendation", "Review item replenishment.")

        elif "product_performance" in context:
            for p in context["product_performance"][:5]:
                p_name = p.get("product_name", "Product")
                key_points.append(
                    f"{p_name}: Total Sales ₹{p.get('total_sales_amount', 0):,.2f}, "
                    f"Units {p.get('total_units_sold', 0)}"
                )
            first_rec = "Review top performing product category velocity."

        elif "stores_summary" in context:
            for st in context["stores_summary"]:
                key_points.append(
                    f"{st.get('store_name')}: Total Sales ₹{st.get('total_sales_amount', 0):,.2f}"
                )
            first_rec = "Compare store sales velocity against inventory allocations."

        else:
            key_points.append("Deterministic sales summary computed.")
            first_rec = "Review executive inventory dashboard."

        return {
            "intent": intent,
            "question": question,
            "answer": f"Identified operational evidence matching your query. ({fallback_reason})",
            "key_points": key_points,
            "supporting_numbers": supporting_numbers,
            "evidence": evidence_objects
            or [
                {
                    "source": "Attention engine",
                    "metric": "attention_findings",
                    "value": len(findings),
                    "supporting_values": {},
                    "period": "Last 90 days",
                }
            ],
            "recommendation": first_rec,
            "assumptions": [
                "Analysis based on factual historical daily sales velocity from Python backend."
            ],
            "data_sufficiency": sufficiency,
        }
