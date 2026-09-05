"""
ShelfIQ Analytics Engine
Pure Python deterministic calculations for sales summaries, product performance,
inventory health, stock-out risks, slow-moving items, overstock, and sales anomalies.
"""

import math
import datetime
from typing import Dict, List, Any, Optional, Tuple

# Transparent Deterministic Threshold Configurations
STOCKOUT_CRITICAL_DAYS = 4.0   # <= 4.0 days remaining -> CRITICAL
STOCKOUT_HIGH_DAYS = 7.0       # 4.1 to 7.0 days remaining -> HIGH
STOCKOUT_MEDIUM_DAYS = 14.0    # 7.1 to 14.0 days remaining -> MEDIUM

SLOW_MOVING_VELOCITY_THRESHOLD = 0.3  # avg daily units < 0.3
OVERSTOCK_DAYS_THRESHOLD = 60.0       # days of stock remaining > 60.0

SPIKE_PERCENT_THRESHOLD = 50.0        # % increase over baseline
DROP_PERCENT_THRESHOLD = -30.0        # % decrease over baseline

MIN_DAYS_SUFFICIENT = 14               # min days for SUFFICIENT data quality
MIN_DAYS_LIMITED = 5                   # 5-13 days for LIMITED data quality
RECENT_SPIKE_DROP_WINDOW = 7           # recent days window for anomaly detection

