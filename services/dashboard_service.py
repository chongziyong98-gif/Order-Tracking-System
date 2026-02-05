from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from db import JOB_ORDER_FILE, json_loads_list, read_table
from services.order_service import JOB_ORDER_COLUMNS


def list_orders(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    month = filters.get("month")
    year = filters.get("year")
    status = filters.get("status")

    if not month or not year:
        today = date.today()
        month = month or today.month
        year = year or today.year

    job_order_df = read_table(JOB_ORDER_FILE, columns=JOB_ORDER_COLUMNS)
    if job_order_df.empty:
        return []

    def _match_month(value: Any) -> bool:
        try:
            parts = str(value).split("-")
            return int(parts[0]) == int(year) and int(parts[1]) == int(month)
        except (ValueError, IndexError):
            return False

    filtered = job_order_df[job_order_df["issue_date"].apply(_match_month)]
    if status:
        filtered = filtered[filtered["status"].astype(str) == str(status)]

    results: list[dict[str, Any]] = []
    def _clean(value: Any) -> str:
        if pd.isna(value):
            return ""
        return str(value)

    for _, row in filtered.iterrows():
        po_list = json_loads_list(row.get("client_po_list", ""))
        supplier_list = json_loads_list(row.get("do_to_supplier_list", ""))
        results.append(
            {
                "issue_date": _clean(row.get("issue_date", "")),
                "jo_number": _clean(row.get("jo_number", "")),
                "client_po_list": ", ".join(po_list),
                "client_name": _clean(row.get("client_name", "")),
                "required_date": _clean(row.get("required_date", "")),
                "do_to_supplier_first": supplier_list[0] if supplier_list else "",
                "do_client_number": _clean(row.get("do_to_client_number", "")),
                "status": _clean(row.get("status", "")),
                "complete_date": _clean(row.get("complete_date", "")),
            }
        )
    return results
