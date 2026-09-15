"""
Generates a synthetic but realistic e-commerce dataset for a data-analyst
portfolio project: customers, products, and orders (2 years of activity).
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

# ---------------------------------------------------------------- CUSTOMERS
N_CUSTOMERS = 500
REGIONS = ["North", "South", "East", "West", "Central"]
SEGMENTS = ["Consumer", "Corporate", "Small Business"]
FIRST_NAMES = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "William","Elizabeth","David","Barbara","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Charles","Karen","Ana","Priya","Wei","Fatima","Carlos",
    "Yuki","Omar","Sofia","Liam","Emma"]
LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson","White"]

customers = pd.DataFrame({
    "customer_id": [f"CUST-{i:04d}" for i in range(1, N_CUSTOMERS + 1)],
    "customer_name": [f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}" for _ in range(N_CUSTOMERS)],
    "region": rng.choice(REGIONS, N_CUSTOMERS, p=[0.22, 0.20, 0.22, 0.20, 0.16]),
    "segment": rng.choice(SEGMENTS, N_CUSTOMERS, p=[0.55, 0.28, 0.17]),
    "signup_date": [
        (datetime(2023, 1, 1) + timedelta(days=int(d)))
        for d in rng.integers(0, 640, N_CUSTOMERS)
    ],
})

# ------------------------------------------------------------------ PRODUCTS
CATALOG = {
    "Electronics": [("Wireless Mouse", 19.99), ("Bluetooth Speaker", 45.00),
        ("USB-C Hub", 29.50), ("Noise Cancelling Headphones", 89.99),
        ("4K Webcam", 55.00), ("Portable SSD 1TB", 79.99), ("Smart Watch", 129.99),
        ("Mechanical Keyboard", 69.99)],
    "Home & Kitchen": [("Stainless Steel Pan", 34.99), ("Coffee Maker", 42.00),
        ("Air Fryer", 74.99), ("Knife Set", 39.99), ("Blender", 32.50),
        ("Electric Kettle", 24.99), ("Cutting Board Set", 18.99)],
    "Office Supplies": [("Ergonomic Chair", 149.99), ("Standing Desk", 219.00),
        ("Desk Organizer", 14.99), ("Notebook 3-Pack", 9.99),
        ("Printer Paper (Case)", 39.99), ("Desk Lamp", 22.50)],
    "Apparel": [("Cotton T-Shirt", 12.99), ("Running Shoes", 64.99),
        ("Winter Jacket", 89.00), ("Backpack", 45.99), ("Baseball Cap", 15.99)],
    "Sports & Outdoors": [("Yoga Mat", 21.99), ("Water Bottle", 11.99),
        ("Camping Tent (2p)", 99.99), ("Resistance Bands Set", 17.99),
        ("Cycling Helmet", 38.00)],
}
rows = []
pid = 1
for cat, items in CATALOG.items():
    for name, price in items:
        rows.append((f"PROD-{pid:04d}", name, cat, round(price, 2), round(price * rng.uniform(0.45, 0.62), 2)))
        pid += 1
products = pd.DataFrame(rows, columns=["product_id", "product_name", "category", "unit_price", "unit_cost"])

# -------------------------------------------------------------------- ORDERS
N_ORDERS = 6000
start_date = datetime(2024, 1, 1)
end_date = datetime(2025, 12, 31)
date_range_days = (end_date - start_date).days

# Slight seasonal + weekend effect + gentle upward trend over time
def sample_order_date():
    d = int(rng.triangular(0, date_range_days * 0.65, date_range_days))
    date = start_date + timedelta(days=d)
    # boost November/December (holiday season) by resampling some into Nov/Dec
    if rng.random() < 0.18:
        year = rng.choice([2024, 2025])
        month = rng.choice([11, 12])
        day = int(rng.integers(1, 28))
        date = datetime(year, month, day)
    return date

customer_ids = customers["customer_id"].values
# give some customers much higher purchase frequency (power-law-ish loyalty)
cust_weights = rng.pareto(2.5, N_CUSTOMERS) + 0.2
cust_weights = cust_weights / cust_weights.sum()

product_ids = products["product_id"].values
product_prices = dict(zip(products.product_id, products.unit_price))
product_costs = dict(zip(products.product_id, products.unit_cost))

order_rows = []
for i in range(1, N_ORDERS + 1):
    cust = rng.choice(customer_ids, p=cust_weights)
    prod = rng.choice(product_ids)
    qty = int(rng.choice([1, 1, 1, 2, 2, 3, 4, 5], p=[0.35,0.2,0.15,0.12,0.08,0.05,0.03,0.02]))
    order_date = sample_order_date()
    if order_date > end_date:
        order_date = end_date
    unit_price = product_prices[prod]
    unit_cost = product_costs[prod]
    discount_pct = round(float(rng.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20], p=[0.55,0.1,0.1,0.1,0.08,0.05,0.02])), 2)
    gross_revenue = round(unit_price * qty, 2)
    discount_amount = round(gross_revenue * discount_pct, 2)
    net_revenue = round(gross_revenue - discount_amount, 2)
    total_cost = round(unit_cost * qty, 2)
    profit = round(net_revenue - total_cost, 2)
    ship_days = int(rng.integers(1, 8))
    order_rows.append((
        f"ORD-{i:05d}", cust, prod, order_date.date().isoformat(),
        qty, unit_price, discount_pct, gross_revenue, discount_amount,
        net_revenue, total_cost, profit,
        (order_date + timedelta(days=ship_days)).date().isoformat(),
        rng.choice(["Standard", "Express"], p=[0.8, 0.2]),
    ))

orders = pd.DataFrame(order_rows, columns=[
    "order_id", "customer_id", "product_id", "order_date", "quantity",
    "unit_price", "discount_pct", "gross_revenue", "discount_amount",
    "net_revenue", "total_cost", "profit", "ship_date", "shipping_type",
])

customers["signup_date"] = customers["signup_date"].dt.date.astype(str)

customers.to_csv("data/customers.csv", index=False)
products.to_csv("data/products.csv", index=False)
orders.to_csv("data/orders.csv", index=False)

print("customers:", customers.shape)
print("products:", products.shape)
print("orders:", orders.shape)
print(orders.head(3).to_string())
print("Total net revenue:", orders.net_revenue.sum())
print("Date range:", orders.order_date.min(), orders.order_date.max())
