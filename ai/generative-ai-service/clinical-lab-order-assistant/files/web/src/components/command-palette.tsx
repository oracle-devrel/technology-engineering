"use client";

import { useEffect } from "react";
import { Brain, Globe2, Moon, PanelRight, Plus, RotateCcw, UserRound } from "lucide-react";
import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator } from "@/components/ui/command";
import { reasoningDescriptions, reasoningEfforts, reasoningLabels, type ReasoningEffort } from "@/lib/reasoning";
import type { PatientSummary } from "@/lib/types";

export function CommandPalette({ open, onOpenChange, patients, mrn, onSelectPatient, effort, onEffortChange, onNewConsult, onToggleBoard, onToggleTheme, onToggleLanguage, onReset, busy }: {
  open: boolean; onOpenChange: (open: boolean) => void; patients: PatientSummary[]; mrn: string | null; onSelectPatient: (mrn: string) => void;
  effort: ReasoningEffort; onEffortChange: (effort: ReasoningEffort) => void; onNewConsult: () => void; onToggleBoard: () => void; onToggleTheme: () => void; onToggleLanguage: () => void; onReset: () => void; busy: boolean;
}) {
  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey) && !event.isComposing && !event.repeat) { event.preventDefault(); onOpenChange(!open); }
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onOpenChange]);
  const run = (action: () => void) => { onOpenChange(false); action(); };

  return <CommandDialog open={open} onOpenChange={onOpenChange} title="LabSense commands" description="Switch patient, choose thinking effort, or run an action." className="lab-command-dialog" showCloseButton={false}>
    <Command loop>
      <CommandInput placeholder="Patient, setting or action…" aria-label="Search commands"/>
      <CommandList>
        <CommandEmpty>No commands found.</CommandEmpty>
        <CommandGroup heading="Patients">
          {patients.map(p => <CommandItem key={p.mrn} value={`Patient ${p.name} ${p.mrn}`} keywords={[p.name_ar, ...p.conditions]} data-checked={mrn === p.mrn} onSelect={() => run(() => onSelectPatient(p.mrn))}><UserRound/><span className="flex min-w-0 flex-col gap-0.5"><span>{p.name}</span><span className="text-xs text-muted-foreground">{p.mrn} · {p.conditions.join(", ") || "No chronic conditions"}</span></span></CommandItem>)}
        </CommandGroup>
        <CommandSeparator/>
        <CommandGroup heading="Thinking effort · applies to the next request">
          {reasoningEfforts.map(value => <CommandItem key={value} value={`Thinking ${reasoningLabels[value]}`} keywords={["reasoning", "effort", value]} data-checked={effort === value} onSelect={() => run(() => onEffortChange(value))}><Brain/><span className="flex min-w-0 flex-col gap-0.5"><span>Thinking: {reasoningLabels[value]}</span><span className="text-xs text-muted-foreground">{reasoningDescriptions[value]}</span></span></CommandItem>)}
        </CommandGroup>
        <CommandSeparator/>
        <CommandGroup heading="Actions">
          <CommandItem value="New consult clear conversation" onSelect={() => run(onNewConsult)}><Plus/>New consult for this patient</CommandItem>
          <CommandItem value="Toggle order board" onSelect={() => run(onToggleBoard)}><PanelRight/>Toggle order board</CommandItem>
          <CommandItem value="Toggle color theme dark light" onSelect={() => run(onToggleTheme)}><Moon/>Toggle color theme</CommandItem>
          <CommandItem value="Toggle language Arabic English" keywords={["العربية"]} onSelect={() => run(onToggleLanguage)}><Globe2/>Switch Arabic / English</CommandItem>
          <CommandItem value="Reset demo data" onSelect={() => run(onReset)}><RotateCcw/>Reset demo data</CommandItem>
        </CommandGroup>
      </CommandList>
      <div className="flex items-center justify-between gap-3 border-t px-3 py-2 text-xs text-muted-foreground"><span>{busy ? "Current answer keeps its effort" : `Thinking: ${reasoningLabels[effort]}`}</span><span>↑↓ Navigate · ↵ Select · Esc Close</span></div>
    </Command>
  </CommandDialog>;
}
