"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CalendarDays } from "lucide-react";
import type { CatalogTest, Patient } from "@/lib/types";
import { sar } from "@/lib/types";
import type { Lang, Strings } from "@/lib/i18n";

export function VisitsPanel({ patient, catalog, lang, s }: { patient: Patient | null; catalog: CatalogTest[]; lang: Lang; s: Strings }) {
  if (!patient) return <div className="empty-board"><CalendarDays className="size-10" strokeWidth={1.4}/><p>{s.selectPatient}</p></div>;
  const index = Object.fromEntries(catalog.map(t => [t.code, t]));
  const name = (code: string) => (lang === "ar" ? index[code]?.name_ar : index[code]?.name) ?? code;
  const series = patient.visits.reduce<{ date: string; saved: number; spent: number }[]>((acc, v) => [...acc, { date: v.date.slice(2), saved: (acc.at(-1)?.saved ?? 0) + v.saved, spent: v.cost }], []);
  return <div>
    <p className="eyebrow">{lang === "ar" ? "الزيارات" : "VISIT HISTORY"}</p>
    <div className="board-title"><h2>{lang === "ar" ? patient.name_ar : patient.name}</h2><span>{patient.visits.length} {s.visits.toLowerCase()}</span></div>
    <div className="tiles">
      <div className="tile"><span>{s.visits}</span><strong>{patient.visits.length}</strong></div>
      <div className="tile"><span>{s.spentToDate}</span><strong>{sar(patient.spent_total)}</strong></div>
      <div className="tile accent"><span>{s.savedToDate}</span><strong>{sar(patient.saved_total)}</strong></div>
    </div>
    {series.length > 1 && <div className="chart-card"><h3>{s.cumulative}</h3><div className="h-36 w-full min-w-0"><ResponsiveContainer width="100%" height="100%">
      <AreaChart data={series} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs><linearGradient id="visits-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="var(--mint)" stopOpacity=".45"/><stop offset="1" stopColor="var(--mint)" stopOpacity=".02"/></linearGradient></defs>
        <CartesianGrid stroke="var(--border)" vertical={false} strokeDasharray="3 3"/>
        <XAxis dataKey="date" tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} tickLine={false} axisLine={false}/>
        <YAxis width={44} tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} tickLine={false} axisLine={false}/>
        <Tooltip contentStyle={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, fontSize: 12 }} formatter={(value) => sar(Number(value))}/>
        <Area type="monotone" dataKey="saved" stroke="var(--mint)" strokeWidth={2.5} fill="url(#visits-fill)" dot={{ r: 3, fill: "var(--mint)", strokeWidth: 0 }}/>
      </AreaChart>
    </ResponsiveContainer></div></div>}
    <div className="record-section" style={{ marginTop: 14 }}><h3>{s.visitHistory}</h3>
      {patient.visits.length === 0 && <div className="empty-board" style={{ padding: "24px 12px" }}><CalendarDays className="size-8" strokeWidth={1.4}/><p>{s.noVisits}</p></div>}
      {[...patient.visits].reverse().map((v, i) => <div key={`${v.date}-${i}`} className="visit-card">
        <div className="visit-date">{v.date}</div>
        <div className="visit-reason">{v.reason}</div>
        <p className="visit-summary">{v.summary}</p>
        <div className="visit-chips">{v.ordered.map(c => <span key={c} className="pill pill-needed">{name(c)}</span>)}{v.skipped.map(c => <span key={c} className="pill pill-redundant" style={{ textDecoration: "line-through" }}>{name(c)}</span>)}</div>
        <div className="visit-money"><span>{s.spentToDate.split(" ")[0]} <strong>{sar(v.cost)}</strong></span>{v.saved > 0 && <span className="saved">{s.saved} <strong className="saved">{sar(v.saved)}</strong></span>}</div>
      </div>)}
    </div>
  </div>;
}
