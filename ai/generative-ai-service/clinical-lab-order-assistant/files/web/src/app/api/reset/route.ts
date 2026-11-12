import { gateway } from "@/lib/agent";
export async function POST() {
  try { return Response.json(await (await fetch(`${gateway}/reset`, { method: "POST", signal: AbortSignal.timeout(5000) })).json()); }
  catch { return Response.json({ error: "Gateway offline" }, { status: 503 }); }
}
