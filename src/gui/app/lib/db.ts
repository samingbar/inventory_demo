import fs from "node:fs/promises";
import path from "node:path";

const dbRoot = path.join(process.cwd(), "..", "db");
const statePath = path.join(dbRoot, "state.json");
const inventoryPath = path.join(dbRoot, "inventory.json");

export type OrderState =
  | "created"
  | "inventory_reserved"
  | "payment_verified"
  | "address_verified"
  | "paid"
  | "shipped"
  | "failed";

export type Order = {
  orderId: string;
  item?: string;
  state: OrderState;
  status: string;
  history: Array<{ ts: string; stage: string; message: string; state: OrderState }>;
  error?: string;
};

export async function getState(): Promise<{ orders: Record<string, Order> }> {
  const raw = await fs.readFile(statePath, "utf8");
  return JSON.parse(raw);
}

export async function putState(next: { orders: Record<string, Order> }) {
  await fs.writeFile(statePath, JSON.stringify(next, null, 2));
}

export async function getOrder(id: string): Promise<Order | undefined> {
  const s = await getState();
  return s.orders[id];
}

export async function upsertOrder(order: Order) {
  const s = await getState();
  s.orders[order.orderId] = order;
  await putState(s);
}

export async function getInventory(): Promise<{
  metadata: any;
  items: Record<string, {
    sku: string;
    price: number;
    available: number;
    reserved: number;
    location: string;
    updated_at: string;
  }>;
}> {
  const raw = await fs.readFile(inventoryPath, "utf8");
  return JSON.parse(raw);
}

export async function updateInventoryItem(name: string, fn: (item: any) => void) {
  const data = await getInventory();
  const item = data.items[name];
  if (!item) throw new Error(`Item ${name} not found`);
  fn(item);
  await fs.writeFile(inventoryPath, JSON.stringify(data, null, 2));
}

