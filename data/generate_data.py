"""
ShelfIQ Synthetic Retail Data Generator (Standard Library Implementation)
Generates realistic, internally consistent retail data across 4 stores, 55 products,
90 daily sales history records, and inventory snapshots.
Includes controlled generation for 10 specific demo scenarios.
"""

import os
import csv
import random
import datetime

def generate_data():
    random.seed(42)

    data_dir = os.path.dirname(__file__)

    # -------------------------------------------------------------
    # 1. STORES (4 stores)
    # -------------------------------------------------------------
    stores_data = [
        {"store_id": "STR001", "store_name": "Hyderabad Central", "city": "Hyderabad"},
        {"store_id": "STR002", "store_name": "Banjara Hills", "city": "Hyderabad"},
        {"store_id": "STR003", "store_name": "Kukatpally", "city": "Hyderabad"},
        {"store_id": "STR004", "store_name": "Secunderabad", "city": "Secunderabad"},
    ]

    stores_filepath = os.path.join(data_dir, "stores.csv")
    with open(stores_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["store_id", "store_name", "city"])
        writer.writeheader()
        writer.writerows(stores_data)

    # -------------------------------------------------------------
    # 2. PRODUCTS (55 products across 6 categories)
    # -------------------------------------------------------------
    products_raw = [
        # Groceries (10)
        ("PRD001", "Premium Basmati Rice 5kg", "Groceries", 550.0, 420.0),
        ("PRD002", "Refined Sunflower Oil 1L", "Groceries", 165.0, 130.0),
        ("PRD003", "Whole Wheat Atta 5kg", "Groceries", 245.0, 190.0),
        ("PRD004", "Instant Noodles 4-Pack", "Groceries", 60.0, 45.0),
        ("PRD005", "Organic Raw Honey 500g", "Groceries", 380.0, 270.0),
        ("PRD006", "Toor Dal Premium 1kg", "Groceries", 175.0, 135.0),
        ("PRD007", "Iodized Crystal Salt 1kg", "Groceries", 28.0, 18.0),
        ("PRD008", "Refined Sugar 1kg", "Groceries", 52.0, 40.0),
        ("PRD009", "White Poha 500g", "Groceries", 45.0, 32.0),
        ("PRD010", "Roasted Vermicelli 400g", "Groceries", 38.0, 26.0),

        # Beverages (9)
        ("PRD011", "Fresh Mango Juice 1L", "Beverages", 110.0, 75.0),
        ("PRD012", "Green Tea Lemon 100g", "Beverages", 220.0, 150.0),
        ("PRD013", "Carbonated Cola 1.25L", "Beverages", 65.0, 42.0),
        ("PRD014", "Sparkling Water 500ml", "Beverages", 40.0, 22.0),
        ("PRD015", "Packaged Mineral Water 1L", "Beverages", 20.0, 10.0),
        ("PRD016", "Instant Coffee Powder 100g", "Beverages", 290.0, 200.0),
        ("PRD017", "Natural Coconut Water 200ml", "Beverages", 50.0, 32.0),
        ("PRD018", "Energy Drink Citrus 250ml", "Beverages", 125.0, 80.0),
        ("PRD019", "Roasted Filter Coffee 250g", "Beverages", 195.0, 135.0),

        # Snacks (9)
        ("PRD020", "Spicy Potato Chips 100g", "Snacks", 35.0, 22.0),
        ("PRD021", "Chocolate Chip Biscuits 150g", "Snacks", 45.0, 28.0),
        ("PRD022", "Salted Roasted Cashews 200g", "Snacks", 280.0, 200.0),
        ("PRD023", "Premium Almonds 250g", "Snacks", 320.0, 230.0),
        ("PRD024", "Dark Chocolate 100g", "Snacks", 150.0, 95.0),
        ("PRD025", "Masala Peanut Chutney 200g", "Snacks", 60.0, 38.0),
        ("PRD026", "Multigrain Crackers 120g", "Snacks", 75.0, 50.0),
        ("PRD027", "Roasted Corn Snacks 150g", "Snacks", 40.0, 25.0),
        ("PRD028", "Cream Biscuits 120g", "Snacks", 30.0, 18.0),

        # Personal Care (9)
        ("PRD029", "Herbal Hair Shampoo 250ml", "Personal Care", 240.0, 160.0),
        ("PRD030", "Gentle Face Wash 150ml", "Personal Care", 185.0, 120.0),
        ("PRD031", "Antibacterial Hand Wash 250ml", "Personal Care", 95.0, 60.0),
        ("PRD032", "Herbal Soap 125g (3-pack)", "Personal Care", 120.0, 80.0),
        ("PRD033", "Fluoride Toothpaste 150g", "Personal Care", 85.0, 52.0),
        ("PRD034", "Moisturizing Body Lotion 200ml", "Personal Care", 260.0, 175.0),
        ("PRD035", "Sunscreen Lotion SPF50 100ml", "Personal Care", 420.0, 270.0),
        ("PRD036", "Hair Conditioner 180ml", "Personal Care", 210.0, 140.0),
        ("PRD037", "Deodorant Spray 150ml", "Personal Care", 199.0, 130.0),

        # Household (9)
        ("PRD038", "Dishwashing Gel Lemon 500ml", "Household", 115.0, 75.0),
        ("PRD039", "Laundry Detergent Powder 1kg", "Household", 180.0, 120.0),
        ("PRD040", "Floor Cleaner Citrus 1L", "Household", 145.0, 92.0),
        ("PRD041", "Toilet Cleaner 500ml", "Household", 98.0, 62.0),
        ("PRD042", "Garbage Bags Medium 30s", "Household", 130.0, 80.0),
        ("PRD043", "Fabric Softener 800ml", "Household", 210.0, 140.0),
        ("PRD044", "Kitchen Towel Roll 2s", "Household", 110.0, 68.0),
        ("PRD045", "Insect Repellent Spray 250ml", "Household", 175.0, 110.0),
        ("PRD046", "Air Freshener Spray 220ml", "Household", 160.0, 100.0),

        # Dairy (9)
        ("PRD047", "Toned Milk 1L", "Dairy", 56.0, 44.0),
        ("PRD048", "Fresh Greek Yogurt 200g", "Dairy", 70.0, 48.0),
        ("PRD049", "Salted Butter 100g", "Dairy", 58.0, 42.0),
        ("PRD050", "Paneer Fresh 200g", "Dairy", 95.0, 70.0),
        ("PRD051", "New Energy Whey Bar 50g", "Dairy", 90.0, 55.0),
        ("PRD052", "New Protein Shake 300ml", "Dairy", 140.0, 90.0),
        ("PRD053", "Gourmet Imported Cheese 200g", "Dairy", 450.0, 320.0),
        ("PRD054", "Premium Artisanal Tea 250g", "Beverages", 650.0, 450.0),
        ("PRD055", "Organic Quinoa Oats 500g", "Groceries", 390.0, 260.0),
    ]

    products_data = [
        {
            "product_id": p[0],
            "product_name": p[1],
            "category": p[2],
            "unit_price": f"{p[3]:.2f}",
            "cost_price": f"{p[4]:.2f}"
        }
        for p in products_raw
    ]

    products_filepath = os.path.join(data_dir, "products.csv")
    with open(products_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["product_id", "product_name", "category", "unit_price", "cost_price"])
        writer.writeheader()
        writer.writerows(products_data)

    price_map = {p[0]: p[3] for p in products_raw}

    # -------------------------------------------------------------
    # 3. DATE RANGE & SALES (90 Days: 2026-06-01 to 2026-08-29)
    # -------------------------------------------------------------
    start_date = datetime.date(2026, 6, 1)
    dates = [start_date + datetime.timedelta(days=i) for i in range(90)]

    store_ids = [s["store_id"] for s in stores_data]
    product_ids = [p[0] for p in products_raw]

    # Baseline daily sales target rates for each (store, product)
    baseline_rates = {}
    for sid in store_ids:
        for pid in product_ids:
            baseline_rates[(sid, pid)] = round(random.uniform(3.0, 7.0), 2)

    # Controlled Scenario Overrides:

    # Scenario 10: Store Performance Variance
    baseline_rates[("STR001", "PRD001")] = 15.0
    baseline_rates[("STR004", "PRD001")] = 1.5
    baseline_rates[("STR002", "PRD022")] = 12.0
    baseline_rates[("STR003", "PRD022")] = 2.0

    # Scenario 2: Approaching Stock-out (4.1 to 7.0 days remaining)
    baseline_rates[("STR001", "PRD001")] = 8.5
    baseline_rates[("STR002", "PRD005")] = 5.0
    baseline_rates[("STR003", "PRD012")] = 6.0
    baseline_rates[("STR004", "PRD030")] = 4.0

    # Scenario 3: Critical Stock-out Risk (<= 4.0 days remaining)
    baseline_rates[("STR001", "PRD002")] = 10.0
    baseline_rates[("STR002", "PRD048")] = 12.0
    baseline_rates[("STR003", "PRD031")] = 7.5

    # Scenario 4: Slow-Moving Products (velocity < 0.3 units/day)
    baseline_rates[("STR001", "PRD053")] = 0.10
    baseline_rates[("STR002", "PRD043")] = 0.15
    baseline_rates[("STR003", "PRD035")] = 0.08
    baseline_rates[("STR004", "PRD019")] = 0.12

    # Scenario 5: Overstock Products (days remaining > 60 days)
    baseline_rates[("STR001", "PRD038")] = 1.0
    baseline_rates[("STR002", "PRD033")] = 1.5
    baseline_rates[("STR003", "PRD023")] = 0.8
    baseline_rates[("STR004", "PRD040")] = 1.2

    # Scenario 6: Recent Sales Spikes (Last 7 days avg sales > 50% above baseline)
    baseline_rates[("STR001", "PRD011")] = 5.0
    baseline_rates[("STR002", "PRD020")] = 8.0
    baseline_rates[("STR003", "PRD018")] = 4.0

    # Scenario 7: Recent Sales Drops (Last 7 days avg sales > 30% below baseline)
    baseline_rates[("STR001", "PRD004")] = 12.0
    baseline_rates[("STR002", "PRD021")] = 10.0
    baseline_rates[("STR004", "PRD017")] = 15.0

    sales_records = []

    for day_idx, d in enumerate(dates):
        date_str = d.strftime("%Y-%m-%d")
        is_last_7_days = (day_idx >= 83)
        is_last_30_days = (day_idx >= 60)

        for sid in store_ids:
            for pid in product_ids:
                # Scenario 9: New products with short history
                if pid == "PRD051" and sid == "STR001" and day_idx < 85:
                    continue  # Only active last 5 days
                if pid == "PRD052" and sid == "STR002" and day_idx < 86:
                    continue  # Only active last 4 days

                # Scenario 8: Zero recent sales (last 30 days)
                if (pid == "PRD054" and sid == "STR001") or (pid == "PRD055" and sid == "STR003"):
                    if is_last_30_days:
                        continue  # 0 sales in last 30 days

                rate = baseline_rates[(sid, pid)]

                # Apply Spike Overrides for last 7 days
                if is_last_7_days:
                    if sid == "STR001" and pid == "PRD011":
                        rate = 16.0
                    elif sid == "STR002" and pid == "PRD020":
                        rate = 20.0
                    elif sid == "STR003" and pid == "PRD018":
                        rate = 13.0
                    # Apply Drop Overrides for last 7 days
                    elif sid == "STR001" and pid == "PRD004":
                        rate = 3.0
                    elif sid == "STR002" and pid == "PRD021":
                        rate = 2.0
                    elif sid == "STR004" and pid == "PRD017":
                        rate = 4.0

                # Generate daily units
                if rate < 0.5:
                    units = 1 if random.random() < rate else 0
                else:
                    # Bounded variation around target rate
                    var = random.randint(-2, 2)
                    units = max(0, int(round(rate + var)))

                if units > 0:
                    unit_price = price_map[pid]
                    sales_amount = round(units * unit_price, 2)
                    sales_records.append({
                        "date": date_str,
                        "store_id": sid,
                        "product_id": pid,
                        "units_sold": units,
                        "sales_amount": f"{sales_amount:.2f}"
                    })

    sales_filepath = os.path.join(data_dir, "sales.csv")
    with open(sales_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "store_id", "product_id", "units_sold", "sales_amount"])
        writer.writeheader()
        writer.writerows(sales_records)

    # -------------------------------------------------------------
    # 4. CURRENT INVENTORY SNAPSHOT
    # -------------------------------------------------------------
    inventory_records = []
    last_updated = "2026-08-29"

    for sid in store_ids:
        for pid in product_ids:
            stock = random.randint(80, 220)

            # Scenario 2: Approaching stock-out (4.1 to 7.0 days remaining)
            if sid == "STR001" and pid == "PRD001":
                stock = 50  # ~5.9 days remaining (avg 8.5)
            elif sid == "STR002" and pid == "PRD005":
                stock = 30  # ~6.0 days remaining (avg 5.0)
            elif sid == "STR003" and pid == "PRD012":
                stock = 32  # ~5.3 days remaining (avg 6.0)
            elif sid == "STR004" and pid == "PRD030":
                stock = 22  # ~5.5 days remaining (avg 4.0)

            # Scenario 3: Critical stock-out risk (<= 4.0 days remaining)
            elif sid == "STR001" and pid == "PRD002":
                stock = 25  # ~2.5 days remaining (avg 10.0)
            elif sid == "STR002" and pid == "PRD048":
                stock = 30  # ~2.5 days remaining (avg 12.0)
            elif sid == "STR003" and pid == "PRD031":
                stock = 18  # ~2.4 days remaining (avg 7.5)

            # Scenario 4: Slow-moving inventory
            elif sid == "STR001" and pid == "PRD053":
                stock = 45
            elif sid == "STR002" and pid == "PRD043":
                stock = 50
            elif sid == "STR003" and pid == "PRD035":
                stock = 40
            elif sid == "STR004" and pid == "PRD019":
                stock = 60

            # Scenario 5: Overstock products (> 60 days remaining)
            elif sid == "STR001" and pid == "PRD038":
                stock = 130
            elif sid == "STR002" and pid == "PRD033":
                stock = 180
            elif sid == "STR003" and pid == "PRD023":
                stock = 110
            elif sid == "STR004" and pid == "PRD040":
                stock = 150

            # Scenario 8: Zero recent sales
            elif (sid == "STR001" and pid == "PRD054") or (sid == "STR003" and pid == "PRD055"):
                stock = 85

            # Scenario 9: New products
            elif sid == "STR001" and pid == "PRD051":
                stock = 60
            elif sid == "STR002" and pid == "PRD052":
                stock = 75

            inventory_records.append({
                "store_id": sid,
                "product_id": pid,
                "current_stock": stock,
                "last_updated": last_updated
            })

    inventory_filepath = os.path.join(data_dir, "inventory.csv")
    with open(inventory_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["store_id", "product_id", "current_stock", "last_updated"])
        writer.writeheader()
        writer.writerows(inventory_records)

    print(f"Synthetic retail dataset successfully generated!")
    print(f"- Stores: {len(stores_data)}")
    print(f"- Products: {len(products_data)}")
    print(f"- Sales rows: {len(sales_records)}")
    print(f"- Inventory rows: {len(inventory_records)}")

if __name__ == "__main__":
    generate_data()
