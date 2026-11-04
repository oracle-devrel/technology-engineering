export const reasoningEfforts = ["none", "low", "medium", "xhigh"] as const;
export type ReasoningEffort = (typeof reasoningEfforts)[number];
export const defaultReasoningEffort: ReasoningEffort = "low";
export const reasoningLabels: Record<ReasoningEffort, string> = { none: "Off", low: "Low", medium: "Medium", xhigh: "Extra high" };
export const reasoningDescriptions: Record<ReasoningEffort, string> = { none: "Direct answers, no thinking", low: "Light reasoning · default", medium: "More room to weigh exceptions", xhigh: "Most extensive reasoning" };
