import { NextResponse } from "next/server";
import { getOrder } from "../../../lib/db";
import { getTemporalClient } from "../../../lib/temporal";

type Params = { params: { id: string } };

export async function GET(_req: Request, { params }: Params) {
  if (process.env.USE_TEMPORAL === "1") {
    try {
      const client = await getTemporalClient();
      const handle = client.workflow.getHandle(params.id);
      // Try a friendly query first if the workflow defines one
      try {
        // These are candidate query names; if not present, will throw
        const q = (await (handle as any).query("status")) || (await (handle as any).query("progress"));
        return NextResponse.json(q);
      } catch {}
      // Fall back to describe for coarse status
      const d = await handle.describe();
      const status = d.status.name || String(d.status);
      const completed = status.toLowerCase() === "completed";
      const failed = status.toLowerCase() === "failed" || status.toLowerCase() === "terminated";
      let error: string | undefined;
      if (failed) {
        try {
          // Will throw with the underlying failure; because it's already finished, this resolves immediately
          await handle.result();
        } catch (e: any) {
          error = e?.message ? String(e.message) : String(e);
        }
      }
      const mapped = {
        orderId: params.id,
        state: failed ? "failed" : completed ? "shipped" : "created",
        status: failed ? `Failed (${status})` : completed ? "Completed" : "Workflow running",
        history: [
          { ts: new Date().toISOString(), stage: "created", message: "Workflow started", state: "created" },
        ],
        error,
      };
      return NextResponse.json(mapped);
    } catch (e: any) {
      return NextResponse.json({ error: String(e?.message || e) }, { status: 500 });
    }
  } else {
    const order = await getOrder(params.id);
    if (!order) return NextResponse.json({ error: "Not found" }, { status: 404 });
    return NextResponse.json(order);
  }
}
