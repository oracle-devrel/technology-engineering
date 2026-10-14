"use client";

import { Chat, useChat } from "@ai-sdk/react";
import { DefaultChatTransport, type ToolUIPart, type UIMessage } from "ai";
import { AnimatePresence, motion, MotionConfig } from "motion/react";
import { useCallback, useEffect, useMemo, useRef, useState, useSyncExternalStore, type ClipboardEvent } from "react";
import { useTheme } from "next-themes";
import Link from "next/link";
import { ArrowUp, ArrowUpRight, Brain, ClipboardList, Copy, FileImage, Globe2, Loader2, Moon, PanelRightClose, PanelRightOpen, Paperclip, Plus, ShieldCheck, Sparkles, Square, Sun, Wallet, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Conversation, ConversationContent, ConversationScrollButton } from "@/components/ai-elements/conversation";
import { Message, MessageContent, MessageResponse } from "@/components/ai-elements/message";
import { Tool, ToolContent, ToolHeader } from "@/components/ai-elements/tool";
import { Reasoning, ReasoningContent, ReasoningTrigger } from "@/components/ai-elements/reasoning";
import { cn } from "@/lib/utils";
import { clipboardImages } from "@/lib/clipboard-image";
import { AttachmentStore } from "@/lib/attachments";
import { defaultReasoningEffort, reasoningLabels, type ReasoningEffort } from "@/lib/reasoning";
import { t as strings, type Lang } from "@/lib/i18n";
import { scenarios, sampleReportPatient, sampleReportPath } from "@/lib/scenarios";
import type { Artifact, CatalogTest, Evaluation, Health, ImportOutcome, Patient, PatientSummary, VisitReceipt } from "@/lib/types";
import { AttachmentCards, AttachmentInspector } from "./attachment-view";
import { CommandPalette } from "./command-palette";
import { LogoMark, avatarClass, initials } from "./logo";
import { PatientRail } from "./patient-rail";
import { OrderBoard } from "./order-board";
import { RecordPanel } from "./record-panel";
import { VisitsPanel } from "./visits-panel";

const toolLabels: Record<Lang, Record<string, string>> = {
  en: { getPatientRecord: "Reading the patient record", searchTestCatalog: "Checking the test catalog", evaluateOrder: "Checking tests against the record", placeOrder: "Recording the order", readReport: "Reading the external report", importResults: "Adding results to the record" },
  ar: { getPatientRecord: "قراءة سجل المريض", searchTestCatalog: "مراجعة كتالوج الفحوصات", evaluateOrder: "مطابقة الفحوصات مع السجل", placeOrder: "تسجيل الطلب", readReport: "قراءة التقرير الخارجي", importResults: "إضافة النتائج إلى السجل" },
};
type BoardTab = "order" | "record" | "visits";
const NONE = "none";

