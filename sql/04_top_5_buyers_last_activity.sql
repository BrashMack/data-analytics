WITH purchases AS (
    SELECT
        customer_sk,
        COUNT(*) AS purchases_count,
        SUM(gross_amount_rub) AS total_purchase_amount_rub
    FROM dwh.fact_orders
    WHERE status = 'completed'
    GROUP BY customer_sk
),
last_activity AS (
    SELECT
        customer_sk,
        MAX(event_timestamp)::date AS last_activity_date
    FROM dwh.fact_events
    WHERE event_timestamp IS NOT NULL
    GROUP BY customer_sk
)
SELECT
    c.customer_id,
    c.full_name,
    p.purchases_count,
    ROUND(p.total_purchase_amount_rub, 2) AS total_purchase_amount_rub,
    la.last_activity_date
FROM purchases p
JOIN dwh.dim_customers c ON c.customer_sk = p.customer_sk
LEFT JOIN last_activity la ON la.customer_sk = p.customer_sk
WHERE c.customer_id IS NOT NULL
ORDER BY p.purchases_count DESC, p.total_purchase_amount_rub DESC
LIMIT 5;
