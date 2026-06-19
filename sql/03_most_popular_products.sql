SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(o.quantity) AS sold_units,
    COUNT(*) AS completed_orders,
    ROUND(SUM(o.gross_amount_rub), 2) AS revenue_rub
FROM dwh.fact_orders o
JOIN dwh.dim_products p ON p.product_sk = o.product_sk
WHERE o.status = 'completed'
  AND p.product_id IS NOT NULL
GROUP BY p.product_id, p.product_name, p.category
ORDER BY sold_units DESC, revenue_rub DESC
LIMIT 10;
