from __future__ import annotations

from flask import Flask, jsonify, redirect, render_template, request, url_for

from services import (
    cancel_order,
    complete_order,
    confirm_order,
    create_order_draft,
    get_delivery_order,
    list_orders,
)
from db import CLIENT_MASTER_FILE, ITEM_MASTER_FILE, normalize_columns, read_table

app = Flask(__name__)


@app.get("/")
def index():
    return redirect(url_for("dashboard_page"))


@app.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.get("/create-order")
def create_order_page():
    return render_template("create_order.html")


@app.get("/delivery/<do_number>")
def delivery_page(do_number: str):
    return render_template("delivery_order_client.html", do_number=do_number)


@app.get("/api/orders")
def api_list_orders():
    filters = {
        "month": request.args.get("month"),
        "year": request.args.get("year"),
        "status": request.args.get("status"),
    }
    return jsonify(list_orders(filters))


@app.post("/api/orders")
def api_create_order():
    payload = request.get_json(force=True, silent=True) or {}
    try:
        result = create_order_draft(payload)
        return jsonify({"ok": True, "data": result})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/orders/<jo_number>/confirm")
def api_confirm_order(jo_number: str):
    try:
        result = confirm_order(jo_number)
        return jsonify({"ok": True, "data": result})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/orders/<jo_number>/complete")
def api_complete_order(jo_number: str):
    try:
        result = complete_order(jo_number)
        return jsonify({"ok": True, "data": result})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/orders/<jo_number>/cancel")
def api_cancel_order(jo_number: str):
    try:
        result = cancel_order(jo_number)
        return jsonify({"ok": True, "data": result})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/api/delivery/<do_number>")
def api_get_delivery(do_number: str):
    try:
        result = get_delivery_order(do_number)
        return jsonify({"ok": True, "data": result})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/api/clients/<client_code>")
def api_get_client(client_code: str):
    df = read_table(CLIENT_MASTER_FILE)
    if df.empty:
        return jsonify({"ok": False, "error": "client_master.xlsx is empty"}), 404
    df = normalize_columns(df)
    code_col = "client_code" if "client_code" in df.columns else "code"
    if code_col not in df.columns:
        return jsonify({"ok": False, "error": "client_code column missing"}), 400
    row = df[df[code_col].astype(str) == str(client_code)]
    if row.empty:
        return jsonify({"ok": False, "error": "Client code not found"}), 404
    record = row.iloc[0].to_dict()
    payload = {
        "client_code": client_code,
        "client_name": str(record.get("client_name", "")),
        "delivery_address": str(record.get("delivery_address", "")),
        "client_pic": str(record.get("client_pic", "")),
        "client_contact": str(record.get("client_contact", "")),
    }
    return jsonify({"ok": True, "data": payload})


@app.get("/api/items/<item_code>")
def api_get_item(item_code: str):
    df = read_table(ITEM_MASTER_FILE)
    if df.empty:
        return jsonify({"ok": False, "error": "item_master.xlsx is empty"}), 404
    df = normalize_columns(df)
    code_col = "item_code" if "item_code" in df.columns else "code"
    if code_col not in df.columns:
        return jsonify({"ok": False, "error": "item_code column missing"}), 400
    row = df[df[code_col].astype(str) == str(item_code)]
    if row.empty:
        return jsonify({"ok": False, "error": "Item code not found"}), 404
    record = row.iloc[0].to_dict()
    payload = {
        "item_code": item_code,
        "item_description": str(
            record.get("item_description", record.get("description", ""))
        ),
    }
    return jsonify({"ok": True, "data": payload})


if __name__ == "__main__":
    app.run(debug=True)
