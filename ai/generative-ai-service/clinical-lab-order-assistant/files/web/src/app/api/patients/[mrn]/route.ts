import { gateway } from "@/lib/agent";
export async function GET(_req: Request, context: RouteContext<"/api/patients/[mrn]">) {
  const { mrn } = await context.params;
  if (!/^PT-\d{6}$/.test(mrn)) return Response.json({ error: "Invalid MRN" }, { status: 400 });
  try {
    const response = await fetch(`${gateway}/patients/${encodeURIComponent(mrn)}`, { signal: AbortSignal.timeout(5000), cache: "no-store" });
    return Response.json(await response.json(), { status: response.status });
  } catch { return Response.json({ error: "Gateway offline" }, { status: 503 }); }
}
