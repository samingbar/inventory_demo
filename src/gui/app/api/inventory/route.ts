import { NextResponse } from "next/server";
import { getInventory } from "../../lib/db";

export async function GET() {
  const { items } = await getInventory();
  return NextResponse.json({ items });
}
