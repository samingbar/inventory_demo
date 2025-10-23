import { randomUUID } from "node:crypto";
import { setTimeout as delay } from "node:timers/promises";
import { getOrder, upsertOrder, updateInventoryItem } from "./db";

/**
 * Lightweight local simulator that mirrors the Python activities
 * so the UI can demonstrate workflow progress without requiring
 * a running Worker. Each step writes state to src/db/state.json.
 */

export async function startOrder({ item }: { item: string }) {
  const orderId = randomUUID();
  const now = () => new Date().toISOString();

  const base = {
    orderId,
    item,
    state: "created" as const,
    status: "Order created",
    history: [{ ts: now(), stage: "created", message: "Order created", state: "created" as const }],
  };
  await upsertOrder(base);

  // Fire-and-forget background progression
  void (async () => {
    try {
      // Reserve inventory
      await delay(750);
      await updateInventoryItem(item, (it) => {
        if (it.available - it.reserved <= 0) throw new Error("Out of stock");
        it.reserved += 1;
      });
      await mark(orderId, "inventory_reserved", `Reserved inventory for ${item}`);

      // Verify payment (pretend auth check)
      await delay(800);
      await mark(orderId, "payment_verified", "Payment verified");

      // Verify address
      await delay(800);
      await mark(orderId, "address_verified", "Address verified");

      // Process payment (capture)
      await delay(900);
      await mark(orderId, "paid", "Payment processed");

      // Arrange shipping (decrement inventory)
      await delay(900);
      await updateInventoryItem(item, (it) => {
        it.reserved -= 1;
        it.available -= 1;
      });
      await mark(orderId, "shipped", "Shipment arranged");
    } catch (err: any) {
      await fail(orderId, err?.message || String(err));
    }
  })();

  return { orderId };
}

async function mark(orderId: string, state: any, message: string) {
  const now = new Date().toISOString();
  const cur = await getOrder(orderId);
  if (!cur) return;
  cur.state = state;
  cur.status = message;
  cur.history.push({ ts: now, stage: state, message, state });
  await upsertOrder(cur);
}

async function fail(orderId: string, error: string) {
  const cur = await getOrder(orderId);
  if (!cur) return;
  cur.state = "failed";
  cur.status = `Failed: ${error}`;
  cur.error = error;
  cur.history.push({ ts: new Date().toISOString(), stage: "failed", message: error, state: "failed" });
  await upsertOrder(cur);
}

