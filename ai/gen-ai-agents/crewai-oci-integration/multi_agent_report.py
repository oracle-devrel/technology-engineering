"""
Multi-agent report builder with CrewAI + LiteLLM (OCI)
- Planner -> generates outline
- Multiple Section Writers -> draft each section
- Synthesizer -> compiles final report

Run:
  python multi_agent_report.py "Subject to analyze"
"""

import os
import sys
from typing import List
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM

# --- Disable CrewAI phone-home/logs in locked-down environments ---
os.environ["CREWAI_LOGGING_ENABLED"] = "false"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# Make Instructor/OpenAI client use your LiteLLM proxy
os.environ.setdefault("OPENAI_API_KEY", "sk-local-any")
os.environ.setdefault("OPENAI_BASE_URL", "http://localhost:4000/v1")


# =========================
# LLM CONFIG (LiteLLM proxy)
# =========================
def make_llm():
    print("\n=== CONFIGURING LLM ===")
    return LLM(
        model="grok4-fast-oci",  # your LiteLLM model alias
        base_url="http://localhost:4000/v1",  # LiteLLM proxy endpoint
        api_key="sk-local-any",
        temperature=0.2,
        max_tokens=4000,
    )


# =========================
# STRUCTURED OUTPUT MODELS
# =========================
class Outline(BaseModel):
    subject: str
    title: str
    sections: List[str] = Field(..., description="Ordered list of section titles")


class SectionDraft(BaseModel):
    section_title: str
    key_points: List[str]
    content: str


class FinalReport(BaseModel):
    subject: str
    outline: Outline
    executive_summary: str
    sections: List[SectionDraft]


# =========================
# AGENTS
# =========================
def make_planner(llm: LLM) -> Agent:
    print("=== DEFINING PLANNER AGENT ===")
    return Agent(
        role="Planner",
        goal="Create a clear, logically ordered outline for a technical report.",
        backstory=(
            "A senior analyst with strong information architecture skills. "
            "Produces pragmatic outlines tailored to enterprise readers."
        ),
        llm=llm,
        allow_delegation=False,
    )


def make_section_writer(llm: LLM) -> Agent:
    print("=== DEFINING SECTION WRITER AGENT ===")
    return Agent(
        role="Section Writer",
        goal="Write concise, well-structured sections from an outline.",
        backstory=(
            "A staff technical writer focused on clarity, correctness, and actionable insights. "
            "Avoids fluff and repetition; uses bullet points where helpful."
        ),
        llm=llm,
        allow_delegation=False,
    )


def make_synthesizer(llm: LLM) -> Agent:
    print("=== DEFINING SYNTHESIZER AGENT ===")
    return Agent(
        role="Report Synthesizer",
        goal="Assemble a coherent, polished report from multiple section drafts.",
        backstory=(
            "An editor who specializes in executive summaries and narrative cohesion. "
            "Ensures consistency of tone, terminology, and depth across sections."
        ),
        llm=llm,
        allow_delegation=False,
    )


# =========================
# SINGLE-TASK CREWS HELPERS
# (We run 3 stages: plan -> write -> synthesize)
# =========================
def run_planner(subject: str, llm: LLM) -> Outline:
    planner = make_planner(llm)

    print("=== DEFINING PLANNER TASK ===")
    plan_task = Task(
        description=(
            "Create a structured outline for a technical report on the subject:\n"
            f"SUBJECT: {subject}\n\n"
            "Constraints:\n"
            "- Audience: enterprise architects / AI platform owners.\n"
            "- Depth: practical and decision-oriented.\n"
            "- Include 5–8 sections, ordered logically.\n"
            "- Title should be short and informative.\n"
            "Return ONLY a valid JSON object matching the schema.\n"
        ),
        expected_output=(
            "A JSON object with: 'subject', 'title', and 'sections' (array of section titles)."
        ),
        agent=planner,
        output_pydantic=Outline,
    )

    print("=== RUNNING PLANNER CREW ===")
    crew = Crew(agents=[planner], tasks=[plan_task])
    _ = crew.kickoff()

    outline = plan_task.output.pydantic  # type: ignore
    if not outline or not outline.sections:
        raise RuntimeError("Planner produced no sections. Check LLM config or prompts.")
    return outline


