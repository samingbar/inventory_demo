import { Connection, Client } from "@temporalio/client";

let cached: Client | null = null;

export async function getTemporalClient() {
  if (cached) return cached;
  const address = process.env.TEMPORAL_ADDRESS || "localhost:7233";
  const namespace = process.env.TEMPORAL_NAMESPACE || "default";
  const connection = await Connection.connect({ address });
  cached = new Client({ connection, namespace });
  return cached;
}

