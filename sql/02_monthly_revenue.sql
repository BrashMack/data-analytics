SELECT
    DATE_TRUNC('month', o.order_timestamp)::date AS month,
    ROUND(SUM(o.gross_amount_rub), 2) AS revenue_rub,
    COUNT(*) AS completed_orders
FROM dwh.fact_orders o
WHERE o.status = 'completed'
  AND o.order_timestamp IS NOT NULL
GROUP BY 1
ORDER BY 1;
