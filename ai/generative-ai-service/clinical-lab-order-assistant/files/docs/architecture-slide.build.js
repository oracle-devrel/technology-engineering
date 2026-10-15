const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.author = "Oracle";
pres.title = "LabSense solution architecture";

const BG = "053241", CARD = "0B4256", CARD_EDGE = "1F5B70", WHITE = "FFFFFF", MUTED = "9FC3CE", RED = "C74634", TEAL = "6CC4D6", DARK_PILL = "072E3D";
const FONT = "Arial";
const slide = pres.addSlide();
slide.background = { color: BG };

// Title block
slide.addText("LabSense: solution architecture", { x: 0.5, y: 0.38, w: 9.5, h: 0.6, fontFace: FONT, fontSize: 30, bold: true, color: WHITE, margin: 0, isTextBox: true });
slide.addText("Redundant lab-test avoidance for physicians, built on an imported model running on a dedicated OCI Generative AI cluster", { x: 0.5, y: 0.98, w: 10.5, h: 0.35, fontFace: FONT, fontSize: 13, color: MUTED, margin: 0, isTextBox: true });
slide.addText("DEMO · ALL PATIENT DATA FICTIONAL", { x: 9.3, y: 0.45, w: 3.53, h: 0.3, fontFace: FONT, fontSize: 9, bold: true, color: RED, align: "right", margin: 0, isTextBox: true, charSpacing: 1 });

// Four tiers
const cards = [
  { title: "Clinician's browser", sub: "Next.js 16 front end · React 19", pill: "UI", bullets: [
    "Consult chat with streamed reasoning and tool steps",
    "Order board: requested vs recommended cost, validity, savings (Recharts)",
    "Patient record and visit history tabs",
    "Arabic / English, right-to-left layout",
    "Holds no credentials, never calls the model" ] },
  { title: "Agent loop", sub: "Vercel AI SDK · open source (Apache 2.0)", pill: "AGENT", bullets: [
    "ToolLoopAgent inside the Next.js server, no graph framework",
    "Model chooses a tool, the app runs it, result goes back, up to 8 steps",
    "Six tools: patient record, test catalog, evaluate order, place order, read report, import results",
    "OpenAI-compatible provider pointed at the gateway" ] },
  { title: "LabSense gateway", sub: "FastAPI · Python · loopback only", pill: "GATEWAY", bullets: [
    "Signs every request with the OCI API key from ~/.oci/config",
    "Patient records in SQLite: results, orders, visit summaries. This is the memory.",
    "Rules engine: validity windows and prices from catalog.json, deterministic",
    "Report parsing with PyMuPDF; scanned pages and images go to model vision" ] },
  { title: "OCI Generative AI", sub: "Dedicated AI cluster · eu-frankfurt-1", pill: "OCI", red: true, bullets: [
    "Imported model: Qwen 3.8 27B on an H100 hosting unit",
    "OpenAI-compatible Chat Completions route, OCI request signing",
    "Native function calling, streamed reasoning (effort none to xhigh), image understanding",
    "Native chat API used for document vision" ] },
];
const X0 = 0.5, W = 2.45, GAP = 0.84, Y = 1.5, H = 3.65;
cards.forEach((c, i) => {
  const x = X0 + i * (W + GAP);
  slide.addShape(pres.ShapeType.roundRect, { x, y: Y, w: W, h: H, fill: { color: CARD }, line: { color: CARD_EDGE, width: 1 }, rectRadius: 0.12, shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.35 } });
  slide.addShape(pres.ShapeType.roundRect, { x: x + 0.18, y: Y + 0.18, w: 0.95, h: 0.26, fill: { color: c.red ? RED : DARK_PILL }, line: { color: c.red ? RED : CARD_EDGE, width: 0.75 }, rectRadius: 0.13 });
  slide.addText(c.pill, { x: x + 0.18, y: Y + 0.18, w: 0.95, h: 0.26, fontFace: FONT, fontSize: 8.5, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true, charSpacing: 1.5 });
  slide.addText(c.title, { x: x + 0.18, y: Y + 0.52, w: W - 0.3, h: 0.36, fontFace: FONT, fontSize: 14.5, bold: true, color: WHITE, margin: 0, isTextBox: true });
  slide.addText(c.sub, { x: x + 0.18, y: Y + 0.88, w: W - 0.36, h: 0.28, fontFace: FONT, fontSize: 8.5, color: TEAL, margin: 0, isTextBox: true });
  slide.addText(c.bullets.map((t, j) => ({ text: t, options: { bullet: { indent: 10 }, breakLine: j < c.bullets.length - 1, paraSpaceAfter: 4 } })), { x: x + 0.14, y: Y + 1.22, w: W - 0.3, h: H - 1.35, fontFace: FONT, fontSize: 10, color: WHITE, valign: "top", margin: 0, isTextBox: true });
});
// Arrows between tiers
const links = ["SSE stream\n/api/chat", "Tool calls\nHTTP, loopback", "HTTPS\nOCI-signed"];
links.forEach((label, i) => {
  const x1 = X0 + (i + 1) * W + i * GAP + 0.06, x2 = x1 + GAP - 0.12, ym = Y + 1.55;
  slide.addShape(pres.ShapeType.line, { x: x1, y: ym, w: x2 - x1, h: 0, line: { color: TEAL, width: 1.5, beginArrowType: "triangle", endArrowType: "triangle" } });
  slide.addText(label, { x: x1 - 0.1, y: ym + 0.1, w: GAP + 0.08, h: 0.45, fontFace: FONT, fontSize: 8, color: MUTED, align: "center", valign: "top", margin: 0, isTextBox: true });
});

