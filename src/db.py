from pathlib import Path

from sqlalchemy import create_engine

from src.config import database_url


def get_engine():
    return create_engine(database_url(), pool_pre_ping=True)


def execute_sql_file(engine, path: Path):
    sql = path.read_text(encoding="utf-8")
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cursor:
            cursor.execute(sql)
        raw.commit()
    finally:
        raw.close()
