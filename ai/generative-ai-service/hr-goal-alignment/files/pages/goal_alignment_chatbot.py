import streamlit as st
import json
import oracledb
import config
import re
from datetime import datetime
from utils import get_employee_id_by_name, generate_transcript_docx
from langchain.prompts import PromptTemplate
from goal_alignment_backend import (
    insert_goals_to_db,
    check_vertical_alignment_upward,
    check_horizontal_alignment,
    generate_final_recommendations,
    query_llm,
    update_employee_goal_objective
)



@st.cache_resource
def get_db_connection():
    return oracledb.connect(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        dsn=config.DB_DSN
    )
@st.cache_data(show_spinner=False)
def get_employee_and_manager_ids(employee_name):
    connection = get_db_connection()
    employee_id = get_employee_id_by_name(connection, employee_name)
    if not employee_id:
        return None, None
    cursor = connection.cursor()
    cursor.execute("SELECT manager_id FROM Employees WHERE employee_id = :1", (employee_id,))
    result = cursor.fetchone()
    return employee_id, result[0] if result else None

@st.cache_data(show_spinner=False)
def get_all_employees():
    connection = get_db_connection()
    cursor = connection.cursor()

    # Use the confirmed schema: NAME and ROLE
    cursor.execute("SELECT employee_id, name, role FROM Employees ORDER BY name")
    results = cursor.fetchall()  # list of tuples

    # Build label: "Alice Smith (HR Manager) — ID: 103"
    employee_lookup = {
        f"{name.strip()} ({role.strip()}) — ID: {emp_id}": emp_id
        for emp_id, name, role in results
    }

    return employee_lookup



# --- Helpers ---

# ──────────────────────────────────────────────────────────────
# Pull out individual goal sentences / bullet points
# ──────────────────────────────────────────────────────────────

ACTION_VERBS = r'\b(conduct|collect|incorporate|achieve|align|improve|increase|add|ensure|expand|broaden)\b'
def extract_goal_lines(text: str) -> list[str]:
    """
    Keep any line that has at least one digit/percent
    and is longer than ~20 characters.
    """
    cleaned = re.sub(r'[•–—►]', '-', text)
    lines = []

    for raw in cleaned.splitlines():
        line = raw.strip(" -*")
        # skip narrative Insight/Alignment lines
        if re.search(r'\b(insight|aligned|alignment|gap|mismatch|limit)\b', line, re.I):
            # but keep it if it contains an action verb like add/achieve/conduct
            if not re.search(r'\b(add|include|conduct|achieve|increase|improve|collect)\b', line, re.I):
                continue
        if len(line) < 20:
            continue
        if not (re.search(r'\d', line) or re.search(ACTION_VERBS, line, re.I)):
            continue
        lines.append(line)

    return lines


# ──────────────────────────────────────────────────────────────
# 3.  Dumb structuring: title = first nouny chunk before colon
# ──────────────────────────────────────────────────────────────
TITLE_RE = re.compile(r'^[A-Z].{0,60}?[:\-–]')
TIMELINE_RE = re.compile(
    r'\b(Q[1-4]\s*\d{2,4})\b'          # Q4 2025  /  Q1 26
    r'|(\b(?:H[12]|FY)\s*\d{2,4}\b)'    # H1 2026 / FY 2025
    r'|(\b(?:end\s+of\s+)?Q[1-4]\s*\d{4}\b)',  # End of Q4 2025
    flags=re.IGNORECASE
)

def extract_structured_goal(line: str) -> dict | None:
    """
    Returns a dict with clean title/metrics/timeline or None if no numbers present.
    """
    if not re.search(r'\d', line):
        return None

    # ① TIMELINE -----------------------------------------------------------
    m_time = TIMELINE_RE.search(line)
    timeline = m_time.group(0).title().replace("End Of ", "") if m_time else "N/A"

    # strip timeline from line so its digits don't pollute metric list
    core = line.replace(m_time.group(0), "") if m_time else line
    # remove list markers like "1." / "2)" / "3 ." at the start
    core = re.sub(r'^\s*\d+\s*[\.\)]\s*', '', core)

