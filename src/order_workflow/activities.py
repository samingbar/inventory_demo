"""
Demo Activities for the Order workflow.

This module contains Temporal activities that simulate the side effects of an
order pipeline using simple JSON files under `src/db/`. These are intentionally
small and easy to read for live demos.

Talking points for demos:
- Activities are the right place for non-deterministic work (IO, APIs).
- Failures are surfaced back to the Workflow as ApplicationError and, when
  using the Temporal backend in the GUI, appear as user-visible errors.
"""

import asyncio
import json
from pathlib import Path
import uuid
from temporalio import activity
from temporalio.exceptions import ApplicationError


# Resolve paths to JSON "databases"
_SRC_DIR = Path(__file__).resolve().parents[1]
_DB_DIR = _SRC_DIR / "db"
_INVENTORY = _DB_DIR / "inventory.json"
_STATE = _DB_DIR / "state.json"

def _read_json(path):
    """Read and parse JSON from disk (tiny helper for clarity)."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(path, data):
    """Write JSON atomically to avoid partial writes during demos."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    tmp.replace(path)

@activity.defn
async def generate_order_id():
    """Create a new order record and return its ID."""
    await asyncio.sleep(0)
    order_id = str(uuid.uuid4())
    try:
        state = _read_json(_STATE)
        state.setdefault("orders", {})[order_id] = {
            "status": "active",
            "item": None,
            "payment_status": "pending",
            "shipping_status": "pending",
            "address_status": "pending",
        }
        _write_json(_STATE, state)
    except Exception as e:
        raise ApplicationError(f"Failed to create order record: {e}")
    return order_id


@activity.defn
async def reserve_inventory(order_id, item):
    """Reserve one unit of inventory for the given item.

    Raises ApplicationError if item is unknown or out of stock.
    """
    await asyncio.sleep(0)
    inv = _read_json(_INVENTORY)
    state = _read_json(_STATE)
    if order_id not in state.get("orders", {}):
        raise ApplicationError(f"Order ID {order_id} not found in state database.")
    items = inv.get("items", {}).get(item)
    if not items:
        raise ApplicationError(f"Item {item} not found in inventory.")
    if items["available"] <= 0:
        raise ApplicationError(f"Item {item} is out of stock.")
    try:
        # For demo simplicity, reserve and decrement available immediately.
        items["reserved"] += 1
        items["available"] -= 1
        state["orders"][order_id]["item"] = item
        state["orders"][order_id]["shipping_status"] = "reserved"
        state["orders"][order_id]["status"] = "reserved"
        _write_json(_INVENTORY, inv)
        _write_json(_STATE, state)
        return f"Inventory for item {item} reserved for order {order_id}."
    except Exception as e:
        raise ApplicationError(f"Failed to update database: {e}")


@activity.defn
async def check_payment(order_id):
    """Mock payment verification (e.g., 3DS or auth check)."""
    state = _read_json(_STATE)
    order = state.get("orders", {}).get(order_id)
    if not order or order.get("shipping_status") != "reserved":
        raise ApplicationError(f"Order ID {order_id} not in the proper state.")
    await asyncio.sleep(0)
    try:
        order["payment_status"] = "payment_verified"
        _write_json(_STATE, state)
        return f"Payment for order {order_id} verified."
    except Exception as e:
        raise ApplicationError(f"Failed to verify payment for order {order_id}: {e}")


@activity.defn
async def check_address(order_id):
    """Mock address verification (e.g., AVS)."""
    state = _read_json(_STATE)
    order = state.get("orders", {}).get(order_id)
    if not order or order.get("payment_status") != "payment_verified" or order.get("shipping_status") != "reserved":
        raise ApplicationError(f"Order ID {order_id} not in the proper state.")
    await asyncio.sleep(0)
    try:
        order["address_status"] = "verified"
        _write_json(_STATE, state)
        return f"Address for order {order_id} verified."
    except Exception as e:
        raise ApplicationError(f"Failed to verify address for order {order_id}: {e}")


