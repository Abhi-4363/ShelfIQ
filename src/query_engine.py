"""
ShelfIQ Query Engine
Orchestrates Copilot workflow: Intent classification → Deterministic evidence retrieval
→ Evidence packaging → Gemini explanation.

Architecture:
  USER QUESTION
        ↓
  classify_question_intent()  [deterministic regex — no AI needed]
        ↓
  _fetch_deterministic_context()  [Python analytics/rules — source of truth]
        ↓
  gemini.generate_grounded_response()  [AI explains evidence only]
        ↓
  Structured grounded response
"""

import re
from typing import Dict, Any, Optional, List

# Store name → canonical store_id mapping
STORE_NAME_TO_ID = {
    "hyderabad central": "STR001",
    "hyderabad": "STR001",
    "str001": "STR001",
    "banjara hills": "STR002",
    "banjara": "STR002",
    "str002": "STR002",
    "kukatpally": "STR003",
    "str003": "STR003",
    "secunderabad": "STR004",
    "str004": "STR004",
}

# Evidence source labels (human-readable, used for citations)
SOURCE_INVENTORY = "Inventory analysis"
SOURCE_SALES = "Sales analysis"
SOURCE_ATTENTION = "Attention engine"
SOURCE_PRODUCT = "Product performance"
SOURCE_STORE = "Store analysis"
SOURCE_CATALOGUE = "Catalogue analysis"


