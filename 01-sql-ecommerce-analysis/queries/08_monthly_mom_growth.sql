-- Query 08: Tren Bulanan, AOV, dan Pertumbuhan MoM

-- Pertanyaan Bisnis:
--   Bagaimana revenue, jumlah order, dan nilai rata-rata order (AOV)
--   bergerak dari bulan ke bulan?

-- Tabel: orders, order_items
-- Filter: Hanya order dengan status COMPLETE atau CLOSED
-- Catatan: Bulan pertama (2013-07) dan terakhir (2014-07) parsial.
--          Pertumbuhan MoM hanya dihitung jika bulan ini dan bulan
--          sebelumnya sama-sama penuh.
-- Definisi: total_orders = jumlah order valid yang memiliki minimal 1 item
--           (order valid tanpa item tidak ikut karena JOIN ke order_items).

WITH date_range AS (
    SELECT
        MIN(order_date)::date AS min_date,
        MAX(order_date)::date AS max_date
    FROM orders
),
monthly_metrics AS (
    SELECT
        DATE_TRUNC('month', o.order_date)::date AS order_month,
        COUNT(DISTINCT o.order_date::date) AS active_days,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.order_item_subtotal)::numeric AS valid_revenue_usd
    FROM orders AS o
        JOIN order_items AS oi
            ON o.order_id = oi.order_item_order_id
    WHERE o.order_status IN ('COMPLETE', 'CLOSED')
    GROUP BY DATE_TRUNC('month', o.order_date)::date
),
monthly_status AS (
    SELECT
        m.*,
        CASE
            WHEN m.order_month < d.min_date
              OR (m.order_month + INTERVAL '1 month' - INTERVAL '1 day')::date > d.max_date
            THEN 'PARTIAL'
            ELSE 'FULL'
        END AS month_status
    FROM monthly_metrics AS m
        CROSS JOIN date_range AS d
),
monthly_with_prev AS (
    SELECT
        *,
        LAG(valid_revenue_usd) OVER (ORDER BY order_month) AS prev_month_revenue_usd,
        LAG(month_status) OVER (ORDER BY order_month) AS prev_month_status
    FROM monthly_status
)
SELECT
    order_month,
    month_status,
    active_days,
    total_orders,
    ROUND(valid_revenue_usd, 2) AS valid_revenue_usd,
    ROUND(valid_revenue_usd / total_orders, 2) AS avg_order_value_usd,
    ROUND(valid_revenue_usd / active_days, 2) AS avg_daily_revenue_usd,
    ROUND(prev_month_revenue_usd, 2) AS prev_month_revenue_usd,
    CASE
        WHEN month_status = 'FULL' AND prev_month_status = 'FULL'
        THEN ROUND(
            (valid_revenue_usd - prev_month_revenue_usd)
            / NULLIF(prev_month_revenue_usd, 0) * 100,
            2
        )
    END AS mom_growth_pct
FROM monthly_with_prev
ORDER BY order_month;