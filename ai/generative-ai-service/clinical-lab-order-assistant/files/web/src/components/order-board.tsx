"use client";

import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Area, AreaChart, CartesianGrid } from "recharts";
import { Check, ClipboardList, FlaskConical, ShieldCheck, TimerReset } from "lucide-react";
import type { Decision, Evaluation, Patient, VisitReceipt } from "@/lib/types";
import { sar } from "@/lib/types";
import type { Lang, Strings } from "@/lib/i18n";

const statusIcon = { needed: FlaskConical, redundant: ShieldCheck, expiring: TimerReset } as const;
const tooltipStyle = { background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, color: "var(--foreground)", fontSize: 12 };

function validityFraction(d: Decision) {
  if (d.validity_days == null || d.days_remaining == null) return d.status === "needed" ? 0 : 1;
  return Math.max(0, Math.min(1, d.days_remaining / d.validity_days));
}

export function OrderBoard({ evaluation, receipt, patient, lang, s }: { evaluation?: Evaluation; receipt?: VisitReceipt; patient: Patient | null; lang: Lang; s: Strings }) {
  if (receipt) return <Receipt receipt={receipt} patient={patient} s={s}/>;
  if (!evaluation) return <div className="empty-board"><ClipboardList className="size-10" strokeWidth={1.4}/><p>{s.awaitingOrder}</p></div>;
  const t = evaluation.totals;
  const savingPct = t.requested_sar ? Math.round((t.potential_saving_sar / t.requested_sar) * 100) : 0;
  const chartData = [
    { name: s.requested, needed: t.needed_sar, expiring: t.expiring_sar, redundant: t.redundant_sar },
    { name: s.recommended, needed: t.needed_sar, expiring: 0, redundant: 0 },
  ];
  return <div>
    <p className="eyebrow">{lang === "ar" ? "تقييم الطلب" : "ORDER EVALUATION"}</p>
    <div className="board-title"><h2>{evaluation.patient}</h2><span>{evaluation.visit_date}</span></div>
    <div className="tiles">
      <div className="tile"><span>{s.requested}</span><strong>{sar(t.requested_sar)}</strong><small>{t.requested_count} {s.tests}</small></div>
      <div className="tile"><span>{s.recommended}</span><strong>{sar(t.recommended_sar)}</strong><small>{t.needed_count} {s.tests}</small></div>
      <div className="tile accent"><span>{s.avoidable}</span><strong>{sar(t.potential_saving_sar)}</strong><small>{savingPct}% · {t.redundant_count + t.expiring_count} {s.tests}</small></div>
    </div>
    <div className="chart-card">
      <h3>{lang === "ar" ? "التكلفة حسب الحالة" : "Cost by status"}<span className="chart-legend"><span><i style={{ background: "var(--chart-1)" }}/>{s.needed}</span><span><i style={{ background: "var(--amber)" }}/>{s.expiring}</span><span><i style={{ background: "var(--mint)" }}/>{s.redundant}</span></span></h3>
      <div className="h-28 w-full min-w-0"><ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 12, bottom: 0, left: 0 }} barCategoryGap={10}>
          <XAxis type="number" hide/>
          <YAxis type="category" dataKey="name" width={98} tick={{ fill: "var(--muted-foreground)", fontSize: 11 }} tickLine={false} axisLine={false}/>
          <Tooltip contentStyle={tooltipStyle} formatter={(value) => sar(Number(value))} cursor={{ fill: "var(--muted)" }}/>
          <Bar dataKey="needed" stackId="a" fill="var(--chart-1)" radius={[8, 0, 0, 8]} maxBarSize={26}/>
          <Bar dataKey="expiring" stackId="a" fill="var(--amber)" maxBarSize={26}/>
          <Bar dataKey="redundant" stackId="a" fill="var(--mint)" radius={[0, 8, 8, 0]} maxBarSize={26}/>
        </BarChart>
      </ResponsiveContainer></div>
    </div>
    <div className="decision-list">
      {evaluation.decisions.map(d => { const Icon = statusIcon[d.status]; return <div key={d.code} className="decision" data-status={d.status}>
        <div className="decision-icon"><Icon className="size-4"/></div>
        <div className="decision-main">
          <div className="decision-name">{lang === "ar" ? d.name_ar : d.name}<span className={`pill pill-${d.status}`}>{s[d.status]}</span></div>
          <div className="decision-sub">{d.last_date ? <>{s.lastResult} {d.last_date}{d.last_value ? ` · ${d.last_value}` : ""}{d.valid_until ? ` · ${s.validUntil} ${d.valid_until}` : ""}</> : s.noPrior}</div>
          <div className="validity" aria-hidden="true"><i style={{ width: `${validityFraction(d) * 100}%` }}/></div>
        </div>
        <div className={`decision-price${d.status === "redundant" ? " struck" : ""}`}>{sar(d.price_sar)}</div>
      </div>; })}
    </div>
    {evaluation.unknown.length > 0 && <p className="policy-note">{lang === "ar" ? "غير موجود في الكتالوج:" : "Not in the catalog:"} {evaluation.unknown.join(", ")}</p>}
    <p className="policy-note">{s.policyNote} {s.reviewNote}</p>
  </div>;
}

