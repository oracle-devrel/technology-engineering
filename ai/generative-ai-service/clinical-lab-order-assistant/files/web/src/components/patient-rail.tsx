"use client";

import { RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Health, PatientSummary } from "@/lib/types";
import type { Lang, Strings } from "@/lib/i18n";
import { avatarClass, initials } from "./logo";

export function PatientRail({ patients, mrn, onSelect, lang, s, health, onReset, busy }: {
  patients: PatientSummary[]; mrn: string | null; onSelect: (mrn: string) => void; lang: Lang; s: Strings; health: Health; onReset: () => void; busy: boolean;
}) {
  return <aside className="rail" aria-label={s.patients}>
    <div className="rail-header"><span>{s.patients}</span><span>{patients.length}</span></div>
    <div className="patient-list">
      {patients.map(p => <button key={p.mrn} className={cn("patient-card", mrn === p.mrn && "active")} onClick={() => onSelect(p.mrn)} aria-current={mrn === p.mrn ? "true" : undefined}>
        <span className={avatarClass(p.mrn)}>{initials(p.name)}</span>
        <span className="patient-meta">
          <span className="patient-name">{lang === "ar" ? p.name_ar : p.name}</span>
          <span className="patient-sub"><small>{p.mrn}</small> · {p.age}{p.sex} · {p.last_visit ? p.last_visit : s.firstVisit}</span>
          <span className="patient-chips">
            {p.conditions.slice(0, 2).map(c => <span key={c} className="chip">{c}</span>)}
            {p.saved_total > 0 ? <span className="chip chip-saving">{p.saved_total.toLocaleString()} SAR {s.saved}</span> : <span className="chip chip-new">{p.visit_count ? `${p.result_count} ${s.tests}` : s.firstVisit}</span>}
          </span>
        </span>
      </button>)}
    </div>
    <div className="rail-footer">
      <span className={cn("status-dot", health.gateway !== "ready" && "offline")}/>
      <span>{health.gateway === "ready" ? s.gatewayReady : health.gateway === "checking" ? s.connecting : s.gatewayOffline}</span>
      <Button variant="ghost" size="icon-sm" aria-label={s.resetDemo} title={s.resetDemo} disabled={busy} onClick={onReset}><RotateCcw className="size-3.5"/></Button>
    </div>
  </aside>;
}
