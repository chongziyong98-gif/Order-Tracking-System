from __future__ import annotations

from typing import Any

import pandas as pd

from db import (
    DELIVERY_ORDER_FILE,
    DELIVERY_ORDER_ITEMS_FILE,
    json_loads_list,
    read_table,
)
from services.order_service import DELIVERY_ORDER_COLUMNS, DELIVERY_ORDER_ITEM_COLUMNS


def get_delivery_order(do_client_number: str) -> dict[str, Any]:
    delivery_df = read_table(DELIVERY_ORDER_FILE, columns=DELIVERY_ORDER_COLUMNS)
    if delivery_df.empty:
        raise ValueError("No delivery orders found")
    mask = delivery_df["do_client_number"].astype(str) == str(do_client_number)
    if not mask.any():
        raise ValueError(f"DO number not found: {do_client_number}")
    record = delivery_df.loc[mask].iloc[0].to_dict()

    items_df = read_table(
        DELIVERY_ORDER_ITEMS_FILE, columns=DELIVERY_ORDER_ITEM_COLUMNS
    )
    items = items_df[items_df["do_client_number"].astype(str) == str(do_client_number)]

    def _clean(value: Any) -> Any:
        if pd.isna(value):
            return ""
        return value

    items_list = []
    for row in items.to_dict(orient="records"):
        items_list.append({k: _clean(v) for k, v in row.items()})

    return {
        "do_client_number": _clean(record.get("do_client_number", "")),
        "client_code": _clean(record.get("client_code", "")),
        "client_name": _clean(record.get("client_name", "")),
        "delivery_address": _clean(record.get("delivery_address", "")),
        "client_pic": _clean(record.get("client_pic", "")),
        "client_contact": _clean(record.get("client_contact", "")),
        "client_po_list": json_loads_list(record.get("client_po_list", "")),
        "remark": _clean(record.get("remark", "")),
        "items": items_list,
    }
