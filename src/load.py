from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db import execute_sql_file


def _db_ready(df: pd.DataFrame) -> pd.DataFrame:
    return df.astype(object).where(pd.notna(df), None)


def load_dataframe(engine, df: pd.DataFrame, table: str, schema: str, if_exists: str = "append"):
    _db_ready(df).to_sql(
        name=table,
        con=engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
        method="multi",
        chunksize=1000,
    )


def load_all(engine, raw: dict[str, pd.DataFrame], dwh: dict[str, pd.DataFrame], bad_records: pd.DataFrame, ddl_path: Path):
    execute_sql_file(engine, ddl_path)

    for table, df in raw.items():
        load_dataframe(engine, df, f"raw_{table}", "stg", if_exists="replace")

    for table in ["dim_customers", "dim_products", "fact_orders", "fact_payments", "fact_events"]:
        load_dataframe(engine, dwh[table], table, "dwh")

    if not bad_records.empty:
        load_dataframe(engine, bad_records, "etl_bad_records", "dwh")

    summary_rows = []
    for name, df in raw.items():
        summary_rows.append({"layer": "raw", "table_name": f"raw_{name}", "rows_count": len(df)})
    for name, df in dwh.items():
        summary_rows.append({"layer": "dwh", "table_name": name, "rows_count": len(df)})
    summary_rows.append({"layer": "quality", "table_name": "etl_bad_records", "rows_count": len(bad_records)})

    load_dataframe(engine, pd.DataFrame(summary_rows), "etl_run_summary", "dwh")

    with engine.begin() as conn:
        conn.execute(text("ANALYZE dwh.dim_customers"))
        conn.execute(text("ANALYZE dwh.dim_products"))
        conn.execute(text("ANALYZE dwh.fact_orders"))
        conn.execute(text("ANALYZE dwh.fact_payments"))
        conn.execute(text("ANALYZE dwh.fact_events"))
