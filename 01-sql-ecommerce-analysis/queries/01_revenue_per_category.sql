-- Portfolio: E-Commerce SQL Analysis
-- Query 01: Revenue per Category

-- Pertanyaan Bisnis: Kategori produk mana yang menghasilkan revenue terbesar?
--
-- Tabel yang digunakan: categories, products, order_items, orders
--
-- Filter: Hanya order dengan status COMPLETE atau CLOSED

SELECT
    c.category_name,
    SUM(oi.order_item_subtotal) AS revenue
FROM categories AS c
    JOIN products AS p
        ON c.category_id = p.product_category_id
    JOIN order_items AS oi
        ON p.product_id = oi.order_item_product_id
    JOIN orders AS o
        ON oi.order_item_order_id = o.order_id
WHERE o.order_status IN ('COMPLETE', 'CLOSED')
GROUP BY c.category_name
ORDER BY revenue DESC;