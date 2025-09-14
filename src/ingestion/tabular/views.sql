CREATE MATERIALIZED VIEW IF NOT EXISTS order_facts AS
SELECT
    o.order_id,
    o.order_date,
    o.quantity,
    o.order_status,
    c.customer_id,
    c.email AS customer_email,
    c.name AS customer_name,
    p.product_id,
    p.sku AS product_sku,
    p.name AS product_name,
    p.category,
    p.price
FROM orders o
JOIN customers c ON c.customer_id = o.customer_id
JOIN products p ON p.product_id = o.product_id;

-- REFRESH MATERIALIZED VIEW CONCURRENTLY order_facts;


