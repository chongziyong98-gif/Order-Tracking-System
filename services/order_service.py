from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from db import (
    CLIENT_MASTER_FILE,
    ITEM_MASTER_FILE,
    JOB_ORDER_FILE,
    JOB_ORDER_ITEMS_FILE,
    DELIVERY_ORDER_FILE,
    DELIVERY_ORDER_ITEMS_FILE,
    json_dumps_list,
    json_loads_list,
    next_number,
    now_timestamp,
    read_table,
    update_rows,
    append_rows,
    today_date,
    normalize_columns,
)


JOB_ORDER_COLUMNS = [
    "id",
    "jo_number",
    "issue_date",
    "client_po_list",
    "client_code",
    "client_name",
    "required_date",
    "local_export",
    "remark",
    "do_to_supplier_list",
    "do_to_client_number",
    "status",
    "complete_date",
    "created_at",
    "updated_at",
]

JOB_ORDER_ITEM_COLUMNS = [
    "id",
    "jo_number",
    "item_code",
    "item_description",
    "width",
    "length",
    "qty",
    "created_at",
    "updated_at",
]

DELIVERY_ORDER_COLUMNS = [
    "id",
    "do_client_number",
    "issue_date",
    "jo_number",
    "client_code",
    "client_name",
    "delivery_address",
    "client_pic",
    "client_contact",
    "client_po_list",
    "remark",
    "status",
    "complete_date",
    "created_at",
    "updated_at",
]

DELIVERY_ORDER_ITEM_COLUMNS = [
    "id",
    "do_client_number",
    "item_code",
    "item_description",
    "width",
    "length",
    "qty",
    "created_at",
    "updated_at",
]


def _require(value: Any, field: str) -> None:
    if value in (None, "", []):
        raise ValueError(f"Missing required field: {field}")


def _load_client_snapshot(client_code: str) -> dict[str, str]:
    df = read_table(CLIENT_MASTER_FILE)
    if df.empty:
        raise ValueError("client_master.xlsx is empty or missing")
    df = normalize_columns(df)
    code_col = "client_code" if "client_code" in df.columns else "code"
    if code_col not in df.columns:
        raise ValueError("client_master.xlsx missing client_code column")
    row = df[df[code_col].astype(str) == str(client_code)]
    if row.empty:
        raise ValueError(f"Client code not found in masterlist: {client_code}")
    record = row.iloc[0].to_dict()
    return {
        "client_name": str(record.get("client_name", "")),
        "delivery_address": str(record.get("delivery_address", "")),
        "client_pic": str(record.get("client_pic", "")),
        "client_contact": str(record.get("client_contact", "")),
    }


def _load_item_description(item_code: str) -> str:
    df = read_table(ITEM_MASTER_FILE)
    if df.empty:
        return ""
    df = normalize_columns(df)
    code_col = "item_code" if "item_code" in df.columns else "code"
    if code_col not in df.columns:
        return ""
    row = df[df[code_col].astype(str) == str(item_code)]
    if row.empty:
        return ""
    record = row.iloc[0].to_dict()
    return str(record.get("item_description", record.get("description", "")))


def create_order_draft(payload: dict[str, Any]) -> dict[str, Any]:
    _require(payload.get("client_code"), "client_code")
    _require(payload.get("items"), "items")
    _require(payload.get("required_date"), "required_date")
    _require(payload.get("local_export"), "local_export")

    client_code = str(payload["client_code"])
    client_snapshot = _load_client_snapshot(client_code)
    client_name = str(payload.get("client_name") or client_snapshot["client_name"])

    items_input = payload["items"]
    if not isinstance(items_input, list) or not items_input:
        raise ValueError("items must be a non-empty list")

    job_order_df = read_table(JOB_ORDER_FILE, columns=JOB_ORDER_COLUMNS)
    year_two = f"{date.today().year % 100:02d}"
    jo_number = next_number(job_order_df, "jo_number", "JO", year_two)
    now = now_timestamp()

    client_po_list = payload.get("client_po_list") or []
    do_to_supplier_list = payload.get("do_to_supplier_list") or []

    order_record = {
        "id": f"jo-{jo_number}",
        "jo_number": jo_number,
        "issue_date": today_date(),
        "client_po_list": json_dumps_list(client_po_list),
        "client_code": client_code,
        "client_name": client_name,
        "required_date": payload["required_date"],
        "local_export": payload["local_export"],
        "remark": payload.get("remark", ""),
        "do_to_supplier_list": json_dumps_list(do_to_supplier_list),
        "do_to_client_number": "",
        "status": "Preparing",
        "complete_date": "",
        "created_at": now,
        "updated_at": now,
    }

    item_records: list[dict[str, Any]] = []
    for idx, item in enumerate(items_input, start=1):
        _require(item.get("item_code"), f"items[{idx}].item_code")
        _require(item.get("qty"), f"items[{idx}].qty")
        item_code = str(item["item_code"])
        item_description = str(
            item.get("item_description") or _load_item_description(item_code)
        )
        item_records.append(
            {
                "id": f"jo-{jo_number}-item-{idx}",
                "jo_number": jo_number,
                "item_code": item_code,
                "item_description": item_description,
                "width": item.get("width", ""),
                "length": item.get("length", ""),
                "qty": item["qty"],
                "created_at": now,
                "updated_at": now,
            }
        )

    append_rows(JOB_ORDER_FILE, [order_record], columns=JOB_ORDER_COLUMNS)
    append_rows(JOB_ORDER_ITEMS_FILE, item_records, columns=JOB_ORDER_ITEM_COLUMNS)

    def _clean(value: Any) -> Any:
        if pd.isna(value):
            return ""
        return value

    cleaned_items = [{k: _clean(v) for k, v in item.items()} for item in item_records]

    return {
        "jo_number": jo_number,
        "status": "Preparing",
        "issue_date": _clean(order_record["issue_date"]),
        "client_po_list": json_loads_list(order_record["client_po_list"]),
        "do_to_supplier_list": json_loads_list(order_record["do_to_supplier_list"]),
        "items": cleaned_items,
    }


