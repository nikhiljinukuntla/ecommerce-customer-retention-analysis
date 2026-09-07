-- ============================================================
-- ANALYSIS 2: Cohort Retention Analysis
-- Purpose: Understand how customers engage over time by cohort
-- ============================================================

WITH cohort_data AS (
    SELECT
        c.customer_id,
        -- Cohort month = first purchase month
        DATE_FORMAT(MIN(o.order_date), '%Y-%m-01') AS cohort_month,
        -- Order month
        DATE_FORMAT(o.order_date, '%Y-%m-01') AS order_month,
        -- Months since cohort start
        PERIOD_DIFF(DATE_FORMAT(o.order_date, '%Y%m'), DATE_FORMAT(MIN(o.order_date), '%Y%m')) AS months_since_cohort
    FROM customers c
    INNER JOIN orders o 
        ON c.customer_id = o.customer_id 
        AND o.order_status = 'Completed'
    GROUP BY c.customer_id, o.order_date
),

cohort_sizes AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohort_data
    WHERE months_since_cohort = 0
    GROUP BY cohort_month
),

retention_table AS (
    SELECT
        cd.cohort_month,
        cd.months_since_cohort,
        COUNT(DISTINCT cd.customer_id) AS active_users
    FROM cohort_data cd
    GROUP BY cd.cohort_month, cd.months_since_cohort
)

SELECT
    cs.cohort_month,
    rt.months_since_cohort,
    rt.active_users,
    cs.cohort_size,
    ROUND(100.0 * rt.active_users / cs.cohort_size, 2) AS retention_rate_pct
FROM retention_table rt
INNER JOIN cohort_sizes cs 
    ON rt.cohort_month = cs.cohort_month
WHERE rt.months_since_cohort <= 12
ORDER BY cs.cohort_month, rt.months_since_cohort;

-- Key Skills Demonstrated:
-- • DATE_FORMAT for month-level grouping
-- • PERIOD_DIFF for calculating cohort age in months
-- • Retention calculation logic (active_users / cohort_size)
-- • Real business metric: cohort-based retention
