from __future__ import annotations

import json
import re
from datetime import datetime, date
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MASTER_DIR = BASE_DIR / "master"

JOB_ORDER_FILE = DATA_DIR / "job_order.xlsx"
JOB_ORDER_ITEMS_FILE = DATA_DIR / "job_order_items.xlsx"
DELIVERY_ORDER_FILE = DATA_DIR / "delivery_order.xlsx"
DELIVERY_ORDER_ITEMS_FILE = DATA_DIR / "delivery_order_items.xlsx"

CLIENT_MASTER_FILE = MASTER_DIR / "client_master.xlsx"
ITEM_MASTER_FILE = MASTER_DIR / "item_master.xlsx"


def today_date() -> str:
    return date.today().isoformat()


def now_timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def json_dumps_list(values: Iterable[str] | None) -> str:
    if values is None:
        return "[]"
    if isinstance(values, str):
        values = [values]
    return json.dumps(list(values), ensure_ascii=False)


def json_loads_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        pass
    return [str(value)]


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_table(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns or [])
    df = pd.read_excel(path, dtype=object)
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
    return df


def write_table(path: Path, df: pd.DataFrame) -> None:
    _ensure_parent(path)
    df.to_excel(path, index=False)


def append_rows(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    df = read_table(path, columns=columns)
    if rows:
        df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    write_table(path, df)


def update_rows(path: Path, df: pd.DataFrame) -> None:
    write_table(path, df)


def next_number(df: pd.DataFrame, column: str, prefix: str, year_two: str) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}{year_two}-(\d{{3}})$")
    max_seq = 0
    if column in df.columns:
        for value in df[column].dropna().astype(str):
            match = pattern.match(value.strip())
            if match:
                seq = int(match.group(1))
                max_seq = max(max_seq, seq)
    return f"{prefix}{year_two}-{max_seq + 1:03d}"


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df