def run_section_writers(outline: Outline, llm: LLM) -> List[SectionDraft]:
    writer = make_section_writer(llm)

    section_tasks: List[Task] = []
    print("=== DEFINING SECTION TASKS ===")
    for idx, section in enumerate(outline.sections, start=1):
        t = Task(
            description=(
                f"Write the section #{idx} titled '{section}' for a report titled '{outline.title}' "
                f"on the subject '{outline.subject}'.\n\n"
                "Deliverables:\n"
                "- 4–7 key bullet points (actionable and non-redundant).\n"
                "- A concise section narrative (120–250 words), no marketing fluff.\n"
                "- Avoid repeating content from other sections.\n"
                "Return ONLY a valid JSON object matching the schema.\n"
            ),
            expected_output=(
                "A JSON object with 'section_title', 'key_points' (array of strings), and 'content' (string)."
            ),
            agent=writer,
            output_pydantic=SectionDraft,
        )
        section_tasks.append(t)

    print("=== RUNNING SECTION WRITERS CREW ===")
    crew = Crew(agents=[writer], tasks=section_tasks)
    _ = crew.kickoff()

    drafts: List[SectionDraft] = []
    for t in section_tasks:
        p = getattr(t.output, "pydantic", None)
        if not p:
            raise RuntimeError(
                f"Section task for '{t.description[:60]}...' produced no structured output."
            )
        drafts.append(p)
    return drafts


def run_synthesizer(
    outline: Outline, drafts: List[SectionDraft], llm: LLM
) -> FinalReport:
    synthesizer = make_synthesizer(llm)

    print("=== DEFINING SYNTHESIS TASK ===")
    # Prepare a compact representation of drafts for the synthesizer's context
    drafts_context = "\n\n".join(
        [
            f"[{i+1}] {d.section_title}\n- "
            + "\n- ".join(d.key_points)
            + f"\n\n{d.content}"
            for i, d in enumerate(drafts)
        ]
    )

    synth_task = Task(
        description=(
            f"Assemble the final report for SUBJECT: {outline.subject}\n"
            f"TITLE: {outline.title}\n\n"
            "You are given the drafted sections below. Your job:\n"
            "1) Produce a crisp executive summary (120–180 words)\n"
            "2) Preserve the order of sections.\n"
            "3) Normalize terminology and tone across sections.\n"
            "4) Do not introduce new claims; keep it faithful to the drafts.\n"
            "Return ONLY a valid JSON object matching the schema.\n\n"
            f"DRAFTED SECTIONS:\n{drafts_context}\n"
        ),
        expected_output=(
            "A JSON object with: 'subject', 'outline' (with subject/title/sections), "
            "'executive_summary' (string), and 'sections' (array of {section_title,key_points,content})."
        ),
        agent=synthesizer,
        output_pydantic=FinalReport,
    )

    print("=== RUNNING SYNTHESIS CREW ===")
    crew = Crew(agents=[synthesizer], tasks=[synth_task])
    _ = crew.kickoff()

    final_report = synth_task.output.pydantic  # type: ignore
    if not final_report:
        raise RuntimeError("Synthesizer produced no structured report.")
    return final_report


# =========================
# MAIN
# =========================
def main():
    if len(sys.argv) < 2:
        print('Usage: python multi_agent_report.py "Your subject here"')
        sys.exit(1)

    subject = sys.argv[1].strip()
    print(f"\n=== SUBJECT ===\n{subject}\n")

    llm = make_llm()

    # Stage 1: Plan
    outline = run_planner(subject, llm)
    print("\n=== OUTLINE (structured) ===")
    print(outline.model_dump_json(indent=2))

    # Stage 2: Write sections
    drafts = run_section_writers(outline, llm)
    print("\n=== FIRST SECTION DRAFT (preview) ===")
    print(drafts[0].model_dump_json(indent=2))

    # Stage 3: Synthesize final report
    final_report = run_synthesizer(outline, drafts, llm)
    print("\n=== FINAL REPORT (structured) ===")
    print(final_report.model_dump_json(indent=2))

    # Optional: also print a readable text version
    print("\n=== FINAL REPORT (readable) ===\n")
    print(f"# {final_report.outline.title}\n")
    print("## Executive Summary\n")
    print(final_report.executive_summary.strip(), "\n")
    for i, sec in enumerate(final_report.sections, start=1):
        print(f"## {i}. {sec.section_title}")
        if sec.key_points:
            print("\n- " + "\n- ".join(sec.key_points))
        print("\n" + sec.content.strip() + "\n")


if __name__ == "__main__":
    main()
