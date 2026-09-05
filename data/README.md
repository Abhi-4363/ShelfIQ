# ShelfIQ Synthetic Retail Dataset Documentation

> **Synthetic dataset generated for ShelfIQ Retail Sales & Inventory Copilot (Track ID: PS03)**

---

## 📊 Dataset Overview
The dataset models a realistic multi-store retail operation in Hyderabad / Secunderabad, featuring 4 stores, 55 products across 6 retail categories, 90 days of daily sales history (2026-06-01 to 2026-08-29), and snapshot inventory levels.

| File | Records | Key Fields | Description |
| :--- | :--- | :--- | :--- |
| `stores.csv` | 4 | `store_id`, `store_name`, `city` | Master list of retail store locations |
| `products.csv` | 55 | `product_id`, `product_name`, `category`, `unit_price`, `cost_price` | Product catalogue with INR pricing |
| `sales.csv` | 19,064 | `date`, `store_id`, `product_id`, `units_sold`, `sales_amount` | 90 days of daily transactions |
| `inventory.csv` | 220 | `store_id`, `product_id`, `current_stock`, `last_updated` | Current stock snapshot per store & product |

---

## 🏪 Stores
- `STR001`: **Hyderabad Central** (City: Hyderabad) - Flagship store, high traffic
- `STR002`: **Banjara Hills** (City: Hyderabad) - Premium neighborhood store
- `STR003`: **Kukatpally** (City: Hyderabad) - High volume residential store
- `STR004`: **Secunderabad** (City: Secunderabad) - Moderate volume neighborhood store

---

## 📦 Categories & Product Distribution (55 Products)
1. **Groceries** (10 products): Rice, Atta, Cooking Oil, Dal, Sugar, Honey, Salt, Poha, Vermicelli, etc.
2. **Beverages** (9 products): Juices, Green Tea, Cola, Mineral/Sparkling Water, Coffee, Coconut Water, Energy Drinks.
3. **Snacks** (9 products): Chips, Chocolate Biscuits, Cashews, Almonds, Dark Chocolate, Multigrain Crackers, Snacks.
4. **Personal Care** (9 products): Shampoo, Face Wash, Hand Wash, Soaps, Toothpaste, Body Lotion, Sunscreen, Conditioner.
5. **Household** (9 products): Dishwashing Gel, Detergent, Floor/Toilet Cleaners, Garbage Bags, Fabric Softener.
6. **Dairy** (9 products): Toned Milk, Greek Yogurt, Butter, Paneer, Whey Bars, Protein Shakes, Cheese.

---

## 🎯 Intentionally Created Demo Scenarios

The synthetic dataset contains 10 specific, verifiable operational scenarios:

### 1. Normal Healthy Inventory (104 store-product pairs)
- Products with steady sales velocity (3 to 12 units/day) and 10 to 30 days of stock remaining.

### 2. Approaching Stock-Out Risk (5 store-product pairs: 4.1 to 7.0 days remaining)
- **STR001 + PRD001** (*Premium Basmati Rice 5kg*): Current Stock: `50`, Daily Sales: `8.5 units/day`, Days Remaining: `5.9 days`
- **STR002 + PRD005** (*Organic Raw Honey 500g*): Current Stock: `30`, Daily Sales: `4.6 units/day`, Days Remaining: `6.5 days`
- **STR003 + PRD012** (*Green Tea Lemon 100g*): Current Stock: `32`, Daily Sales: `6.0 units/day`, Days Remaining: `5.3 days`
- **STR004 + PRD030** (*Gentle Face Wash 150ml*): Current Stock: `22`, Daily Sales: `3.9 units/day`, Days Remaining: `5.7 days`

### 3. Critical Stock-Out Risk (3 store-product pairs: <= 4.0 days remaining)
- **STR001 + PRD002** (*Refined Sunflower Oil 1L*): Current Stock: `25`, Daily Sales: `10.2 units/day`, Days Remaining: `2.5 days`
- **STR002 + PRD048** (*Fresh Greek Yogurt 200g*): Current Stock: `30`, Daily Sales: `12.1 units/day`, Days Remaining: `2.5 days`
- **STR003 + PRD031** (*Antibacterial Hand Wash 250ml*): Current Stock: `18`, Daily Sales: `7.6 units/day`, Days Remaining: `2.4 days`