@activity.defn
async def process_payment(order_id):
    """Mock capture/settlement after verification and address check."""
    state = _read_json(_STATE)
    order = state.get("orders", {}).get(order_id)
    if not order or order.get("address_status") != "verified" or order.get("payment_status") != "payment_verified" or order.get("shipping_status") != "reserved":
        raise ApplicationError(f"Order ID {order_id} not in the proper state.")
    await asyncio.sleep(0)
    try:
        order["payment_status"] = "paid"
        order["status"] = "processed"
        _write_json(_STATE, state)
        return f"Payment for order {order_id} processed."
    except Exception as e:
        raise ApplicationError(f"Failed to process payment for order {order_id}: {e}")


@activity.defn
async def arrange_shipping(order_id, item):
    """Finalize order as shipped; adjust inventory and order state."""
    #if flag == 1:
        #raise ApplicationError(f"Unexpected logical error for {order_id}: {e}")
    state = _read_json(_STATE)
    order = state.get("orders", {}).get(order_id)
    if not order or order.get("payment_status") != "paid" or order.get("status") != "processed" or order.get("shipping_status") != "reserved":
        raise ApplicationError(f"Order ID {order_id} not in the proper state")
    inv = _read_json(_INVENTORY)
    # Add a small delay so the UI progress is visible during demos.
    await asyncio.sleep(5)
    try:
        it = inv.get("items", {}).get(item)
        if not it:
            raise ApplicationError(f"Item {item} not found in inventory.")
        it["reserved"] -= 1
        it["available"] -= 1
        order["shipping_status"] = "shipped"
        order["status"] = "shipped"
        _write_json(_INVENTORY, inv)
        _write_json(_STATE, state)
        return "Shipping arranged."
    except Exception as e:
        raise ApplicationError(f"Failed to arrange shipping for order {order_id}: {e}")
    

@activity.defn
async def compensate_inventory_reserve(order_id, item):
    """Compensate a reservation by returning stock to available and cancelling."""
    await asyncio.sleep(5)
    inv = _read_json(_INVENTORY)
    state = _read_json(_STATE)
    items = inv.get("items", {}).get(item)
    if not items:
        raise ApplicationError(f"Item {item} not found in inventory.")
    try:
        items["reserved"] -= 1
        items["available"] += 1
        order = state.get("orders", {}).get(order_id)
        if order:
            order["status"] = "cancelled"
        _write_json(_INVENTORY, inv)
        _write_json(_STATE, state)
        return f"Compensated inventory reservation for order {order_id}."
    except Exception as e:
        raise ApplicationError(f"Failed to compensate inventory reservation for order {order_id}: {e}")

@activity.defn
async def compensate_payment(order_id, item):
    """Compensate a payment by marking it refunded (demo only)."""
    await asyncio.sleep(5)
    state = _read_json(_STATE)
    order = state.get("orders", {}).get(order_id)
    if not order:
        raise ApplicationError(f"Order ID {order_id} not found in state database.")
    try:
        order["payment_status"] = "refunded"
        _write_json(_STATE, state)
        return f"Reversed payment for order {order_id}."
    except Exception as e:
        raise ApplicationError(f"Failed to compensate payment for order {order_id}: {e}")

@activity.defn
async def compensate_shipping(order_id, item):
    """Compensate shipping by returning one unit to available and cancelling."""
    await asyncio.sleep(5)
    inv = _read_json(_INVENTORY)
    state = _read_json(_STATE)
    items = inv.get("items", {}).get(item)
    if not items:
        raise ApplicationError(f"Item {item} not found in inventory.")
    try:
        items["available"] += 1
        order = state.get("orders", {}).get(order_id)
        if order:
            order["shipping_status"] = "cancelled"
        _write_json(_INVENTORY, inv)
        _write_json(_STATE, state)
        return f"Cancelled shipping for order {order_id}."
    except Exception as e:
        raise ApplicationError(f"Failed to compensate shipping for order {order_id}: {e}")

@activity.defn
async def compensate_order(order_id, item):
    """Close an order that failed midway through processing (demo state only)."""
    await asyncio.sleep(5)
    state = _read_json(_STATE)
    order = state.get("orders", {}).get(order_id)
    if not order:
        raise ApplicationError(f"Order ID {order_id} not found in state database.")
    try:
        order["status"] = "processing failure"
        _write_json(_STATE, state)
        return f"Closed order {order_id}."
    except Exception as e:
        raise ApplicationError(f"Failed to close order {order_id}: {e}")
