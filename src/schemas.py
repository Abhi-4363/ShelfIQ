"""
ShelfIQ Pydantic Schemas & API Request/Response Models
Defines stable JSON schemas for FastAPI backend endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "ShelfIQ"
    version: str = "1.0.0"
    data_loaded: bool = True
    data_valid: bool = True

class DateRange(BaseModel):
    start_date: str
    end_date: str

class SummaryResponse(BaseModel):
    total_sales: float
    total_units_sold: int
    total_products: int
    total_stores: int
    inventory_value: float
    date_range: DateRange
    stores_summary: List[Dict[str, Any]]
    category_summary: List[Dict[str, Any]]

class InventoryItemSchema(BaseModel):
    product_id: str
    product_name: str
    category: str
    store_id: str
    store_name: str
    current_stock: int
    average_daily_units_sold: float
    days_remaining: Optional[float] = None
    days_remaining_display: str
    inventory_value: float
    status: str
    data_sufficiency: str

class ProductPerformanceSchema(BaseModel):
    product_id: str
    product_name: str
    category: str
    unit_price: float
    total_units_sold: int
    total_sales_amount: float
    avg_daily_units: float
    avg_daily_sales: float
    days_recorded: int
    sales_trend: str
    data_sufficiency: str

class ProductDetailResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    unit_price: float
    cost_price: float
    sales_performance: Dict[str, Any]
    inventory_metrics: List[Dict[str, Any]]
    attention_items: List[Dict[str, Any]]

class ErrorResponse(BaseModel):
    detail: str
    error_type: str = "VALIDATION_OR_NOT_FOUND"

class CopilotRequestSchema(BaseModel):
    question: str
    store_id: Optional[str] = None