function Receipt({ receipt, patient, s }: { receipt: VisitReceipt; patient: Patient | null; s: Strings }) {
  const visits = patient?.visits ?? [];
  const series = visits.reduce<{ date: string; saved: number }[]>((acc, v) => [...acc, { date: v.date.slice(2), saved: (acc.at(-1)?.saved ?? 0) + v.saved }], []);
  return <div>
    <div className="receipt">
      <div className="receipt-head"><div className="receipt-check"><Check className="size-5"/></div><div><strong>{s.orderPlaced}</strong><span>{receipt.visit.date} · {receipt.visit.reason}</span></div></div>
      {receipt.ordered.length > 0 && <div className="receipt-group"><h4>{s.needed}</h4><ul>{receipt.ordered.map(t => <li key={t.code}><span>{t.name}</span><span>{sar(t.price_sar)}</span></li>)}</ul></div>}
      {receipt.skipped.length > 0 && <div className="receipt-group"><h4>{s.skipped}</h4><ul>{receipt.skipped.map(t => <li key={t.code} className="struck"><span>{t.name}</span><span>− {sar(t.price_sar)}</span></li>)}</ul></div>}
      <div className="receipt-total"><span>{s.savedThisVisit}</span><span style={{ color: "var(--ok)" }}>{sar(receipt.visit.saved)}</span></div>
    </div>
    <div className="tiles" style={{ marginTop: 12 }}>
      <div className="tile"><span>{s.spentToDate}</span><strong>{sar(receipt.spent_total_sar)}</strong><small>{receipt.visit_count} {s.visits.toLowerCase()}</small></div>
      <div className="tile accent" style={{ gridColumn: "span 2" }}><span>{s.savedToDate}</span><strong>{sar(receipt.saved_total_sar)}</strong><small>{receipt.patient}</small></div>
    </div>
    {series.length > 1 && <div className="chart-card"><h3>{s.cumulative}</h3><div className="h-36 w-full min-w-0"><ResponsiveContainer width="100%" height="100%">
      <AreaChart data={series} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs><linearGradient id="savings-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--mint)" stopOpacity=".45"/><stop offset="1" stopColor="var(--mint)" stopOpacity=".02"/></linearGradient></defs>
        <CartesianGrid stroke="var(--border)" vertical={false} strokeDasharray="3 3"/>
        <XAxis dataKey="date" tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} tickLine={false} axisLine={false}/>
        <YAxis width={44} tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} tickLine={false} axisLine={false}/>
        <Tooltip contentStyle={tooltipStyle} formatter={(value) => sar(Number(value))}/>
        <Area type="monotone" dataKey="saved" stroke="var(--mint)" strokeWidth={2.5} fill="url(#savings-fill)" dot={{ r: 3, fill: "var(--mint)", strokeWidth: 0 }}/>
      </AreaChart>
    </ResponsiveContainer></div></div>}
    <p className="policy-note">{s.reviewNote}</p>
  </div>;
}
