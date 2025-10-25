from pathlib import Path
import json


def set_db(wm = {"available": 150, "reserved": 10}, mk = {"available": 6, "reserved": 5}, uc = {"available": 500, "reserved": 25}) -> None:
    """Reset the state and inventory JSON files for clean demos.

    Usage examples:
      - python -m src.demo.reset
      - python src/demo/reset.py

    Keyword args adjust initial stock levels quickly during a live demo.
    """
    _SRC_DIR = Path(__file__).parent.parent
    print(f"Source directory: {_SRC_DIR}")
    _DB_DIR = _SRC_DIR / "db"
    _INVENTORY = _DB_DIR / "inventory.json"
    _STATE = _DB_DIR / "state.json"

    initial_inventory ={
    "metadata": {
        "version": 1,
        "generated_at": "2025-10-23T00:00:00Z",
        "currency": "USD"
    },
    "items": {
        "Wireless Mouse": {
        "sku": "SKU-1001",
        "price": 24.99,
        "available": wm["available"],
        "reserved": wm["reserved"],
        "location": "WH-SEA-01",
        "updated_at": "2025-10-23T00:00:00Z"
        },
        "Mechanical Keyboard": {
        "sku": "SKU-2002",
        "price": 89.5,
        "available": mk["available"],
        "reserved": mk["reserved"],
        "location": "WH-SEA-01",
        "updated_at": "2025-10-23T00:00:00Z"
        },
        "USB-C Cable": {
        "sku": "SKU-3003",
        "price": 8.99,
        "available": uc["available"],
        "reserved": uc["reserved"],
        "location": "WH-SFO-02",
        "updated_at": "2025-10-23T00:00:00Z"
        }
    }
    }
    initial_state = {"orders": {}}

    with _INVENTORY.open("w", encoding="utf-8") as f:
        json.dump(initial_inventory, f, indent=2)

    with _STATE.open("w", encoding="utf-8") as f:
        json.dump(initial_state, f, indent=2)


if __name__ == "__main__":
    set_db()
import json
from pathlib import Path
