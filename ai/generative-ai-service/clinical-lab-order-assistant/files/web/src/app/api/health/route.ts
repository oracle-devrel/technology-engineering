import { gateway } from "@/lib/agent";
export async function GET() {
  try {
    const response = await fetch(`${gateway}/health`, { signal: AbortSignal.timeout(3000), cache: "no-store" });
    return Response.json(await response.json());
  } catch { return Response.json({ gateway: "offline" }, { status: 503 }); }
}
