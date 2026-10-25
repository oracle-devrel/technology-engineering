import { gateway } from "@/lib/agent";
export const maxDuration = 300;
export async function POST(req: Request) {
  try {
    const form = await req.formData();
    const file = form.get("file");
    if (!(file instanceof File) || file.size > 12 * 1024 * 1024) return Response.json({ error: "Choose a file smaller than 12 MB." }, { status: 400 });
    const response = await fetch(`${gateway}/documents`, { method: "POST", body: form, signal: AbortSignal.any([req.signal, AbortSignal.timeout(240000)]) });
    const data = await response.json();
    return Response.json(response.ok ? data : { error: data.detail }, { status: response.status });
  } catch { return Response.json({ error: "Report processing failed. Check that the Python gateway is running." }, { status: 502 }); }
}
