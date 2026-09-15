-- =====================================================================
-- Load data from CSV — run AFTER 01_schema.sql
-- =====================================================================

-- ---- PostgreSQL (run from psql, adjust the path to /data) ----
-- \copy customers FROM 'data/customers.csv' WITH (FORMAT csv, HEADER true);
-- \copy products  FROM 'data/products.csv'  WITH (FORMAT csv, HEADER true);
-- \copy orders    FROM 'data/orders.csv'    WITH (FORMAT csv, HEADER true);

-- ---- MySQL (enable local_infile, adjust the path to /data) ----
-- LOAD DATA LOCAL INFILE 'data/customers.csv' INTO TABLE customers
--   FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
-- LOAD DATA LOCAL INFILE 'data/products.csv' INTO TABLE products
--   FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;
-- LOAD DATA LOCAL INFILE 'data/orders.csv' INTO TABLE orders
--   FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

-- ---- SQLite (run from the sqlite3 CLI) ----
-- .mode csv
-- .import --skip 1 data/customers.csv customers
-- .import --skip 1 data/products.csv products
-- .import --skip 1 data/orders.csv orders

-- A ready-to-run alternative for any engine: scripts/build_database.py
-- builds ecommerce.db (SQLite) directly from the CSVs with pandas.
