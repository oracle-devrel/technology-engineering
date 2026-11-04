import { createAgentUIStreamResponse } from "ai";
import { z } from "zod";
import { createLabAgent } from "@/lib/agent";
import { defaultReasoningEffort, reasoningEfforts } from "@/lib/reasoning";

export const maxDuration = 800;
const requestSchema = z.object({
  messages: z.array(z.unknown()).max(200),
  mrn: z.string().regex(/^PT-\d{6}$/).nullable().default(null),
  documentIds: z.array(z.string().regex(/^[a-f0-9]{32}$/)).max(8).default([]),
  reasoningEffort: z.enum(reasoningEfforts).default(defaultReasoningEffort),
});

export async function POST(req: Request) {
  try {
    const { messages, mrn, documentIds, reasoningEffort } = requestSchema.parse(await req.json());
    if (JSON.stringify(messages).length > 1500000) return Response.json({ error: "Conversation is too long. Start a new consult." }, { status: 413 });
    const completeMessages = messages.map(message => {
      if (message && typeof message === "object" && "role" in message && message.role === "user" && "parts" in message && Array.isArray(message.parts) && "metadata" in message) {
        const metadata = z.object({ attachments: z.array(z.object({ id: z.string(), name: z.string().max(300) })).max(8) }).safeParse(message.metadata);
        const refs = metadata.success ? metadata.data.attachments.filter(item => documentIds.includes(item.id)) : [];
        if (refs.length) return { ...message, parts: [...message.parts, { type: "text", text: `External reports attached to this message (use readReport): ${JSON.stringify(refs)}` }] };
      }
      if (!message || typeof message !== "object" || !("role" in message) || message.role !== "assistant" || !("parts" in message) || !Array.isArray(message.parts)) return message;
      // A stopped generation can leave a half-finished tool call; never send it back without a result.
      return { ...message, parts: message.parts.filter((part: { type?: string; state?: string }) => !part.type?.startsWith("tool-") || !["input-streaming", "input-available"].includes(part.state || "")) };
    }).filter(message => !(message && typeof message === "object" && "parts" in message && Array.isArray(message.parts) && message.parts.length === 0));
    const started = Date.now();
    return await createAgentUIStreamResponse({
      agent: createLabAgent(mrn, documentIds, reasoningEffort),
      uiMessages: completeMessages,
      abortSignal: req.signal,
      keepAliveMs: 15000,
      sendReasoning: true,
      messageMetadata: ({ part }) => part.type === "finish" ? { elapsedMs: Date.now() - started } : undefined,
      onError: (error) => error instanceof Error ? error.message : "The request failed. Check the local gateway and retry.",
    });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Invalid request" }, { status: 400 });
  }
}
