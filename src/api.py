"""
ShelfIQ FastAPI REST API Router
Exposes validated retail data, deterministic analytics, and business attention items.
"""

import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path

from src.schemas import (
    HealthResponse,
    SummaryResponse,
    DateRange,
    InventoryItemSchema,
    ProductDetailResponse,
    ErrorResponse,
    CopilotRequestSchema,
    CopilotResponseSchema
)

def create_api_router(data_loader, analytics_engine, attention_engine, query_engine=None) -> APIRouter:
    router = APIRouter(prefix="/api")

    # Helper function to validate store_id
    def _validate_store_id(store_id: Optional[str]):
        if not store_id:
            return
        valid_stores = {s["store_id"] for s in data_loader.get_stores()}
        if store_id not in valid_stores:
            raise HTTPException(status_code=400, detail=f"Invalid store_id: '{store_id}'. Valid stores: {sorted(list(valid_stores))}")

    # Helper function to validate product_id
    def _validate_product_id(product_id: Optional[str]):
        if not product_id:
            return
        valid_products = {p["product_id"] for p in data_loader.get_products()}
        if product_id not in valid_products:
            raise HTTPException(status_code=404, detail=f"Product not found: '{product_id}'")

    # Helper function to validate ISO date strings
    def _validate_date_str(date_str: Optional[str], param_name: str):
        if not date_str:
            return
        try:
            datetime.date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid ISO date format for {param_name}: '{date_str}'. Expected format YYYY-MM-DD.")

    @router.get("/health", response_model=HealthResponse)
    async def get_health():
        """System health and data loader status check."""
        return HealthResponse(
            status="ok",
            app="ShelfIQ",
            version="1.0.0",
            data_loaded=data_loader.is_loaded,
            data_valid=bool(data_loader.last_validation_result and data_loader.last_validation_result.is_valid)
        )

    @router.get("/summary", response_model=SummaryResponse)
    async def get_summary():
        """Executive summary metrics across all stores and categories."""
        sales_sum = analytics_engine.calculate_sales_summary()
        stores_sum = analytics_engine.calculate_store_summary()
        cat_sum = analytics_engine.calculate_category_summary()
        
        products = data_loader.get_products()
        stores = data_loader.get_stores()
        total_inv_val = round(sum(st["inventory_value"] for st in stores_sum), 2)

        return SummaryResponse(
            total_sales=sales_sum["total_sales_amount"],
            total_units_sold=sales_sum["total_units_sold"],
            total_products=len(products),
            total_stores=len(stores),
            inventory_value=total_inv_val,
            date_range=DateRange(
                start_date=sales_sum["date_range"]["start_date"],
                end_date=sales_sum["date_range"]["end_date"]
            ),
            stores_summary=stores_sum,
            category_summary=cat_sum
        )

    @router.get("/stores")
    async def get_stores():
        """Get catalogue of retail stores."""
        return {"stores": data_loader.get_stores()}

    @router.get("/stores/{store_id}")
    async def get_store_detail(store_id: str = Path(..., description="Store ID")):
        """Get metrics and attention alerts for a specific store."""
        _validate_store_id(store_id)
        stores_map = {s["store_id"]: s for s in data_loader.get_stores()}
        store_info = stores_map[store_id]

        sales_sum = analytics_engine.calculate_sales_summary(store_id=store_id)
        inv_metrics = analytics_engine.calculate_inventory_metrics(store_id=store_id)
        attention_items = attention_engine.get_all_attention_items(store_id=store_id)

        inv_val = round(sum(i["inventory_value"] for i in inv_metrics), 2)

        return {
            "store": store_info,
            "sales_summary": sales_sum,
            "inventory_value": inv_val,
            "inventory_count": len(inv_metrics),
            "attention_items_count": len(attention_items),
            "attention_items": attention_items
        }

    @router.get("/products")
    async def get_products(category: Optional[str] = Query(None)):
        """Get catalogue of products with optional category filtering."""
        products = data_loader.get_products()
        if category:
            products = [p for p in products if p["category"].lower() == category.lower()]
        return {"count": len(products), "products": products}

    @router.get("/products/{product_id}")
    async def get_product_detail(product_id: str = Path(..., description="Product ID")):
        """Get detailed sales, inventory, and attention info for a product."""
        _validate_product_id(product_id)
        products_map = {p["product_id"]: p for p in data_loader.get_products()}
        p_info = products_map[product_id]

        sales_perf = analytics_engine.calculate_product_performance(product_id=product_id)
        inv_metrics = analytics_engine.calculate_inventory_metrics(product_id=product_id)
        
        all_attentions = attention_engine.get_all_attention_items()
        p_attentions = [a for a in all_attentions if a["product_id"] == product_id]

        perf_data = sales_perf[0] if sales_perf else {}

        return ProductDetailResponse(
            product_id=p_info["product_id"],
            product_name=p_info["product_name"],
            category=p_info["category"],
            unit_price=p_info["unit_price"],
            cost_price=p_info["cost_price"],
            sales_performance=perf_data,
            inventory_metrics=inv_metrics,
            attention_items=p_attentions
        )

    @router.get("/inventory")
    async def get_inventory(
        store_id: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        search: Optional[str] = Query(None),
        status: Optional[str] = Query(None)
    ):
        """Get inventory health metrics with filtering and search."""
        _validate_store_id(store_id)
        inv_items = analytics_engine.calculate_inventory_metrics(store_id=store_id)

        # Apply category filter
        if category:
            inv_items = [i for i in inv_items if i["category"].lower() == category.lower()]

        # Apply status filter
        if status:
            inv_items = [i for i in inv_items if i["status"].upper() == status.upper()]

        # Apply search filter (product_name or product_id)
        if search:
            q = search.lower().strip()
            inv_items = [
                i for i in inv_items
                if q in i["product_name"].lower() or q in i["product_id"].lower()
            ]

        return {
            "count": len(inv_items),
            "inventory": inv_items
        }

    @router.get("/sales")
    async def get_sales(
        store_id: Optional[str] = Query(None),
        product_id: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        start_date: Optional[str] = Query(None),
        end_date: Optional[str] = Query(None)
    ):
        """Get sales metrics, summaries, and product performance."""
        _validate_store_id(store_id)
        _validate_product_id(product_id)
        _validate_date_str(start_date, "start_date")
        _validate_date_str(end_date, "end_date")

        sales_sum = analytics_engine.calculate_sales_summary(
            store_id=store_id,
            category=category,
            start_date=start_date,
            end_date=end_date
        )

        perf = analytics_engine.calculate_product_performance(
            store_id=store_id,
            category=category,
            product_id=product_id
        )

        return {
            "summary": sales_sum,
            "product_performance_count": len(perf),
            "product_performance": perf
        }

    @router.get("/attention")
    async def get_attention(
        store_id: Optional[str] = Query(None),
        category: Optional[str] = Query(None),
        attention_type: Optional[str] = Query(None),
        severity: Optional[str] = Query(None)
    ):
        """Get prioritized business attention items and recommendations."""
        _validate_store_id(store_id)
        
        if attention_type:
            valid_types = {"STOCK_OUT_RISK", "SLOW_MOVING", "OVERSTOCK", "SALES_SPIKE", "SALES_DROP"}
            if attention_type.upper() not in valid_types:
                raise HTTPException(status_code=400, detail=f"Invalid attention_type: '{attention_type}'. Valid types: {sorted(list(valid_types))}")

        if severity:
            valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
            if severity.upper() not in valid_severities:
                raise HTTPException(status_code=400, detail=f"Invalid severity: '{severity}'. Valid severities: {sorted(list(valid_severities))}")

        attention_items = attention_engine.get_all_attention_items(
            store_id=store_id,
            category=category,
            attention_type=attention_type.upper() if attention_type else None,
            severity=severity.upper() if severity else None
        )

        severity_counts = {
            "CRITICAL": sum(1 for a in attention_items if a["severity"] == "CRITICAL"),
            "HIGH": sum(1 for a in attention_items if a["severity"] == "HIGH"),
            "MEDIUM": sum(1 for a in attention_items if a["severity"] == "MEDIUM"),
            "LOW": sum(1 for a in attention_items if a["severity"] == "LOW"),
            "INFO": sum(1 for a in attention_items if a["severity"] == "INFO")
        }

        return {
            "count": len(attention_items),
            "severity_counts": severity_counts,
            "attention_items": attention_items
        }

    @router.post("/ai/analyze", response_model=CopilotResponseSchema)
    async def analyze_question(payload: CopilotRequestSchema):
        """Analyze natural-language user question grounded in deterministic retail evidence."""
        if not payload.question or not payload.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        if len(payload.question) > 500:
            raise HTTPException(status_code=400, detail="Question is too long (maximum 500 characters).")

        if payload.store_id:
            _validate_store_id(payload.store_id)

        if query_engine is None:
            raise HTTPException(status_code=503, detail="AI Query Engine service is not initialized.")

        try:
            res = query_engine.process_query(
                question=payload.question.strip(),
                store_id=payload.store_id,
                previous_intent=payload.previous_intent,
                previous_product_id=payload.previous_product_id
            )
            return res
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Copilot query execution failed: {str(e)}")

    return router
