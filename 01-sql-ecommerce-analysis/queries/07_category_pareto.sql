-- Query 07: Kontribusi Kategori & Kumulatif Pareto

-- Pertanyaan Bisnis:
--   Kategori mana yang menjadi inti revenue, dan berapa banyak kategori
--   yang dibutuhkan untuk mencapai sekitar 80% revenue?

-- Tabel: orders, order_items, products, categories
-- Filter: Hanya order dengan status COMPLETE atau CLOSED
-- Catatan: total_orders per kategori tidak boleh dijumlahkan antar kategori,
--          karena satu order bisa memuat produk dari beberapa kategori.

WITH category_sales AS (
    SELECT
        c.category_id,
        c.category_name,
        COUNT(DISTINCT o.order_id) AS total_orders,
        SUM(oi.order_item_subtotal)::numeric AS valid_revenue_usd
    FROM orders AS o
        JOIN order_items AS oi
            ON o.order_id = oi.order_item_order_id
        JOIN products AS p
            ON oi.order_item_product_id = p.product_id
        JOIN categories AS c
            ON p.product_category_id = c.category_id
    WHERE o.order_status IN ('COMPLETE', 'CLOSED')
    GROUP BY c.category_id, c.category_name
),
category_pareto AS (
    SELECT
        category_id,
        category_name,
        total_orders,
        valid_revenue_usd,
        valid_revenue_usd / SUM(valid_revenue_usd) OVER () * 100 AS pct_contribution,
        SUM(valid_revenue_usd) OVER (
            ORDER BY valid_revenue_usd DESC, category_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / SUM(valid_revenue_usd) OVER () * 100 AS cumulative_pct
    FROM category_sales
)
SELECT
    ROW_NUMBER() OVER (ORDER BY valid_revenue_usd DESC, category_id) AS revenue_rank,
    category_id,
    category_name,
    total_orders,
    ROUND(valid_revenue_usd, 2) AS valid_revenue_usd,
    ROUND(pct_contribution, 2) AS pct_contribution,
    ROUND(cumulative_pct, 2) AS cumulative_pct,
    CASE
        WHEN cumulative_pct - pct_contribution < 80 THEN 'A: kontributor utama (s.d. 80%)'
        ELSE 'B: kontributor lainnya'
    END AS pareto_group
FROM category_pareto
ORDER BY revenue_rank;