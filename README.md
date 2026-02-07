# Order Tracking System

A lightweight order tracking system that connects the flow from `Job Order (JO)` to `Delivery Order (DO)` with clear creation, confirmation, completion/cancellation, and query capabilities.

## At A Glance

- Roles / scenario: order admin, delivery follow-up
- Core flow: Create JO -> Confirm to generate DO -> Complete or cancel delivery
- Storage: Excel files (no database required)
- Main pages: Dashboard / Create Order / Delivery Order

## Feature Overview

- Order creation: validates required fields and generates JO numbers
- Auto DO generation: confirming a JO creates a DO with line items
- State machine: `Preparing -> Delivering -> Completed/Canceled`
- Master data sync: client/item data auto-filled from masterlists
- Dashboard filtering: filter by month/year/status

## Quick Start

```powershell
# 1) Install dependencies
pip install flask pandas openpyxl

# 2) Run the app
python app.py

# 3) Open in browser
# http://127.0.0.1:5000
```

## Pages & Routes

- Dashboard: `/dashboard` - order list and status actions
- Create Order: `/create-order` - create/confirm orders
- Delivery Order: `/delivery/<do_number>` - DO details

## API Summary

| Method | Path | Description |
| --- | --- | --- |
| GET | `/api/orders` | Order list (supports `year/month/status`) |
| POST | `/api/orders` | Create order draft |
| POST | `/api/orders/<jo_number>/confirm` | Confirm order and generate DO |
| POST | `/api/orders/<jo_number>/complete` | Complete order |
| POST | `/api/orders/<jo_number>/cancel` | Cancel order |
| GET | `/api/delivery/<do_number>` | Get DO details |
| GET | `/api/clients/<client_code>` | Query client master data |
| GET | `/api/items/<item_code>` | Query item master data |

## Data Files

> The project uses Excel files as storage. Ensure master data files exist and columns are correct.

- `master/client_master.xlsx`
  - Required columns: `client_code` or `code`
  - Optional columns: `client_name`, `delivery_address`, `client_pic`, `client_contact`
- `master/item_master.xlsx`
  - Required columns: `item_code` or `code`
  - Optional columns: `item_description` or `description`
- `data/job_order.xlsx`
- `data/job_order_items.xlsx`
- `data/delivery_order.xlsx`
- `data/delivery_order_items.xlsx`

## Project Structure

```
.
├─ app.py                  # Flask entry
├─ db.py                   # Excel I/O and numbering
├─ services/               # Business logic
├─ templates/              # UI templates
├─ static/                 # Frontend styles and scripts
├─ master/                 # Master data (client/item)
└─ data/                   # Business data (JO/DO)
```

## FAQ

- If required columns are missing in master data, APIs will return errors.
- Empty Excel files result in "not found" responses.

## Scope & Limitations

- Best for lightweight internal workflows
- No user authentication or audit logs
- No database or multi-user concurrency control

---

