"use client";

import Image from "next/image";
import { FileText, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageResponse } from "@/components/ai-elements/message";
import type { Attachment } from "@/lib/attachments";

export function AttachmentCards({ items, onInspect, onRemove }: { items: Attachment[]; onInspect: (id: string) => void; onRemove?: (id: string) => void }) {
  return <div className="attachment-cards">{items.map(item => <div key={item.id} className="attachment-card" data-status={item.status}>
    <button type="button" className="attachment-inspect" aria-label={`Inspect ${item.file.name}`} onClick={() => onInspect(item.id)}>
      <span className="attachment-image">{item.previewUrl ? <Image src={item.previewUrl} alt={item.file.name} width={144} height={90} unoptimized/> : <FileText className="size-7"/>}</span>
      <span className="attachment-name" title={item.file.name}>{item.file.name}</span>
      <span className="attachment-status">{item.status === "processing" && <Loader2 className="size-3 animate-spin"/>}{item.status === "draft" ? "Not sent" : item.status === "processing" ? "Processing…" : item.status === "error" ? "Needs attention" : "View extracted data"}</span>
    </button>
    {item.status === "draft" && onRemove && <Button type="button" variant="secondary" size="icon-xs" className="attachment-remove" aria-label={`Remove ${item.file.name}`} onClick={() => onRemove(item.id)}><X className="size-3"/></Button>}
  </div>)}</div>;
}

export function AttachmentInspector({ item, onClose }: { item?: Attachment; onClose: () => void }) {
  return <Dialog open={!!item} onOpenChange={open => { if (!open) onClose(); }}>
    <DialogContent className="attachment-dialog">
      <DialogHeader><DialogTitle className="pr-6 truncate">{item?.file.name || "Attachment"}</DialogTitle><DialogDescription>{item?.status === "draft" ? "Local preview only. Processing starts when you send your message." : "Inspect the original and the extracted data used by the assistant."}</DialogDescription></DialogHeader>
      {item && <Tabs key={item.id} defaultValue={item.document ? "data" : "original"} className="min-h-0 flex flex-col gap-3">
        <TabsList><TabsTrigger value="original">{item.previewUrl ? "Original image" : "File"}</TabsTrigger><TabsTrigger value="data">Extracted data</TabsTrigger></TabsList>
        <TabsContent value="original" className="attachment-original">{item.previewUrl ? <Image src={item.previewUrl} alt={item.file.name} width={1600} height={1200} unoptimized/> : <div className="flex flex-col items-center gap-3 p-8"><FileText className="size-10"/><p>{item.file.name}</p><p className="text-muted-foreground">{(item.file.size / 1024).toFixed(1)} KB</p></div>}</TabsContent>
        <TabsContent value="data" className="attachment-data">
          {item.document ? <><Badge variant="secondary">{item.document.method}</Badge><p className="text-xs text-muted-foreground">{item.document.characters.toLocaleString()} characters · AI transcriptions may need review.</p>{item.document.pages.map(page => <section key={page.page}><h3>Page {page.page}</h3><MessageResponse>{page.text}</MessageResponse></section>)}</> : <div className="flex items-center gap-3 p-6 text-muted-foreground" role="status">{item.status === "processing" && <Loader2 className="size-4 animate-spin"/>}{item.status === "draft" ? "Not processed yet. Press Enter or Send to analyze this attachment." : item.status === "error" ? item.error : "Extracting data from this attachment…"}</div>}
        </TabsContent>
      </Tabs>}
    </DialogContent>
  </Dialog>;
}
