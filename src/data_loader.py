"""
ShelfIQ Data Loader & Validation Module
Handles reading, validating, and normalizing CSV datasets (stores, products, sales, inventory).
Ensures data integrity, foreign key compliance, type safety, and mathematical consistency.
"""

import os
import csv
import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

@dataclass
class ValidationError:
    """Represents a single data validation issue."""
    file_name: str
    row_index: Optional[int]
    field_name: Optional[str]
    message: str
    severity: str = "ERROR"  # ERROR | WARNING

@dataclass
class ValidationResult:
    """Encapsulates the complete result of dataset loading and validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)

class DataLoader:
    """
    Data Loader & Validator for ShelfIQ retail dataset.
    Loads and validates stores, products, sales, and inventory CSV files.
    """
    REQUIRED_COLUMNS = {
        "stores": ["store_id", "store_name", "city"],
        "products": ["product_id", "product_name", "category", "unit_price", "cost_price"],
        "sales": ["date", "store_id", "product_id", "units_sold", "sales_amount"],
        "inventory": ["store_id", "product_id", "current_stock", "last_updated"]
    }

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.stores: List[Dict[str, Any]] = []
        self.products: List[Dict[str, Any]] = []
        self.sales: List[Dict[str, Any]] = []
        self.inventory: List[Dict[str, Any]] = []
        
        # Fast lookup maps
        self.store_ids: set = set()
        self.product_ids: set = set()
        self.product_prices: Dict[str, float] = {}
        
        self.is_loaded: bool = False
        self.last_validation_result: Optional[ValidationResult] = None

    def load_all_data(self) -> Tuple[bool, ValidationResult]:
        """
        Load all four CSV files safely and perform comprehensive data validation.
        Returns (is_valid, validation_result).
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []
        stats: Dict[str, Any] = {}

        # Reset state
        self.stores.clear()
        self.products.clear()
        self.sales.clear()
        self.inventory.clear()
        self.store_ids.clear()
        self.product_ids.clear()
        self.product_prices.clear()

        # 1. Check file existence
        for file_key in ["stores", "products", "sales", "inventory"]:
            file_path = os.path.join(self.data_dir, f"{file_key}.csv")
            if not os.path.exists(file_path):
                errors.append(ValidationError(
                    file_name=f"{file_key}.csv",
                    row_index=None,
                    field_name=None,
                    message=f"Required data file missing: {file_path}",
                    severity="ERROR"
                ))

        if errors:
            self.last_validation_result = ValidationResult(is_valid=False, errors=errors, warnings=warnings)
            return False, self.last_validation_result

        # 2. Load & Validate stores.csv
        self._load_and_validate_stores(errors, warnings)

        # 3. Load & Validate products.csv
        self._load_and_validate_products(errors, warnings)

        # 4. Load & Validate inventory.csv
        self._load_and_validate_inventory(errors, warnings)

        # 5. Load & Validate sales.csv
        self._load_and_validate_sales(errors, warnings)

        # Determine overall validity
        is_valid = len(errors) == 0
        self.is_loaded = is_valid

        stats = {
            "stores_count": len(self.stores),
            "products_count": len(self.products),
            "inventory_count": len(self.inventory),
            "sales_count": len(self.sales),
            "total_errors": len(errors),
            "total_warnings": len(warnings)
        }

        self.last_validation_result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            summary_stats=stats
        )

        return is_valid, self.last_validation_result

    def _load_and_validate_stores(self, errors: List[ValidationError], warnings: List[ValidationError]):
        """Load and validate stores.csv."""
        file_path = os.path.join(self.data_dir, "stores.csv")
        file_name = "stores.csv"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                # Check header columns
                if not reader.fieldnames or not set(self.REQUIRED_COLUMNS["stores"]).issubset(set(reader.fieldnames)):
                    missing = set(self.REQUIRED_COLUMNS["stores"]) - set(reader.fieldnames or [])
                    errors.append(ValidationError(file_name, None, None, f"Missing required columns: {missing}"))
                    return

                for idx, row in enumerate(reader, start=1):
                    sid = (row.get("store_id") or "").strip()
                    sname = (row.get("store_name") or "").strip()
                    city = (row.get("city") or "").strip()

                    # Missing values
                    if not sid or not sname or not city:
                        errors.append(ValidationError(file_name, idx, "store_id/name/city", "Missing required field in stores row"))
                        continue

                    # Duplicate check
                    if sid in self.store_ids:
                        errors.append(ValidationError(file_name, idx, "store_id", f"Duplicate store_id detected: '{sid}'"))
                    else:
                        self.store_ids.add(sid)

                    self.stores.append({
                        "store_id": sid,
                        "store_name": sname,
                        "city": city
                    })
        except Exception as e:
            errors.append(ValidationError(file_name, None, None, f"Failed to read file: {str(e)}"))

    def _load_and_validate_products(self, errors: List[ValidationError], warnings: List[ValidationError]):
        """Load and validate products.csv."""
        file_path = os.path.join(self.data_dir, "products.csv")
        file_name = "products.csv"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames or not set(self.REQUIRED_COLUMNS["products"]).issubset(set(reader.fieldnames)):
                    missing = set(self.REQUIRED_COLUMNS["products"]) - set(reader.fieldnames or [])
                    errors.append(ValidationError(file_name, None, None, f"Missing required columns: {missing}"))
                    return

                for idx, row in enumerate(reader, start=1):
                    pid = (row.get("product_id") or "").strip()
                    pname = (row.get("product_name") or "").strip()
                    cat = (row.get("category") or "").strip()
                    price_str = (row.get("unit_price") or "").strip()
                    cost_str = (row.get("cost_price") or "").strip()

                    if not pid or not pname or not cat:
                        errors.append(ValidationError(file_name, idx, "product_id/name/category", "Missing required field in products"))
                        continue

                    # Duplicate check
                    if pid in self.product_ids:
                        errors.append(ValidationError(file_name, idx, "product_id", f"Duplicate product_id detected: '{pid}'"))
                    else:
                        self.product_ids.add(pid)

                    # Type & non-negative check
                    try:
                        unit_price = float(price_str)
                        cost_price = float(cost_str)
                        if unit_price <= 0:
                            errors.append(ValidationError(file_name, idx, "unit_price", f"unit_price must be positive, got {unit_price}"))
                        if cost_price <= 0:
                            errors.append(ValidationError(file_name, idx, "cost_price", f"cost_price must be positive, got {cost_price}"))
                    except ValueError:
                        errors.append(ValidationError(file_name, idx, "unit_price/cost_price", f"Invalid numeric price values: price='{price_str}', cost='{cost_str}'"))
                        unit_price, cost_price = 0.0, 0.0

                    self.product_prices[pid] = unit_price
                    self.products.append({
                        "product_id": pid,
                        "product_name": pname,
                        "category": cat,
                        "unit_price": unit_price,
                        "cost_price": cost_price
                    })
        except Exception as e:
            errors.append(ValidationError(file_name, None, None, f"Failed to read file: {str(e)}"))

    def _load_and_validate_inventory(self, errors: List[ValidationError], warnings: List[ValidationError]):
        """Load and validate inventory.csv."""
        file_path = os.path.join(self.data_dir, "inventory.csv")
        file_name = "inventory.csv"
        inv_keys = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames or not set(self.REQUIRED_COLUMNS["inventory"]).issubset(set(reader.fieldnames)):
                    missing = set(self.REQUIRED_COLUMNS["inventory"]) - set(reader.fieldnames or [])
                    errors.append(ValidationError(file_name, None, None, f"Missing required columns: {missing}"))
                    return

                for idx, row in enumerate(reader, start=1):
                    sid = (row.get("store_id") or "").strip()
                    pid = (row.get("product_id") or "").strip()
                    stock_str = (row.get("current_stock") or "").strip()
                    updated_str = (row.get("last_updated") or "").strip()

                    # Foreign Key checks
                    if sid not in self.store_ids:
                        errors.append(ValidationError(file_name, idx, "store_id", f"Invalid store_id reference: '{sid}'"))
                    if pid not in self.product_ids:
                        errors.append(ValidationError(file_name, idx, "product_id", f"Invalid product_id reference: '{pid}'"))

                    # Duplicate check
                    inv_key = (sid, pid)
                    if inv_key in inv_keys:
                        errors.append(ValidationError(file_name, idx, "store_id,product_id", f"Duplicate inventory record for pair ({sid}, {pid})"))
                    inv_keys.add(inv_key)

                    # Stock validation
                    try:
                        current_stock = int(stock_str)
                        if current_stock < 0:
                            errors.append(ValidationError(file_name, idx, "current_stock", f"current_stock cannot be negative, got {current_stock}"))
                    except ValueError:
                        errors.append(ValidationError(file_name, idx, "current_stock", f"Invalid integer current_stock: '{stock_str}'"))
                        current_stock = 0

                    # Date validation
                    try:
                        datetime.date.fromisoformat(updated_str)
                    except ValueError:
                        errors.append(ValidationError(file_name, idx, "last_updated", f"Invalid ISO date format: '{updated_str}'"))

                    self.inventory.append({
                        "store_id": sid,
                        "product_id": pid,
                        "current_stock": current_stock,
                        "last_updated": updated_str
                    })
        except Exception as e:
            errors.append(ValidationError(file_name, None, None, f"Failed to read file: {str(e)}"))

    def _load_and_validate_sales(self, errors: List[ValidationError], warnings: List[ValidationError]):
        """Load and validate sales.csv."""
        file_path = os.path.join(self.data_dir, "sales.csv")
        file_name = "sales.csv"
        sales_keys = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames or not set(self.REQUIRED_COLUMNS["sales"]).issubset(set(reader.fieldnames)):
                    missing = set(self.REQUIRED_COLUMNS["sales"]) - set(reader.fieldnames or [])
                    errors.append(ValidationError(file_name, None, None, f"Missing required columns: {missing}"))
                    return

                for idx, row in enumerate(reader, start=1):
                    date_str = (row.get("date") or "").strip()
                    sid = (row.get("store_id") or "").strip()
                    pid = (row.get("product_id") or "").strip()
                    units_str = (row.get("units_sold") or "").strip()
                    amount_str = (row.get("sales_amount") or "").strip()

                    # Date validation
                    try:
                        datetime.date.fromisoformat(date_str)
                    except ValueError:
                        errors.append(ValidationError(file_name, idx, "date", f"Invalid ISO date format: '{date_str}'"))

                    # Foreign Key checks
                    if sid not in self.store_ids:
                        errors.append(ValidationError(file_name, idx, "store_id", f"Invalid store_id reference: '{sid}'"))
                    if pid not in self.product_ids:
                        errors.append(ValidationError(file_name, idx, "product_id", f"Invalid product_id reference: '{pid}'"))

                    # Duplicate check
                    sales_key = (date_str, sid, pid)
                    if sales_key in sales_keys:
                        errors.append(ValidationError(file_name, idx, "date,store_id,product_id", f"Duplicate sales record for ({date_str}, {sid}, {pid})"))
                    sales_keys.add(sales_key)

                    # Units and Amount validation
                    try:
                        units_sold = int(units_str)
                        sales_amount = float(amount_str)

                        if units_sold < 0:
                            errors.append(ValidationError(file_name, idx, "units_sold", f"units_sold cannot be negative, got {units_sold}"))
                        if sales_amount < 0:
                            errors.append(ValidationError(file_name, idx, "sales_amount", f"sales_amount cannot be negative, got {sales_amount}"))

                        # Mathematical consistency check: sales_amount == units_sold * unit_price
                        if pid in self.product_prices:
                            unit_price = self.product_prices[pid]
                            expected_amount = round(units_sold * unit_price, 2)
                            if abs(sales_amount - expected_amount) > 0.01:
                                errors.append(ValidationError(
                                    file_name, idx, "sales_amount",
                                    f"Mathematical mismatch for product {pid}: sales_amount={sales_amount}, expected units({units_sold}) * price({unit_price}) = {expected_amount}"
                                ))

                    except ValueError:
                        errors.append(ValidationError(file_name, idx, "units_sold/sales_amount", f"Invalid numeric values: units='{units_str}', amount='{amount_str}'"))
                        units_sold, sales_amount = 0, 0.0

                    self.sales.append({
                        "date": date_str,
                        "store_id": sid,
                        "product_id": pid,
                        "units_sold": units_sold,
                        "sales_amount": sales_amount
                    })
        except Exception as e:
            errors.append(ValidationError(file_name, None, None, f"Failed to read file: {str(e)}"))

    def get_stores(self) -> List[Dict[str, Any]]:
        """Return validated stores list."""
        return self.stores

    def get_products(self) -> List[Dict[str, Any]]:
        """Return validated products list."""
        return self.products

    def get_sales(self) -> List[Dict[str, Any]]:
        """Return validated sales list."""
        return self.sales

    def get_inventory(self) -> List[Dict[str, Any]]:
        """Return validated inventory list."""
        return self.inventory

    def get_stores_df(self):
        """Return validated stores as pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self.stores)

    def get_products_df(self):
        """Return validated products as pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self.products)

    def get_sales_df(self):
        """Return validated sales as pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self.sales)

    def get_inventory_df(self):
        """Return validated inventory as pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame(self.inventory)
