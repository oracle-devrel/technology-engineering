export type ParsedDocument = { id: string; name: string; method: string; pages: { page: number; text: string }[]; characters: number };
export type Attachment = {
  id: string; workspace: string; file: File; previewUrl?: string;
  status: "draft" | "processing" | "ready" | "error";
  messageId?: string; document?: ParsedDocument; error?: string;
};

/** Local files are never uploaded by enqueue. Only processMessage performs I/O. */
export class AttachmentStore {
  private items: Attachment[] = [];
  private listeners = new Set<() => void>();
  private active = new Map<string, AbortController>();
  getSnapshot = () => this.items;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  private update(items: Attachment[]) { this.items = items; this.listeners.forEach(listener => listener()); }
  private patch(id: string, patch: Partial<Attachment>) { this.update(this.items.map(item => item.id === id ? { ...item, ...patch } : item)); }

  enqueue(workspace: string, files: File[]) {
    if (!files.length) return;
    if (files.length + this.items.filter(item => item.workspace === workspace).length > 8) throw new Error("Attach up to eight files per workspace. Start a new session for more.");
    for (const file of files) {
      if (file.size > 12 * 1024 * 1024) throw new Error(`${file.name}: maximum file size is 12 MB.`);
      if (!/\.(pdf|docx|txt|md|csv|json|png|jpe?g|webp)$/i.test(file.name)) throw new Error(`${file.name}: unsupported file type.`);
    }
    this.update([...this.items, ...files.map(file => ({ id: crypto.randomUUID(), workspace, file,
      previewUrl: /\.(png|jpe?g|webp)$/i.test(file.name) ? URL.createObjectURL(file) : undefined,
      status: "draft" as const }))]);
  }
  assignDrafts(workspace: string, messageId: string) {
    this.update(this.items.map(item => item.workspace === workspace && item.status === "draft" ? { ...item, messageId, status: "processing" } : item));
  }
  removeDraft(id: string) { this.remove(item => item.id === id && item.status === "draft"); }
  removeMessage(messageId: string) { this.remove(item => item.messageId === messageId); }
  private remove(match: (item: Attachment) => boolean) {
    this.items.filter(match).forEach(item => { if (item.previewUrl) URL.revokeObjectURL(item.previewUrl); });
    this.update(this.items.filter(item => !match(item)));
  }
  cancel(workspace: string) { this.active.get(workspace)?.abort(); }
  clear(workspace: string) { this.cancel(workspace); this.remove(item => item.workspace === workspace); }
  dispose() { this.active.forEach(controller => controller.abort()); this.remove(() => true); }

  async processMessage(workspace: string, messageId: string) {
    if (this.active.has(workspace)) throw new Error("Attachment processing is already in progress.");
    const controller = new AbortController(); this.active.set(workspace, controller);
    const targets = this.items.filter(item => item.workspace === workspace && item.messageId === messageId && item.status !== "ready");
    targets.forEach(item => this.patch(item.id, { status: "processing", error: undefined }));
    try {
      for (const item of targets) {
        controller.signal.throwIfAborted();
        const form = new FormData(); form.append("file", item.file);
        const response = await fetch("/api/documents", { method: "POST", body: form, signal: controller.signal });
        const data = await response.json();
        controller.signal.throwIfAborted();
        if (!response.ok) throw new Error(`${item.file.name}: ${data.error || "Could not process file"}`);
        this.patch(item.id, { status: "ready", document: data });
      }
      return this.items.filter(item => item.workspace === workspace && item.document).map(item => item.document!);
    } catch (error) {
      const message = controller.signal.aborted ? "Processing stopped. Retry when ready." : error instanceof Error ? error.message : "Attachment processing failed.";
      targets.forEach(item => {
        if (this.items.find(current => current.id === item.id)?.status !== "ready") this.patch(item.id, { status: "error", error: message });
      });
      throw error;
    } finally { if (this.active.get(workspace) === controller) this.active.delete(workspace); }
  }
}
