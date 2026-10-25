import { gateway } from "@/lib/agent";
export async function GET() {
  try { return Response.json(await (await fetch(`${gateway}/catalog`, { signal: AbortSignal.timeout(5000) })).json()); }
  catch { return Response.json([], { status: 503 }); }
}
