"""
ShelfIQ Query Engine
Orchestrates Copilot workflow: Intent parsing -> Deterministic calculation -> Evidence formatting -> Gemini explanation.
"""

from typing import Dict, Any, Optional

class QueryEngine:
    """
    Query Engine for ShelfIQ.
    Coordinates question intent classification, deterministic data retrieval,
    evidence packaging, and grounded Gemini response generation.
    """
    def __init__(self, data_loader, analytics_engine, attention_engine, gemini_copilot):
        self.data_loader = data_loader
        self.analytics = analytics_engine
        self.attention = attention_engine
        self.gemini = gemini_copilot

    def process_query(self, question: str, store_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process natural-language user question end-to-end.
        1. Classify question intent.
        2. Fetch exact deterministic facts from analytics & rules engine.
        3. Send evidence to Gemini for grounded response synthesis.
        """
        intent = self.gemini.classify_question_intent(question)
        context = self._fetch_deterministic_context(question, intent, store_id)

        response = self.gemini.generate_grounded_response(
            user_question=question,
            deterministic_context=context
        )

        return response

    def _fetch_deterministic_context(self, question: str, intent: str, store_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch targeted deterministic evidence from Python backend based on question and intent."""
        q_lower = question.lower().strip()

        # Check for specific product mention in the question
        matched_product = None
        products = self.data_loader.get_products()
        for p in products:
            if p["product_name"].lower() in q_lower or p["product_id"].lower() in q_lower:
                matched_product = p
                break

        if matched_product:
            p_id = matched_product["product_id"]
            perf = self.analytics.calculate_product_performance(product_id=p_id, store_id=store_id)
            inv = self.analytics.calculate_inventory_metrics(product_id=p_id, store_id=store_id)
            attentions = [a for a in self.attention.get_all_attention_items(store_id=store_id) if a.get("product_id") == p_id]

            return {
                "intent": intent,
                "target_product": matched_product,
                "product_performance": perf,
                "inventory_metrics": inv,
                "attention_items": attentions,
                "data_sufficiency": "SUFFICIENT" if (perf or inv) else "INSUFFICIENT"
            }

        if intent in ["STOCK_OUT_RISK", "SLOW_MOVING", "OVERSTOCK", "SALES_SPIKE", "SALES_DROP"]:
            findings = self.attention.get_all_attention_items(store_id=store_id, attention_type=intent)
            return {
                "intent": intent,
                "findings": findings,
                "data_sufficiency": "SUFFICIENT" if findings else "LIMITED"
            }
        elif intent == "ATTENTION_SUMMARY":
            findings = self.attention.get_all_attention_items(store_id=store_id)
            return {
                "intent": intent,
                "findings": findings,
                "data_sufficiency": "SUFFICIENT" if findings else "LIMITED"
            }
        elif intent == "STORE_GROWTH":
            stores_summary = self.analytics.calculate_store_summary()
            return {
                "intent": intent,
                "stores_summary": stores_summary,
                "data_sufficiency": "SUFFICIENT"
            }
        elif intent == "PRODUCT_PERFORMANCE":
            perf = self.analytics.calculate_product_performance(store_id=store_id)
            return {
                "intent": intent,
                "product_performance": perf[:10],
                "data_sufficiency": "SUFFICIENT"
            }
        elif intent == "UNSUPPORTED_DATA":
            return {
                "intent": intent,
                "findings": [],
                "data_sufficiency": "INSUFFICIENT"
            }
        else:
            # General query default context
            summary = self.analytics.calculate_sales_summary(store_id=store_id)
            top_findings = self.attention.get_all_attention_items(store_id=store_id)
            return {
                "intent": intent,
                "sales_summary": summary,
                "top_findings": top_findings[:5],
                "data_sufficiency": "SUFFICIENT"
            }
