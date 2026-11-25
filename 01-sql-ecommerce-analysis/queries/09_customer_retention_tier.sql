-- Query 09: Segmentasi Retensi Pelanggan

-- Pertanyaan Bisnis:
--   Berapa proporsi pelanggan sekali beli, berulang, dan setia,
--   dan seberapa besar kontribusi masing-masing terhadap revenue?

-- Tabel: orders, order_items
-- Filter: Hanya order dengan status COMPLETE atau CLOSED
-- Catatan: Tingkat ditentukan dari jumlah order VALID dalam periode data
--          (±1 tahun). Pelanggan tanpa order valid tidak ikut dihitung.
--          Pelanggan yang baru bergabung di akhir periode punya waktu
--          lebih sedikit untuk membeli ulang, sehingga proporsi
--          "One-time Buyer" bisa terlihat lebih tinggi dari sebenarnya.
-- Definisi: order_count = jumlah order valid yang memiliki minimal 1 item.
--           Pelanggan yang seluruh order validnya tanpa item tidak ikut dihitung.

WITH customer_orders AS (
    SELECT
        o.order_customer_id,
        COUNT(DISTINCT o.order_id) AS order_count,
        SUM(oi.order_item_subtotal)::numeric AS customer_revenue_usd
    FROM orders AS o
        JOIN order_items AS oi
            ON o.order_id = oi.order_item_order_id
    WHERE o.order_status IN ('COMPLETE', 'CLOSED')
    GROUP BY o.order_customer_id
),
customer_segments AS (
    SELECT
        order_customer_id,
        order_count,
        customer_revenue_usd,
        CASE
            WHEN order_count = 1 THEN '1. One-time Buyer (1x)'
            WHEN order_count BETWEEN 2 AND 3 THEN '2. Repeat Buyer (2-3x)'
            ELSE '3. Loyal Buyer (4x+)'
        END AS retention_tier
    FROM customer_orders
)
SELECT
    retention_tier,
    COUNT(*) AS total_customers,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_customers,
    SUM(order_count) AS total_orders,
    ROUND(SUM(customer_revenue_usd), 2) AS total_revenue_usd,
    ROUND(SUM(customer_revenue_usd) * 100 / SUM(SUM(customer_revenue_usd)) OVER (), 2) AS pct_revenue,
    ROUND(SUM(customer_revenue_usd) / COUNT(*), 2) AS avg_revenue_per_customer_usd
FROM customer_segments
GROUP BY retention_tier
ORDER BY retention_tier;