-- ============================================================
-- ANALYSIS 6: Customer Acquisition / LTV (Step-by-Step for Ryzen 5)
-- Replaces expensive correlated subquery with JOIN approach
-- ============================================================

-- ============================================================
-- STEP 1: Create temp table with first purchase date per customer
-- Simple GROUP BY - very fast
-- ============================================================
DROP TABLE IF EXISTS temp_first_purchase;

CREATE TABLE temp_first_purchase AS
SELECT
    customer_id,
    MIN(order_date) AS first_purchase_date
FROM orders
WHERE order_status = 'Completed'
GROUP BY customer_id;

CREATE INDEX idx_temp_first ON temp_first_purchase(customer_id);

-- ============================================================
-- STEP 2: Create temp table with first order details
-- Use JOIN instead of correlated subquery (much faster!)
-- ============================================================
DROP TABLE IF EXISTS temp_first_order;

CREATE TABLE temp_first_order AS
SELECT
    fp.customer_id,
    fp.first_purchase_date,
    o.order_amount AS first_order_amount,
    DATEDIFF(fp.first_purchase_date, c.registration_date) AS days_to_first_purchase
FROM temp_first_purchase fp
INNER JOIN orders o ON fp.customer_id = o.customer_id 
    AND fp.first_purchase_date = o.order_date 
    AND o.order_status = 'Completed'
INNER JOIN customers c ON fp.customer_id = c.customer_id;

-- Handle edge case: multiple orders on first date - pick minimum
-- (Some customers might have multiple orders on their first day)
CREATE INDEX idx_temp_first_order ON temp_first_order(customer_id);

-- ============================================================
-- STEP 3: Create temp table with customer lifetime value
-- Simple aggregation - very fast
-- ============================================================
DROP TABLE IF EXISTS temp_customer_ltv;

CREATE TABLE temp_customer_ltv AS
SELECT
    customer_id,
    ROUND(SUM(order_amount), 2) AS customer_lifetime_value,
    COUNT(DISTINCT order_id) AS total_orders
FROM orders
WHERE order_status = 'Completed'
GROUP BY customer_id;

CREATE INDEX idx_temp_ltv ON temp_customer_ltv(customer_id);

-- ============================================================
-- STEP 4: Final acquisition analysis (joins pre-aggregated tables)
-- This is fast because all heavy work is already done!
-- ============================================================
SELECT
    DATE_FORMAT(fo.first_purchase_date, '%Y-%m-01') AS acquisition_month,
    COUNT(DISTINCT fo.customer_id) AS new_customers,
    ROUND(AVG(fo.days_to_first_purchase), 1) AS avg_days_to_first_purchase,
    ROUND(AVG(fo.first_order_amount), 2) AS avg_first_order_value,
    ROUND(AVG(lt.customer_lifetime_value), 2) AS avg_customer_ltv,
    ROUND(AVG(lt.customer_lifetime_value) / AVG(fo.first_order_amount), 2) AS ltv_to_first_order_ratio,
    ROUND(AVG(lt.total_orders), 1) AS avg_lifetime_orders
FROM temp_first_order fo
INNER JOIN temp_customer_ltv lt ON fo.customer_id = lt.customer_id
GROUP BY DATE_FORMAT(fo.first_purchase_date, '%Y-%m-01')
ORDER BY acquisition_month DESC;

-- ============================================================
-- BONUS: Customer-level detail (if you want to drill down)
-- ============================================================
SELECT
    fo.customer_id,
    fo.first_purchase_date,
    fo.first_order_amount,
    fo.days_to_first_purchase,
    lt.customer_lifetime_value,
    lt.total_orders,
    ROUND(lt.customer_lifetime_value / fo.first_order_amount, 2) AS ltv_ratio
FROM temp_first_order fo
INNER JOIN temp_customer_ltv lt ON fo.customer_id = lt.customer_id
ORDER BY lt.customer_lifetime_value DESC
LIMIT 20;

-- ============================================================
-- CLEANUP (optional)
-- ============================================================
-- DROP TABLE IF EXISTS temp_first_purchase;
-- DROP TABLE IF EXISTS temp_first_order;
-- DROP TABLE IF EXISTS temp_customer_ltv;
