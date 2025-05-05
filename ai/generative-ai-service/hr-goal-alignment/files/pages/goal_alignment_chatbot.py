import streamlit as st
import json
import oracledb
import config
import re
from datetime import datetime
from utils import get_employee_id_by_name, generate_transcript_docx
from langchain.prompts import PromptTemplate
from goal_alignment_backend import (
    check_vertical_alignment_upward,
    check_horizontal_alignment,
    generate_final_recommendations,
    query_llm,
    update_employee_goal_objective
)

# --- Helpers ---
def is_refinement_suggestion(text: str) -> bool:
    keywords = [
        "i suggest refining", "consider adding a goal", "consider including",
        "you could strengthen alignment by", "i recommend creating", "you could add",
        "i suggest you add", "you could include"
    ]
    return any(kw in text.lower() for kw in keywords)

def extract_possible_goal(chat_message: str) -> str:
    match = re.search(r'your goal,.*?\"(.*?)\"', chat_message)
    return match.group(1) if match else "Refined Goal"

def add_goal_refinement(goal_title, refined_objective):
    existing = next((g for g in st.session_state.ga_goal_refinements if g["goal_title"] == goal_title), None)
    if not existing:
        st.session_state.ga_goal_refinements.append({
            "goal_title": goal_title,
            "refined_objective": refined_objective,
            "timestamp": datetime.utcnow().isoformat(),
            "applied": False
        })

def render_refinement_action(refinement, idx):
    st.markdown(f"**Goal:** {refinement['goal_title']}")
    st.text_area("Refined Objective", value=refinement["refined_objective"], height=120, key=f"refined_{idx}", disabled=True)
    if not refinement["applied"]:
        if st.button(f"✅ Apply to DB (Goal: {refinement['goal_title']})", key=f"apply_{idx}"):
            try:
                connection = oracledb.connect(
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    dsn=config.DB_DSN
                )
                employee_id = get_employee_id_by_name(connection, st.session_state.ga_employee_name)
                msg = update_employee_goal_objective(connection, employee_id, refinement["refined_objective"])
                refinement["applied"] = True
                st.success(f"Updated: {msg}")
            except Exception as e:
                st.error(f"Error updating DB: {e}")
            finally:
                if 'connection' in locals():
                    connection.close()

# --- Main Chatbot ---
def run_goal_alignment_chatbot():
    st.title("📊 Goal Alignment Chatbot")

    st.session_state.setdefault("ga_goal_refinements", [])
    st.session_state.setdefault("ga_chat_history", [])
    st.session_state.setdefault("ga_conversation_complete", False)

    if "ga_report" not in st.session_state:
        employee_name = st.text_input("Enter Employee Name:", key="ga_employee_input")

        if st.button("Generate Report", key="ga_generate_report_btn"):
            with st.spinner("Connecting and compiling alignment report..."):
                connection = None
                try:
                    connection = oracledb.connect(
                        user=config.DB_USER,
                        password=config.DB_PASSWORD,
                        dsn=config.DB_DSN
                    )
                    employee_id = get_employee_id_by_name(connection, employee_name)

                    if not employee_id:
                        st.error(f"Employee '{employee_name}' not found in the database.")
                        return

                    cursor = connection.cursor()
                    cursor.execute("SELECT manager_id FROM Employees WHERE employee_id = :1", (employee_id,))
                    result = cursor.fetchone()
                    if not result:
                        st.error(f"No manager found for employee '{employee_name}'")
                        return
                    manager_id = result[0]

                    compiled_report = {
                        "vertical_alignment": check_vertical_alignment_upward(connection, manager_id, employee_id),
                        "horizontal_alignment": check_horizontal_alignment(connection, employee_id),
                        "final_recommendations": generate_final_recommendations(connection, employee_id)
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
                    st.error(f"Error: {e}")
                finally:
                    if connection:
                        connection.close()

    # --- Chat Interface ---
    if "ga_report" in st.session_state:
        st.subheader("Chat with your Career Mentor")
        employee_name = st.session_state.ga_employee_name

        for exchange in st.session_state.ga_chat_history:
            if "User" in exchange:
                with st.chat_message("user", avatar="🧑‍💼"):
                    st.markdown(exchange["User"])
            if "Chatbot" in exchange:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(exchange["Chatbot"])

        if not st.session_state.ga_conversation_complete:
            user_msg = st.chat_input("You:", key="ga_user_input")
            if user_msg:
                st.session_state.ga_chat_history.append({"User": user_msg})

                if any(phrase in user_msg.strip().lower() for phrase in [
                    "no thanks", "no thank you", "i'm good", "im good",
                    "no i'm good", "no im good", "that's all", "we're done",
                    "we are done", "stop", "all set"]):
                    closing = "I hope you're feeling more confident in refining your goal sheet. Best of luck as you continue developing your plan!"
                    st.session_state.ga_chat_history.append({"Chatbot": closing})
                    st.session_state.ga_conversation_complete = True
                    st.rerun()

                prompt = PromptTemplate(
                    input_variables=["employee_name", "chat_input", "chat_history", "full_report"],
                    template="""
You are a helpful career mentor chatbot coaching {employee_name} on goal alignment.

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
- - Give the impression that you're reducing the user's cognitive load, not adding to it.
                    """
                )
                response = query_llm(prompt, {
                    "employee_name": employee_name,
                    "chat_input": user_msg,
                    "chat_history": json.dumps(st.session_state.ga_chat_history, indent=2),
                    "full_report": json.dumps(st.session_state.ga_report, indent=2)
                })

                st.session_state.ga_chat_history.append({"Chatbot": response})
                if is_refinement_suggestion(response):
                    possible_goal = extract_possible_goal(response)
                    add_goal_refinement(possible_goal, response)
                st.rerun()

        if st.button("Stop Conversation") and not st.session_state.ga_conversation_complete:
            st.session_state.ga_chat_history.append({
                "Chatbot": "I hope you're feeling more confident in refining your goal sheet. Best of luck as you continue developing your plan!"
            })
            st.session_state.ga_conversation_complete = True
            st.rerun()

        if st.session_state.ga_conversation_complete and st.session_state.ga_chat_history:
            transcript_file = generate_transcript_docx(st.session_state.ga_chat_history, employee_name)
            st.download_button(
                label="📥 Download Conversation Transcript",
                data=transcript_file,
                file_name=f"{employee_name}_GoalAlignmentChat_transcript.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="ga_download_btn"
            )

        if st.session_state.ga_conversation_complete and st.session_state.ga_goal_refinements:
            st.markdown("### ✍️ Apply Refined Goals to the Database")
            st.info("Below are refined objectives suggested during your chat. You can apply them to the goal sheet.")
            for idx, refinement in enumerate(st.session_state.ga_goal_refinements):
                render_refinement_action(refinement, idx)

run_goal_alignment_chatbot()