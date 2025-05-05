import streamlit as st
import oracledb
import config
from langchain.prompts import PromptTemplate
from utils import get_employee_id_by_name
from goal_alignment_backend import query_llm

def run_meeting_preparation_chatbot():
    st.title("Manager Meeting Preparation Chatbot")

    employee_name = st.text_input("Enter Employee Name:", key="prep_employee_input")

    if employee_name:
        try:
            with st.spinner("Connecting and fetching data..."):
                connection = oracledb.connect(
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    dsn=config.DB_DSN
                )
                cursor = connection.cursor()

                employee_id = get_employee_id_by_name(connection, employee_name)

                if not employee_id:
                    st.error(f"Employee '{employee_name}' not found.")
                    return

                cursor.execute(
                    """
                    SELECT sa.key_achievements, sa.skill_development, sa.strengths, sa.areas_for_improvement, sa.alignment_with_career_goals,
                           mb.quantitative_performance, mb.perception_gap, mb.manager_context, mb.tenure, mb.cross_departmental_contributions, mb.career_alignment_prompt
                    FROM Self_Assessments sa
                    LEFT JOIN Manager_Briefings mb ON sa.employee_id = mb.employee_id
                    WHERE sa.employee_id = :1
                    """,
                    (employee_id,)
                )

                result = cursor.fetchone()
                if not result:
                    st.warning(f"No data found for employee ID: {employee_id}")
                    return

                # Handle LOBs
                def read_lob(lob): return lob.read() if lob else "N/A"
                (
                    key_achievements, skill_dev, strengths, areas_improvement, alignment_goals,
                    quant_perf, perception_gap, manager_context, tenure, cross_dept, career_prompt
                ) = [read_lob(lob) for lob in result]

                st.subheader("Briefing Overview")
                st.write(f"**Key Achievements:** {key_achievements}")
                st.write(f"**Skill Development:** {skill_dev}")
                st.write(f"**Strengths:** {strengths}")
                st.write(f"**Areas for Improvement:** {areas_improvement}")
                st.write(f"**Alignment with Career Goals:** {alignment_goals}")
                st.write(f"**Quantitative Performance:** {quant_perf}")
                st.write(f"**Perception Gap:** {perception_gap}")
                st.write(f"**Manager Context:** {manager_context}")
                st.write(f"**Tenure:** {tenure}")
                st.write(f"**Cross-Departmental Contributions:** {cross_dept}")
                st.write(f"**Career Alignment Prompt:** {career_prompt}")

                st.subheader("Chat with Meeting Prep Bot")
                st.write("Ask questions or discuss points to prepare for your meeting.")

                if "prep_messages" not in st.session_state:
                    st.session_state.prep_messages = []

                for message in st.session_state.prep_messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                if user_input := st.chat_input("What do you want to discuss?", key="prep_chat_input"):
                    st.session_state.prep_messages.append({"role": "user", "content": user_input})
                    with st.chat_message("user"):
                        st.markdown(user_input)

                    context = {
                        "employee_name": employee_name,
                        "user_input": user_input,
                        "key_achievements": key_achievements,
                        "skill_development": skill_dev,
                        "strengths": strengths,
                        "areas_for_improvement": areas_improvement,
                        "alignment_with_career_goals": alignment_goals,
                        "quantitative_performance": quant_perf,
                        "perception_gap": perception_gap,
                        "manager_context": manager_context,
                        "tenure": tenure,
                        "cross_departmental_contributions": cross_dept,
                        "career_alignment_prompt": career_prompt
                    }

                    prompt = PromptTemplate(
                        input_variables=list(context.keys()),
                        template="""
                        You are a helpful HR assistant chatbot.
                        You are helping {employee_name} prepare for their meeting with their manager based on their self-assessment and the manager's briefing notes.

                        Self-Assessment - Key Achievements: {key_achievements}
                        Self-Assessment - Skill Development: {skill_development}
                        Self-Assessment - Strengths: {strengths}
                        Self-Assessment - Areas for Improvement: {areas_for_improvement}
                        Self-Assessment - Alignment with Career Goals: {alignment_with_career_goals}
                        Manager Briefing - Quantitative Performance: {quantitative_performance}
                        Manager Briefing - Perception Gap: {perception_gap}
                        Manager Briefing - Manager Context: {manager_context}
                        Manager Briefing - Tenure: {tenure}
                        Manager Briefing - Cross-Departmental Contributions: {cross_departmental_contributions}
                        Manager Briefing - Career Alignment Prompt: {career_alignment_prompt}

                        Respond to the user's query: {user_input}
                        Keep your response focused on helping them prepare for the meeting, referencing the provided data points.
                        """
                    )

                    response = query_llm(prompt, context)
                    st.session_state.prep_messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(response)

        except oracledb.Error as db_err:
            st.error(f"Database error: {db_err}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
        finally:
            if 'cursor' in locals(): cursor.close()
            if 'connection' in locals(): connection.close()
            


run_meeting_preparation_chatbot()