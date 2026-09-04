// Copyright (c) 2026 Oracle and/or its affiliates.
// Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  BarChart3,
  CheckCircle2,
  Database,
  Loader2,
  Play,
  RefreshCcw,
  Search,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
  XCircle,
} from "lucide-react";
import {
  Bar,
  BarChart as ReBarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import styles from "./page.module.css";

const initialForm = {
  prompt: "",
  oacMcpUrl: "",
  accessToken: "",
  baseUrl: "",
  genAiApiKey: "",
  projectId: "",
  model: "openai.gpt-oss-120b",
  region: "eu-frankfurt-1",
  timeoutSeconds: 60,
};

const MODEL_OPTIONS = [
  { label: "OpenAI gpt-oss-120b", value: "openai.gpt-oss-120b" },
  { label: "Google Gemini 2.5 Flash", value: "google.gemini-2.5-flash" },
];

const quickPrompts = [
  {
    label: "Capabilities",
    value:
      "What can this Oracle Analytics MCP server do? List the tools, available subject areas, and a few good test questions.",
  },
  {
    label: "Discover Data",
    value:
      "Discover available Oracle Analytics subject areas and datasets. Summarize what is available, then recommend one useful read-only analysis I can run next. Do not execute Logical SQL yet.",
  },
  {
    label: "Sample Sales",
    value:
      "Using Sample Sales Lite, describe the useful measures and dimensions, then run a simple read-only sales analysis. Include the Logical SQL used and a short business interpretation.",
  },
  {
    label: "Revenue Chart",
    value:
      "Using Sample Sales Lite, show the top 10 product types by revenue. Include the Logical SQL used, summarize the result, and return data suitable for a bar chart.",
  },
  {
    label: "Graph Demo",
    value:
      "Show a demo graph with sample product revenue rows. Do not call OAC.",
  },
  {
    label: "Year Chart",
    value:
      "Using Sample Sales Lite, show revenue and billed quantity by year. Include the Logical SQL used and render the result as a chart.",
  },
  {
    label: "Sample Targets",
    value:
      "Using Sample Targets Lite, describe the useful measures and dimensions, then run a simple read-only target analysis. Include the Logical SQL used and summarize what the target data shows.",
  },
  {
    label: "Follow-Up",
    value:
      "Using the same data model from the previous answer, break the result down by month and highlight any trend worth investigating.",
  },
];

export default function OacDemoPage() {
  const [form, setForm] = useState(initialForm);
  const [messages, setMessages] = useState([]);
  const [previousResponseId, setPreviousResponseId] = useState("");
  const [sessionNotes, setSessionNotes] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    fetch("/api/oac-demo")
      .then((response) => response.json())
      .then((payload) => {
        if (!active || !payload.ok) return;
        setForm((current) => ({
          ...current,
          prompt: payload.config.defaultPrompt || current.prompt,
          oacMcpUrl: payload.config.oacMcpUrl || current.oacMcpUrl,
          baseUrl: payload.config.baseUrl || current.baseUrl,
          projectId: payload.config.projectId || current.projectId,
          model: payload.config.model || current.model,
          region: payload.config.region || current.region,
        }));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const status = useMemo(
    () => computeStatus({ result, error, busy, previousResponseId }),
    [result, error, busy, previousResponseId]
  );

  function updateField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  function applyQuickPrompt(value) {
    updateField("prompt", value);
  }

  function clearSession() {
    setMessages([]);
    setPreviousResponseId("");
    setSessionNotes("");
    setResult(null);
    setError(null);
  }

  async function sendPrompt() {
    const prompt = form.prompt.trim();
    if (!prompt || busy) return;
    setBusy("chat");
    setError(null);
    setMessages((current) => [...current, { role: "user", content: prompt }]);

    try {
      const payload = await postOac({
        action: "chat",
        ...form,
        prompt,
        previousResponseId,
        sessionNotes,
        previousChart: result?.chart || null,
      });
      setResult(payload);
      setPreviousResponseId(payload.responseId || "");
      setSessionNotes(payload.sessionNotes || "");
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: payload.answer || "No final answer returned.",
          toolCalls: payload.toolCalls || [],
        },
      ]);
    } catch (requestError) {
      setError(requestError.message);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: `Request failed: ${requestError.message}`, error: true },
      ]);
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className={styles.shell}>
      <section className={styles.header}>
        <div className={styles.brand}>
          <div>
            <h1>OCI Enterprise AI Agents connected to an OAC MCP server</h1>
            <p>Any model works. The effort is the MCP connectivity and the backend, not the model.</p>
          </div>
        </div>
        <div className={styles.headerMeta}>
          <StatusPill tone={status.sessionTone} label={status.sessionLabel} />
          <StatusPill tone="blue" label="OAC MCP" />
          <label className={styles.modelPicker}>
            <Sparkles size={14} />
            <select
              value={form.model}
              onChange={(event) => updateField("model", event.target.value)}
              disabled={Boolean(busy)}
              aria-label="Model"
            >
              {MODEL_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className={styles.sessionButton}
            onClick={clearSession}
            disabled={Boolean(busy)}
          >
            <RefreshCcw size={14} />
            New Session
          </button>
        </div>
      </section>

      <section className={styles.grid}>
        <section className={styles.workspace}>
          <div className={styles.stageBar}>
            <StageItem icon={Search} label="Discover" status={status.discover} />
            <StageItem icon={Database} label="Describe" status={status.describe} />
            <StageItem icon={TerminalSquare} label="Logical SQL" status={status.sql} />
            <StageItem icon={BarChart3} label="Answer" status={status.answer} />
          </div>

          {error ? (
            <div className={styles.errorBox}>
              <XCircle size={18} />
              <span>{error}</span>
            </div>
          ) : null}

          <section className={styles.chatPanel}>
            <div className={styles.panelHeader}>
              <Sparkles size={18} />
              <h2>Analysis Session</h2>
              {previousResponseId ? <span className={styles.resultCount}>chained</span> : null}
            </div>

            <div className={styles.quickPrompts}>
              {quickPrompts.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => applyQuickPrompt(item.value)}
                  disabled={Boolean(busy)}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className={styles.messages}>
              {messages.length ? (
                messages.map((message, index) => (
                  <ChatMessage key={`${message.role}-${index}`} message={message} />
                ))
              ) : (
                <div className={styles.empty}>
                  Ask a business question. The assistant will discover the right OAC model,
                  describe only relevant metadata, execute read-only Logical SQL, and keep
                  the session chained for follow-ups.
                </div>
              )}
            </div>

            <div className={styles.composer}>
              <textarea
                value={form.prompt}
                onChange={(event) => updateField("prompt", event.target.value)}
                rows={4}
                placeholder="Ask an OAC business question..."
              />
              <button type="button" onClick={sendPrompt} disabled={Boolean(busy) || !form.prompt.trim()}>
                {busy === "chat" ? <Loader2 className={styles.spin} size={16} /> : <Play size={16} />}
                Run Analysis
              </button>
            </div>
          </section>

          <section className={styles.chartPanel}>
            <div className={styles.panelHeader}>
              <BarChart3 size={18} />
              <h2>Result Chart</h2>
            </div>
            {result?.chart ? (
              <ResultChart chart={result.chart} />
            ) : (
              <ChartEmpty result={result} />
            )}
          </section>

          <div className={styles.outputGrid}>
            <section className={styles.outputPanel}>
              <div className={styles.panelHeader}>
                <TerminalSquare size={18} />
                <h2>Logical SQL</h2>
              </div>
              <pre className={styles.codeBlock}>
                {result?.logicalSql?.length
                  ? maskSensitive(result.logicalSql.join("\n\n---\n\n"))
                  : "Logical SQL will appear after an executed analysis."}
              </pre>
            </section>

            <section className={styles.outputPanel}>
              <div className={styles.panelHeader}>
                <ShieldCheck size={18} />
                <h2>Tool Timeline</h2>
              </div>
              <ToolTimeline calls={result?.toolCalls || []} busy={busy === "chat"} />
            </section>
          </div>

        </section>
      </section>
    </main>
  );
}

