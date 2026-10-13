
-- Query 05: Revenue Harian

-- Pertanyaan Bisnis: Bagaimana tren revenue harian perusahaan?

-- Tabel: orders, order_items
-- Filter: Hanya order dengan status COMPLETE atau CLOSED


SELECT
    o.order_date,
    SUM(oi.order_item_subtotal) AS daily_revenue
FROM orders AS o
    JOIN order_items AS oi
        ON o.order_id = oi.order_item_order_id
WHERE o.order_status IN ('COMPLETE', 'CLOSED')
GROUP BY o.order_date
ORDER BY o.order_date;