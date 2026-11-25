-- Query 04: Distribusi Order Status

-- Pertanyaan Bisnis: Bagaimana distribusi status order di seluruh sistem?

-- Tabel: orders

SELECT
    o.order_status,
    COUNT(o.order_id) AS total_order,
    ROUND(
        100.0 * COUNT(o.order_id) / SUM(COUNT(o.order_id)) OVER (),
        2
    ) AS pct_of_orders
FROM orders AS o
GROUP BY o.order_status
ORDER BY total_order DESC;