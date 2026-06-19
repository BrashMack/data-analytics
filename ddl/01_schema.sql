DROP SCHEMA IF EXISTS stg CASCADE;
DROP SCHEMA IF EXISTS dwh CASCADE;

CREATE SCHEMA stg;
CREATE SCHEMA dwh;

CREATE TABLE dwh.dim_customers (
    customer_sk BIGINT PRIMARY KEY,
    customer_id BIGINT UNIQUE,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    city TEXT,
    created_at DATE
);

CREATE TABLE dwh.dim_products (
    product_sk BIGINT PRIMARY KEY,
    product_id BIGINT UNIQUE,
    product_name TEXT,
    category TEXT,
    price NUMERIC(14, 2),
    currency TEXT,
    is_active BOOLEAN
);

CREATE TABLE dwh.fact_orders (
    order_id BIGINT PRIMARY KEY,
    customer_sk BIGINT NOT NULL REFERENCES dwh.dim_customers(customer_sk),
    product_sk BIGINT NOT NULL REFERENCES dwh.dim_products(product_sk),
    quantity INTEGER,
    unit_price NUMERIC(14, 2),
    currency TEXT,
    gross_amount NUMERIC(16, 2),
    gross_amount_rub NUMERIC(18, 2),
    order_timestamp TIMESTAMP,
    status TEXT
);

CREATE TABLE dwh.fact_payments (
    payment_id BIGINT PRIMARY KEY,
    order_id BIGINT REFERENCES dwh.fact_orders(order_id),
    raw_order_id BIGINT,
    payment_method TEXT,
    amount NUMERIC(16, 2),
    amount_rub NUMERIC(18, 2),
    currency TEXT,
    payment_timestamp TIMESTAMP
);

CREATE TABLE dwh.fact_events (
    event_id BIGINT PRIMARY KEY,
    customer_sk BIGINT NOT NULL REFERENCES dwh.dim_customers(customer_sk),
    product_sk BIGINT NOT NULL REFERENCES dwh.dim_products(product_sk),
    event_type TEXT,
    event_timestamp TIMESTAMP
);

CREATE TABLE dwh.etl_bad_records (
    bad_record_id BIGSERIAL PRIMARY KEY,
    source_table TEXT NOT NULL,
    source_record_id TEXT,
    issue TEXT NOT NULL,
    raw_payload TEXT,
    logged_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE dwh.etl_run_summary (
    summary_id BIGSERIAL PRIMARY KEY,
    layer TEXT NOT NULL,
    table_name TEXT NOT NULL,
    rows_count BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fact_orders_customer ON dwh.fact_orders(customer_sk);
CREATE INDEX idx_fact_orders_product ON dwh.fact_orders(product_sk);
CREATE INDEX idx_fact_orders_status_month ON dwh.fact_orders(status, order_timestamp);
CREATE INDEX idx_fact_payments_order ON dwh.fact_payments(order_id);
CREATE INDEX idx_fact_events_customer_time ON dwh.fact_events(customer_sk, event_timestamp);
CREATE INDEX idx_fact_events_product ON dwh.fact_events(product_sk);
