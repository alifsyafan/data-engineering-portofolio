-- Query 03: Customer Analysis - Top 10 Customer by Order Count

-- Pertanyaan Bisnis: Customer mana yang paling sering melakukan order?

-- Tabel: customers, orders
-- Filter: Hanya order dengan status COMPLETE atau CLOSED

SELECT
    c.customer_id,
    c.customer_fname || ' ' || c.customer_lname AS customer_name,
    COUNT(o.order_id) AS total_orders
FROM customers AS c
    JOIN orders AS o
        ON c.customer_id = o.order_customer_id
WHERE o.order_status IN ('COMPLETE', 'CLOSED')
GROUP BY c.customer_id, c.customer_fname, c.customer_lname
ORDER BY total_orders DESC
LIMIT 10;