import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config import DATA_DIR, DDL_DIR
from src.db import get_engine
from src.extract import extract_all
from src.load import load_all
from src.transform import transform_all


def main():
    raw = extract_all(DATA_DIR)
    _, dwh, bad_records = transform_all(raw)
    engine = get_engine()
    load_all(engine, raw, dwh, bad_records, DDL_DIR / "01_schema.sql")
    print(f"Loaded DWH tables. Bad records logged: {len(bad_records)}")


if __name__ == "__main__":
    main()
