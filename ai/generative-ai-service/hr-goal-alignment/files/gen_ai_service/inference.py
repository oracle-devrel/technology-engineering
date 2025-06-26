# Copyright (c) 2025 Oracle and/or its affiliates.
import json
import logging
import sys
import os
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # <- write logs into a file called app.log
        logging.StreamHandler()          # <- also allow printing to the console (terminal)
    ]
)
logger = logging.getLogger(__name__)

def get_embedding_model():
    embedding_model = OCIGenAIEmbeddings(
        model_id=config.EMBEDDING_MODEL,
        service_endpoint=config.GEN_AI_ENDPOINT,
        truncate="NONE",
        compartment_id=config.OCI_COMPARTMENT_ID,
        auth_type=config.AUTH_TYPE,
        auth_profile=config.CONFIG_PROFILE,
    )

    return embedding_model


def get_llm_model(temperature: float = 0, max_tokens: int = 4000):
    llm_model = ChatOCIGenAI(
        auth_type=config.AUTH_TYPE,
        model_id=config.LLM_MODEL,
        service_endpoint=config.GEN_AI_ENDPOINT,
        compartment_id=config.OCI_COMPARTMENT_ID,
        provider=config.PROVIDER,
        model_kwargs={
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    )
    return llm_model


def recommend_courses(profile, feedback) -> dict:
    model = get_llm_model()
    response = {}
    try:
        response = model.with_structured_output(schema).invoke(
            [
                SystemMessage(content=prompt_sys),
                HumanMessage(
                    content=prompt_user.format(
                        EMPLOYEE_PROFILE=profile, MANAGER_FEEDBACK=feedback
                    )
                ),
            ]
        )
    except Exception as e:
        logger.error(f"Error during recommended_courses execution: {e}")

    return response # type: ignore



def classify_smart_goal(goal_description) -> dict:
    model = get_llm_model(temperature=0, max_tokens=600)
    response = {}
    try:
        response = model.invoke(
            [
                HumanMessage(content=goals_prompt_sys.format(GOAL_DESCRIPTION=goal_description, INSTRUCTIONS=instructions_prompt)),
            ]
        )
    except Exception as e:
        logger.error(f"Error during recommended_courses execution: {e}")

    return json.loads(response.content) # type: ignore


prompt_sys = """
# AI-powered Training Recommendation Engine
You are an AI-powered Training Recommendation Engine specialized in matching professional development courses to employee needs with strict prioritization rules.

**Primary Objective:**
Analyze information to identify skill gaps and recommend relevant training courses according to this specific priority order:
1. Issues highlighted in manager feedback (highest priority)
2. Alignment with job title requirements and responsibilities
3. Complementing existing skills while addressing gaps
4. Appropriate for years of experience and current skill level

**Output Requirements:**
1. Identify 3 clear focus areas derived primarily from the manager feedback
2. For each focus area, provide exactly 2 course recommendations that:
   - Explicitly include difficulty level in the title: "(Beginner)", "(Intermediate)", or "(Advanced)"
   - Are specific and descriptive of the skill being developed
   - Match the employee's current experience level appropriately
3. All recommendations must be ordered by priority following the hierarchy above

**Response Format:**
Return a clean, properly formatted JSON object with one keys:
- "recommended_courses": {
    "Focus Area 1": [2 courses addressing this area],
    "Focus Area 2": [2 courses addressing this area],
    "Focus Area 3": [2 courses addressing this area]
  }

Example response (exactly as shown, without code formatting, backticks, or extra newlines):
{
  "recommended_courses": {
    "Strategic Communication": [
      "Influential Communication for Technical Professionals (Intermediate)",
      "Executive Presence and Presentation Skills (Advanced)"
    ],
    "Technical Leadership": [
      "Leading High-Performance Technical Teams (Intermediate)", 
      "Strategic Technical Decision Making (Advanced)"
    ],
    "Project Estimation": [
      "Fundamentals of Project Estimation (Beginner)",
      "Advanced Techniques in Project Scoping and Estimation (Intermediate)"
    ]
  }
}

DO NOT wrap your response in code blocks, backticks, or any other formatting. Return ONLY the raw JSON object itself.
"""

prompt_user = """
Based on the following information about an employee and their performance, recommend appropriate training courses:

**Employee Profile:**
{EMPLOYEE_PROFILE}

**Manager Feedback:**
{MANAGER_FEEDBACK}

Carefully analyze both sources of information with this strict priority order:
1. Address the most critical issues in the manager's feedback FIRST
2. Then consider the employee's job title and core responsibilities
3. Then look at their existing skills and experience level
4. Finally, consider their years of experience

Provide:
1. Three (3) specific focus areas this employee should develop (prioritized by importance)
2. For each focus area, recommend exactly 2 courses that address the specific skill gaps (total of 4-6 courses)

Remember:
- Include the appropriate difficulty level in each course title: "(Beginner)", "(Intermediate)", or "(Advanced)"
- Order focus areas by importance with manager feedback concerns taking highest priority
- Match course difficulty to the employee's current experience level
- Format your response as a proper JSON object with "focus_areas" and "recommended_courses" keys, where "recommended_courses" is an object with focus areas as keys and arrays of 2 courses as values
- Return ONLY the raw JSON object itself with no markdown formatting, code blocks, or backticks
"""
goals_prompt_sys = """
Determine if the following goal is SMART or not:\n
"{GOAL_DESCRIPTION}"
{INSTRUCTIONS}
"""
instructions_prompt = """
Provide a structured response in this exact JSON format:
{
    "classification": "<SMART | Not SMART>",
    "details": {
        "Specific": "<Met | Not Met>",
        "Measurable": "<Met | Not Met>",
        "Achievable": "<Met | Not Met>",
        "Relevant": "<Met | Not Met>",
        "TimeBound": "<Met | Not Met>"
    }
}
Return ONLY the JSON response without additional text, explanations, or formatting.
"""
schema = {
    "title": "RecommendedCourses",
    "type": "object",
    "description": "A tool for retrieving recommended courses by skill area",
    "properties": {
        "recommended_courses": {
            "type": "object",
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
            "description": "A mapping of skill areas to lists of recommended courses",
        }
    },
    "required": ["recommended_courses"],
}
