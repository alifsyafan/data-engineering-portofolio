-- Query 06: Revenue Bulanan

-- Pertanyaan Bisnis: Bagaimana pertumbuhan revenue dari bulan ke bulan?

-- Tabel: orders, order_items
-- Filter: Hanya order dengan status COMPLETE atau CLOSED


SELECT
    to_char(o.order_date, 'YYYY-MM') AS month,
    SUM(oi.order_item_subtotal) AS monthly_revenue
FROM orders AS o
    JOIN order_items AS oi
        ON o.order_id = oi.order_item_order_id
WHERE o.order_status IN ('COMPLETE', 'CLOSED')
GROUP BY to_char(o.order_date, 'YYYY-MM')
ORDER BY month;