def confirm_order(jo_number: str) -> dict[str, Any]:
    job_order_df = read_table(JOB_ORDER_FILE, columns=JOB_ORDER_COLUMNS)
    if job_order_df.empty:
        raise ValueError("No job orders found")
    mask = job_order_df["jo_number"].astype(str) == str(jo_number)
    if not mask.any():
        raise ValueError(f"JO number not found: {jo_number}")
    job_order = job_order_df.loc[mask].iloc[0].to_dict()
    if job_order.get("status") != "Preparing":
        raise ValueError("Only Preparing orders can be confirmed")

    year_two = f"{date.today().year % 100:02d}"
    delivery_df = read_table(DELIVERY_ORDER_FILE, columns=DELIVERY_ORDER_COLUMNS)
    do_number = next_number(delivery_df, "do_client_number", "DO", year_two)
    now = now_timestamp()

    client_code = str(job_order["client_code"])
    client_snapshot = _load_client_snapshot(client_code)

    delivery_record = {
        "id": f"do-{do_number}",
        "do_client_number": do_number,
        "issue_date": today_date(),
        "jo_number": job_order["jo_number"],
        "client_code": client_code,
        "client_name": client_snapshot["client_name"],
        "delivery_address": client_snapshot["delivery_address"],
        "client_pic": client_snapshot["client_pic"],
        "client_contact": client_snapshot["client_contact"],
        "client_po_list": job_order.get("client_po_list", "[]"),
        "remark": job_order.get("remark", ""),
        "status": "Delivering",
        "complete_date": "",
        "created_at": now,
        "updated_at": now,
    }

    items_df = read_table(JOB_ORDER_ITEMS_FILE, columns=JOB_ORDER_ITEM_COLUMNS)
    items = items_df[items_df["jo_number"].astype(str) == str(jo_number)]
    delivery_items: list[dict[str, Any]] = []
    for idx, row in items.iterrows():
        delivery_items.append(
            {
                "id": f"do-{do_number}-item-{len(delivery_items) + 1}",
                "do_client_number": do_number,
                "item_code": row.get("item_code", ""),
                "item_description": row.get("item_description", ""),
                "width": row.get("width", ""),
                "length": row.get("length", ""),
                "qty": row.get("qty", ""),
                "created_at": now,
                "updated_at": now,
            }
        )

    job_order_df.loc[mask, "status"] = "Delivering"
    job_order_df.loc[mask, "do_to_client_number"] = do_number
    job_order_df.loc[mask, "updated_at"] = now
    update_rows(JOB_ORDER_FILE, job_order_df)

    append_rows(DELIVERY_ORDER_FILE, [delivery_record], columns=DELIVERY_ORDER_COLUMNS)
    append_rows(
        DELIVERY_ORDER_ITEMS_FILE, delivery_items, columns=DELIVERY_ORDER_ITEM_COLUMNS
    )

    def _clean(value: Any) -> Any:
        if pd.isna(value):
            return ""
        return value

    cleaned_items = [{k: _clean(v) for k, v in item.items()} for item in delivery_items]

    return {
        "do_client_number": do_number,
        "client_snapshot": {k: _clean(v) for k, v in client_snapshot.items()},
        "status": "Delivering",
        "items": cleaned_items,
    }