# ② METRICS ----------------------------------------------------
    raw_metrics = re.findall(
    r'''(?ix)
        (?<!goal\ \d)          # not in "Goal 1"
        (?:\d+\.\d+%?          # 7.5   7.5%
        |\d+\+                 # 2+    3+
        |\d+%                  # 10%   85%
        |\d+(?![\.\)]) )       # bare int *not* followed by "." or ")" 
    ''',
    core
)

    metrics = list(dict.fromkeys(raw_metrics))   # dedupe, preserve order



    # ③ TITLE -------------------------------------------------------------
    # Remove leading filler like “I suggest adding a goal to”
    cleaned = re.sub(
        r'''(?ix) ^
            \s*
            (?:  i\s+suggest(?:\s+adding)?      # I suggest…
            |  suggested\s+action
            |  add(?:ing)?\s+(?:a\s+)?sub\-?goal
            |  new\s+goal
            |  note
            |  current\s+goal
            |  revised\s+goal
            |  fatima,\s*let['’]s
            |  to\s+fix\s+this,\s*i\s+recommend
            |  one\s+key\s+insight.*?is\s+that
            )
            [\s:—\-]*''',
        '',
        core,                                 # <-- use the timeline-stripped line
    )
    # Take first ~8 words for title
    # --- Preferred title: first bold/italic phrase --------------------------
    m_emph = re.search(r'(\*\*([^*]{3,40})\*\*|\*([^*]{3,40})\*)', cleaned)
    if m_emph:
        title = re.sub(r'\*', '', m_emph.group(0)).strip()
    else:
        # existing logic: first ~8 words
        title = " ".join(cleaned.split()[:8]).rstrip(':*').capitalize()

    return {
        "goal_title": title,
        "objective": line.strip(),
        "metrics": metrics,
        "timeline": timeline,
        "stakeholders": [],
    }


def extract_possible_goal(chat_message: str) -> str:
    # Try extracting quoted text after common phrases
    match = re.search(r'["“](Achieve|Contribute|Align|Develop|Design|Support|Implement|Increase).*?["”]', chat_message, re.IGNORECASE)
    if match:
        return match.group(0).strip('“”" ')

    # Fallback: extract the first strong objective-like sentence
    sentences = re.split(r'(?<=[.!?]) +', chat_message.strip())
    for sentence in sentences:
        if re.search(r'\b(achieve|align|improve|contribute|support|implement|design|develop|increase|enhance)\b', sentence, re.IGNORECASE):
            # Exclude generic vague patterns
            if "your goal is" not in sentence.lower() and len(sentence.strip()) > 30:
                return sentence.strip()

    # Final fallback
    return "Achieve 75% employee participation in upskilling by Q2 2025."


def add_goal_refinement(goal_title, refined_objective):
    # Prevent duplicates
    for existing in st.session_state.ga_goal_refinements:
        if existing["goal_title"] == goal_title and existing["refined_objective"] == refined_objective:
            return  # Already exists
    st.session_state.ga_goal_refinements.append({
        "goal_title": goal_title,
        "refined_objective": refined_objective,
        "timestamp": datetime.utcnow().isoformat(),
        "applied": False
    })

