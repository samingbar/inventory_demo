from __future__ import annotations
from datetime import timedelta
from temporalio import workflow


def _now_iso():
    # Use Temporal-safe, deterministic time inside workflows
    return workflow.now().isoformat()


@workflow.defn(name="OrderWorkflow")
class OrderWorkflow:
    def __init__(self) -> None:
        self._state = {
            "orderId": "",
            "item": None,
            "state": "created",
            "status": "Order created",
            "history": [
                {"ts": _now_iso(), "stage": "created", "message": "Order created", "state": "created"}
            ],
        }

    @workflow.query
    def status(self):
        return self._state

    @workflow.query
    def progress(self):
        return self._state

    def _mark(self, state: str, message: str):
        self._state["state"] = state
        self._state["status"] = message
        self._state["history"].append({
            "ts": _now_iso(),
            "stage": state,
            "message": message,
            "state": state,
        })

    @workflow.run
    async def run(self, item: str) -> str:
        self._state["item"] = item

        order_id = await workflow.execute_activity(
            "generate_order_id", schedule_to_close_timeout=timedelta(seconds=30)
        )
        self._state["orderId"] = order_id
        await workflow.sleep(1)

        await workflow.execute_activity(
            "reserve_inventory", args=(order_id, item), schedule_to_close_timeout=timedelta(seconds=30)
        )
        self._mark("inventory_reserved", f"Reserved inventory for {item}")
        await workflow.sleep(1)

        await workflow.execute_activity(
            "check_payment", args=(order_id,), schedule_to_close_timeout=timedelta(seconds=30)
        )
        self._mark("payment_verified", "Payment verified")
        await workflow.sleep(1)

        await workflow.execute_activity(
            "check_address", args=(order_id,), schedule_to_close_timeout=timedelta(seconds=30)
        )
        self._mark("address_verified", "Address verified")
        await workflow.sleep(1)

        await workflow.execute_activity(
            "process_payment", args=(order_id,), schedule_to_close_timeout=timedelta(seconds=30)
        )
        self._mark("paid", "Payment processed")
        await workflow.sleep(1)

        await workflow.execute_activity(
            "arrange_shipping", args=(order_id, item), schedule_to_close_timeout=timedelta(seconds=30)
        )
        self._mark("shipped", "Shipment arranged")
        await workflow.sleep(1)

        return f"Order {order_id} completed successfully."
