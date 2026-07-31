# Contract Comparison Sample Case

Two fictional managed-services contracts offered to the same client (Meridian Logistics
Group PLC) for the same scope: managed IT infrastructure and cloud operations for a
430-server hybrid estate. Designed to showcase the Planner → Section Writer → Report
Writer pipeline on a multi-entity comparison with chartable numeric differences.

- `NorthBridge_MSA.pdf` — NorthBridge Digital Services Ltd (premium: shorter term, strict
  SLAs, client-friendly risk terms, higher price).
- `Velocita_MSA.pdf` — Velocita Cloud Solutions S.A. (cheaper: long lock-in, weaker SLAs,
  vendor-friendly risk terms). Deliberately drafted in a different house style
  (Articles/Annexes vs Clauses/Schedules) so clause numbering does not align 1:1.

All companies, people and figures are fictitious.

## Ingestion

Plain-text PDFs (8 pages each, ~5,000 words, 5 tables). No XLSX handling needed and chunk
rewriting is optional — standard PDF ingestion is sufficient.

**Document Processing tab.** Upload each PDF; the Entity field auto-suggests up to three
name variants from the filename — pick one (or type your own), then Process:

- `NorthBridge_MSA.pdf` → suggested `NorthBridge`; for this showcase choose
  **`NorthBridge Digital Services`** (type it — it reads better in the report).
- `Velocita_MSA.pdf` → suggested `Velocita`; choose **`Velocita Cloud Solutions`**.

The entity name is the join key between ingestion and retrieval — it is stored as
`entity.strip().lower()` and retrieval filters on it with an exact match. It does **not**
need to be the legal name; it only needs to be the same string you select at query time.

**Inference & Query tab.** "Include PDF" is on by default, and ingesting a PDF auto-ticks
it. Use the **Entities to compare** picker — it is populated from the tags actually in the
store (hit ↻ Refresh after ingesting), so any selection is guaranteed to match retrieval.
Select **NorthBridge Digital Services** and **Velocita Cloud Solutions**, then Run. Leaving
the picker empty falls back to non-deterministic LLM extraction from the prompt (works, but
can vary by model — prefer explicit selection when testing across models).

If you re-ingest under a different entity name, the old chunks remain (replacement keys on
entity+filename); delete the PDF collection first in the Vector Store Viewer tab to avoid
stale tags cluttering the picker.

## Ground-truth key (for grading generated reports)

| Term | NorthBridge (clause) | Velocita (article) |
|---|---|---|
| Initial term | 36 months (4.1) | 60 months (2.1) |
| Auto-renewal / notice | 12 mo / 90 days (4.2) | 24 mo / 180 days (2.2) |
| Monthly fee | USD 184,500, arrears (5.1) | USD 151,200, quarterly in advance (6.1) |
| Transition/onboarding | USD 95,000 (3.2) | USD 250,000 "waived", amortised 36 mo, unamortised due on exit (5.2) |
| Indexation from Year 2 | CPI capped 4% (6.1) | 5% fixed + up to 3% offshore (7.1–7.2) |
| Payment / late interest | Net 30 / 1.5% mo (5.3–5.4) | Net 45 / 1.0% mo, pay-first-dispute-later (6.2–6.3) |
| Minimum commitment | none (volume discount 5% >500 inst., 5.2) | USD 1.6M per Contract Year (6.4) + exclusivity (3.1) |
| Availability | 99.95% (7.1) | 99.80% (8.1) |
| P1 response / restore | 15 min / 4 h @95% (7.2, SL-02/03) | 30 min / 8 h @90% (8.2, KPI-2/3) |
| Critical patching | 14 days, 72 h if exploited (11.5) | 30 days (13.5) |
| Service credit cap / regime | 10%, no earn-back, credits not exclusive (7.3–7.4) | 20%, 50% earn-back, sole & exclusive remedy (8.3–8.4) |
| RTO / RPO (Tier 1) | 4 h / 15 min, contractual, 2 DR tests/yr (12.1–12.2) | 24 h / 4 h, targets only, 1 test/yr, extra USD 12k (14.2–14.3) |
| Breach notification | 24 h (11.3) | 72 h (13.3) |
| SOC 2 Type II | committed annually (11.2) | best-efforts, "if and when produced" (13.2) |
| Offshore limit | 40% UK/EEA-only privileged access (9.3) | up to 70% Pune (11.1) |
| Liability cap | 12 months' fees ≈ USD 2.214M per year; 3x for data/confidentiality (17.2–17.3) | USD 1.5M whole-of-term, data breach inside cap, loss of data excluded (19.2–19.3) |
| Insurance (cyber/PI/CGL) | 10M / 10M / 5M (18.1) | 5M / 5M / 2M (20.1) |
| Convenience termination | after mo 12, 90 days, 3 months' fee, zero after mo 30 (19.1) | after mo 36, 180 days, 50% of remaining term + unamortised onboarding (21.2); vendor may exit on 120 days (21.3) |
| Exit assistance | 180 days at rate card, no uplift, SLAs apply (20.1, 20.3) | 90 days at +15%, min 160 h, SLAs suspended, data export gated on payment (22.1–22.4) |
| IP in deliverables | client owns (13.1) | vendor retains; licence dies at exit unless USD 75k fee (15.1–15.3) |
| Confidentiality survival | 3 years (14.2) | 5 years (16.2) |
| Governance / reporting | monthly review, report in 5 BD (8.1–8.2) | quarterly review, report in 10 BD (10.1–10.2) |
| Key personnel | 30 days + client approval (9.2) | 60 days, no approval right (11.2) |
| Audit | annual, 10 BD notice (22.1) | every 24 mo, 30 days notice, client cost, 2-day cap (24.1) |
| Benchmarking | yes, adjustment if >7.5% over median (6.2–6.3) | none |
| Force majeure | subcontractor failure excluded (21.1) | subcontractor/cloud-provider failure included (23.1) |
| Non-solicitation | 12 months (23.1) | 24 months + 50% salary liquidated damages (25.1) |
| Law / forum | England & Wales, London courts (24.1, 24.3) | Switzerland, ICC arbitration Geneva, 3 arbitrators (26.1–26.2) |

Worked-example checks the report should get right:
- NorthBridge annual liability cap ≈ 12 × 184,500 = USD 2,214,000 (vs Velocita 1.5M for the whole 60-month term).
- Termination at month 40: NorthBridge fee = USD 0 (after month 30); Velocita ≈ 50% × 20 remaining months × indexed fee, plus nothing for onboarding (fully amortised) — roughly USD 1.6M+.
- 36-month base-fee TCO at CPI-at-cap: NorthBridge ≈ 184.5k×12 + 191.9k×12 + 199.6k×12 + 95k transition ≈ USD 7.0M; Velocita ≈ 151.2k×12 + 158.8k×12 + 166.7k×12 ≈ USD 5.7M (before the exit penalties that make leaving at month 36 impossible for free).