def render_refinement_action(refinement, idx):
    st.markdown(f"### 🎯 Goal #{idx + 1}: {refinement.get('goal_title', 'Untitled Goal')}")

    # Determine whether it's a structured or unstructured refinement
    if "objective" in refinement:
        # Structured refinement
        st.markdown(f"**Objective:** {refinement.get('objective', 'N/A')}")
        st.markdown(f"**Metrics:** {'; '.join(refinement.get('metrics', [])) if refinement.get('metrics') else 'N/A'}")
        st.markdown(f"**Timeline:** {refinement.get('timeline', 'N/A')}")
        st.markdown(f"**Stakeholders:** {', '.join(refinement.get('stakeholders', [])) if refinement.get('stakeholders') else 'None listed'}")
    else:
        # Fallback: old unstructured refinement
        st.markdown("**Refined Objective (Unstructured):**")
        st.text_area("Text", value=refinement.get("refined_objective", ""), height=120, key=f"refined_{idx}", disabled=True)

    if not refinement.get("applied", False):
        if st.button(f"✅ Apply to DB", key=f"apply_{idx}"):
            try:
                connection = get_db_connection()
                employee_id = get_employee_id_by_name(connection, st.session_state.ga_employee_name)

                # Determine which function to call based on structure
                if "objective" in refinement:
                    from goal_alignment_backend import insert_goals_to_db
                    insert_goals_to_db(connection, employee_id, [refinement])
                else:
                    from goal_alignment_backend import update_employee_goal_objective
                    update_employee_goal_objective(connection, employee_id, refinement["refined_objective"])

                refinement["applied"] = True
                st.success("✅ Goal successfully saved to database.")
            except Exception as e:
                st.error(f"❌ Error saving goal: {e}")

    st.markdown(f"**Status:** {'✅ Applied' if refinement.get('applied') else '🕒 Not Applied'}")
    st.markdown("---")



def _finalise_conversation():
    """
    One-shot routine that:
      • harvests refinements from the whole chat
      • appends a farewell
      • flips the ‘conversation complete’ flag

    Streamlit will auto-rerun after the callback; no explicit st.rerun().
    """
    if st.session_state.ga_finalise_ran:
        return                              # already executed in this session

    # ----- 2.1  harvest goal refinements from all chatbot messages
    for msg in st.session_state.ga_chat_history:
        bot_text = msg.get("Chatbot", "")
        for line in extract_goal_lines(bot_text):
            structured = extract_structured_goal(line)
            if structured:
                 _deduped_append(structured)        # helper below
            else:
                add_goal_refinement(
                    extract_possible_goal(line),    # title
                    line                            # raw text
                )

    # ----- 2.2  add a single farewell once
    st.session_state.ga_chat_history.append({
        "Chatbot": (
            "I hope you're feeling more confident in refining your goal sheet. "
            "Best of luck as you continue developing your plan!"
        )
    })

    # ----- 2.3  mark complete & guard
    st.session_state.ga_conversation_complete = True
    st.session_state.ga_finalise_ran = True

def _deduped_append(structured):
    """Prevent duplicates in session_state.ga_goal_refinements"""
    if not any(
        r.get("objective") == structured.get("objective") and
        r.get("goal_title") == structured.get("goal_title")
        for r in st.session_state.ga_goal_refinements
    ):
        st.session_state.ga_goal_refinements.append({
            **structured,
            "timestamp": datetime.utcnow().isoformat(),
            "applied": False
        })

def render_goal_review_tools():
    st.header("✍️ Apply Refined Goals to the Database")

    if not st.session_state.ga_goal_refinements:
        st.info("No refined goals were detected in this session.")
        return

    # Debug section (optional – remove in production)
    with st.expander("Debug » Raw goal objects"):
        st.json(st.session_state.ga_goal_refinements)

    # Per-goal UI
    for idx, refinement in enumerate(st.session_state.ga_goal_refinements):
        render_refinement_action(refinement, idx)

    # Bulk-apply button
    unapplied = [r for r in st.session_state.ga_goal_refinements if not r["applied"]]
    if unapplied and st.button("✅ Apply ALL refined goals"):
        _apply_all_goals(unapplied)

