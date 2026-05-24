-- ============================================================
-- Sales Data Analysis — Advanced SQL Queries
-- Author  : Praveena
-- Purpose : Revenue trends, customer behaviour & regional KPIs
-- ============================================================


-- ──────────────────────────────────────────────────────────
-- 1. TOTAL REVENUE & PROFIT SUMMARY
-- ──────────────────────────────────────────────────────────
SELECT
    COUNT(*)                        AS total_orders,
    COUNT(DISTINCT customer_id)     AS unique_customers,
    ROUND(SUM(sales), 2)            AS total_revenue,
    ROUND(SUM(profit), 2)           AS total_profit,
    ROUND(AVG(sales), 2)            AS avg_order_value,
    ROUND(SUM(profit)/SUM(sales)*100, 2) AS profit_margin_pct
FROM sales;


-- ──────────────────────────────────────────────────────────
-- 2. REGIONAL PERFORMANCE (with Ranking)
-- ──────────────────────────────────────────────────────────
SELECT
    region,
    COUNT(*)                           AS total_orders,
    ROUND(SUM(sales), 2)               AS total_sales,
    ROUND(AVG(sales), 2)               AS avg_sale,
    ROUND(SUM(profit), 2)              AS total_profit,
    RANK() OVER (ORDER BY SUM(sales) DESC) AS revenue_rank
FROM sales
GROUP BY region
ORDER BY total_sales DESC;


-- ──────────────────────────────────────────────────────────
-- 3. MONTHLY REVENUE WITH MONTH-OVER-MONTH GROWTH (CTE)
-- ──────────────────────────────────────────────────────────
WITH monthly_sales AS (
    SELECT
        year,
        month,
        ROUND(SUM(sales), 2) AS revenue
    FROM sales
    GROUP BY year, month
),
mom_growth AS (
    SELECT
        year,
        month,
        revenue,
        LAG(revenue) OVER (PARTITION BY year ORDER BY month) AS prev_month_revenue,
        ROUND(
            (revenue - LAG(revenue) OVER (PARTITION BY year ORDER BY month))
            / NULLIF(LAG(revenue) OVER (PARTITION BY year ORDER BY month), 0) * 100,
        2) AS mom_growth_pct
    FROM monthly_sales
)
SELECT * FROM mom_growth
ORDER BY year, month;


-- ──────────────────────────────────────────────────────────
-- 4. CATEGORY REVENUE SHARE (Window Function)
-- ──────────────────────────────────────────────────────────
SELECT
    category,
    ROUND(SUM(sales), 2) AS category_revenue,
    ROUND(
        SUM(sales) * 100.0 / SUM(SUM(sales)) OVER (),
    2) AS revenue_share_pct,
    RANK() OVER (ORDER BY SUM(sales) DESC) AS category_rank
FROM sales
GROUP BY category
ORDER BY category_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 5. TOP 10 CUSTOMERS BY LIFETIME VALUE
-- ──────────────────────────────────────────────────────────
SELECT
    customer_id,
    COUNT(DISTINCT order_id)   AS total_orders,
    ROUND(SUM(sales), 2)       AS lifetime_value,
    ROUND(AVG(sales), 2)       AS avg_order_value,
    ROUND(SUM(profit), 2)      AS total_profit,
    ROUND(SUM(quantity), 0)    AS total_items_bought,
    NTILE(4) OVER (ORDER BY SUM(sales) DESC) AS customer_tier
FROM sales
GROUP BY customer_id
ORDER BY lifetime_value DESC
LIMIT 10;


-- ──────────────────────────────────────────────────────────
-- 6. SEASONAL SALES PATTERN (Quarter Analysis)
-- ──────────────────────────────────────────────────────────
SELECT
    year,
    quarter,
    ROUND(SUM(sales), 2)   AS quarterly_revenue,
    ROUND(AVG(sales), 2)   AS avg_order_value,
    COUNT(*)               AS total_orders,
    ROUND(
        SUM(sales) * 100.0 / SUM(SUM(sales)) OVER (PARTITION BY year),
    2) AS pct_of_annual_revenue
FROM sales
GROUP BY year, quarter
ORDER BY year, quarter;


-- ──────────────────────────────────────────────────────────
-- 7. HIGH DISCOUNT IMPACT ANALYSIS (Subquery)
-- ──────────────────────────────────────────────────────────
SELECT
    category,
    ROUND(AVG(discount) * 100, 1)    AS avg_discount_pct,
    ROUND(AVG(profit), 2)             AS avg_profit,
    ROUND(AVG(sales), 2)              AS avg_sales,
    COUNT(*)                          AS order_count,
    -- compare against overall avg profit
    ROUND(AVG(profit) - (SELECT AVG(profit) FROM sales), 2) AS vs_overall_avg_profit
FROM sales
WHERE discount > 0
GROUP BY category
ORDER BY avg_discount_pct DESC;


-- ──────────────────────────────────────────────────────────
-- 8. RUNNING TOTAL REVENUE PER REGION (Window Function)
-- ──────────────────────────────────────────────────────────
SELECT
    region,
    year,
    month,
    ROUND(SUM(sales), 2) AS monthly_sales,
    ROUND(
        SUM(SUM(sales)) OVER (
            PARTITION BY region, year
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ), 2
    ) AS running_total
FROM sales
GROUP BY region, year, month
ORDER BY region, year, month;


-- ──────────────────────────────────────────────────────────
-- 9. SEGMENT-WISE PERFORMANCE COMPARISON
-- ──────────────────────────────────────────────────────────
SELECT
    segment,
    COUNT(DISTINCT customer_id)      AS unique_customers,
    ROUND(SUM(sales), 2)             AS total_revenue,
    ROUND(AVG(sales), 2)             AS avg_order_value,
    ROUND(SUM(profit)/SUM(sales)*100, 2) AS profit_margin_pct
FROM sales
GROUP BY segment
ORDER BY total_revenue DESC;


-- ──────────────────────────────────────────────────────────
-- 10. YOY GROWTH (Self-Join via CTE)
-- ──────────────────────────────────────────────────────────
WITH yearly AS (
    SELECT year, ROUND(SUM(sales), 2) AS annual_revenue
    FROM sales
    GROUP BY year
)
SELECT
    a.year,
    a.annual_revenue,
    b.annual_revenue         AS prev_year_revenue,
    ROUND(
        (a.annual_revenue - b.annual_revenue) / b.annual_revenue * 100,
    2) AS yoy_growth_pct
FROM yearly a
LEFT JOIN yearly b ON a.year = b.year + 1
ORDER BY a.year;
