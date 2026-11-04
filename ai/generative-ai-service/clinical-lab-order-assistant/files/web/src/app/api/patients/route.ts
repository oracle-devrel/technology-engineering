import { gateway } from "@/lib/agent";
export async function GET() {
  try { return Response.json(await (await fetch(`${gateway}/patients`, { signal: AbortSignal.timeout(5000), cache: "no-store" })).json()); }
  catch { return Response.json([], { status: 503 }); }
}
