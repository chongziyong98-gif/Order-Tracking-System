from __future__ import annotations

from typing import Any

from db import (
    DELIVERY_ORDER_FILE,
    JOB_ORDER_FILE,
    now_timestamp,
    read_table,
    update_rows,
)
from services.order_service import JOB_ORDER_COLUMNS, DELIVERY_ORDER_COLUMNS


def complete_order(jo_number: str) -> dict[str, Any]:
    job_order_df = read_table(JOB_ORDER_FILE, columns=JOB_ORDER_COLUMNS)
    if job_order_df.empty:
        raise ValueError("No job orders found")
    mask = job_order_df["jo_number"].astype(str) == str(jo_number)
    if not mask.any():
        raise ValueError(f"JO number not found: {jo_number}")
    if job_order_df.loc[mask, "status"].iloc[0] != "Delivering":
        raise ValueError("Only Delivering orders can be completed")

    now = now_timestamp()
    job_order_df.loc[mask, "status"] = "Completed"
    job_order_df.loc[mask, "complete_date"] = now.split("T")[0]
    job_order_df.loc[mask, "updated_at"] = now
    update_rows(JOB_ORDER_FILE, job_order_df)

    delivery_df = read_table(DELIVERY_ORDER_FILE, columns=DELIVERY_ORDER_COLUMNS)
    if not delivery_df.empty:
        dmask = delivery_df["jo_number"].astype(str) == str(jo_number)
        if dmask.any():
            delivery_df.loc[dmask, "status"] = "Completed"
            delivery_df.loc[dmask, "complete_date"] = now.split("T")[0]
            delivery_df.loc[dmask, "updated_at"] = now
            update_rows(DELIVERY_ORDER_FILE, delivery_df)

    return {"jo_number": jo_number, "status": "Completed"}


def cancel_order(jo_number: str) -> dict[str, Any]:
    job_order_df = read_table(JOB_ORDER_FILE, columns=JOB_ORDER_COLUMNS)
    if job_order_df.empty:
        raise ValueError("No job orders found")
    mask = job_order_df["jo_number"].astype(str) == str(jo_number)
    if not mask.any():
        raise ValueError(f"JO number not found: {jo_number}")
    status = job_order_df.loc[mask, "status"].iloc[0]
    if status not in ("Preparing", "Delivering"):
        raise ValueError("Only Preparing or Delivering orders can be canceled")

    now = now_timestamp()
    job_order_df.loc[mask, "status"] = "Canceled"
    job_order_df.loc[mask, "complete_date"] = now.split("T")[0]
    job_order_df.loc[mask, "updated_at"] = now
    update_rows(JOB_ORDER_FILE, job_order_df)

    delivery_df = read_table(DELIVERY_ORDER_FILE, columns=DELIVERY_ORDER_COLUMNS)
    if not delivery_df.empty:
        dmask = delivery_df["jo_number"].astype(str) == str(jo_number)
        if dmask.any():
            delivery_df.loc[dmask, "status"] = "Canceled"
            delivery_df.loc[dmask, "complete_date"] = now.split("T")[0]
            delivery_df.loc[dmask, "updated_at"] = now
            update_rows(DELIVERY_ORDER_FILE, delivery_df)

    return {"jo_number": jo_number, "status": "Canceled"}
