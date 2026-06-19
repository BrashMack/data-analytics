import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data" / "raw"
REPORTS_DIR = BASE_DIR / "reports"
DDL_DIR = BASE_DIR / "ddl"
SQL_DIR = BASE_DIR / "sql"

CURRENCY_RATES_RUB = {
    "RUB": 1.0,
    "USD": 90.0,
    "EUR": 100.0,
}


def database_url():
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "analytics"),
    )
