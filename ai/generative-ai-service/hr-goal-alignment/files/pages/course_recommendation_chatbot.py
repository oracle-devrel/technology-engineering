import streamlit as st
import logging
import oracledb
import config

# Import necessary components from the current project
from course_vector_utils import CourseVectorStore
from gen_ai_service import inference as gen_ai

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

ICONS = {
    'beginner': '🥉 Beginner',
    'intermediate': '🥈 Intermediate',
    'advanced': '🥇 Advanced',
    'default': '🎯 General'
}

def display_course(course):
    """Display a single course recommendation block in Streamlit."""
    name = course.get('NAME', 'No Name Provided')
    url = course.get('URL', '#')
    rating = course.get('RATING', 'N/A')
    level_key = course.get('DIFFICULTYLEVEL', 'default').strip().lower()
    icon = ICONS.get(level_key, ICONS['default'])
    university = course.get('UNIVERSITY', 'N/A')
    description = course.get('DESCRIPTION', 'No description provided.')
    skills = course.get('SKILLS', 'N/A')

    st.markdown(f"**[{name}]({url})** (⭐ {rating})")
    st.markdown(f"> {icon} | 🏛️ {university}")
    st.markdown(f"> _{description[:150]}{'...' if len(description) > 150 else ''}_")
    st.markdown(f"> **Skills:** {skills}\n\n")

@st.cache_resource
def initialize_resources():
    db_conn = None
    try:
        logger.info("Initializing database connection...")
        db_conn = oracledb.connect(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dsn=config.DB_DSN
        )
        logger.info("Database connection successful.")

        logger.info("Initializing vector store...")
        vector_store = CourseVectorStore(db_conn)
        logger.info("Vector store initialized successfully.")
        return vector_store

    except oracledb.Error as db_err:
        logger.error(f"Oracle Database connection error: {db_err}", exc_info=True)
        st.error("Failed to connect to the database. Please check credentials and network.")
        if db_conn:
            db_conn.close()
        return None
    except Exception as e:
        logger.error(f"Failed to initialize resources: {e}", exc_info=True)
        st.error("Failed to initialize resources. Please check logs or contact support.")
        if db_conn:
            db_conn.close()
        return None

vector_store = initialize_resources()

st.title("🎓 Course Recommendation Chatbot")

st.write("""
Enter your learning goals, desired skills, or topics you're interested in.
The chatbot will search the course catalog and recommend relevant training.
""")

user_input = st.text_area("Describe your learning needs:", height=100)

if st.button("🔍 Find Courses") and vector_store:
    if not user_input:
        st.warning("Please enter your learning needs in the text area.")
    else:
        with st.spinner("Searching for relevant courses and generating recommendations..."):
            try:
                logger.info(f"Performing vector search for query: '{user_input}'")
                retrieved_docs = vector_store.similarity_search(user_input, k=5)

                if not retrieved_docs:
                    st.info("No directly matching courses found in the vector store based on your query.")
                else:
                    context = "\n\n".join([
                        f"Course: {doc.metadata.get('NAME', 'N/A')}\nDescription: {doc.metadata.get('DESCRIPTION', 'N/A')}\nSkills: {doc.metadata.get('SKILLS', 'N/A')}"
                        for doc in retrieved_docs
                    ])
                    logger.info(f"Context prepared for LLM:\n{context[:500]}...")

                    logger.info("Calling GenAI service for recommendations...")
                    recommendations = gen_ai.recommend_courses(user_input, context)
                    logger.info(f"Received recommendations from GenAI: {recommendations}")

                    if recommendations and isinstance(recommendations, list):
                        st.markdown("### 💡 Recommended Courses")
                        for item in recommendations:
                            display_course(item)

                    elif isinstance(recommendations, dict) and recommendations.get("recommended_courses"):
                        st.markdown("### 💡 Recommended Courses")
                        focus_areas_data = recommendations["recommended_courses"]
                        if not focus_areas_data:
                            st.info("The AI could not determine specific recommendations based on the search results.")
                        else:
                            courses_list = []
                            if isinstance(focus_areas_data, list):
                                courses_list = focus_areas_data
                            elif isinstance(focus_areas_data, dict):
                                st.markdown("### 💡 Recommended Courses by Focus Area")
                                for focus_area, courses in focus_areas_data.items():
                                    st.subheader(f"📌 {focus_area}")
                                    if not isinstance(courses, list):
                                        st.warning(f"Unexpected structure under '{focus_area}' — skipping.")
                                        continue
                                    for item in courses:
                                        if isinstance(item, dict):
                                            display_course(item)
                                        elif isinstance(item, str):
                                            st.markdown(f"- 📚 {item}")
                                        else:
                                            st.warning("Unrecognized course format.")
                            if courses_list:
                                for item in courses_list:
                                    display_course(item)

                    else:
                        st.info("The AI assistant processed the search results but didn't provide specific recommendations in the expected format.")
                        logger.warning(f"Unexpected recommendation format: {recommendations}")
            except Exception as e:
                logger.error(f"An error occurred while recommending courses: {e}", exc_info=True)
                st.error("Something went wrong while processing your request. Please try again.")

st.markdown("---")
st.info("Powered by Oracle Cloud Infrastructure Generative AI")
