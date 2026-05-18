import streamlit as st
import json
from langchain.prompts import PromptTemplate
from utils import (
    get_employee_id_by_name,
    generate_transcript_docx,
    detect_covered_topic
)
from goal_alignment_backend import (
    load_self_assessment_from_db,
    load_manager_briefing_from_db,
    query_llm
)
import oracledb
import config

def run_self_assessment_chatbot():
    st.title("Self-Assessment Chatbot")

    if "sa_chat_history" not in st.session_state:
        st.session_state.sa_chat_history = []
    if "sa_conversation_complete" not in st.session_state:
        st.session_state.sa_conversation_complete = False
    if "sa_covered_topics" not in st.session_state:
        st.session_state.sa_covered_topics = []
    if "sa_interaction_count" not in st.session_state:
        st.session_state.sa_interaction_count = 0
    if "sa_report" not in st.session_state:
        st.session_state.sa_report = None
    if "sa_employee_name" not in st.session_state:
        st.session_state.sa_employee_name = ""
    if "sa_employee_id" not in st.session_state:
        st.session_state.sa_employee_id = ""

    if st.session_state.sa_report is None:
        employee_name_input = st.text_input("Enter Employee Name:", key="sa_employee_input")

        if st.button("Start Self-Assessment Chat", key="sa_gather_data_btn"):
            if not employee_name_input:
                st.warning("Please enter an employee name.")
                return

            try:
                with st.spinner("Connecting to database and gathering data..."):
                    connection = oracledb.connect(
                        user=config.DB_USER,
                        password=config.DB_PASSWORD,
                        dsn=config.DB_DSN
                    )
                    employee_id = get_employee_id_by_name(connection, employee_name_input)

                    if not employee_id:
                        st.error(f"Employee '{employee_name_input}' not found in the database.")
                        return

                    st.session_state.sa_employee_id = employee_id
                    st.session_state.sa_employee_name = employee_name_input

                    self_assessment = load_self_assessment_from_db(connection, employee_id)
                    manager_briefing = load_manager_briefing_from_db(connection, employee_id)

                    if not self_assessment and not manager_briefing:
                        st.error(f"No self-assessment or manager briefing data found for {employee_name_input}.")
                        return

                    st.session_state.sa_report = {
                        "self_assessment": self_assessment or {"message": "No self-assessment data found."},
                        "manager_briefing": manager_briefing or {"message": "No manager briefing data found."},
                    }

                    quantitative_performance = st.session_state.sa_report.get("manager_briefing", {}).get(
                        "quantitative_performance", "your recent performance"
                    ) or "your recent performance"

                    prompt = PromptTemplate(
                        input_variables=["employee_name", "quantitative_performance"],
                        template="""
                        You are a career mentor chatbot guiding {employee_name}.
                        Your aim is to prepare the employee for their upcoming quarterly evaluation with their manager.
                        Start the conversation with: "Good morning, {employee_name}. We're approaching your quarterly self-evaluation. I've gathered some performance insights to help."
                        Continue by mentioning the following insight: {quantitative_performance}
                        Ask what specific changes might have contributed to this. Keep it under 150 words. Tone is light and conversational.
                        Important rules: do not combine asking a question and concluding in the same message. Only conclude once the user has indicated they are done.
                        Ensure you balance references between manager briefing and self-evaluation, surfacing gaps or complementary insights.
                        """
                    )

                    initial_msg = query_llm(prompt, {
                        "employee_name": employee_name_input,
                        "quantitative_performance": quantitative_performance
                    })

                    st.session_state.sa_chat_history = [{"Chatbot": initial_msg}]
                    st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                if 'connection' in locals():
                    connection.close()

    if st.session_state.sa_report:
        st.subheader(f"Chat with Mentor for {st.session_state.sa_employee_name}")

        for exchange in st.session_state.sa_chat_history:
            if "User" in exchange:
                with st.chat_message("user", avatar="🧑🏽‍💼"):
                    st.write(exchange["User"])
            if "Chatbot" in exchange:
                with st.chat_message("assistant", avatar="💬"):
                    st.write(exchange["Chatbot"])

        if st.button("Stop Conversation", key="sa_stop_btn"):
            st.session_state.sa_conversation_complete = True
            if not st.session_state.sa_chat_history[-1].get("Chatbot", "").startswith("Got it! Best of luck"):
                st.session_state.sa_chat_history.append(
                    {"Chatbot": "Okay, ending the conversation here. Best of luck!"}
                )
            st.rerun()

        user_input = st.chat_input("You:", key="sa_user_chat_input", disabled=st.session_state.sa_conversation_complete)
        if user_input and not st.session_state.sa_conversation_complete:
            st.session_state.sa_chat_history.append({"User": user_input})
            st.session_state.sa_interaction_count += 1

            done_phrases = [
                "no i'm good", "no im good", "i'm good", "im good",
                "no thanks", "no thank you", "that's all", "stop", "can we stop", "we're done", "we are done", "all set"
            ]

            if any(phrase in user_input.lower() for phrase in done_phrases):
                st.session_state.sa_chat_history.append({
                    "Chatbot": "Got it! Best of luck in your meeting with your manager. I'll send a summary of this chat for your reference."
                })
                st.session_state.sa_conversation_complete = True
                st.rerun()

            history_str = "\n".join(
                [f"{k}: {v}" for exchange in st.session_state.sa_chat_history[-5:] for k, v in exchange.items()]
            )

            prompt = PromptTemplate(
                input_variables=["employee_name", "chat_input", "chat_history", "full_report", "covered_topics"],
                template="""
                You are a helpful career mentor guiding {employee_name}. Your goal is to discuss their self-assessment and manager's briefing points to prepare them for an evaluation meeting.

                **Chat History (recent first):**
                {chat_history}

                **Latest input from {employee_name}:**
                {chat_input}

                **Reference Report Data (Self Assessment & Manager Briefing):**
                {full_report}

                **Topics Already Covered (Do not revisit these):**
                {covered_topics}

                [.. trimmed instructions ..]
                """
            )

            try:
                response = query_llm(prompt, {
                    "employee_name": st.session_state.sa_employee_name,
                    "chat_input": user_input,
                    "chat_history": history_str,
                    "full_report": json.dumps(st.session_state.sa_report, indent=2),
                    "covered_topics": json.dumps(st.session_state.sa_covered_topics),
                })

                report_data = {
                    **st.session_state.sa_report.get("self_assessment", {}),
                    **st.session_state.sa_report.get("manager_briefing", {})
                }
                topic = detect_covered_topic(response, report_data)
                if topic and topic not in st.session_state.sa_covered_topics:
                    st.session_state.sa_covered_topics.append(topic)

                st.session_state.sa_chat_history.append({"Chatbot": response})
                if "Best of luck in your meeting" in response:
                    st.session_state.sa_conversation_complete = True

                if st.session_state.sa_interaction_count >= 10 and not st.session_state.sa_conversation_complete:
                    st.session_state.sa_chat_history.append({
                        "Chatbot": "We've covered quite a bit. Is there anything else you'd like to discuss before we wrap up?"
                    })

            except Exception as e:
                st.error(f"Error from LLM: {e}")
                st.session_state.sa_chat_history.append({
                    "Chatbot": "Sorry, I encountered an error trying to generate a response."
                })

            st.rerun()

        if st.session_state.sa_conversation_complete and st.session_state.sa_chat_history:
            file = generate_transcript_docx(st.session_state.sa_chat_history, st.session_state.sa_employee_name)
            st.download_button(
                label="📥 Download Conversation Transcript",
                data=file,
                file_name=f"{st.session_state.sa_employee_name}_SelfAssessmentChat_transcript.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="sa_download_btn"
            )
run_self_assessment_chatbot()
if __name__ == "__streamlit__":
    run_self_assessment_chatbot()
