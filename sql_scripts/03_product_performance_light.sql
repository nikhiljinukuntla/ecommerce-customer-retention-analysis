-- ============================================================
-- ANALYSIS 3: Product Performance (Step-by-Step for Ryzen 5)
-- Run each block separately in MySQL Workbench
-- ============================================================

-- ============================================================
-- STEP 1: Create a temp table with product sales data
-- This pre-aggregates order_items so we don't join 520K rows repeatedly
-- ============================================================
DROP TABLE IF EXISTS temp_product_sales;

CREATE TABLE temp_product_sales AS
SELECT
    oi.product_id,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    SUM(oi.quantity) AS total_quantity_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM order_items oi
INNER JOIN orders o ON oi.order_id = o.order_id AND o.order_status = 'Completed'
GROUP BY oi.product_id;

-- Add index for faster lookups
CREATE INDEX idx_temp_product ON temp_product_sales(product_id);

-- ============================================================
-- STEP 2: Create a temp table with product review averages
-- Pre-aggregate reviews so we don't join 100K rows repeatedly
-- ============================================================
DROP TABLE IF EXISTS temp_product_reviews;

CREATE TABLE temp_product_reviews AS
SELECT
    product_id,
    ROUND(AVG(rating), 2) AS avg_rating,
    COUNT(DISTINCT review_id) AS review_count
FROM customer_reviews
GROUP BY product_id;

CREATE INDEX idx_temp_reviews ON temp_product_reviews(product_id);

-- ============================================================
-- STEP 3: Join everything together (now much faster!)
-- This joins: products (500) + temp_sales (500) + temp_reviews (500)
-- Instead of: products (500) + order_items (520K) + reviews (100K)
-- ============================================================
SELECT
    p.category,
    p.product_id,
    p.product_name,
    ROUND(p.price, 2) AS product_price,
    COALESCE(s.total_orders, 0) AS total_orders,
    COALESCE(s.total_quantity_sold, 0) AS total_quantity_sold,
    COALESCE(s.total_revenue, 0) AS total_revenue,
    COALESCE(r.avg_rating, 0) AS avg_rating,
    COALESCE(r.review_count, 0) AS review_count
FROM products p
LEFT JOIN temp_product_sales s ON p.product_id = s.product_id
LEFT JOIN temp_product_reviews r ON p.product_id = r.product_id
WHERE s.total_orders > 0
ORDER BY p.category, s.total_revenue DESC;

-- ============================================================
-- STEP 4: Ranking within category (run separately if needed)
-- This is lighter because it works on the result above
-- ============================================================
SELECT
    category,
    product_id,
    product_name,
    product_price,
    total_orders,
    total_quantity_sold,
    total_revenue,
    avg_rating,
    review_count,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category,
    ROW_NUMBER() OVER (ORDER BY total_revenue DESC) AS overall_rank
FROM (
    SELECT
        p.category,
        p.product_id,
        p.product_name,
        p.price AS product_price,
        COALESCE(s.total_orders, 0) AS total_orders,
        COALESCE(s.total_quantity_sold, 0) AS total_quantity_sold,
        COALESCE(s.total_revenue, 0) AS total_revenue,
        COALESCE(r.avg_rating, 0) AS avg_rating,
        COALESCE(r.review_count, 0) AS review_count
    FROM products p
    LEFT JOIN temp_product_sales s ON p.product_id = s.product_id
    LEFT JOIN temp_product_reviews r ON p.product_id = r.product_id
    WHERE s.total_orders > 0
) ranked_data
ORDER BY category, total_revenue DESC;

-- ============================================================
-- CLEANUP (optional - run after you're done viewing results)
-- ============================================================
-- DROP TABLE IF EXISTS temp_product_sales;
-- DROP TABLE IF EXISTS temp_product_reviews;