export default function Console() {
  const [lang, setLang] = useState<Lang>("en");
  const s = strings(lang);
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [catalog, setCatalog] = useState<CatalogTest[]>([]);
  const [mrn, setMrn] = useState<string | null>(null);
  const [record, setRecord] = useState<Patient | null>(null);
  const patient = mrn && record?.mrn === mrn ? record : null;
  const [health, setHealth] = useState<Health>({ gateway: "checking" });
  const [input, setInput] = useState("");
  const [boardOpen, setBoardOpen] = useState(true);
  const [boardTab, setBoardTab] = useState<BoardTab>("order");
  const [commandOpen, setCommandOpen] = useState(false);
  const [reasoningEffort, setReasoningEffort] = useState<ReasoningEffort>(defaultReasoningEffort);
  const [uploadError, setUploadError] = useState("");
  const [elapsed, setElapsed] = useState(0);
  const [epoch, setEpoch] = useState(0);
  const [inspectedAttachment, setInspectedAttachment] = useState<string | null>(null);
  const [attachmentStore] = useState(() => new AttachmentStore());
  const allAttachments = useSyncExternalStore(attachmentStore.subscribe, attachmentStore.getSnapshot, attachmentStore.getSnapshot);
  const key = mrn ?? NONE;
  const attachments = allAttachments.filter(item => item.workspace === key);
  const drafts = attachments.filter(item => item.status === "draft");
  const documents = attachments.flatMap(item => item.document ? [item.document] : []);
  const uploading = attachments.some(item => item.status === "processing");
  const failedAttachments = attachments.some(item => item.status === "error");
  const sending = useRef(new Set<string>());
  const fileRef = useRef<HTMLInputElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { theme, setTheme } = useTheme();
  const [chats] = useState(() => new Map<string, Chat<UIMessage>>());
  const chat = useMemo(() => {
    const id = `${epoch}:${key}`;
    let existing = chats.get(id);
    if (!existing) { existing = new Chat({ id, transport: new DefaultChatTransport({ api: "/api/chat" }) }); chats.set(id, existing); }
    return existing;
  }, [chats, epoch, key]);
  const { messages, sendMessage, status, error, stop, setMessages, regenerate, clearError } = useChat({ chat, throttle: 80, onFinish: ({ message }) => { if (message.parts.some(p => (p.type === "tool-evaluateOrder" || p.type === "tool-placeOrder") && "state" in p && p.state === "output-available")) setBoardTab("order"); } });
  const busy = uploading || status === "submitted" || status === "streaming";

  const loadPatients = useCallback(() => fetch("/api/patients").then(r => r.json()).then((list: PatientSummary[]) => setPatients(Array.isArray(list) ? list : [])).catch(() => {}), []);
  const loadPatient = useCallback((id: string | null) => { if (!id) return; fetch(`/api/patients/${id}`).then(r => r.ok ? r.json() : null).then(data => { if (data) setRecord(data); }).catch(() => {}); }, []);

  useEffect(() => {
    const check = () => fetch("/api/health").then(r => r.json()).then(setHealth).catch(() => setHealth({ gateway: "offline" }));
    check(); const timer = setInterval(check, 30000);
    loadPatients(); fetch("/api/catalog").then(r => r.json()).then((list: CatalogTest[]) => setCatalog(Array.isArray(list) ? list : [])).catch(() => {});
    return () => clearInterval(timer);
  }, [loadPatients]);
  useEffect(() => { loadPatient(mrn); }, [mrn, loadPatient]);
  useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  useEffect(() => () => { chats.forEach(c => { void c.stop(); }); }, [chats]);
  useEffect(() => () => attachmentStore.dispose(), [attachmentStore]);
  useEffect(() => { if (!busy) return; const timer = setInterval(() => setElapsed(v => v + 1), 1000); return () => clearInterval(timer); }, [busy]);

  const toolParts = messages.flatMap(message => message.parts.filter(p => p.type.startsWith("tool-")) as ToolUIPart[]);
  const artifacts = toolParts.filter(p => p.state === "output-available" && p.output && typeof p.output === "object" && "kind" in p.output).map(p => p.output as Artifact);
  const lastBoardArtifact = [...artifacts].reverse().find(a => a.kind === "evaluation" || a.kind === "visit");
  const evaluation = lastBoardArtifact?.kind === "evaluation" ? (lastBoardArtifact as Evaluation) : undefined;
  const receipt = lastBoardArtifact?.kind === "visit" ? (lastBoardArtifact as VisitReceipt) : undefined;
  const mutations = artifacts.filter(a => a.kind === "visit" || a.kind === "import").length;
  const imports = artifacts.filter(a => a.kind === "import").length;
  const completedTools = toolParts.filter(p => p.state === "output-available").length;
  const seenMutations = useRef(0);
  useEffect(() => { if (mutations !== seenMutations.current) { seenMutations.current = mutations; loadPatient(mrn); loadPatients(); } }, [mutations, mrn, loadPatient, loadPatients]);
  const seenImports = useRef(0);
  useEffect(() => { if (imports > seenImports.current) { const last = [...artifacts].reverse().find(a => a.kind === "import") as ImportOutcome | undefined; if (last) toast.success(lang === "ar" ? `أُضيفت ${last.added.length} نتيجة إلى السجل` : `${last.added.length} result(s) added to the record`); } seenImports.current = imports; }, [imports, artifacts, lang]);

  async function submit(text: string) {
    if (!mrn) { toast.info(s.selectPatient); return; }
    if ((!text.trim() && !drafts.length) || busy || sending.current.has(key)) return;
    if (failedAttachments) { toast.error("Retry or remove the failed attachment before continuing."); return; }
    const message: UIMessage = { id: crypto.randomUUID(), role: "user", parts: [{ type: "text", text: text.trim() || "Read the attached report, add its results to the record and re-evaluate." }] };
    setInput(""); clearError(); setUploadError(""); setElapsed(0);
    attachmentStore.assignDrafts(key, message.id);
    setMessages(current => [...current, message]);
    await processAndSend(message);
  }
  async function processAndSend(message: UIMessage) {
    if (sending.current.has(key)) return;
    sending.current.add(key); setUploadError(""); clearError(); setElapsed(0);
    try {
      const parsed = await attachmentStore.processMessage(key, message.id);
      const refs = attachmentStore.getSnapshot().filter(item => item.messageId === message.id && item.document).map(item => ({ id: item.document!.id, name: item.file.name }));
      await sendMessage({ messageId: message.id, role: "user", parts: message.parts, metadata: { attachments: refs } }, { body: { mrn, documentIds: parsed.map(doc => doc.id), reasoningEffort } });
    } catch (err) { if (!(err instanceof DOMException && err.name === "AbortError")) setUploadError(err instanceof Error ? err.message : "Attachment processing failed."); }
    finally { sending.current.delete(key); }
  }
  function queueFiles(files: File[]) {
    if (!mrn) { toast.info(s.selectPatient); return; }
    try { attachmentStore.enqueue(key, files); setUploadError(""); } catch (err) { toast.error(err instanceof Error ? err.message : "Could not attach files."); }
  }
  function pasteImage(event: ClipboardEvent<HTMLTextAreaElement>) {
    try { const files = clipboardImages(event.clipboardData); if (!files.length) return; event.preventDefault(); queueFiles(files); }
    catch (err) { event.preventDefault(); toast.error(err instanceof Error ? err.message : "Could not paste image."); }
  }
  async function loadSampleReport() {
    try {
      const blob = await (await fetch(sampleReportPath)).blob();
      queueFiles([new File([blob], "Al-Noor Medical Center — lab report.png", { type: "image/png" })]);
      setInput(scenarios[sampleReportPatient][lang][1]); inputRef.current?.focus();
    } catch { toast.error("Sample report is missing. Run scripts/make_sample_report.py."); }
  }
  function stopRequest() { attachmentStore.cancel(key); void stop(); }
  function selectPatient(id: string) {
    if (id === mrn) return;
    if (busy) { stopRequest(); toast.info("Generation stopped. The conversation is kept for that patient."); }
    setMrn(id); setBoardTab("order"); setInput(""); setUploadError(""); setElapsed(0);
  }
  function newConsult() { stopRequest(); attachmentStore.clear(key); setInspectedAttachment(null); setMessages([]); setInput(""); setUploadError(""); clearError(); }
  async function resetDemo() {
    stopRequest(); attachmentStore.dispose();
    chats.forEach(c => { void c.stop(); }); chats.clear(); setEpoch(e => e + 1);
    try { await fetch("/api/reset", { method: "POST" }); toast.success(lang === "ar" ? "تمت إعادة ضبط البيانات" : "Demo data reset"); } catch { toast.error("Reset failed. Is the gateway running?"); }
    loadPatients(); loadPatient(mrn);
  }
  const starters = mrn ? scenarios[mrn]?.[lang] ?? [] : [];
  const summary = patients.find(p => p.mrn === mrn);
  const displayName = (p: { name: string; name_ar: string }) => lang === "ar" ? p.name_ar : p.name;

  return <MotionConfig reducedMotion="user"><div className="app-shell" dir={lang === "ar" ? "rtl" : "ltr"}>
    <AttachmentInspector item={attachments.find(item => item.id === inspectedAttachment)} onClose={() => setInspectedAttachment(null)}/>
    <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} patients={patients} mrn={mrn} onSelectPatient={selectPatient} effort={reasoningEffort} onEffortChange={v => { setReasoningEffort(v); toast.success(`${s.thinking}: ${reasoningLabels[v]}`); }} onNewConsult={newConsult} onToggleBoard={() => setBoardOpen(v => !v)} onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")} onToggleLanguage={() => setLang(l => l === "en" ? "ar" : "en")} onReset={resetDemo} busy={busy}/>
    <header className="topbar">
      <Link className="brand" href="/" aria-label="LabSense home"><LogoMark size={34}/><span><span className="brand-name">{s.appName}</span><span className="brand-sub">{s.tagline}</span></span></Link>
      {summary && <div className="patient-banner"><span className={cn(avatarClass(summary.mrn), "avatar-sm")}>{initials(summary.name)}</span><strong>{displayName(summary)}</strong><span>{summary.mrn} · {summary.age}{summary.sex === "F" ? "F" : "M"}</span>{summary.conditions.slice(0, 2).map(c => <span key={c} className="chip">{c}</span>)}</div>}
      <select className="patient-select" aria-label={s.patients} value={mrn ?? ""} onChange={e => selectPatient(e.target.value)}><option value="" disabled>{s.selectPatient}</option>{patients.map(p => <option key={p.mrn} value={p.mrn}>{displayName(p)} · {p.mrn}</option>)}</select>
      <div className="topbar-actions">
        <Button variant="outline" size="sm" className="wide" onClick={() => setCommandOpen(true)} aria-keyshortcuts="Meta+K Control+K"><Brain className="size-4"/>{s.thinking}: {reasoningLabels[reasoningEffort]}<kbd>⌘K</kbd></Button>
        <Button variant="ghost" size="sm" onClick={() => setLang(l => l === "en" ? "ar" : "en")}><Globe2 className="size-4"/>{lang === "en" ? "العربية" : "English"}</Button>
        <Button variant="ghost" size="icon-sm" aria-label="Toggle color theme" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{theme === "dark" ? <Sun className="size-4"/> : <Moon className="size-4"/>}</Button>
        <Button variant="ghost" size="icon-sm" aria-label={s.board} onClick={() => setBoardOpen(v => !v)}>{boardOpen ? <PanelRightClose className="size-4"/> : <PanelRightOpen className="size-4"/>}</Button>
      </div>
    </header>
    <div className={cn("app-body", boardOpen && "board-open")}>
      <PatientRail patients={patients} mrn={mrn} onSelect={selectPatient} lang={lang} s={s} health={health} onReset={resetDemo} busy={busy}/>
      <motion.main key={key} className="consult" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} onDragOver={e => { if (e.dataTransfer.types.includes("Files")) e.preventDefault(); }} onDrop={e => { if (e.dataTransfer.files.length) { e.preventDefault(); queueFiles(Array.from(e.dataTransfer.files)); } }}>
        <Conversation className="conversation" initial={messages.length ? "smooth" : false} resize="smooth"><ConversationContent className={cn("conversation-inner", !messages.length && "empty-conversation")}>
          {!messages.length ? <AnimatePresence mode="wait"><motion.div key={key} initial={{ opacity: 0, y: 14, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} exit={{ opacity: 0, y: -8, filter: "blur(4px)" }} transition={{ duration: 0.3 }} className="hero">
            <div className="hero-mark"><LogoMark size={44}/></div>
            <h1>{s.welcomeTitle}</h1>
            <p>{s.welcomeBody}</p>
            {summary ? <>
              <div className="hero-patient"><span className={cn(avatarClass(summary.mrn), "avatar-sm")}>{initials(summary.name)}</span><strong>{displayName(summary)}</strong><span className="text-muted-foreground">· {summary.visit_count ? `${summary.visit_count} ${s.visits.toLowerCase()}` : s.firstVisit}</span></div>
              <div className="starters">{starters.map((text, index) => <button key={text} className="starter" disabled={uploading} onClick={() => { if (index === 1 && mrn === sampleReportPatient) { void loadSampleReport(); return; } void submit(text); }}><span className="starter-step">{index + 1}</span><span>{text}</span><ArrowUpRight className="size-4"/></button>)}</div>
            </> : <div className="hero-patient"><span className="status-dot"/>{s.selectPatient}</div>}
            <div className="hero-note"><span><ShieldCheck className="size-3"/>{lang === "ar" ? "نموذج مخصص على OCI" : "Dedicated model on OCI"}</span><span><Wallet className="size-3"/>{lang === "ar" ? "تكلفة كل فحص" : "Cost of every test"}</span><span><FileImage className="size-3"/>{lang === "ar" ? "قراءة التقارير الخارجية" : "Reads external reports"}</span></div>
          </motion.div></AnimatePresence> : messages.map(message => <motion.div key={message.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="message-wrap">
            <div className="message-author">{message.role === "assistant" ? <><span className="assistant-avatar"><Sparkles className="size-3.5"/></span>{s.assistant}</> : <><span className="human-avatar">Dr</span>{s.you}</>}</div>
            <Message from={message.role}><MessageContent>{message.parts.map((part, index) => {
              if (part.type === "text") return <div dir="auto" key={index}><MessageResponse>{part.text}</MessageResponse></div>;
              if (part.type === "reasoning") return <Reasoning key={index} defaultOpen={false} isStreaming={busy && message.id === messages.at(-1)?.id && part.state === "streaming"} className="reasoning-step"><ReasoningTrigger/><ReasoningContent dir="auto">{part.text}</ReasoningContent></Reasoning>;
              if (part.type.startsWith("tool-")) {
                const p = part as ToolUIPart; const name = p.type.slice(5); const out = p.state === "output-available" ? p.output : undefined;
                return <Tool key={index} className="tool-step"><ToolHeader type={p.type} state={p.state} title={toolLabels[lang][name] || name}/><ToolContent><pre className="tool-json">{JSON.stringify(p.state === "output-error" ? { error: p.errorText } : out ?? p.input, null, 2)}</pre></ToolContent></Tool>;
              }
              return null;
            })}{message.role === "user" && <AttachmentCards items={attachments.filter(item => item.messageId === message.id)} onInspect={setInspectedAttachment}/>}</MessageContent></Message>
            {attachments.some(item => item.messageId === message.id && item.status === "error") && <Alert variant="destructive"><AlertDescription><span>Report processing did not finish.</span><div className="flex gap-2"><Button size="sm" variant="outline" disabled={busy} onClick={() => processAndSend(message)}>Retry</Button><Button size="sm" variant="ghost" disabled={busy} onClick={() => { attachmentStore.removeMessage(message.id); setMessages(current => current.filter(m => m.id !== message.id)); setUploadError(""); }}>Remove message</Button></div></AlertDescription></Alert>}
            {message.role === "assistant" && message.parts.some(p => p.type === "text" && p.text.trim()) && <div className="message-actions"><button aria-label="Copy response" onClick={() => { navigator.clipboard.writeText(message.parts.filter(p => p.type === "text").map(p => p.text).join("\n")); toast.success("Copied"); }}><Copy className="size-3.5"/></button>{!!message.metadata && <span>{(((message.metadata as { elapsedMs?: number }).elapsedMs ?? 0) / 1000).toFixed(1)}s</span>}</div>}
          </motion.div>)}
          {busy && <div className="working-indicator" role="status"><span/><span/><span/><p>{uploading ? s.processingReport : toolParts.at(-1)?.state === "input-streaming" ? s.preparingTool : s.working}<span className="elapsed-label">{elapsed}s</span></p></div>}
        </ConversationContent><ConversationScrollButton/></Conversation>
        <div className="composer-area">
          {error && <Alert variant="destructive" className="mb-3"><AlertDescription><span>{error.message}</span><Button size="sm" variant="outline" onClick={() => regenerate({ body: { mrn, documentIds: documents.map(d => d.id), reasoningEffort } })}>Retry</Button></AlertDescription></Alert>}
          {uploadError && <Alert variant="destructive" className="mb-3"><AlertDescription>{uploadError}</AlertDescription></Alert>}
          {drafts.length > 0 && <div className="draft-attachments" aria-label="Unsent attachments"><AttachmentCards items={drafts} onInspect={setInspectedAttachment} onRemove={id => attachmentStore.removeDraft(id)}/><p>{lang === "ar" ? "لم يُرسل بعد · تبدأ القراءة عند الإرسال" : "Not sent · reading starts when you press Enter"}</p></div>}
          {mrn && messages.length > 0 && <div className="composer-chips">{starters.slice(1).map((text, i) => <Button key={text} variant="outline" size="xs" disabled={busy} onClick={() => { if (i === 0 && mrn === sampleReportPatient) { void loadSampleReport(); return; } setInput(text); inputRef.current?.focus(); }}>{text.length > 60 ? text.slice(0, 58) + "…" : text}</Button>)}<span>{busy ? "" : "⌘K"}</span></div>}
          <form className={cn("composer", busy && "composer-busy")} onSubmit={e => { e.preventDefault(); void submit(input); }}>
            <textarea ref={inputRef} aria-label="Message LabSense" value={input} onChange={e => setInput(e.target.value)} onPaste={pasteImage} placeholder={mrn ? s.placeholder : s.selectPatient} dir="auto" rows={2} disabled={!mrn} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void submit(input); } }}/>
            <div className="composer-toolbar">
              <div className="flex items-center gap-1">
                <Button type="button" variant="ghost" size="icon-sm" aria-label={s.attach} title={s.attach} disabled={busy || uploading || !mrn} onClick={() => fileRef.current?.click()}>{uploading ? <Loader2 className="size-4 animate-spin"/> : <Paperclip className="size-4"/>}</Button>
                {mrn === sampleReportPatient && <Button type="button" variant="ghost" size="sm" disabled={busy || uploading} onClick={() => void loadSampleReport()}><FileImage className="size-4"/>{s.sampleReport}</Button>}
                <Button type="button" variant="ghost" size="sm" disabled={!mrn || !messages.length} onClick={newConsult}><Plus className="size-4"/>{s.newConsult}</Button>
              </div>
              {busy ? <Button type="button" size="icon" aria-label={s.stop} onClick={stopRequest}><Square className="size-3.5 fill-current"/></Button> : <Button type="submit" size="icon" className="send-button" aria-label={s.send} disabled={!mrn || (!input.trim() && !drafts.length) || failedAttachments}><ArrowUp className="size-5"/></Button>}
            </div>
          </form>
          <div className="composer-footnote"><span className="composer-model"><ShieldCheck className="size-3"/>{health.gateway === "ready" ? `${s.gatewayReady} · ${health.region}` : s.gatewayOffline}</span><span>{s.reviewNote}</span></div>
          <input ref={fileRef} type="file" multiple className="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp,.txt,.csv" onChange={e => { queueFiles(Array.from(e.target.files ?? [])); e.target.value = ""; }}/>
        </div>
      </motion.main>
      <AnimatePresence>{boardOpen && <motion.aside className="board" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 24 }} transition={{ duration: 0.25 }}>
        <div className="board-header">
          <Tabs value={boardTab} onValueChange={v => setBoardTab(String(v) as BoardTab)}><TabsList><TabsTrigger value="order"><ClipboardList className="size-3.5"/>{s.order}</TabsTrigger><TabsTrigger value="record">{s.record}{patient ? ` · ${new Set(patient.results.map(r => r.code)).size}` : ""}</TabsTrigger><TabsTrigger value="visits">{s.visits}{patient ? ` · ${patient.visits.length}` : ""}</TabsTrigger></TabsList></Tabs>
          <Button variant="ghost" size="icon-sm" aria-label="Close board" onClick={() => setBoardOpen(false)}><X className="size-4"/></Button>
        </div>
        <div className="board-content"><AnimatePresence mode="wait"><motion.div key={`${boardTab}-${key}-${artifacts.length}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.2 }}>
          {boardTab === "order" ? <OrderBoard evaluation={evaluation} receipt={receipt} patient={patient} lang={lang} s={s}/> : boardTab === "record" ? <RecordPanel patient={patient} catalog={catalog} lang={lang} s={s}/> : <VisitsPanel patient={patient} catalog={catalog} lang={lang} s={s}/>}
        </motion.div></AnimatePresence></div>
        <div className="board-footer"><span className={cn("status-dot", health.gateway !== "ready" && "offline")}/><span>{busy ? s.working : completedTools ? `${completedTools} tool steps` : s.board}</span><span>ORACLE · OCI</span></div>
      </motion.aside>}</AnimatePresence>
    </div>
  </div></MotionConfig>;
}
