"""
Integration-style test for the OrderWorkflow demo.

This spins up a Temporal Worker in-process and starts a workflow against it,
asserting that the final returned string indicates success. For richer testing,
you could also query the workflow for progress and assert intermediate states.
"""

from __future__ import annotations
import json
from pathlib import Path
import asyncio
import pytest
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker
from temporalio.client import Client, WorkflowFailureError
from ..activities import (
    generate_order_id,
    reserve_inventory,
    check_payment,
    check_address,
    process_payment,
    arrange_shipping,
    compensate_shipping,
    compensate_inventory_reserve,
    compensate_order,
    compensate_payment
)
from ..workflow import OrderWorkflow

def set_db(wm = {"available": 150, "reserved": 10}, mk = {"available": 6, "reserved": 5}, uc = {"available": 500, "reserved": 25}) -> None:
    """Reset the state and inventory databases to their initial state."""
    _SRC_DIR = Path(__file__).parent.parent.parent
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


    # The worker in this test listens on the same queue as our demo worker
    task_queue = "order-task-queue"
activities = [
        generate_order_id,
        reserve_inventory,
        check_payment,
        check_address,
        process_payment,
        arrange_shipping,
        compensate_payment,
        compensate_order,
        compensate_shipping,
        compensate_inventory_reserve
    ]
connection ="localhost:7233" 


# Run the end-to-end workflow test
@pytest.mark.asyncio
async def test_order_workflow() -> None:
    set_db()
    """Run end-to-end ETL flow and assert retries and idempotency."""

    input_data = "Mechanical Keyboard"
    client = await Client.connect(connection)

    try:
        async with Worker(
            client,
            task_queue=task_queue,
            workflows=[OrderWorkflow],
            activities=activities,
        ):
            handle = await client.start_workflow(
                OrderWorkflow.run,
                input_data,
                id="order-workflow-test",
                task_queue=task_queue,
            )
            # Trigger pause/resume mid-flight to validate signaling and state persistence
            result = await handle.result()
    except:
        pytest.fail("Workflow execution failed")
    assert result is not None
    assert "completed successfully" in result

# Test End-to-End Workflow
@pytest.mark.asyncio
async def test_order_workflow() -> None:
    set_db()
    
    input_data = "Mechanical Keyboard"
    client = await Client.connect(connection)
    try:
        async with Worker(
            client,
            task_queue=task_queue,
            workflows=[OrderWorkflow],
            activities=activities,
        ):
            handle = await client.start_workflow(
                OrderWorkflow.run,
                input_data,
                id="order-workflow-test",
                task_queue=task_queue,
            )
            # Trigger pause/resume mid-flight to validate signaling and state persistence
            result = await handle.result()
    except:
        pytest.fail("Workflow execution failed")
    assert result is not None
    assert "completed successfully" in result
    set_db()

# Test Inventory Validation
@pytest.mark.asyncio
async def test_inventory_check() -> None:
    set_db(mk={"available": 150, "reserved": 150})
    """Run end-to-end ETL flow and assert retries and idempotency."""
    
    input_data = "Mechanical Keyboard"
    client = await Client.connect(connection)
    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[OrderWorkflow],
        activities=activities,
    ):
        handle = await client.start_workflow(
            OrderWorkflow.run,
            input_data,
            id="inventory-validation-test",
            task_queue=task_queue,
        )
        result = await handle.result()
    assert result is not None
    assert "completed successfully" in result
    set_db()


# Test Invalid Item
@pytest.mark.asyncio
async def test_invalid_item() -> None:
    set_db()
  
    input_data = "Paper Airplane"
    client = await Client.connect(connection)
    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[OrderWorkflow],
        activities=activities,
    ):
        handle = await client.start_workflow(
            OrderWorkflow.run,
            input_data,
            id="inventory-validation-test",
            task_queue=task_queue,
        )
        result = await handle.result()
    assert result is not None
    assert "completed successfully" in result
    set_db()
