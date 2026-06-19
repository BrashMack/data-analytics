import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


def read_events(path: Path) -> pd.DataFrame:
    root = ET.parse(path).getroot()
    rows = []
    for event in root.findall("event"):
        rows.append({child.tag: child.text for child in event})
    return pd.DataFrame(rows)


def extract_all(data_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "customers": pd.read_csv(data_dir / "customers.csv"),
        "orders": pd.read_json(data_dir / "orders.json"),
        "products": pd.read_excel(data_dir / "products.xlsx"),
        "events": read_events(data_dir / "events.xml"),
        "payments": pd.read_csv(data_dir / "payments.csv", sep="^"),
    }
