-- ============================================================
-- ANALYSIS 4: Churn Analysis (Step-by-Step for Ryzen 5)
-- Replaces expensive PERCENTILE_CONT with simpler approach
-- ============================================================

-- ============================================================
-- STEP 1: Create temp table with customer activity metrics
-- This is a simple aggregation - should run in under 5 seconds
-- ============================================================
DROP TABLE IF EXISTS temp_customer_activity;

CREATE TABLE temp_customer_activity AS
SELECT
    c.customer_id,
    c.customer_name,
    c.registration_date,
    MAX(o.order_date) AS last_purchase_date,
    COUNT(DISTINCT o.order_id) AS lifetime_purchases,
    ROUND(SUM(o.order_amount), 2) AS lifetime_value,
    DATEDIFF('2024-01-01', MAX(o.order_date)) AS days_since_last_purchase
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.order_status = 'Completed'
GROUP BY c.customer_id, c.customer_name, c.registration_date;

CREATE INDEX idx_temp_activity ON temp_customer_activity(customer_id);

-- ============================================================
-- STEP 2: Calculate quartile thresholds for value segmentation
-- Instead of PERCENTILE_CONT (expensive), we use ORDER BY + LIMIT
-- This approximates percentiles efficiently
-- ============================================================

-- Get total count
SELECT COUNT(*) AS total_customers FROM temp_customer_activity WHERE lifetime_value > 0;

-- Calculate 25th and 75th percentile thresholds manually
-- (Run these separately to note the values, then use in Step 3)

-- 25th percentile (Low/Medium boundary)
SELECT lifetime_value 
FROM temp_customer_activity 
WHERE lifetime_value > 0 
ORDER BY lifetime_value 
LIMIT 1 OFFSET 12500;  -- ~25% of 50K = 12,500

-- 75th percentile (Medium/High boundary)  
SELECT lifetime_value 
FROM temp_customer_activity 
WHERE lifetime_value > 0 
ORDER BY lifetime_value 
LIMIT 1 OFFSET 37500;  -- ~75% of 50K = 37,500

-- ============================================================
-- STEP 3: Classify customers using the thresholds from Step 2
-- Replace the placeholder values below with what you got from Step 2
-- Typical values: p25 ~ $8000, p75 ~ $25000 (but check yours!)
-- ============================================================
DROP TABLE IF EXISTS temp_churn_status;

CREATE TABLE temp_churn_status AS
SELECT
    customer_id,
    customer_name,
    registration_date,
    last_purchase_date,
    lifetime_purchases,
    lifetime_value,
    days_since_last_purchase,
    -- Churn status based on days inactive
    CASE
        WHEN days_since_last_purchase > 180 THEN 'Churned'
        WHEN days_since_last_purchase BETWEEN 91 AND 180 THEN 'At Risk'
        WHEN days_since_last_purchase BETWEEN 31 AND 90 THEN 'Inactive'
        WHEN days_since_last_purchase <= 30 THEN 'Active'
        ELSE 'Never Purchased'
    END AS customer_status,
    -- Value segment using pre-calculated thresholds
    -- UPDATE these numbers after running Step 2!
    CASE
        WHEN lifetime_value > 25000 THEN 'High Value'    -- REPLACE with your p75
        WHEN lifetime_value > 8000 THEN 'Medium Value'     -- REPLACE with your p25
        ELSE 'Low Value'
    END AS value_segment
FROM temp_customer_activity;

CREATE INDEX idx_temp_churn ON temp_churn_status(customer_status, value_segment);

-- ============================================================
-- STEP 4: Final aggregation (this is now super fast!)
-- ============================================================
SELECT
    customer_status,
    value_segment,
    COUNT(DISTINCT customer_id) AS customer_count,
    ROUND(AVG(lifetime_value), 2) AS avg_lifetime_value,
    ROUND(MAX(lifetime_value), 2) AS max_lifetime_value
FROM temp_churn_status
GROUP BY customer_status, value_segment
ORDER BY 
    FIELD(customer_status, 'Active', 'Inactive', 'At Risk', 'Churned', 'Never Purchased'),
    FIELD(value_segment, 'High Value', 'Medium Value', 'Low Value');

-- ============================================================
-- BONUS: Quick percentage breakdown
-- ============================================================
SELECT
    customer_status,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM temp_churn_status), 2) AS pct
FROM temp_churn_status
GROUP BY customer_status
ORDER BY FIELD(customer_status, 'Active', 'Inactive', 'At Risk', 'Churned', 'Never Purchased');

-- ============================================================
-- CLEANUP (optional)
-- ============================================================
-- DROP TABLE IF EXISTS temp_customer_activity;
-- DROP TABLE IF EXISTS temp_churn_status;