class QueryEngine:
    """
    Query Engine for ShelfIQ Copilot.

    Coordinates:
    1. Question intent classification (deterministic regex)
    2. Targeted evidence retrieval from analytics & rules engines
    3. Evidence packaging into structured evidence objects
    4. Grounded response synthesis via Gemini (explanation only)
    """

    def __init__(self, data_loader, analytics_engine, attention_engine, gemini_copilot):
        self.data_loader = data_loader
        self.analytics = analytics_engine
        self.attention = attention_engine
        self.gemini = gemini_copilot

    def process_query(
        self,
        question: str,
        store_id: Optional[str] = None,
        previous_intent: Optional[str] = None,
        previous_product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a natural-language user question end-to-end.

        Steps:
        1. Classify question intent and resolve store/product entities or follow-ups.
        2. Fetch exact deterministic facts from analytics & rules engine.
        3. Send structured evidence to Gemini for grounded response synthesis.
        """
        q_lower = question.lower().strip()

        # Extract store_id from question text if not supplied explicitly
        detected_store_id = store_id
        if not detected_store_id:
            for s_term, s_id in STORE_NAME_TO_ID.items():
                if s_term in q_lower:
                    detected_store_id = s_id
                    break

        # Detect contextual follow-up questions (e.g. "What about Hyderabad Central?")
        is_followup = bool(
            re.search(r"what about|how about|show for|show only|and what about|same for", q_lower)
            or (detected_store_id and len(q_lower.split()) <= 5)
        )

        intent = self.gemini.classify_question_intent(question)

        # Inherit previous intent for follow-up queries
        if is_followup and previous_intent and previous_intent not in [
            "UNSUPPORTED_DATA", "UNKNOWN", "AMBIGUOUS"
        ]:
            intent = previous_intent

        context = self._fetch_deterministic_context(
            question=question,
            intent=intent,
            store_id=detected_store_id,
            previous_product_id=previous_product_id,
        )

        response = self.gemini.generate_grounded_response(
            user_question=question,
            deterministic_context=context,
        )

        return response

    def _fetch_deterministic_context(
        self,
        question: str,
        intent: str,
        store_id: Optional[str] = None,
        previous_product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch targeted deterministic evidence from Python backend based on question intent.

        CRITICAL: Only the relevant, minimal evidence is sent to Gemini.
        The entire CSV dataset is NEVER sent.
        Every factual claim is traceable to an evidence object.
        """
        q_lower = question.lower().strip()
        products = self.data_loader.get_products()
        stores_map = {s["store_id"]: s["store_name"] for s in self.data_loader.get_stores()}

        # Short-circuit for intents that need no evidence lookup
        if intent in ["UNSUPPORTED_DATA", "UNKNOWN"]:
            return {
                "intent": intent,
                "question": question,
                "findings": [],
                "evidence": [],
                "supporting_numbers": [],
                "data_sufficiency": "INSUFFICIENT",
            }

        # --- Product entity detection ---
        # Look for explicit product mentions in the question text
        matched_products = self._find_matched_products(q_lower, products)

        # If generic term matches multiple products and intent is PRODUCT_PERFORMANCE → AMBIGUOUS
        if (
            len(matched_products) > 1
            and intent not in [
                "INVENTORY_RISK", "SLOW_MOVING", "OVERSTOCK",
                "SALES_SPIKE", "SALES_DROP", "GENERAL_ATTENTION", "STORE_SUMMARY",
            ]
        ):
            return {
                "intent": "AMBIGUOUS",
                "question": question,
                "candidates": matched_products,
                "evidence": [
                    {
                        "source": SOURCE_CATALOGUE,
                        "product_id": p["product_id"],
                        "product_name": p["product_name"],
                        "metric": "matched_product",
                        "value": p["category"],
                        "period": "Current Catalog",
                    }
                    for p in matched_products
                ],
                "supporting_numbers": [],
                "data_sufficiency": "INSUFFICIENT",
            }

        matched_product = matched_products[0] if matched_products else None

        # Use previous product ID if this is a follow-up with no new product mentioned
        if not matched_product and previous_product_id:
            p_found = [p for p in products if p["product_id"] == previous_product_id]
            if p_found:
                matched_product = p_found[0]

        # --- Route by intent ---

        # PRODUCT_PERFORMANCE or specific product mention
        if matched_product:
            return self._build_product_context(
                matched_product, store_id, stores_map, question
            )

        # Attention-based intents: INVENTORY_RISK, SLOW_MOVING, OVERSTOCK, SALES_SPIKE, SALES_DROP, GENERAL_ATTENTION
        if intent in [
            "INVENTORY_RISK", "SLOW_MOVING", "OVERSTOCK",
            "SALES_SPIKE", "SALES_DROP", "GENERAL_ATTENTION",
        ]:
            return self._build_attention_context(
                intent, q_lower, store_id, stores_map, question
            )

        # STORE_SUMMARY
        if intent == "STORE_SUMMARY":
            return self._build_store_summary_context(store_id, stores_map, question)

        # Fallback — general attention context
        return self._build_general_fallback_context(store_id, stores_map, question)

    # ------------------------------------------------------------------
    # Private evidence builders — one per intent type
    # ------------------------------------------------------------------

    def _find_matched_products(self, q_lower: str, products: List[Dict]) -> List[Dict]:
        """Scan question for product name tokens and return matching products."""
        matched = []
        for p in products:
            p_name_lower = p["product_name"].lower()
            p_id_lower = p["product_id"].lower()

            # Exact full name or ID match
            if p_name_lower in q_lower or p_id_lower in q_lower:
                matched.append(p)
                continue

            # Token-level matching (e.g. "amul", "milk", "rice", "pepsi")
            stop_tokens = {"pack", "liter", "litre", "grams", "gram", "with", "from", "and", "the"}
            p_tokens = [
                w for w in re.findall(r"\w+", p_name_lower)
                if len(w) >= 4 and w not in stop_tokens
            ]
            for tok in p_tokens:
                if tok in q_lower:
                    if p not in matched:
                        matched.append(p)
                    break

        return matched

    def _build_product_context(
        self,
        matched_product: Dict,
        store_id: Optional[str],
        stores_map: Dict,
        question: str,
    ) -> Dict[str, Any]:
        """Build evidence context for a specific product performance query."""
        p_id = matched_product["product_id"]
        p_name = matched_product["product_name"]

        perf = self.analytics.calculate_product_performance(product_id=p_id, store_id=store_id)
        inv = self.analytics.calculate_inventory_metrics(product_id=p_id, store_id=store_id)
        attentions = [
            a for a in self.attention.get_all_attention_items(store_id=store_id)
            if a.get("product_id") == p_id
        ]

        evidence_list = []
        supporting_numbers = []

        # Inventory evidence objects
        for i in inv:
            s_name = i.get("store_name", stores_map.get(i.get("store_id", ""), "Store"))
            evidence_list.append({
                "source": SOURCE_INVENTORY,
                "product_id": p_id,
                "product_name": p_name,
                "store_id": i.get("store_id"),
                "store_name": s_name,
                "metric": "days_remaining",
                "value": i.get("days_remaining"),
                "supporting_values": {
                    "current_stock": i.get("current_stock"),
                    "average_daily_units": i.get("average_daily_units_sold"),
                    "days_remaining_display": i.get("days_remaining_display"),
                    "status": i.get("status"),
                    "inventory_value": i.get("inventory_value"),
                },
                "period": "Last 90 days",
            })
            supporting_numbers.extend([
                {
                    "product_name": p_name,
                    "store_name": s_name,
                    "metric": "Current Stock",
                    "value": f"{i.get('current_stock')} units",
                },
                {
                    "product_name": p_name,
                    "store_name": s_name,
                    "metric": "Average Daily Sales",
                    "value": f"{i.get('average_daily_units_sold')} units/day",
                },
                {
                    "product_name": p_name,
                    "store_name": s_name,
                    "metric": "Days Remaining",
                    "value": i.get("days_remaining_display"),
                },
            ])

        # Sales performance evidence
        if perf:
            p_perf = perf[0]
            evidence_list.append({
                "source": SOURCE_PRODUCT,
                "product_id": p_id,
                "product_name": p_name,
                "metric": "sales_performance",
                "value": f"₹{p_perf.get('total_sales_amount', 0):,.2f}",
                "supporting_values": {
                    "total_units_sold": p_perf.get("total_units_sold"),
                    "avg_daily_units": p_perf.get("avg_daily_units"),
                    "sales_trend": p_perf.get("sales_trend"),
                    "days_recorded": p_perf.get("days_recorded"),
                },
                "period": "Last 90 days",
            })
            supporting_numbers.append({
                "product_name": p_name,
                "store_name": "All Stores",
                "metric": "Total Revenue",
                "value": f"₹{p_perf.get('total_sales_amount', 0):,.2f}",
            })

        # Attention items as evidence
        for a in attentions[:3]:
            ev = a.get("evidence", {})
            evidence_list.append({
                "source": SOURCE_ATTENTION,
                "product_id": p_id,
                "product_name": p_name,
                "store_id": a.get("store_id"),
                "store_name": a.get("store_name", "Store"),
                "metric": a.get("attention_type", "").lower(),
                "value": a.get("severity"),
                "supporting_values": {
                    "metric_summary": a.get("metric_summary"),
                    "recommendation": a.get("recommendation"),
                    "days_remaining": ev.get("days_remaining"),
                },
                "period": ev.get("calculation_period", "Last 90 days"),
            })

        return {
            "intent": "PRODUCT_PERFORMANCE",
            "question": question,
            "target_product": matched_product,
            "product_performance": perf,
            "inventory_metrics": inv,
            "attention_items": attentions,
            "evidence": evidence_list,
            "supporting_numbers": supporting_numbers,
            "data_sufficiency": "SUFFICIENT" if (perf or inv) else "INSUFFICIENT",
        }

    def _build_attention_context(
        self,
        intent: str,
        q_lower: str,
        store_id: Optional[str],
        stores_map: Dict,
        question: str,
    ) -> Dict[str, Any]:
        """Build evidence context for attention-based intents."""
        # Map Copilot intent to rules engine attention_type
        attn_type_map = {
            "INVENTORY_RISK": "STOCK_OUT_RISK",
            "SLOW_MOVING": "SLOW_MOVING",
            "OVERSTOCK": "OVERSTOCK",
            "SALES_SPIKE": "SALES_SPIKE",
            "SALES_DROP": "SALES_DROP",
            "GENERAL_ATTENTION": None,  # All types
        }
        attn_type = attn_type_map.get(intent)

        findings = self.attention.get_all_attention_items(
            store_id=store_id, attention_type=attn_type
        )

        # Apply numerical days-remaining threshold filter for INVENTORY_RISK
        # e.g. "Which products have less than 3 days of stock?"
        days_match = re.search(r"less than (\d+) days?", q_lower)
        if days_match and intent == "INVENTORY_RISK":
            threshold_days = float(days_match.group(1))
            findings = [
                f for f in findings
                if f.get("evidence", {}).get("days_remaining") is not None
                and f.get("evidence", {}).get("days_remaining") <= threshold_days
            ]

        # Cap evidence to top 10 items (most critical first)
        evidence_limit = 10 if intent == "GENERAL_ATTENTION" else 8
        evidence_list = []
        supporting_numbers = []

        for f in findings[:evidence_limit]:
            p_name = f.get("product_name", f.get("product_id", "Product"))
            s_name = f.get("store_name", stores_map.get(f.get("store_id", ""), "Store"))
            ev_detail = f.get("evidence", {})

            # Choose source label and primary metric by intent
            if intent in ["SALES_SPIKE", "SALES_DROP"]:
                src_label = SOURCE_SALES
                metric_name = "sales_change"
                pct_val = ev_detail.get("percentage_change", 0.0)
                val_str = f"{pct_val:+.1f}%"
            elif intent in ["INVENTORY_RISK", "SLOW_MOVING", "OVERSTOCK"]:
                src_label = SOURCE_INVENTORY
                metric_name = intent.lower()
                val_str = ev_detail.get(
                    "days_remaining_display",
                    ev_detail.get("average_daily_units_sold", "N/A"),
                )
            else:
                src_label = SOURCE_ATTENTION
                metric_name = f.get("attention_type", "").lower()
                val_str = ev_detail.get(
                    "days_remaining_display",
                    ev_detail.get("average_daily_units_sold", "N/A"),
                )

            ev_obj = {
                "source": src_label,
                "product_id": f.get("product_id"),
                "product_name": p_name,
                "store_id": f.get("store_id"),
                "store_name": s_name,
                "metric": metric_name,
                "value": val_str,
                "supporting_values": {
                    "severity": f.get("severity"),
                    "summary": f.get("metric_summary"),
                    "current_stock": ev_detail.get("current_stock"),
                    "avg_daily_sales": ev_detail.get("average_daily_units_sold"),
                    "recommendation": f.get("recommendation"),
                },
                "period": ev_detail.get("calculation_period", "Last 90 days"),
            }

            # Add sales comparison fields for spike/drop intents
            if intent in ["SALES_SPIKE", "SALES_DROP"]:
                ev_obj["recent_value"] = ev_detail.get("recent_daily_avg")
                ev_obj["baseline_value"] = ev_detail.get("baseline_daily_avg")
                ev_obj["percentage_change"] = ev_detail.get("percentage_change")
                ev_obj["supporting_values"]["recent_value"] = ev_detail.get("recent_daily_avg")
                ev_obj["supporting_values"]["baseline_value"] = ev_detail.get("baseline_daily_avg")
                ev_obj["supporting_values"]["percentage_change"] = ev_detail.get("percentage_change")

            evidence_list.append(ev_obj)

            # Build supporting numbers (displayed in the UI metric cards)
            if "days_remaining_display" in ev_detail:
                supporting_numbers.append({
                    "product_name": p_name,
                    "store_name": s_name,
                    "metric": "Days Remaining",
                    "value": str(ev_detail["days_remaining_display"]),
                })
            if "current_stock" in ev_detail:
                supporting_numbers.append({
                    "product_name": p_name,
                    "store_name": s_name,
                    "metric": "Current Stock",
                    "value": f"{ev_detail['current_stock']} units",
                })
            if intent in ["SALES_SPIKE", "SALES_DROP"] and "percentage_change" in ev_detail:
                supporting_numbers.append({
                    "product_name": p_name,
                    "store_name": s_name,
                    "metric": "Sales Velocity Change",
                    "value": f"{ev_detail['percentage_change']:+.1f}%",
                })

        return {
            "intent": intent,
            "question": question,
            "findings": findings,
            "evidence": evidence_list,
            "supporting_numbers": supporting_numbers,
            "data_sufficiency": "SUFFICIENT" if findings else "INSUFFICIENT",
        }

    def _build_store_summary_context(
        self,
        store_id: Optional[str],
        stores_map: Dict,
        question: str,
    ) -> Dict[str, Any]:
        """Build evidence context for store performance summary queries."""
        stores_summary = self.analytics.calculate_store_summary()
        evidence_list = []
        supporting_numbers = []

        for st in stores_summary:
            s_name = st.get("store_name", "Store")
            evidence_list.append({
                "source": SOURCE_STORE,
                "store_id": st.get("store_id"),
                "store_name": s_name,
                "metric": "total_sales",
                "value": f"₹{st.get('total_sales_amount', 0):,.2f}",
                "supporting_values": {
                    "total_units_sold": st.get("total_units_sold"),
                    "inventory_value": st.get("inventory_value"),
                    "attention_count": st.get("attention_count"),
                },
                "period": "Last 90 days",
            })
            supporting_numbers.append({
                "product_name": "All Products",
                "store_name": s_name,
                "metric": "Total Sales Revenue",
                "value": f"₹{st.get('total_sales_amount', 0):,.2f}",
            })

        return {
            "intent": "STORE_SUMMARY",
            "question": question,
            "stores_summary": stores_summary,
            "evidence": evidence_list,
            "supporting_numbers": supporting_numbers,
            "data_sufficiency": "SUFFICIENT",
        }

    def _build_general_fallback_context(
        self,
        store_id: Optional[str],
        stores_map: Dict,
        question: str,
    ) -> Dict[str, Any]:
        """Fallback evidence context for unclassified but retail-domain queries."""
        summary = self.analytics.calculate_sales_summary(store_id=store_id)
        top_findings = self.attention.get_all_attention_items(store_id=store_id)

        return {
            "intent": "GENERAL_ATTENTION",
            "question": question,
            "sales_summary": summary,
            "findings": top_findings[:8],
            "evidence": [
                {
                    "source": SOURCE_SALES,
                    "metric": "total_sales",
                    "value": f"₹{summary.get('total_sales_amount', 0):,.2f}",
                    "supporting_values": {
                        "total_units_sold": summary.get("total_units_sold"),
                        "date_range": summary.get("date_range"),
                    },
                    "period": "Last 90 days",
                }
            ],
            "supporting_numbers": [
                {
                    "product_name": "All Products",
                    "store_name": "All Stores" if not store_id else stores_map.get(store_id, store_id),
                    "metric": "Total Sales",
                    "value": f"₹{summary.get('total_sales_amount', 0):,.2f}",
                }
            ],
            "data_sufficiency": "SUFFICIENT",
        }
