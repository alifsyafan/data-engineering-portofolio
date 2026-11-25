-- Query 02: Top 10 Produk Terlaris (berdasarkan quantity)

-- Pertanyaan Bisnis:
--   Produk apa saja yang paling banyak terjual?

-- Tabel: products, order_items, orders
-- Filter: Hanya order dengan status COMPLETE atau CLOSED

SELECT p.product_id,
    p.product_name,
    SUM(oi.order_item_quantity) AS total_quantity,
    ROUND(SUM(oi.order_item_subtotal)::numeric, 2) AS total_revenue_usd
FROM products AS p
    JOIN order_items AS oi
        ON p.product_id = oi.order_item_product_id
    JOIN orders AS o
        ON oi.order_item_order_id = o.order_id
WHERE o.order_status IN ('COMPLETE', 'CLOSED')
GROUP BY p.product_id, p.product_name
ORDER BY total_quantity DESC, p.product_id
LIMIT 10;