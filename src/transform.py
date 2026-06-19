import json

import pandas as pd

from src.config import CURRENCY_RATES_RUB

TEXT_COLUMNS = {
    "customers": ["full_name", "email", "phone", "city"],
    "products": ["product_name", "category", "currency"],
    "orders": ["currency", "status"],
    "payments": ["payment_method", "currency"],
    "events": ["event_type"],
}


def _payload(row: pd.Series) -> str:
    data = row.astype(object).where(pd.notna(row), None).to_dict()
    return json.dumps(data, ensure_ascii=False, default=str)


def _log(logs: list[dict], source: str, record_id, issue: str, row: pd.Series):
    logs.append(
        {
            "source_table": source,
            "source_record_id": None if pd.isna(record_id) else str(record_id),
            "issue": issue,
            "raw_payload": _payload(row),
        }
    )


def _strip_text(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.copy()
    for col in TEXT_COLUMNS.get(source, []):
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip()
            df[col] = df[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    return df


def _deduplicate(df: pd.DataFrame, source: str, key: str, logs: list[dict]) -> pd.DataFrame:
    invalid_key = df[key].isna()
    for _, row in df[invalid_key].iterrows():
        _log(logs, source, row.get(key), f"invalid_{key}", row)

    df = df[~invalid_key].copy()
    duplicates = df.duplicated(key, keep="first")
    for _, row in df[duplicates].iterrows():
        _log(logs, source, row.get(key), f"duplicate_{key}", row)

    return df[~duplicates].copy()


def _to_nullable_int(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def _amount_rub(amount: pd.Series, currency: pd.Series) -> pd.Series:
    return amount * currency.map(CURRENCY_RATES_RUB)


def clean_customers(df: pd.DataFrame, logs: list[dict]) -> pd.DataFrame:
    source = "customers"
    df = _strip_text(df, source)
    df["customer_id"] = _to_nullable_int(df["customer_id"])
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", format="mixed").dt.date

    for _, row in df[df["created_at"].isna()].iterrows():
        _log(logs, source, row.get("customer_id"), "invalid_created_at", row)

    df = df.sort_values(["customer_id", "created_at"], ascending=[True, False], na_position="last")
    df = _deduplicate(df, source, "customer_id", logs)
    return df[["customer_id", "full_name", "email", "phone", "city", "created_at"]]


def clean_products(df: pd.DataFrame, logs: list[dict]) -> pd.DataFrame:
    source = "products"
    df = _strip_text(df, source)
    df["product_id"] = _to_nullable_int(df["product_id"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    for _, row in df[df["price"].isna()].iterrows():
        _log(logs, source, row.get("product_id"), "invalid_price", row)

    df = df.sort_values(["product_id"], ascending=True, na_position="last")
    df = _deduplicate(df, source, "product_id", logs)
    return df[["product_id", "product_name", "category", "price", "currency", "is_active"]]


def clean_orders(df: pd.DataFrame, logs: list[dict]) -> pd.DataFrame:
    source = "orders"
    df = _strip_text(df, source)
    df["order_id"] = _to_nullable_int(df["order_id"])
    df["customer_id"] = _to_nullable_int(df["customer_id"])
    df["product_id"] = _to_nullable_int(df["product_id"])
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["order_timestamp"] = pd.to_datetime(df["order_timestamp"], errors="coerce", format="mixed")

    for _, row in df[df["order_timestamp"].isna()].iterrows():
        _log(logs, source, row.get("order_id"), "invalid_order_timestamp", row)
    for _, row in df[df["customer_id"].isna()].iterrows():
        _log(logs, source, row.get("order_id"), "missing_customer_id", row)
    for _, row in df[df["quantity"].isna() | (df["quantity"] <= 0)].iterrows():
        _log(logs, source, row.get("order_id"), "invalid_quantity", row)
    for _, row in df[df["unit_price"].isna() | (df["unit_price"] < 0)].iterrows():
        _log(logs, source, row.get("order_id"), "invalid_unit_price", row)
    for _, row in df[~df["currency"].isin(CURRENCY_RATES_RUB)].iterrows():
        _log(logs, source, row.get("order_id"), "unknown_currency", row)

    df = df.sort_values(["order_id", "order_timestamp"], ascending=[True, False], na_position="last")
    df = _deduplicate(df, source, "order_id", logs)
    df["gross_amount"] = df["quantity"].astype("float") * df["unit_price"]
    df["gross_amount_rub"] = _amount_rub(df["gross_amount"], df["currency"])
    return df[
        [
            "order_id",
            "customer_id",
            "product_id",
            "quantity",
            "unit_price",
            "currency",
            "gross_amount",
            "gross_amount_rub",
            "order_timestamp",
            "status",
        ]
    ]


def clean_payments(df: pd.DataFrame, logs: list[dict]) -> pd.DataFrame:
    source = "payments"
    df = _strip_text(df, source)
    df["payment_id"] = _to_nullable_int(df["payment_id"])
    df["order_id"] = _to_nullable_int(df["order_id"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["payment_timestamp"] = pd.to_datetime(df["payment_timestamp"], errors="coerce", format="mixed")

    for _, row in df[df["amount"].isna() | (df["amount"] < 0)].iterrows():
        _log(logs, source, row.get("payment_id"), "invalid_amount", row)
    for _, row in df[df["payment_timestamp"].isna()].iterrows():
        _log(logs, source, row.get("payment_id"), "invalid_payment_timestamp", row)
    for _, row in df[df["payment_method"].isna()].iterrows():
        _log(logs, source, row.get("payment_id"), "missing_payment_method", row)
    for _, row in df[~df["currency"].isin(CURRENCY_RATES_RUB)].iterrows():
        _log(logs, source, row.get("payment_id"), "unknown_currency", row)

    df = df.sort_values(["payment_id", "payment_timestamp"], ascending=[True, False], na_position="last")
    df = _deduplicate(df, source, "payment_id", logs)
    df["amount_rub"] = _amount_rub(df["amount"], df["currency"])
    return df[["payment_id", "order_id", "payment_method", "amount", "amount_rub", "currency", "payment_timestamp"]]


def clean_events(df: pd.DataFrame, logs: list[dict]) -> pd.DataFrame:
    source = "events"
    df = _strip_text(df, source)
    df["event_id"] = _to_nullable_int(df["event_id"])
    df["customer_id"] = _to_nullable_int(df["customer_id"])
    df["product_id"] = _to_nullable_int(df["product_id"])
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", format="mixed")

    for _, row in df[df["event_timestamp"].isna()].iterrows():
        _log(logs, source, row.get("event_id"), "invalid_event_timestamp", row)
    for _, row in df[df["customer_id"].isna()].iterrows():
        _log(logs, source, row.get("event_id"), "missing_customer_id", row)

    df = df.sort_values(["event_id", "event_timestamp"], ascending=[True, False], na_position="last")
    df = _deduplicate(df, source, "event_id", logs)
    return df[["event_id", "customer_id", "product_id", "event_type", "event_timestamp"]]


def build_dwh(clean: dict[str, pd.DataFrame], logs: list[dict]) -> dict[str, pd.DataFrame]:
    customers = clean["customers"].copy()
    products = clean["products"].copy()
    orders = clean["orders"].copy()
    payments = clean["payments"].copy()
    events = clean["events"].copy()

    dim_customers = customers.reset_index(drop=True).copy()
    dim_customers.insert(0, "customer_sk", range(1, len(dim_customers) + 1))
    unknown_customer = {
        "customer_sk": 0,
        "customer_id": None,
        "full_name": "Unknown customer",
        "email": None,
        "phone": None,
        "city": None,
        "created_at": None,
    }
    dim_customers = pd.DataFrame(
        [unknown_customer] + dim_customers.to_dict("records"),
        columns=dim_customers.columns,
    )

    dim_products = products.reset_index(drop=True).copy()
    dim_products.insert(0, "product_sk", range(1, len(dim_products) + 1))
    unknown_product = {
        "product_sk": 0,
        "product_id": None,
        "product_name": "Unknown product",
        "category": None,
        "price": None,
        "currency": None,
        "is_active": None,
    }
    dim_products = pd.DataFrame(
        [unknown_product] + dim_products.to_dict("records"),
        columns=dim_products.columns,
    )

    customer_map = dim_customers.dropna(subset=["customer_id"]).set_index("customer_id")["customer_sk"].to_dict()
    product_map = dim_products.dropna(subset=["product_id"]).set_index("product_id")["product_sk"].to_dict()
    valid_orders = set(orders["order_id"].dropna().astype(int))

    for _, row in orders[orders["customer_id"].notna() & ~orders["customer_id"].isin(customer_map)].iterrows():
        _log(logs, "orders", row.get("order_id"), "customer_not_found", row)
    for _, row in orders[orders["product_id"].notna() & ~orders["product_id"].isin(product_map)].iterrows():
        _log(logs, "orders", row.get("order_id"), "product_not_found", row)
    for _, row in payments[payments["order_id"].notna() & ~payments["order_id"].isin(valid_orders)].iterrows():
        _log(logs, "payments", row.get("payment_id"), "order_not_found", row)
    for _, row in events[events["customer_id"].notna() & ~events["customer_id"].isin(customer_map)].iterrows():
        _log(logs, "events", row.get("event_id"), "customer_not_found", row)
    for _, row in events[events["product_id"].notna() & ~events["product_id"].isin(product_map)].iterrows():
        _log(logs, "events", row.get("event_id"), "product_not_found", row)

    fact_orders = orders.copy()
    fact_orders["customer_sk"] = fact_orders["customer_id"].map(customer_map).fillna(0).astype(int)
    fact_orders["product_sk"] = fact_orders["product_id"].map(product_map).fillna(0).astype(int)
    fact_orders = fact_orders[
        [
            "order_id",
            "customer_sk",
            "product_sk",
            "quantity",
            "unit_price",
            "currency",
            "gross_amount",
            "gross_amount_rub",
            "order_timestamp",
            "status",
        ]
    ]

    fact_payments = payments.copy()
    fact_payments["raw_order_id"] = fact_payments["order_id"]
    fact_payments.loc[~fact_payments["order_id"].isin(valid_orders), "order_id"] = pd.NA
    fact_payments = fact_payments[
        [
            "payment_id",
            "order_id",
            "raw_order_id",
            "payment_method",
            "amount",
            "amount_rub",
            "currency",
            "payment_timestamp",
        ]
    ]

    fact_events = events.copy()
    fact_events["customer_sk"] = fact_events["customer_id"].map(customer_map).fillna(0).astype(int)
    fact_events["product_sk"] = fact_events["product_id"].map(product_map).fillna(0).astype(int)
    fact_events = fact_events[["event_id", "customer_sk", "product_sk", "event_type", "event_timestamp"]]

    return {
        "dim_customers": dim_customers,
        "dim_products": dim_products,
        "fact_orders": fact_orders,
        "fact_payments": fact_payments,
        "fact_events": fact_events,
    }


def transform_all(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame]:
    logs: list[dict] = []
    clean = {
        "customers": clean_customers(raw["customers"], logs),
        "products": clean_products(raw["products"], logs),
        "orders": clean_orders(raw["orders"], logs),
        "payments": clean_payments(raw["payments"], logs),
        "events": clean_events(raw["events"], logs),
    }
    dwh = build_dwh(clean, logs)
    bad_records = pd.DataFrame(logs, columns=["source_table", "source_record_id", "issue", "raw_payload"])
    return clean, dwh, bad_records
