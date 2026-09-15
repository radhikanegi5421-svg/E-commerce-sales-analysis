-- =====================================================================
-- E-Commerce Sales Analysis — Database Schema
-- Works on PostgreSQL / MySQL / SQLite (minor type tweaks noted below)
-- =====================================================================

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    region          TEXT NOT NULL,
    segment         TEXT NOT NULL,
    signup_date     DATE NOT NULL
);

CREATE TABLE products (
    product_id      TEXT PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL,
    unit_cost       NUMERIC(10,2) NOT NULL
);

CREATE TABLE orders (
    order_id          TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL REFERENCES customers(customer_id),
    product_id        TEXT NOT NULL REFERENCES products(product_id),
    order_date        DATE NOT NULL,
    quantity          INTEGER NOT NULL,
    unit_price        NUMERIC(10,2) NOT NULL,
    discount_pct      NUMERIC(4,2) NOT NULL,
    gross_revenue     NUMERIC(12,2) NOT NULL,
    discount_amount   NUMERIC(12,2) NOT NULL,
    net_revenue       NUMERIC(12,2) NOT NULL,
    total_cost        NUMERIC(12,2) NOT NULL,
    profit            NUMERIC(12,2) NOT NULL,
    ship_date         DATE NOT NULL,
    shipping_type     TEXT NOT NULL
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_product  ON orders(product_id);
CREATE INDEX idx_orders_date     ON orders(order_date);