async function postOac(payload) {
  const response = await fetch("/api/oac-demo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!data.ok) {
    throw new Error(data.error?.message || "Request failed");
  }
  return data;
}

function StatusPill({ label, tone }) {
  return <span className={`${styles.statusPill} ${styles[tone]}`}>{label}</span>;
}

function StageItem({ label, icon: Icon, status }) {
  const statusIcon =
    status === "done" ? <CheckCircle2 size={16} /> : status === "error" ? <XCircle size={16} /> : <Icon size={16} />;
  return (
    <div className={`${styles.stage} ${styles[status] || ""}`}>
      {statusIcon}
      <span>{label}</span>
    </div>
  );
}

function ChatMessage({ message }) {
  return (
    <article className={`${styles.message} ${styles[message.role]} ${message.error ? styles.messageError : ""}`}>
      <div className={styles.messageRole}>{message.role === "user" ? "You" : "OAC Analyst"}</div>
      <div className={styles.messageText}>
        {message.role === "assistant" ? (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{maskSensitive(message.content)}</ReactMarkdown>
        ) : (
          message.content
        )}
      </div>
      {message.toolCalls?.length ? (
        <div className={styles.messageTools}>
          {message.toolCalls.map((call, index) => (
            <span key={`${call.name || call.type}-${index}`}>{call.name || call.type}</span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function ToolTimeline({ calls, busy }) {
  if (busy) {
    return (
      <div className={styles.timelineEmpty}>
        <Loader2 className={styles.spin} size={18} />
        <span>Calling OAC MCP tools...</span>
      </div>
    );
  }
  if (!calls.length) {
    return <div className={styles.timelineEmpty}>No OAC tool calls yet.</div>;
  }
  return (
    <div className={styles.timeline}>
      {calls.map((call, index) => (
        <div key={`${call.name || call.type}-${index}`} className={styles.timelineItem}>
          <div className={styles.timelineDot} />
          <div>
            <strong>{call.name || call.type}</strong>
            <span>{call.status || "completed"}</span>
            {call.arguments ? <pre>{maskSensitive(formatToolOutput(call.arguments))}</pre> : null}
            {call.output || call.modelOutput ? (
              <pre>{maskSensitive(formatToolOutput(call.output || call.modelOutput))}</pre>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function formatToolOutput(value) {
  if (value == null) return "";
  const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  return text.length > 1800 ? `${text.slice(0, 1800)}\n...` : text;
}

// Display-only masking so demo recordings never show the dataset owner email,
// OCIDs, or similar identifiers that appear inside Logical SQL and tool output.
function maskSensitive(value) {
  if (value == null) return value;
  let text = typeof value === "string" ? value : String(value);
  text = text.replace(/XSA\('[^']*'\./g, "XSA('...'.");
  text = text.replace(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, "[hidden]");
  text = text.replace(/ocid1\.[a-z0-9._-]+/gi, "ocid1....");
  return text;
}

function ChartEmpty({ result }) {
  return <div className={styles.chartEmpty}>{chartEmptyMessage(result)}</div>;
}

function ResultChart({ chart }) {
  const data = Array.isArray(chart?.data) ? chart.data : [];
  const valueKeys = Array.isArray(chart?.valueKeys) ? chart.valueKeys : [];
  const categoryKey = chart?.categoryKey;
  if (!data.length || !valueKeys.length || !categoryKey) {
    return <div className={styles.timelineEmpty}>No plottable result rows returned.</div>;
  }
  const colors = ["#2f73ba", "#2f8f61", "#b46a12"];
  return (
    <div className={styles.chartWrap}>
      <ResponsiveContainer width="100%" height={320}>
        <ReBarChart data={data} margin={{ top: 8, right: 18, bottom: 36, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dfe5ec" />
          <XAxis
            dataKey={categoryKey}
            tick={{ fontSize: 11, fill: "#526171" }}
            tickFormatter={truncateTick}
            interval={0}
            angle={-18}
            textAnchor="end"
            height={64}
          />
          <YAxis tick={{ fontSize: 11, fill: "#526171" }} width={72} />
          <Tooltip
            formatter={(value, name) => [formatNumber(value), name]}
            labelFormatter={(label) => String(label)}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {valueKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              fill={colors[index % colors.length]}
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
            />
          ))}
        </ReBarChart>
      </ResponsiveContainer>
    </div>
  );
}

function chartEmptyMessage(result) {
  if (!result) {
    return "Run an analysis that returns at least one text/category column and one numeric measure.";
  }
  const calls = Array.isArray(result.toolCalls) ? result.toolCalls : [];
  const sqlCall = [...calls].reverse().find((call) => call.name === "execute_logical_sql");
  if (!sqlCall) {
    return "No chart yet because no Logical SQL result rows were returned.";
  }
  if (sqlCall.status === "failed") {
    return "No chart because the Logical SQL call failed before OAC returned rows.";
  }
  return "No chart because the SQL result did not include plottable numeric rows.";
}

function computeStatus({ result, error, busy, previousResponseId }) {
  if (error) {
    return {
      sessionTone: "red",
      sessionLabel: "Error",
      discover: "error",
      describe: "error",
      sql: "error",
      answer: "error",
    };
  }
  if (busy === "chat") {
    return {
      sessionTone: "blue",
      sessionLabel: previousResponseId ? "Continuing" : "Starting",
      discover: "running",
      describe: "idle",
      sql: "idle",
      answer: "idle",
    };
  }
  const toolNames = new Set((result?.toolCalls || []).map((call) => call.name));
  const sqlCall = (result?.toolCalls || []).find((call) => call.name === "execute_logical_sql");
  return {
    sessionTone: previousResponseId ? "green" : "amber",
    sessionLabel: previousResponseId ? "Persistent session" : "New session",
    discover: toolNames.has("discover_data") ? "done" : "idle",
    describe: toolNames.has("describe_data") ? "done" : "idle",
    sql: sqlCall?.status === "failed" ? "error" : result?.logicalSql?.length || sqlCall ? "done" : "idle",
    answer: result?.answer ? "done" : "idle",
  };
}

function truncateTick(value) {
  const text = String(value ?? "");
  return text.length > 18 ? `${text.slice(0, 17)}...` : text;
}

function formatNumber(value) {
  if (typeof value !== "number") return value;
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(value);
}