// Bottom panels
const BY = 5.4, BH = 1.15;
slide.addShape(pres.ShapeType.roundRect, { x: 0.5, y: BY, w: 6.1, h: BH, fill: { color: DARK_PILL }, line: { color: CARD_EDGE, width: 0.75 }, rectRadius: 0.1 });
slide.addText("Deliberately not used", { x: 0.7, y: BY + 0.12, w: 5.7, h: 0.28, fontFace: FONT, fontSize: 11, bold: true, color: RED, margin: 0, isTextBox: true });
slide.addText([
  { text: "OCI Responses API ", options: { bold: true } }, { text: "(returns 400 for imported models)  ·  " },
  { text: "OCI Generative AI Agents  ·  MCP  ·  hosted apps  ·  LangGraph / LangChain  ·  vector search  ·  any Vercel hosting or service", options: {} },
], { x: 0.7, y: BY + 0.42, w: 5.7, h: 0.7, fontFace: FONT, fontSize: 9.5, color: WHITE, valign: "top", margin: 0, isTextBox: true });

slide.addShape(pres.ShapeType.roundRect, { x: 6.94, y: BY, w: 5.89, h: BH, fill: { color: DARK_PILL }, line: { color: CARD_EDGE, width: 0.75 }, rectRadius: 0.1 });
slide.addText("Design principles", { x: 7.14, y: BY + 0.12, w: 5.5, h: 0.28, fontFace: FONT, fontSize: 11, bold: true, color: TEAL, margin: 0, isTextBox: true });
slide.addText([
  { text: "The AI is never the system of record: it reads and writes through an interface the hospital owns", options: { bullet: { indent: 10 }, breakLine: true, paraSpaceAfter: 2 } },
  { text: "Rules decide validity and cost; the model explains and handles clinical exceptions", options: { bullet: { indent: 10 }, breakLine: true, paraSpaceAfter: 2 } },
  { text: "Credentials stay server-side; both services bind to localhost; validity windows are illustrative", options: { bullet: { indent: 10 } } },
], { x: 7.1, y: BY + 0.42, w: 5.6, h: 0.72, fontFace: FONT, fontSize: 9.5, color: WHITE, valign: "top", margin: 0, isTextBox: true });

// Footer
slide.addText("ORACLE", { x: 0.5, y: 6.85, w: 1.5, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: RED, margin: 0, isTextBox: true, charSpacing: 2 });
slide.addText("LabSense demo  ·  October 2026", { x: 7.0, y: 6.87, w: 5.83, h: 0.3, fontFace: FONT, fontSize: 9, color: MUTED, align: "right", margin: 0, isTextBox: true });
slide.addNotes("Architecture of the LabSense demo. Four tiers left to right: browser UI, agent loop (open-source Vercel AI SDK, no Vercel services), the gateway we control, and the dedicated OCI endpoint hosting the imported Qwen model. Bottom left lists what was deliberately not used, including the Responses API which OCI rejects for imported models.");

pres.writeFile({ fileName: "labsense-architecture.pptx" }).then(f => console.log("wrote", f));
