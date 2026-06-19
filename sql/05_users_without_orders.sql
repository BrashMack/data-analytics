SELECT
    c.customer_id,
    c.full_name,
    c.email,
    c.city,
    c.created_at
FROM dwh.dim_customers c
LEFT JOIN dwh.fact_orders o ON o.customer_sk = c.customer_sk
WHERE c.customer_id IS NOT NULL
  AND o.order_id IS NULL
ORDER BY c.customer_id;