class AnalyticsEngine:
    """
    Deterministic Analytics Engine for ShelfIQ.
    Operates on validated data from DataLoader.
    Produces structured numbers, calculations, and evidence records.
    """
    def __init__(self, data_loader):
        self.loader = data_loader

    def _get_sales_data(self, store_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter sales records by store_id and product category if specified."""
        sales = self.loader.get_sales()
        products_map = {p["product_id"]: p for p in self.loader.get_products()}

        filtered = []
        for row in sales:
            if store_id and row["store_id"] != store_id:
                continue
            pid = row["product_id"]
            p_info = products_map.get(pid, {})
            if category and p_info.get("category") != category:
                continue
            
            # Enrich row with product and store names
            enriched = dict(row)
            enriched["product_name"] = p_info.get("product_name", pid)
            enriched["category"] = p_info.get("category", "Unknown")
            enriched["unit_price"] = p_info.get("unit_price", 0.0)
            filtered.append(enriched)

        return filtered

    def _get_inventory_data(self, store_id: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filter inventory records by store_id and product category if specified."""
        inventory = self.loader.get_inventory()
        products_map = {p["product_id"]: p for p in self.loader.get_products()}
        stores_map = {s["store_id"]: s for s in self.loader.get_stores()}

        filtered = []
        for row in inventory:
            if store_id and row["store_id"] != store_id:
                continue
            pid = row["product_id"]
            p_info = products_map.get(pid, {})
            if category and p_info.get("category") != category:
                continue
            
            s_info = stores_map.get(row["store_id"], {})
            enriched = dict(row)
            enriched["product_name"] = p_info.get("product_name", pid)
            enriched["category"] = p_info.get("category", "Unknown")
            enriched["unit_price"] = p_info.get("unit_price", 0.0)
            enriched["store_name"] = s_info.get("store_name", row["store_id"])
            filtered.append(enriched)

        return filtered

    def evaluate_data_sufficiency(self, unique_days: int) -> str:
        """Evaluate data sufficiency based on historical observation days."""
        if unique_days >= MIN_DAYS_SUFFICIENT:
            return "SUFFICIENT"
        elif unique_days >= MIN_DAYS_LIMITED:
            return "LIMITED"
        else:
            return "INSUFFICIENT"

    def calculate_sales_summary(
        self,
        store_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate overall sales summary metrics for selected filters and date range."""
        sales = self._get_sales_data(store_id, category)

        # Date range filtering
        if start_date or end_date:
            filtered_sales = []
            for s in sales:
                d = s["date"]
                if start_date and d < start_date:
                    continue
                if end_date and d > end_date:
                    continue
                filtered_sales.append(s)
            sales = filtered_sales

        if not sales:
            return {
                "total_sales_amount": 0.0,
                "total_units_sold": 0,
                "total_transactions": 0,
                "unique_days_count": 0,
                "avg_daily_sales_amount": 0.0,
                "avg_daily_units_sold": 0.0,
                "date_range": {"start_date": start_date or "N/A", "end_date": end_date or "N/A"},
                "data_sufficiency": "INSUFFICIENT"
            }

        dates = sorted(list(set(s["date"] for s in sales)))
        min_date = dates[0]
        max_date = dates[-1]
        
        # Calculate total days in window
        d_start = datetime.date.fromisoformat(min_date)
        d_end = datetime.date.fromisoformat(max_date)
        days_span = max(1, (d_end - d_start).days + 1)

        total_amount = round(sum(s["sales_amount"] for s in sales), 2)
        total_units = sum(s["units_sold"] for s in sales)
        tx_count = len(sales)

        avg_daily_amount = round(total_amount / days_span, 2)
        avg_daily_units = round(total_units / days_span, 2)
        sufficiency = self.evaluate_data_sufficiency(days_span)

        return {
            "total_sales_amount": total_amount,
            "total_units_sold": total_units,
            "total_transactions": tx_count,
            "unique_days_count": days_span,
            "avg_daily_sales_amount": avg_daily_amount,
            "avg_daily_units_sold": avg_daily_units,
            "date_range": {"start_date": min_date, "end_date": max_date},
            "data_sufficiency": sufficiency
        }

    def calculate_product_performance(
        self,
        store_id: Optional[str] = None,
        category: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate per-product sales performance metrics."""
        sales = self._get_sales_data(store_id, category)
        products_map = {p["product_id"]: p for p in self.loader.get_products()}

        # Group sales by product_id
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for row in sales:
            pid = row["product_id"]
            if product_id and pid != product_id:
                continue
            if pid not in grouped:
                grouped[pid] = []
            grouped[pid].append(row)

        results = []
        for pid, p_info in products_map.items():
            if product_id and pid != product_id:
                continue
            if category and p_info["category"] != category:
                continue

            p_sales = grouped.get(pid, [])
            if not p_sales:
                results.append({
                    "product_id": pid,
                    "product_name": p_info["product_name"],
                    "category": p_info["category"],
                    "unit_price": p_info["unit_price"],
                    "total_units_sold": 0,
                    "total_sales_amount": 0.0,
                    "avg_daily_units": 0.0,
                    "avg_daily_sales": 0.0,
                    "days_recorded": 0,
                    "sales_trend": "NO_SALES",
                    "data_sufficiency": "INSUFFICIENT"
                })
                continue

            dates = sorted(list(set(s["date"] for s in p_sales)))
            d_start = datetime.date.fromisoformat(dates[0])
            d_end = datetime.date.fromisoformat(dates[-1])
            days_span = max(1, (d_end - d_start).days + 1)

            tot_units = sum(s["units_sold"] for s in p_sales)
            tot_amount = round(sum(s["sales_amount"] for s in p_sales), 2)
            avg_units = round(tot_units / days_span, 2)
            avg_amount = round(tot_amount / days_span, 2)

            # Determine basic sales trend if enough history
            trend = "STABLE"
            if len(dates) >= 14:
                half = len(dates) // 2
                first_half_units = sum(s["units_sold"] for s in p_sales if s["date"] in dates[:half])
                second_half_units = sum(s["units_sold"] for s in p_sales if s["date"] in dates[half:])
                if second_half_units > first_half_units * 1.2:
                    trend = "UPWARD"
                elif second_half_units < first_half_units * 0.8:
                    trend = "DOWNWARD"

            sufficiency = self.evaluate_data_sufficiency(days_span)

            results.append({
                "product_id": pid,
                "product_name": p_info["product_name"],
                "category": p_info["category"],
                "unit_price": p_info["unit_price"],
                "total_units_sold": tot_units,
                "total_sales_amount": tot_amount,
                "avg_daily_units": avg_units,
                "avg_daily_sales": avg_amount,
                "days_recorded": days_span,
                "sales_trend": trend,
                "data_sufficiency": sufficiency
            })

        return results

    def calculate_daily_sales_trend(
        self,
        store_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate daily sales totals for charts and period comparisons."""
        sales = self._get_sales_data(store_id, category)
        daily: Dict[str, Dict[str, Any]] = {}

        for row in sales:
            row_date = row["date"]
            if start_date and row_date < start_date:
                continue
            if end_date and row_date > end_date:
                continue

            if row_date not in daily:
                daily[row_date] = {
                    "date": row_date,
                    "sales_amount": 0.0,
                    "units_sold": 0,
                    "transactions": 0
                }
            daily[row_date]["sales_amount"] += row["sales_amount"]
            daily[row_date]["units_sold"] += row["units_sold"]
            daily[row_date]["transactions"] += 1

        return [
            {
                "date": item["date"],
                "sales_amount": round(item["sales_amount"], 2),
                "units_sold": item["units_sold"],
                "transactions": item["transactions"]
            }
            for item in sorted(daily.values(), key=lambda x: x["date"])
        ]

    def calculate_sales_growth(
        self,
        store_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare recent half of the selected period against the previous half."""
        trend = self.calculate_daily_sales_trend(store_id, category, start_date, end_date)
        if len(trend) < 2:
            return {
                "percentage_change": None,
                "recent_sales": 0.0,
                "baseline_sales": 0.0,
                "period": "Insufficient comparable history",
                "data_sufficiency": "INSUFFICIENT"
            }

        midpoint = len(trend) // 2
        baseline = trend[:midpoint]
        recent = trend[midpoint:]
        baseline_sales = round(sum(d["sales_amount"] for d in baseline), 2)
        recent_sales = round(sum(d["sales_amount"] for d in recent), 2)

        if baseline_sales <= 0:
            percentage_change = None
            sufficiency = "INSUFFICIENT"
        else:
            percentage_change = round(((recent_sales - baseline_sales) / baseline_sales) * 100.0, 1)
            sufficiency = self.evaluate_data_sufficiency(len(trend))

        return {
            "percentage_change": percentage_change,
            "recent_sales": recent_sales,
            "baseline_sales": baseline_sales,
            "period": "Recent half vs previous half of selected date range",
            "data_sufficiency": sufficiency
        }

    def calculate_inventory_metrics(
        self,
        store_id: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate inventory health metrics for product-store pairs."""
        inv_data = self._get_inventory_data(store_id)
        
        # Precompute sales velocity per (store_id, product_id) over full history
        sales_by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for s in self.loader.get_sales():
            key = (s["store_id"], s["product_id"])
            if key not in sales_by_pair:
                sales_by_pair[key] = []
            sales_by_pair[key].append(s)

        results = []
        total_span = 90  # 90-day dataset window

        for item in inv_data:
            sid = item["store_id"]
            pid = item["product_id"]
            if product_id and pid != product_id:
                continue

            stock = item["current_stock"]
            records = sales_by_pair.get((sid, pid), [])

            tot_units = sum(r["units_sold"] for r in records)
            avg_daily_units = round(tot_units / total_span, 2)

            # Safe days remaining calculation (handling zero sales)
            if avg_daily_units <= 0:
                days_remaining = None
                days_display = "UNAVAILABLE"
                status = "ZERO_SALES"
            else:
                raw_days = stock / avg_daily_units
                days_remaining = round(raw_days, 1)
                days_display = f"{days_remaining}"

                if days_remaining <= STOCKOUT_CRITICAL_DAYS:
                    status = "CRITICAL"
                elif days_remaining <= STOCKOUT_HIGH_DAYS:
                    status = "HIGH"
                elif days_remaining <= STOCKOUT_MEDIUM_DAYS:
                    status = "MEDIUM"
                elif days_remaining > OVERSTOCK_DAYS_THRESHOLD:
                    status = "OVERSTOCKED"
                else:
                    status = "HEALTHY"

            inv_value = round(stock * item["unit_price"], 2)
            sufficiency = self.evaluate_data_sufficiency(total_span if records else 0)

            results.append({
                "product_id": pid,
                "product_name": item["product_name"],
                "category": item["category"],
                "store_id": sid,
                "store_name": item["store_name"],
                "current_stock": stock,
                "average_daily_units_sold": avg_daily_units,
                "days_remaining": days_remaining,
                "days_remaining_display": days_display,
                "inventory_value": inv_value,
                "status": status,
                "data_sufficiency": sufficiency
            })

        return results

    def detect_stockout_risks(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Identify products likely to run out (CRITICAL, HIGH, or MEDIUM risk levels)."""
        metrics = self.calculate_inventory_metrics(store_id)
        risks = []

        for m in metrics:
            if m["status"] in ["CRITICAL", "HIGH", "MEDIUM"]:
                risks.append({
                    "product_id": m["product_id"],
                    "product_name": m["product_name"],
                    "category": m["category"],
                    "store_id": m["store_id"],
                    "store_name": m["store_name"],
                    "current_stock": m["current_stock"],
                    "average_daily_units_sold": m["average_daily_units_sold"],
                    "days_remaining": m["days_remaining"],
                    "days_remaining_display": m["days_remaining_display"],
                    "risk_level": m["status"],
                    "data_sufficiency": m["data_sufficiency"],
                    "threshold_used": f"<= {STOCKOUT_MEDIUM_DAYS} days remaining"
                })

        # Sort by highest risk (fewest days remaining)
        risks.sort(key=lambda x: (x["days_remaining"] if x["days_remaining"] is not None else 999))
        return risks

    def detect_slow_moving_products(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Identify products with unusually low sales velocity despite available stock."""
        metrics = self.calculate_inventory_metrics(store_id)
        slow_items = []

        # Find earliest sales date to check established products
        all_sales = self.loader.get_sales()
        if not all_sales:
            return []

        sales_by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for s in all_sales:
            key = (s["store_id"], s["product_id"])
            if key not in sales_by_pair:
                sales_by_pair[key] = []
            sales_by_pair[key].append(s)

        for m in metrics:
            sid = m["store_id"]
            pid = m["product_id"]
            records = sales_by_pair.get((sid, pid), [])

            if not records:
                continue

            dates = sorted([r["date"] for r in records])
            first_sale_dt = datetime.date.fromisoformat(dates[0])
            last_sale_dt = datetime.date.fromisoformat(dates[-1])
            days_span = max(1, (last_sale_dt - first_sale_dt).days + 1)

            # Check established product condition (history >= 14 days and stock >= 30)
            if days_span >= MIN_DAYS_SUFFICIENT and m["current_stock"] >= 30:
                if 0 < m["average_daily_units_sold"] < SLOW_MOVING_VELOCITY_THRESHOLD:
                    slow_items.append({
                        "product_id": pid,
                        "product_name": m["product_name"],
                        "category": m["category"],
                        "store_id": sid,
                        "store_name": m["store_name"],
                        "current_stock": m["current_stock"],
                        "total_units_sold": sum(r["units_sold"] for r in records),
                        "average_daily_units_sold": m["average_daily_units_sold"],
                        "days_remaining": m["days_remaining"],
                        "days_remaining_display": m["days_remaining_display"],
                        "comparison_period": f"{days_span} days",
                        "threshold_used": f"velocity < {SLOW_MOVING_VELOCITY_THRESHOLD} units/day",
                        "data_sufficiency": m["data_sufficiency"]
                    })

        return slow_items

    def detect_overstocked_products(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Identify products with excessive inventory relative to sales velocity."""
        metrics = self.calculate_inventory_metrics(store_id)
        overstock_items = []

        for m in metrics:
            stock = m["current_stock"]
            avg_units = m["average_daily_units_sold"]
            days_rem = m["days_remaining"]

            if avg_units > 0 and days_rem is not None and days_rem > OVERSTOCK_DAYS_THRESHOLD:
                overstock_items.append({
                    "product_id": m["product_id"],
                    "product_name": m["product_name"],
                    "category": m["category"],
                    "store_id": m["store_id"],
                    "store_name": m["store_name"],
                    "current_stock": stock,
                    "average_daily_units_sold": avg_units,
                    "estimated_days_of_inventory": days_rem,
                    "estimated_days_display": f"{days_rem} days",
                    "overstock_status": "OVERSTOCKED",
                    "threshold_used": f"> {OVERSTOCK_DAYS_THRESHOLD} days of stock remaining",
                    "data_sufficiency": m["data_sufficiency"]
                })
            elif avg_units == 0 and stock >= 50:
                overstock_items.append({
                    "product_id": m["product_id"],
                    "product_name": m["product_name"],
                    "category": m["category"],
                    "store_id": m["store_id"],
                    "store_name": m["store_name"],
                    "current_stock": stock,
                    "average_daily_units_sold": 0.0,
                    "estimated_days_of_inventory": None,
                    "estimated_days_display": "UNAVAILABLE (Zero Sales)",
                    "overstock_status": "ZERO_SALES_OVERSTOCK",
                    "threshold_used": f"Zero sales with current stock >= 50",
                    "data_sufficiency": "INSUFFICIENT"
                })

        return overstock_items

    def detect_sales_spikes(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect recent sales velocity spikes compared to historical baseline."""
        all_sales = self._get_sales_data(store_id)
        if not all_sales:
            return []

        dates = sorted(list(set(s["date"] for s in all_sales)))
        if len(dates) < RECENT_SPIKE_DROP_WINDOW + 7:
            return []  # Not enough global date history

        cutoff_date = (datetime.date.fromisoformat(dates[-1]) - datetime.timedelta(days=RECENT_SPIKE_DROP_WINDOW - 1)).strftime("%Y-%m-%d")

        # Group by (store_id, product_id)
        sales_by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for s in all_sales:
            key = (s["store_id"], s["product_id"])
            if key not in sales_by_pair:
                sales_by_pair[key] = []
            sales_by_pair[key].append(s)

        spikes = []
        for (sid, pid), records in sales_by_pair.items():
            recent_records = [r for r in records if r["date"] >= cutoff_date]
            baseline_records = [r for r in records if r["date"] < cutoff_date]

            if not recent_records or not baseline_records:
                continue

            recent_units = sum(r["units_sold"] for r in recent_records)
            recent_days = RECENT_SPIKE_DROP_WINDOW
            recent_avg = recent_units / recent_days

            baseline_units = sum(r["units_sold"] for r in baseline_records)
            baseline_days = 90 - RECENT_SPIKE_DROP_WINDOW
            baseline_avg = baseline_units / baseline_days if baseline_days > 0 else 0.0

            # Only flag spikes if baseline has meaningful activity
            if baseline_avg >= 1.0:
                pct_change = round(((recent_avg - baseline_avg) / baseline_avg) * 100.0, 1)
                if pct_change >= SPIKE_PERCENT_THRESHOLD:
                    spikes.append({
                        "product_id": pid,
                        "product_name": records[0]["product_name"],
                        "category": records[0]["category"],
                        "store_id": sid,
                        "store_name": records[0].get("store_name", sid),
                        "recent_daily_avg": round(recent_avg, 2),
                        "baseline_daily_avg": round(baseline_avg, 2),
                        "percentage_change": pct_change,
                        "detection_threshold": f">= +{SPIKE_PERCENT_THRESHOLD}% over baseline",
                        "data_sufficiency": "SUFFICIENT"
                    })

        return spikes

    def detect_sales_drops(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Detect recent sales velocity drops compared to historical baseline."""
        all_sales = self._get_sales_data(store_id)
        if not all_sales:
            return []

        dates = sorted(list(set(s["date"] for s in all_sales)))
        if len(dates) < RECENT_SPIKE_DROP_WINDOW + 7:
            return []

        cutoff_date = (datetime.date.fromisoformat(dates[-1]) - datetime.timedelta(days=RECENT_SPIKE_DROP_WINDOW - 1)).strftime("%Y-%m-%d")

        sales_by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for s in all_sales:
            key = (s["store_id"], s["product_id"])
            if key not in sales_by_pair:
                sales_by_pair[key] = []
            sales_by_pair[key].append(s)

        drops = []
        for (sid, pid), records in sales_by_pair.items():
            recent_records = [r for r in records if r["date"] >= cutoff_date]
            baseline_records = [r for r in records if r["date"] < cutoff_date]

            if not baseline_records:
                continue

            recent_units = sum(r["units_sold"] for r in recent_records) if recent_records else 0
            recent_days = RECENT_SPIKE_DROP_WINDOW
            recent_avg = recent_units / recent_days

            baseline_units = sum(r["units_sold"] for r in baseline_records)
            baseline_days = 90 - RECENT_SPIKE_DROP_WINDOW
            baseline_avg = baseline_units / baseline_days if baseline_days > 0 else 0.0

            if baseline_avg >= 1.5:
                pct_change = round(((recent_avg - baseline_avg) / baseline_avg) * 100.0, 1)
                if pct_change <= DROP_PERCENT_THRESHOLD:
                    drops.append({
                        "product_id": pid,
                        "product_name": records[0]["product_name"],
                        "category": records[0]["category"],
                        "store_id": sid,
                        "store_name": records[0].get("store_name", sid),
                        "recent_daily_avg": round(recent_avg, 2),
                        "baseline_daily_avg": round(baseline_avg, 2),
                        "percentage_change": pct_change,
                        "detection_threshold": f"<= {DROP_PERCENT_THRESHOLD}% under baseline",
                        "data_sufficiency": "SUFFICIENT"
                    })

        return drops

    def calculate_category_summary(self, store_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Calculate aggregated sales and inventory health per product category."""
        sales = self._get_sales_data(store_id)
        inventory = self._get_inventory_data(store_id)

        cat_sales: Dict[str, float] = {}
        cat_units: Dict[str, int] = {}
        for s in sales:
            cat = s["category"]
            cat_sales[cat] = cat_sales.get(cat, 0.0) + s["sales_amount"]
            cat_units[cat] = cat_units.get(cat, 0) + s["units_sold"]

        cat_stock: Dict[str, int] = {}
        cat_val: Dict[str, float] = {}
        for inv in inventory:
            cat = inv["category"]
            stock = inv["current_stock"]
            cat_stock[cat] = cat_stock.get(cat, 0) + stock
            cat_val[cat] = cat_val.get(cat, 0.0) + (stock * inv["unit_price"])

        all_categories = sorted(list(set(list(cat_sales.keys()) + list(cat_stock.keys()))))
        results = []

        for cat in all_categories:
            results.append({
                "category": cat,
                "total_sales_amount": round(cat_sales.get(cat, 0.0), 2),
                "total_units_sold": cat_units.get(cat, 0),
                "total_stock_count": cat_stock.get(cat, 0),
                "total_inventory_value": round(cat_val.get(cat, 0.0), 2),
                "data_sufficiency": "SUFFICIENT"
            })

        return results

    def calculate_store_summary(self) -> List[Dict[str, Any]]:
        """Calculate high-level operational summary for each store."""
        stores = self.loader.get_stores()
        results = []

        for st in stores:
            sid = st["store_id"]
            s_name = st["store_name"]
            
            s_sales = self.calculate_sales_summary(store_id=sid)
            s_inv = self.calculate_inventory_metrics(store_id=sid)

            total_inv_val = round(sum(i["inventory_value"] for i in s_inv), 2)
            low_stock_cnt = sum(1 for i in s_inv if i["status"] in ["CRITICAL", "HIGH"])

            results.append({
                "store_id": sid,
                "store_name": s_name,
                "city": st["city"],
                "total_sales_amount": s_sales["total_sales_amount"],
                "total_units_sold": s_sales["total_units_sold"],
                "inventory_value": total_inv_val,
                "low_stock_items_count": low_stock_cnt,
                "data_sufficiency": s_sales["data_sufficiency"]
            })

        return results
