"""
Temporal Workflow definition for the demo Order process.

This workflow orchestrates a linear set of activities while maintaining a
lightweight progress state that the GUI queries to render a live timeline.

Demo highlights:
- Determinism: use `workflow.now()` and `workflow.sleep()` (not wall-clock IO).
- Queries: `status` and `progress` return the same JSON-friendly dict.
- Error handling: on exceptions, a simple compensation sequence is executed
  in reverse order of successful steps to illustrate the saga pattern.
"""

from __future__ import annotations
from datetime import timedelta
from temporalio import workflow


def _now_iso():
    """Return a Temporal-safe timestamp string for history entries."""
    return workflow.now().isoformat()


@workflow.defn(name="OrderWorkflow")
class OrderWorkflow:
    def __init__(self) -> None:
        # Progress state consumed by the GUI (via workflow queries)
        self._state = {
            "orderId": "",
            "item": None,
            "state": "created",
            "status": "Order created",
            "history": [
                {"ts": _now_iso(), "stage": "created", "message": "Order created", "state": "created"}
            ],
        }
        # Track successful steps to demonstrate a minimal compensation pattern
        self.compensation = []

    @workflow.query
    def status(self):
        """Primary query used by the GUI to show progress."""
        return self._state

    @workflow.query
    def progress(self):
        """Alias query for compatibility with other sample UIs."""
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
    @workflow.signal
    def workflow_inputs(self, input):
        """Example signal to show how external inputs could be received."""
        self.input = input

    @workflow.run
    async def run(self, item: str) -> str:
        # Persist the item being ordered so the GUI can display it
        self._state["item"] = item

        # Generate an order ID and remember it for subsequent steps
        order_id = await workflow.execute_activity(
            "generate_order_id", schedule_to_close_timeout=timedelta(seconds=30)
        )
        self.compensation.append("order")

              
        self._state["orderId"] = order_id
        await workflow.sleep(1)
        try: 
            await workflow.execute_activity(
                "reserve_inventory", args=(order_id, item), schedule_to_close_timeout=timedelta(seconds=30)
            )
            self.compensation.append("inventory_reserve")
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
            self.compensation.append("payment")

            await workflow.execute_activity(
                "arrange_shipping", args=(order_id, item), schedule_to_close_timeout=timedelta(seconds=30)
            )
            self._mark("shipped", "Shipment arranged")
            await workflow.sleep(1)
            self.compensation.append("shipping")
            self.compensation.remove("inventory_reserve")
        except Exception as e:
            # On any step failure, run compensating actions in reverse order.
            if self.compensation:
                for action in reversed(self.compensation):
                    await workflow.execute_activity(
                        f"compensate_{action}", args=(order_id, item), schedule_to_close_timeout=timedelta(seconds=30)
                    )
        return f"Order {order_id} completed successfully."
