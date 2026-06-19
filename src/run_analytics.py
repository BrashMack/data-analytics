import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.config import REPORTS_DIR, SQL_DIR
from src.db import get_engine


def main():
    REPORTS_DIR.mkdir(exist_ok=True)
    engine = get_engine()
    with engine.connect() as conn:
        for path in sorted(SQL_DIR.glob("*.sql")):
            query = path.read_text(encoding="utf-8")
            df = pd.read_sql_query(query, conn)
            output_path = REPORTS_DIR / f"{path.stem}.csv"
            df.to_csv(output_path, index=False)
            print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
