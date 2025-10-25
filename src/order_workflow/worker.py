from __future__ import annotations

import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from .activities import (
    generate_order_id,
    reserve_inventory,
    check_payment,
    check_address,
    process_payment,
    arrange_shipping,
    compensate_inventory_reserve,
    compensate_order,
    compensate_payment,
    compensate_shipping
)
from .workflow import OrderWorkflow

"""
Temporal Worker that hosts the OrderWorkflow and related activities.

Talking points for demos:
- Connects to Temporal Server at localhost:7233 by default.
- Uses task queue "order-task-queue" to receive work.
- Registers both the workflow class and each activity function.
"""
interrupt_event = asyncio.Event()


async def main():
    # Connect to Temporal Server. Change address if needed for your demo.
    client = await Client.connect("localhost:7233")
    async with Worker(
        client,
        task_queue="order-task-queue",
        workflows=[OrderWorkflow],
        activities=[
            generate_order_id,
            reserve_inventory,
            check_payment,
            check_address,
            process_payment,
            arrange_shipping,
            compensate_shipping,
            compensate_inventory_reserve,
            compensate_payment,
            compensate_order
        ],
    ):
        # Keep the worker alive until interrupted (Ctrl+C during demos)
        await interrupt_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