### 4. Slow-Moving Products (4 store-product pairs: velocity < 0.3 units/day)
- **STR001 + PRD053** (*Gourmet Imported Cheese 200g*): `0.16 units/day`, Stock: `45`
- **STR002 + PRD043** (*Fabric Softener 800ml*): `0.19 units/day`, Stock: `50`
- **STR003 + PRD035** (*Sunscreen Lotion SPF50 100ml*): `0.10 units/day`, Stock: `40`
- **STR004 + PRD019** (*Roasted Filter Coffee 250g*): `0.16 units/day`, Stock: `60`

### 5. Overstocked Inventory (11 store-product pairs: > 60 days of stock remaining)
- **STR001 + PRD038** (*Dishwashing Gel Lemon 500ml*): `1.07 units/day`, Stock: `130` (121.9 days remaining)
- **STR002 + PRD033** (*Fluoride Toothpaste 150g*): `1.91 units/day`, Stock: `180` (94.2 days remaining)
- **STR003 + PRD023** (*Premium Almonds 250g*): `1.29 units/day`, Stock: `110` (85.3 days remaining)
- **STR004 + PRD040** (*Floor Cleaner Citrus 1L*): `1.22 units/day`, Stock: `150` (122.7 days remaining)

### 6. Recent Sales Spikes (4 store-product pairs: > +50% in last 7 days vs 83-day baseline)
- **STR001 + PRD011** (*Fresh Mango Juice 1L*): Baseline: `5.12/day` → Recent 7d: `15.86/day` (**+209.7% spike**)
- **STR002 + PRD020** (*Spicy Potato Chips 100g*): Baseline: `7.89/day` → Recent 7d: `18.43/day` (**+133.5% spike**)
- **STR003 + PRD018** (*Energy Drink Citrus 250ml*): Baseline: `4.07/day` → Recent 7d: `14.14/day` (**+247.3% spike**)

### 7. Recent Sales Drops (8 store-product pairs: > -30% in last 7 days vs 83-day baseline)
- **STR001 + PRD004** (*Instant Noodles 4-Pack*): Baseline: `12.04/day` → Recent 7d: `3.00/day` (**-75.1% drop**)
- **STR002 + PRD021** (*Chocolate Chip Biscuits 150g*): Baseline: `10.02/day` → Recent 7d: `2.57/day` (**-74.3% drop**)
- **STR004 + PRD017** (*Natural Coconut Water 200ml*): Baseline: `14.94/day` → Recent 7d: `4.00/day` (**-73.2% drop**)

### 8. Zero Recent Sales (2 store-product pairs: 0 sales in last 30 days)
- **STR001 + PRD054** (*Premium Artisanal Tea 250g*): `0` sales in last 30 days (408 historical units, Stock: 85)
- **STR003 + PRD055** (*Organic Quinoa Oats 500g*): `0` sales in last 30 days (368 historical units, Stock: 85)

### 9. Insufficient / New Sales History (2 store-product pairs: <= 5 days history)
- **STR001 + PRD051** (*New Energy Whey Bar 50g*): Only `5` days of sales history recorded.
- **STR002 + PRD052** (*New Protein Shake 300ml*): Only `4` days of sales history recorded.

### 10. Store Performance Variance (2 products with vastly different demand by location)
- **PRD001** (*Premium Basmati Rice 5kg*): `8.47 units/day` at Hyderabad Central vs `1.67 units/day` at Secunderabad.
- **PRD022** (*Salted Roasted Cashews 200g*): `11.93 units/day` at Banjara Hills vs `1.97 units/day` at Kukatpally.

---

## 🛠️ Reproducibility & Validation
- Generator script: `python data/generate_data.py` (fixed random seed = 42)
- Validation script: `python data/validate_data.py`
