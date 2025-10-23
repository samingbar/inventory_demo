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
)
from .workflow import OrderWorkflow

"""A worker that hosts the OrderWorkflow and its activities."""
interrupt_event = asyncio.Event()


async def main():
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
        ],
    ):
       await interrupt_event.wait()

if __name__ == "__main__":
   asyncio.run(main())
