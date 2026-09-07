-- ============================================================
-- ANALYSIS 5: Month-over-Month Revenue Growth
-- Purpose: Track business growth trends
-- ============================================================

WITH monthly_revenue AS (
    SELECT
        DATE_FORMAT(o.order_date, '%Y-%m-01') AS order_month,
        ROUND(SUM(o.order_amount), 2) AS total_revenue,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT o.customer_id) AS unique_customers,
        ROUND(AVG(o.order_amount), 2) AS avg_order_value
    FROM orders o
    WHERE o.order_status = 'Completed'
    GROUP BY DATE_FORMAT(o.order_date, '%Y-%m-01')
),

revenue_growth AS (
    SELECT
        order_month,
        total_revenue,
        total_orders,
        unique_customers,
        avg_order_value,
        LAG(total_revenue) OVER (ORDER BY order_month) AS prev_month_revenue,
        total_revenue - LAG(total_revenue) OVER (ORDER BY order_month) AS revenue_change,
        ROUND(
            100.0 * (total_revenue - LAG(total_revenue) OVER (ORDER BY order_month))
            / NULLIF(LAG(total_revenue) OVER (ORDER BY order_month), 0),
            2
        ) AS growth_rate_pct
    FROM monthly_revenue
)

SELECT
    order_month,
    total_revenue,
    total_orders,
    unique_customers,
    avg_order_value,
    ROUND(prev_month_revenue, 2) AS prev_month_revenue,
    ROUND(revenue_change, 2) AS revenue_change,
    growth_rate_pct
FROM revenue_growth
ORDER BY order_month;

-- Key Skills Demonstrated:
-- • LAG() for previous row comparison
-- • Date truncation with DATE_FORMAT
-- • Percentage growth calculation with NULLIF (division safety)
-- • Critical business growth analysis
