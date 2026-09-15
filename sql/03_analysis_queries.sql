-- =====================================================================
-- E-Commerce Sales Analysis — Business Questions
-- Tested on SQLite; portable to PostgreSQL/MySQL with trivial date-fn edits
-- =====================================================================

-- Q1. What is monthly net revenue and profit over the last two years?
SELECT
    strftime('%Y-%m', order_date) AS month,
    ROUND(SUM(net_revenue), 2)    AS net_revenue,
    ROUND(SUM(profit), 2)         AS profit,
    COUNT(DISTINCT order_id)      AS orders
FROM orders
GROUP BY 1
ORDER BY 1;

-- Q2. Which product categories generate the most revenue and profit?
SELECT
    p.category,
    ROUND(SUM(o.net_revenue), 2) AS net_revenue,
    ROUND(SUM(o.profit), 2)      AS profit,
    ROUND(100.0 * SUM(o.profit) / NULLIF(SUM(o.net_revenue), 0), 1) AS profit_margin_pct
FROM orders o
JOIN products p ON p.product_id = o.product_id
GROUP BY p.category
ORDER BY net_revenue DESC;

-- Q3. What are the top 10 products by net revenue?
SELECT
    p.product_name,
    p.category,
    ROUND(SUM(o.net_revenue), 2) AS net_revenue,
    SUM(o.quantity)              AS units_sold
FROM orders o
JOIN products p ON p.product_id = o.product_id
GROUP BY p.product_id
ORDER BY net_revenue DESC
LIMIT 10;

-- Q4. Which regions drive the most revenue, and what is the average order value (AOV)?
SELECT
    c.region,
    COUNT(o.order_id)                              AS orders,
    ROUND(SUM(o.net_revenue), 2)                   AS net_revenue,
    ROUND(SUM(o.net_revenue) / COUNT(o.order_id), 2) AS avg_order_value
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.region
ORDER BY net_revenue DESC;

-- Q5. Who are the top 10 customers by lifetime net revenue (VIP list)?
SELECT
    c.customer_id,
    c.customer_name,
    c.segment,
    COUNT(o.order_id)            AS orders,
    ROUND(SUM(o.net_revenue), 2) AS lifetime_revenue
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
GROUP BY c.customer_id
ORDER BY lifetime_revenue DESC
LIMIT 10;

-- Q6. RFM segmentation: Recency, Frequency, Monetary value per customer
-- (Reference date = the day after the last order in the dataset)
WITH last_order AS (SELECT MAX(order_date) AS max_date FROM orders),
rfm_base AS (
    SELECT
        o.customer_id,
        CAST(julianday((SELECT max_date FROM last_order)) - julianday(MAX(o.order_date)) AS INTEGER) AS recency_days,
        COUNT(o.order_id) AS frequency,
        ROUND(SUM(o.net_revenue), 2) AS monetary
    FROM orders o
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,   -- 4 = most recent
    NTILE(4) OVER (ORDER BY frequency ASC)     AS f_score,
    NTILE(4) OVER (ORDER BY monetary ASC)      AS m_score
FROM rfm_base
ORDER BY monetary DESC;

-- Q7. How does discounting affect profit margin? (bucketed by discount tier)
SELECT
    CASE
        WHEN discount_pct = 0 THEN '0% (no discount)'
        WHEN discount_pct <= 0.10 THEN '1-10%'
        ELSE '11%+'
    END AS discount_tier,
    COUNT(*)                                                        AS orders,
    ROUND(SUM(net_revenue), 2)                                      AS net_revenue,
    ROUND(100.0 * SUM(profit) / NULLIF(SUM(net_revenue), 0), 1)     AS avg_profit_margin_pct
FROM orders
GROUP BY 1
ORDER BY 1;

-- Q8. What is month-over-month revenue growth (%)?
WITH monthly AS (
    SELECT strftime('%Y-%m', order_date) AS month, SUM(net_revenue) AS revenue
    FROM orders
    GROUP BY 1
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month)) / NULLIF(LAG(revenue) OVER (ORDER BY month), 0), 1) AS mom_growth_pct
FROM monthly
ORDER BY month;

-- Q9. Customer segment performance: Consumer vs Corporate vs Small Business
SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(o.order_id)             AS orders,
    ROUND(SUM(o.net_revenue), 2)  AS net_revenue,
    ROUND(SUM(o.net_revenue) / COUNT(DISTINCT c.customer_id), 2) AS revenue_per_customer
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
GROUP BY c.segment
ORDER BY net_revenue DESC;

-- Q10. Express vs Standard shipping — does faster shipping correlate with bigger orders?
SELECT
    shipping_type,
    COUNT(*)                                   AS orders,
    ROUND(AVG(net_revenue), 2)                 AS avg_order_value,
    ROUND(AVG(julianday(ship_date) - julianday(order_date)), 1) AS avg_fulfillment_days
FROM orders
GROUP BY shipping_type;

-- Q11. Identify at-risk customers: previously active, no order in the last 90 days
WITH last_order AS (SELECT MAX(order_date) AS max_date FROM orders),
cust_last AS (
    SELECT customer_id, MAX(order_date) AS last_purchase, COUNT(*) AS orders, SUM(net_revenue) AS lifetime_revenue
    FROM orders
    GROUP BY customer_id
)
SELECT
    customer_id,
    last_purchase,
    orders,
    ROUND(lifetime_revenue, 2) AS lifetime_revenue,
    CAST(julianday((SELECT max_date FROM last_order)) - julianday(last_purchase) AS INTEGER) AS days_since_last_order
FROM cust_last
WHERE orders >= 3
  AND julianday((SELECT max_date FROM last_order)) - julianday(last_purchase) > 90
ORDER BY lifetime_revenue DESC
LIMIT 15;

-- Q12. New vs. returning customer revenue split, by month
WITH first_purchase AS (
    SELECT customer_id, MIN(order_date) AS first_order_date
    FROM orders
    GROUP BY customer_id
)
SELECT
    strftime('%Y-%m', o.order_date) AS month,
    CASE WHEN o.order_date = fp.first_order_date THEN 'New' ELSE 'Returning' END AS customer_type,
    ROUND(SUM(o.net_revenue), 2) AS net_revenue,
    COUNT(DISTINCT o.customer_id) AS customers
FROM orders o
JOIN first_purchase fp ON fp.customer_id = o.customer_id
GROUP BY 1, 2
ORDER BY 1, 2;
