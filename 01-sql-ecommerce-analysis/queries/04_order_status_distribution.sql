-- Query 04: Distribusi Order Status

-- Pertanyaan Bisnis: Bagaimana distribusi status order di seluruh sistem?

-- Tabel: orders

SELECT
    order_status,
    COUNT(*) AS total_order
FROM orders
GROUP BY order_status
ORDER BY total_order DESC;