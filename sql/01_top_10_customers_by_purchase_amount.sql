SELECT
    c.customer_id,
    c.full_name,
    c.email,
    ROUND(SUM(o.gross_amount_rub), 2) AS total_purchase_amount_rub,
    COUNT(*) AS completed_orders
FROM dwh.fact_orders o
JOIN dwh.dim_customers c ON c.customer_sk = o.customer_sk
WHERE o.status = 'completed'
  AND c.customer_id IS NOT NULL
GROUP BY c.customer_id, c.full_name, c.email
ORDER BY total_purchase_amount_rub DESC
LIMIT 10;