def _apply_all_goals(refinements):
    """
    Bulk-save every un-applied goal object in *refinements*.

    Marks each refinement as applied and surfaces a Streamlit
    success (or error) message per goal.
    """
    if not refinements:
        st.info("Nothing to apply.")
        return

    try:
        connection = get_db_connection()
        employee_id = get_employee_id_by_name(
            connection,
            st.session_state.ga_employee_name
        )

        structured = [r for r in refinements if "objective" in r]
        legacy     = [r for r in refinements if "refined_objective" in r]

        # --- structured goals -------------------------------------
        if structured:
            insert_goals_to_db(connection, employee_id, structured)
            for r in structured:
                r["applied"] = True
                st.success(f"Inserted structured goal: {r['goal_title']}")

        # --- legacy / unstructured goals --------------------------
        for r in legacy:
            update_employee_goal_objective(
                connection,
                employee_id,
                r["refined_objective"]
            )
            r["applied"] = True
            st.success(f"Saved legacy goal: {r['refined_objective'][:60]}…")

    except Exception as e:
        st.error(f"Bulk update failed: {e}")

    finally:
        pass

# --- Main Chatbot ---
def run_goal_alignment_chatbot():
    st.title("📊 Goal Alignment Chatbot")

    st.session_state.setdefault("ga_goal_refinements", [])
    st.session_state.setdefault("ga_chat_history", [])
    st.session_state.setdefault("ga_conversation_complete", False)
    st.session_state.setdefault("ga_finalise_ran", False)  
    st.session_state.setdefault("ga_topics_done", set())
    st.session_state.setdefault("ga_current_topic", None)
    employee_lookup = get_all_employees()

    selected_label = st.selectbox("Select an Employee:", list(employee_lookup.keys()), key="ga_employee_select")
    employee_id = employee_lookup[selected_label]
    employee_name = selected_label.split(" (")[0]  # Just the name

    # Reset session state if a new employee is selected
    # This ensures we start fresh for each employee
    if (
        "ga_selected_employee" not in st.session_state
        or st.session_state.ga_selected_employee != employee_id
    ):
        # ▼  New employee selected → wipe per-employee data
        st.session_state.ga_selected_employee = employee_id
        st.session_state.ga_goal_refinements = []
        st.session_state.ga_chat_history     = []
        st.session_state.ga_conversation_complete = False
        st.session_state.ga_finalise_ran     = False

    if st.button("Generate Report", key="ga_generate_report_btn"):
        try:
            with st.spinner("Looking up employee and manager..."):
                employee_id, manager_id = get_employee_and_manager_ids(employee_name)

            if not employee_id:
                st.error(f"Employee '{employee_name}' not found in the database.")
                return
            if not manager_id:
                st.error(f"No manager found for employee '{employee_name}'.")
                return

            with st.spinner("Checking vertical alignment..."):
                vertical = check_vertical_alignment_upward(get_db_connection(), manager_id, employee_id)

            with st.spinner("Checking horizontal alignment..."):
                horizontal = check_horizontal_alignment(get_db_connection(), employee_id)

            with st.spinner("Generating final recommendations..."):
                recommendations = generate_final_recommendations(get_db_connection(), employee_id)

            compiled_report = {
                "vertical_alignment": vertical,
                "horizontal_alignment": horizontal,
                "final_recommendations": recommendations
            }

            st.session_state.ga_report = compiled_report
            st.session_state.ga_employee_name = employee_name
            st.success(f"Report compiled for {employee_name}!")

            report_json = json.dumps(compiled_report, indent=2)
            st.download_button(
                label="📄 Download JSON Report",
                data=report_json,
                file_name=f"goal_alignment_report_{employee_name}.json",
                mime="application/json"
            )

            # Initial message from the chatbot
            initial_prompt = PromptTemplate(
                input_variables=["employee_name", "final_recommendations"],
                template="""
You are a career mentor guiding {employee_name}.

**Initial Guidance:**  
{final_recommendations}

Start the conversation:  
- Give a friendly greeting in less than 100 words.  
- Highlight one key insight from the report about how the employee aligns (or not) with their manager in less than 100 words.  
- Suggest a concrete measure for {employee_name} to fix this, making reference to the text they have now in their own goal sheet and how it differs from that of their manager's.
- Only use the information in {final_recommendations}.
                """
            )
            initial_message = query_llm(initial_prompt, {
                "employee_name": employee_name,
                "final_recommendations": compiled_report["final_recommendations"]
            })
            st.session_state.ga_chat_history = [{"Chatbot": initial_message}]

        except Exception as e:
            st.error(f"Error during report generation or LLM query: {e}")

    # --- Chat Interface ---
    if "ga_report" in st.session_state:
        st.subheader("Chat with your Career Mentor")
        employee_name = st.session_state.ga_employee_name

        # ✅ Always show chat history
        for exchange in st.session_state.ga_chat_history:
            if "User" in exchange:
                with st.chat_message("user", avatar="🧑‍💼"):
                    st.markdown(exchange["User"])
            if "Chatbot" in exchange:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(exchange["Chatbot"])

        # ✅ If chat is still active, handle input
        if not st.session_state.ga_conversation_complete:
            user_msg = st.chat_input("You:")

            # Step 1: Store input and rerun
            if user_msg and "ga_pending_input" not in st.session_state:
                st.session_state.ga_chat_history.append({"User": user_msg})
                st.session_state.ga_pending_input = user_msg
                st.rerun()

            # Step 2: Process after rerun
            if "ga_pending_input" in st.session_state:
                user_msg = st.session_state.ga_pending_input
                del st.session_state.ga_pending_input

                # Check for end phrases
                if any(phrase in user_msg.lower().strip() for phrase in [
                    "no thanks", "no thank you", "i'm good", "im good",
                    "no i'm good", "no im good", "that's all", "we're done",
                    "we are done", "stop", "all set"
                ]):
                    st.session_state.ga_chat_history.append({
                        "Chatbot": "I hope you're feeling more confident in refining your goal sheet. Best of luck as you continue developing your plan!"
                    })
                    st.session_state.ga_conversation_complete = True
                    st.rerun()
                else:
                    chat_prompt = PromptTemplate(
                        input_variables=["employee_name", "chat_input", "chat_history", "full_report"],
                        template="""You are a helpful career mentor chatbot coaching {employee_name} on goal alignment.

Here is the previous chat history:
{chat_history}

Employee's latest message:
{chat_input}

Report Findings:
{full_report}

Instructions:
- Address one topic at a time from the Report Findings: vertical, horizontal, and recommendations.
- If the conversation history has had more than 2 messages on a single topic, move on to the next topic in the report.
- If the current topic was already discussed and the user gave any positive or acknowledging response (even brief ones like "ok", "will do", "makes sense"), move on to the next topic.
- Avoid restating earlier suggestions unless the user expressed confusion or disagreement.
- If there's a lack of agency in what they last said, suggest something to help them refine this goal but you're moving on regardless!
- Don’t repeat topics already covered in chat history. 
- Don't ask open ended questions unless there's really no other option.
- Give the impression that you're reducing the user's cognitive load, not adding to it.
                        """ 
                    )
                    response = query_llm(chat_prompt, {
                        "employee_name": employee_name,
                        "chat_input": user_msg,
                        "chat_history": json.dumps(st.session_state.ga_chat_history, indent=2),
                        "full_report": json.dumps(st.session_state.ga_report, indent=2)
                    })

                    st.session_state.ga_chat_history.append({"Chatbot": response})

                    goal_lines = extract_goal_lines(response)
                    for line in goal_lines:
                        structured = extract_structured_goal(line)
                        if structured:
                            _deduped_append(structured)
                    st.rerun()

        st.button(
            "🚦 End Conversation & Review Goals",
            on_click=_finalise_conversation,
            disabled=st.session_state.ga_conversation_complete, key="ga_end_conversation_btn"
)

    # ---------- POST-CHAT TOOLS ----------
    if st.session_state.ga_conversation_complete:
        render_goal_review_tools()      # see next snippet



run_goal_alignment_chatbot()