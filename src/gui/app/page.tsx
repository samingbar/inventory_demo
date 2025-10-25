"use client";

// Demo checkout UI: starts an order and polls for progress.
// Works with Temporal by default, or a local simulator when USE_TEMPORAL=0.

import { useEffect, useMemo, useState } from "react";

type InventoryItem = {
  sku: string;
  price: number;
  available: number;
  reserved: number;
  location: string;
};

type Inventory = Record<string, InventoryItem>;

type OrderState =
  | "created"
  | "inventory_reserved"
  | "payment_verified"
  | "address_verified"
  | "paid"
  | "shipped"
  | "failed";

type Order = {
  orderId: string;
  item?: string;
  state: OrderState;
  status: string;
  history: Array<{ ts: string; stage: string; message: string; state: OrderState }>;
  error?: string;
};

// Small fetch helper with typed return for convenience
async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function Page() {
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [selectedItem, setSelectedItem] = useState<string>("");
  const [placing, setPlacing] = useState(false);
  const [orderId, setOrderId] = useState<string | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [polling, setPolling] = useState(false);

  // Load inventory once on page load
  useEffect(() => {
    fetchJSON<{ items: Inventory }>("/api/inventory")
      .then((d) => {
        setInventory(d.items);
        const first = Object.keys(d.items)[0];
        setSelectedItem(first ?? "");
      })
      .catch((e) => console.error(e));
  }, []);

  // Fixed stage labels rendered as a timeline
  const stages = useMemo(
    () => [
      { key: "created", label: "Order Created" },
      { key: "inventory_reserved", label: "Inventory Reserved" },
      { key: "payment_verified", label: "Payment Verified" },
      { key: "address_verified", label: "Address Verified" },
      { key: "paid", label: "Payment Processed" },
      { key: "shipped", label: "Shipped" },
    ],
    []
  );

  // Start polling once we have an order ID
  useEffect(() => {
    if (!orderId) return;
    setPolling(true);
    let active = true;
    const tick = async () => {
      try {
        const data = await fetchJSON<Order>(`/api/orders/${orderId}`);
        if (!active) return;
        setOrder(data);
        if (data.state === "shipped" || data.state === "failed") {
          setPolling(false);
          return;
        }
      } catch (e) {
        console.error(e);
      }
      if (active) setTimeout(tick, 1000);
    };
    tick();
    return () => {
      active = false;
    };
  }, [orderId]);

  // Start a new order by POSTing the selected item
  async function placeOrder() {
    if (!selectedItem) return;
    setPlacing(true);
    setOrder(null);
    setOrderId(null);
    try {
      const res = await fetchJSON<{ orderId: string }>("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: selectedItem }),
      });
      setOrderId(res.orderId);
    } catch (e) {
      alert(`Failed to place order: ${e}`);
    } finally {
      setPlacing(false);
    }
  }

  return (
    <div>
      <section style={{ marginBottom: 24 }}>
        <h2 style={{ margin: "0 0 8px" }}>Create Order</h2>
        {!inventory ? (
          <p>Loading inventory…</p>
        ) : (
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <select
              value={selectedItem}
              onChange={(e) => setSelectedItem(e.target.value)}
              style={{ padding: 8, minWidth: 260 }}
            >
              {Object.entries(inventory).map(([name, it]) => (
                <option key={name} value={name}>
                  {name} — ${it.price.toFixed(2)} (avail {it.available})
                </option>
              ))}
            </select>
            <button onClick={placeOrder} disabled={placing || !selectedItem}>
              {placing ? "Placing…" : "Place Order"}
            </button>
          </div>
        )}
      </section>

      <section>
        <h2 style={{ margin: "16px 0 8px" }}>Progress</h2>
        {!orderId && <p>No order yet. Create one above.</p>}
        {orderId && !order && <p>Starting order {orderId}…</p>}
        {order && (
          <div>
            <div style={{ marginBottom: 8, color: "#555" }}>
              <strong>Order ID:</strong> {order.orderId} {order.item ? `• ${order.item}` : ""}
            </div>
            <ol style={{ listStyle: "none", padding: 0, margin: 0 }}>
              {stages.map((s, idx) => {
                const isDone = order.history.some((h) => h.state === s.key);
                const isActive = order.state === s.key;
                const isFailed = order.state === "failed";
                return (
                  <li
                    key={s.key}
                    style={{
                      padding: "10px 12px",
                      marginBottom: 8,
                      borderRadius: 8,
                      border: "1px solid #e5e7eb",
                      background: isDone ? "#ecfdf5" : isActive ? "#eff6ff" : "#fff",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span aria-hidden>
                        {isDone ? "✅" : isActive ? "⏳" : "⬜️"}
                      </span>
                      <span>
                        {idx + 1}. {s.label}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ol>
            {order.error && (
              <div style={{
                marginTop: 12,
                padding: 12,
                borderRadius: 8,
                border: "1px solid #fecaca",
                background: "#fef2f2",
                color: "#991b1b",
              }}>
                <strong>Error:</strong> {order.error}
                {order.error.toLowerCase().includes("out of stock") && (
                  <div style={{ marginTop: 6, color: "#7f1d1d" }}>
                    The selected item is out of stock. Please choose a different item or try again later.
                  </div>
                )}
              </div>
            )}
            <div style={{ marginTop: 12, color: "#555" }}>{order.status}</div>
            <div style={{ marginTop: 16 }}>
              <button onClick={() => { setOrderId(null); setOrder(null); }} disabled={polling}>
                Reset
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
