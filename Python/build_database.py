import sqlite3
import pandas as pd

conn = sqlite3.connect("data/ecommerce_sample.db")
cur = conn.cursor()

with open("sql/01_schema.sql") as f:
    schema = f.read()
# SQLite doesn't support NUMERIC(p,s) exactly like Postgres but accepts the syntax fine.
cur.executescript(schema)

customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv")

customers.to_sql("customers", conn, if_exists="append", index=False)
products.to_sql("products", conn, if_exists="append", index=False)
orders.to_sql("orders", conn, if_exists="append", index=False)

conn.commit()
print("Rows loaded -> customers:", cur.execute("select count(*) from customers").fetchone()[0])
print("Rows loaded -> products:", cur.execute("select count(*) from products").fetchone()[0])
print("Rows loaded -> orders:", cur.execute("select count(*) from orders").fetchone()[0])
conn.close()
