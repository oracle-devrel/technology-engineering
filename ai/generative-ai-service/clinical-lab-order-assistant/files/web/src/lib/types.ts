export type CatalogTest = { code: string; name: string; name_ar: string; category: string; validity_days: number | null; price_sar: number; aliases?: string[] };
export type LabResult = { code: string; value: string; date: string; source: string };
export type Visit = { date: string; reason: string; summary: string; ordered: string[]; skipped: string[]; full_cost: number; cost: number; saved: number };
export type PatientSummary = { mrn: string; name: string; name_ar: string; sex: "M" | "F"; age: number; conditions: string[]; last_visit: string | null; visit_count: number; result_count: number; saved_total: number };
export type Patient = PatientSummary & { allergies: string[]; medications: string[]; results: LabResult[]; visits: Visit[]; spent_total: number };
export type DecisionStatus = "needed" | "redundant" | "expiring";
export type Decision = { code: string; name: string; name_ar: string; category: string; price_sar: number; validity_days: number | null; last_date: string | null; last_value: string | null; last_source: string | null; valid_until: string | null; days_remaining: number | null; status: DecisionStatus; reason: string };
export type Evaluation = { kind: "evaluation"; mrn: string; patient: string; visit_date: string; decisions: Decision[]; unknown: string[]; policy_note: string; totals: { requested_sar: number; needed_sar: number; redundant_sar: number; expiring_sar: number; recommended_sar: number; potential_saving_sar: number; requested_count: number; needed_count: number; redundant_count: number; expiring_count: number } };
export type VisitReceipt = { kind: "visit"; mrn: string; patient: string; visit: Visit; ordered: { code: string; name: string; price_sar: number }[]; skipped: { code: string; name: string; price_sar: number }[]; saved_total_sar: number; spent_total_sar: number; visit_count: number };
export type ImportOutcome = { kind: "import"; mrn: string; added: { code: string; name: string; value: string; date: string; source: string }[]; skipped_duplicates: number };
export type Artifact = Evaluation | VisitReceipt | ImportOutcome;
export type Health = { gateway: string; region?: string; endpoint?: boolean; patients?: number; tests?: number };

export const sar = (value: number) => `${value.toLocaleString("en-US")} SAR`;
export const daysBetween = (from: string, to: Date) => Math.round((to.getTime() - new Date(from).getTime()) / 86400000);
