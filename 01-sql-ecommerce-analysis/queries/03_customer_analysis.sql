-- Query 03: Customer Analysis - Top 10 Customer by Order Count

-- Pertanyaan Bisnis: Customer mana yang paling sering melakukan order?

-- Tabel: customers, orders, order_items
-- Filter: Hanya order dengan status COMPLETE atau CLOSED
-- Definisi: total_orders = jumlah order valid yang memiliki minimal 1 item
--           (order valid tanpa item tidak ikut karena JOIN ke order_items).

SELECT
    c.customer_id,
    CONCAT(c.customer_fname, ' ', c.customer_lname) AS full_name,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.order_item_subtotal)::numeric, 2) AS total_valid_revenue_usd
FROM customers AS c
    JOIN orders AS o
        ON c.customer_id = o.order_customer_id
    JOIN order_items AS oi
        ON o.order_id = oi.order_item_order_id
WHERE o.order_status IN ('COMPLETE', 'CLOSED')
GROUP BY c.customer_id, c.customer_fname, c.customer_lname
ORDER BY total_orders DESC, total_valid_revenue_usd DESC, c.customer_id
LIMIT 10;