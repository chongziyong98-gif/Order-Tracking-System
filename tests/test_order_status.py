from __future__ import annotations

from pathlib import Path

import pandas as pd

import db
from services import order_service, order_status_service


def _setup_paths(tmp_path: Path) -> dict[str, Path]:
    data_dir = tmp_path / "data"
    master_dir = tmp_path / "master"
    data_dir.mkdir(parents=True, exist_ok=True)
    master_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "DATA_DIR": data_dir,
        "MASTER_DIR": master_dir,
        "JOB_ORDER_FILE": data_dir / "job_order.xlsx",
        "JOB_ORDER_ITEMS_FILE": data_dir / "job_order_items.xlsx",
        "DELIVERY_ORDER_FILE": data_dir / "delivery_order.xlsx",
        "DELIVERY_ORDER_ITEMS_FILE": data_dir / "delivery_order_items.xlsx",
        "CLIENT_MASTER_FILE": master_dir / "client_master.xlsx",
        "ITEM_MASTER_FILE": master_dir / "item_master.xlsx",
    }

    db.DATA_DIR = data_dir
    db.MASTER_DIR = master_dir
    db.JOB_ORDER_FILE = paths["JOB_ORDER_FILE"]
    db.JOB_ORDER_ITEMS_FILE = paths["JOB_ORDER_ITEMS_FILE"]
    db.DELIVERY_ORDER_FILE = paths["DELIVERY_ORDER_FILE"]
    db.DELIVERY_ORDER_ITEMS_FILE = paths["DELIVERY_ORDER_ITEMS_FILE"]
    db.CLIENT_MASTER_FILE = paths["CLIENT_MASTER_FILE"]
    db.ITEM_MASTER_FILE = paths["ITEM_MASTER_FILE"]

    order_service.JOB_ORDER_FILE = paths["JOB_ORDER_FILE"]
    order_service.JOB_ORDER_ITEMS_FILE = paths["JOB_ORDER_ITEMS_FILE"]
    order_service.DELIVERY_ORDER_FILE = paths["DELIVERY_ORDER_FILE"]
    order_service.DELIVERY_ORDER_ITEMS_FILE = paths["DELIVERY_ORDER_ITEMS_FILE"]
    order_service.CLIENT_MASTER_FILE = paths["CLIENT_MASTER_FILE"]
    order_service.ITEM_MASTER_FILE = paths["ITEM_MASTER_FILE"]

    order_status_service.JOB_ORDER_FILE = paths["JOB_ORDER_FILE"]
    order_status_service.DELIVERY_ORDER_FILE = paths["DELIVERY_ORDER_FILE"]

    return paths


def _seed_master(paths: dict[str, Path]) -> None:
    client_df = pd.DataFrame(
        [
            {
                "client_code": "C001",
                "client_name": "Test Pte Ltd",
                "delivery_address": "1, Raffles Mall",
                "client_pic": "Zy",
                "client_contact": "+65 12345678",
            }
        ]
    )
    item_df = pd.DataFrame(
        [{"item_code": "00015", "item_description": "Fire Rated Pyran S 6mm"}]
    )
    client_df.to_excel(paths["CLIENT_MASTER_FILE"], index=False)
    item_df.to_excel(paths["ITEM_MASTER_FILE"], index=False)


def test_complete_order(tmp_path: Path) -> None:
    paths = _setup_paths(tmp_path)
    _seed_master(paths)

    payload = {
        "client_code": "C001",
        "items": [{"item_code": "00015", "qty": 10}],
        "required_date": "2026-02-05",
        "local_export": "Local",
    }
    draft = order_service.create_order_draft(payload)
    order_service.confirm_order(draft["jo_number"])

    result = order_status_service.complete_order(draft["jo_number"])
    assert result["status"] == "Completed"

    job_order_df = pd.read_excel(paths["JOB_ORDER_FILE"], dtype=object)
    assert job_order_df.loc[0, "status"] == "Completed"

    delivery_df = pd.read_excel(paths["DELIVERY_ORDER_FILE"], dtype=object)
    assert delivery_df.loc[0, "status"] == "Completed"


def test_cancel_order(tmp_path: Path) -> None:
    paths = _setup_paths(tmp_path)
    _seed_master(paths)

    payload = {
        "client_code": "C001",
        "items": [{"item_code": "00015", "qty": 10}],
        "required_date": "2026-02-05",
        "local_export": "Local",
    }
    draft = order_service.create_order_draft(payload)

    result = order_status_service.cancel_order(draft["jo_number"])
    assert result["status"] == "Canceled"

    job_order_df = pd.read_excel(paths["JOB_ORDER_FILE"], dtype=object)
    assert job_order_df.loc[0, "status"] == "Canceled"
