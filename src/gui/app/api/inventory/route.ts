import { NextResponse } from "next/server";
import { getInventory } from "../../lib/db";

// GET /api/inventory
// Returns the full inventory map used to populate the item selector.

export async function GET() {
  const { items } = await getInventory();
  return NextResponse.json({ items });
}
