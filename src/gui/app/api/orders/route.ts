import { NextResponse } from "next/server";
import { startOrder } from "../../lib/workflowSim";
import { getTemporalClient } from "../../lib/temporal";
import { randomUUID } from "node:crypto";

// POST /api/orders
// Starts an order either via Temporal (default) or the local simulator.

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const item = String(body?.item || "").trim();
  if (!item) return NextResponse.json({ error: "Missing item" }, { status: 400 });

  // Default to Temporal unless explicitly disabled with USE_TEMPORAL=0
  if (process.env.USE_TEMPORAL !== "0") {
    try {
      const client = await getTemporalClient();
      const workflowId = `order-${randomUUID()}`;
      await client.workflow.start("OrderWorkflow", {
        taskQueue: process.env.TEMPORAL_TASK_QUEUE || "order-task-queue",
        workflowId,
        args: [item],
      });
      return NextResponse.json({ orderId: workflowId });
    } catch (e: any) {
      return NextResponse.json({ error: String(e?.message || e) }, { status: 500 });
    }
  } else {
    const { orderId } = await startOrder({ item });
    return NextResponse.json({ orderId });
  }
}
