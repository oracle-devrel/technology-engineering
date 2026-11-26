"use client";

import { Activity, Pill, ShieldAlert, Stethoscope } from "lucide-react";
import type { CatalogTest, LabResult, Patient } from "@/lib/types";
import { daysBetween } from "@/lib/types";
import type { Lang, Strings } from "@/lib/i18n";

function validity(result: LabResult, test: CatalogTest | undefined) {
  if (!test) return { status: "needed" as const, fraction: 0, label: "" };
  if (test.validity_days == null) return { status: "redundant" as const, fraction: 1, label: "∞" };
  const age = daysBetween(result.date, new Date());
  const remaining = test.validity_days - age;
  const status = remaining <= 0 ? "needed" : remaining <= 14 ? "expiring" : "redundant";
  return { status, fraction: Math.max(0, Math.min(1, remaining / test.validity_days)), label: remaining > 0 ? `${remaining} d` : `${-remaining} d ago` };
}

export function RecordPanel({ patient, catalog, lang, s }: { patient: Patient | null; catalog: CatalogTest[]; lang: Lang; s: Strings }) {
  if (!patient) return <div className="empty-board"><Stethoscope className="size-10" strokeWidth={1.4}/><p>{s.selectPatient}</p></div>;
  const index = Object.fromEntries(catalog.map(t => [t.code, t]));
  const latest = new Map<string, { result: LabResult; older: number }>();
  for (const r of patient.results) { const cur = latest.get(r.code); if (!cur) latest.set(r.code, { result: r, older: 0 }); else cur.older += 1; }
  const rows = Array.from(latest.values()).sort((a, b) => b.result.date.localeCompare(a.result.date));
  return <div>
    <p className="eyebrow">{lang === "ar" ? "سجل المريض" : "PATIENT RECORD"}</p>
    <div className="board-title"><h2>{lang === "ar" ? patient.name_ar : patient.name}</h2><span>{patient.mrn}</span></div>
    <div className="record-section"><div className="profile-grid">
      <div className="profile-card"><span><Stethoscope className="inline size-3 me-1"/>{s.conditions}</span><div>{patient.conditions.length ? patient.conditions.map(c => <span key={c} className="chip">{c}</span>) : <span className="chip">{s.none}</span>}</div></div>
      <div className="profile-card"><span><ShieldAlert className="inline size-3 me-1"/>{s.allergies}</span><div>{patient.allergies.length ? patient.allergies.map(c => <span key={c} className="chip" style={{ background: "var(--warn-bg)", color: "var(--warn)" }}>{c}</span>) : <span className="chip">{s.none}</span>}</div></div>
      <div className="profile-card" style={{ gridColumn: "1 / -1" }}><span><Pill className="inline size-3 me-1"/>{s.medications}</span><div>{patient.medications.length ? patient.medications.map(c => <span key={c} className="chip">{c}</span>) : <span className="chip">{s.none}</span>}</div></div>
    </div></div>
    <div className="record-section"><h3>{s.results} · {rows.length}</h3>
      {rows.length === 0 && <div className="empty-board" style={{ padding: "24px 12px" }}><Activity className="size-8" strokeWidth={1.4}/><p>{s.noVisits}</p></div>}
      <div className="decision-list" style={{ marginTop: 0 }}>{rows.map(({ result, older }) => { const test = index[result.code]; const v = validity(result, test); return <div key={result.code} className="decision" data-status={v.status}>
        <div className="decision-icon"><Activity className="size-4"/></div>
        <div className="decision-main">
          <div className="decision-name">{test ? (lang === "ar" ? test.name_ar : test.name) : result.code}{older > 0 && <span className="chip">+{older}</span>}</div>
          <div className="decision-sub">{result.date} · {result.value}<br/>{result.source}</div>
          <div className="validity" aria-hidden="true"><i style={{ width: `${v.fraction * 100}%` }}/></div>
        </div>
        <div className="decision-price" style={{ fontFamily: "var(--font-mono-base)", fontSize: 11, color: "var(--muted-foreground)" }}>{v.label}</div>
      </div>; })}</div>
    </div>
  </div>;
}
