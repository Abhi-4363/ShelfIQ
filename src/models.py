"""
ShelfIQ Data Models & Schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Store(BaseModel):
    store_id: str
    store_name: str
    city: str

class Product(BaseModel):
    product_id: str
    product_name: str
    category: str
    unit_price: float
    cost_price: float

class InventoryRecord(BaseModel):
    product_id: str
    store_id: str
    current_stock: int
    reorder_level: int
    last_restock_date: str

class DailySalesRecord(BaseModel):
    date: str
    product_id: str
    store_id: str
    units_sold: int
    total_revenue: float

class AttentionItem(BaseModel):
    id: str
    severity: str  # CRITICAL, HIGH, WATCH, HEALTHY
    category: str  # STOCK_OUT, SLOW_MOVING, OVERSTOCK, SALES_SPIKE, SALES_DROP
    product_name: str
    store_name: str
    metric: str
    reason: str
    supporting_data: Dict[str, Any]
    recommendation: str
    assumptions: List[str]

class CopilotQuery(BaseModel):
    question: str
    store_filter: Optional[str] = None
    date_range: Optional[str] = None

class Evidence(BaseModel):
    source_files: List[str]
    relevant_period: str
    metrics: Dict[str, Any]
    calculation_explanation: str

class CopilotResponse(BaseModel):
    question: str
    answer: str
    supporting_numbers: List[Dict[str, Any]]
    evidence: Evidence
    recommendation: str
    assumptions: List[str]
    data_sufficiency: str  # Sufficient | Insufficient
