import oracledb
import config
import json
import uuid
from langchain.prompts import PromptTemplate
from langchain.schema import AIMessage
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.runnables import RunnableSequence

# Initialize Oracle LLM
llm = ChatOCIGenAI(
    model_id=config.GENERATION_MODEL_ID,
    service_endpoint=config.OCI_SERVICE_ENDPOINT,
    compartment_id=config.OCI_COMPARTMENT_ID,
    model_kwargs={"temperature": 0.1, "max_tokens": 500},
)

def query_llm(prompt_template, inputs):
    """Formats prompt and calls the Oracle LLM"""
    if not isinstance(prompt_template, PromptTemplate):
        raise TypeError(" query_llm expected a PromptTemplate object.")

    for key, value in inputs.items():
        if isinstance(value, AIMessage):  
            inputs[key] = value.content
        elif not isinstance(value, str):  
            inputs[key] = json.dumps(value, indent=2)

    chain = RunnableSequence(prompt_template | llm)
    response = chain.invoke(inputs)

    return response.content if isinstance(response, AIMessage) else response

# --- Database Data Loading Functions ---

def load_self_assessment_from_db(connection, employee_id):
    """Loads self assessment data from the Self_Assessments table."""
    assessment_data = {}
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT assessment_id, key_achievements, skill_development, strengths,
                   areas_for_improvement, alignment_with_career_goals
            FROM Self_Assessments
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        result = cursor.fetchone()
        if result:
            # Read CLOBs properly
            assessment_id, key_achievements_lob, skill_dev_lob, strengths_lob, areas_lob, alignment_lob = result
            assessment_data = {
                "assessment_id": assessment_id,
                "key_achievements": key_achievements_lob.read() if key_achievements_lob else None,
                "skill_development": skill_dev_lob.read() if skill_dev_lob else None,
                "strengths": strengths_lob.read() if strengths_lob else None,
                "areas_for_improvement": areas_lob.read() if areas_lob else None,
                "alignment_with_career_goals": alignment_lob.read() if alignment_lob else None,
            }
        cursor.close() # Close cursor after use
    except oracledb.Error as error:
        print(f"Error loading self assessment for {employee_id}: {error}")
        # Return empty dict or raise error depending on desired handling
    return assessment_data

def load_manager_briefing_from_db(connection, employee_id):
    """Loads manager briefing data from the Manager_Briefings table."""
    briefing_data = {}
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT briefing_id, quantitative_performance, perception_gap, manager_context,
                   tenure, cross_departmental_contributions, career_alignment_prompt
            FROM Manager_Briefings
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        result = cursor.fetchone()
        if result:
             # Read CLOBs properly
            briefing_id, quant_perf_lob, percep_gap_lob, mgr_context_lob, tenure_lob, cross_dept_lob, career_prompt_lob = result
            briefing_data = {
                "briefing_id": briefing_id,
                "quantitative_performance": quant_perf_lob.read() if quant_perf_lob else None,
                "perception_gap": percep_gap_lob.read() if percep_gap_lob else None,
                "manager_context": mgr_context_lob.read() if mgr_context_lob else None,
                "tenure": tenure_lob.read() if tenure_lob else None,
                "cross_departmental_contributions": cross_dept_lob.read() if cross_dept_lob else None,
                "career_alignment_prompt": career_prompt_lob.read() if career_prompt_lob else None,
            }
        cursor.close() # Close cursor after use
    except oracledb.Error as error:
        print(f"Error loading manager briefing for {employee_id}: {error}")
        # Return empty dict or raise error
    return briefing_data



def insert_goals_to_db(connection, employee_id, refined_goals):
    """
    Inserts structured goals into the 'Goals' table using the expected schema.
    Assumes metrics are stored as serialized JSON strings in the CLOB column.
    """
    try:
        cursor = connection.cursor()

        for goal in refined_goals:
            # Required fields
            goal_id = str(uuid.uuid4())
            title = goal.get("goal_title", "Untitled Goal")[:255]  # Truncate to fit VARCHAR2(255)
            objective = goal.get("objective", "")

            # Optional fields
            metrics_list = goal.get("metrics", [])
            timeline = goal.get("timeline", "TBD")[:255]  # Truncate if needed

            # Convert metrics list to JSON string
            if isinstance(metrics_list, list):
                metrics_json = json.dumps(metrics_list, ensure_ascii=False, indent=2)
            else:
                metrics_json = json.dumps([str(metrics_list)])

            # Insert into DB
            cursor.execute("""
                INSERT INTO Goals (goal_id, employee_id, title, objective, metrics, timeline)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, (
                goal_id,
                employee_id,
                title,
                objective,
                metrics_json,
                timeline
            ))

        connection.commit()
        return f"{len(refined_goals)} goal(s) successfully added for employee {employee_id}."

    except oracledb.Error as error:
        print("Error inserting goals:", error)
        return f"⚠️ Failed to insert goals: {error}"


# 🚀 Goal Alignment Functions (Database Version)

def get_horizontal_peers(connection, employee_id):
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT e2.name
            FROM Employees e1
            JOIN Employees e2 ON e1.manager_id = e2.manager_id
            WHERE e1.employee_id = :1 AND e2.employee_id != :1
            """, 
            (employee_id, employee_id) 
        )
        peers = [row[0] for row in cursor.fetchall()]
        return peers
    except oracledb.Error as error:
        print("Error fetching horizontal peers:")
        print(error)
        return []


def vertical_downward_employees(connection, manager_id):
    """Finds employees who report directly to a given manager."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT name
            FROM Employees
            WHERE manager_id = :1
            """,
            (manager_id,)
        )
        reports = [row[0] for row in cursor.fetchall()]
        return reports
    except oracledb.Error as error:
        print("Error fetching vertical downward employees:")
        print(error)
        return []

def check_vertical_alignment_upward(connection, manager_id, employee_id):
    """Checks vertical alignment between an employee and their manager."""
    try:
        cursor = connection.cursor()
        # Fetch manager and employee data
        cursor.execute(
            """
            SELECT e1.name, e1.role, e2.name, e2.role
            FROM Employees e1
            JOIN Employees e2 ON e1.employee_id = e2.manager_id
            WHERE e1.employee_id = :1 AND e2.employee_id = :2
            """,
            (manager_id, employee_id)
        )
        result = cursor.fetchone()

        if not result:
            return f"No record found for employee_id {employee_id} or manager_id {manager_id}."

        manager_name, manager_role, employee_name, employee_role = result

        # Fetch manager goals
        cursor.execute(
            """
            SELECT title, objective, metrics, timeline
            FROM Goals
            WHERE employee_id = :1
            """,
            (manager_id,)
        )
        manager_goals = [
            tuple(col.read() if isinstance(col, oracledb.LOB) else col for col in row)
            for row in cursor.fetchall()
        ]

        # Fetch employee goals
        cursor.execute(
            """
            SELECT title, objective, metrics, timeline
            FROM Goals
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        employee_goals = [
            tuple(col.read() if isinstance(col, oracledb.LOB) else col for col in row)
            for row in cursor.fetchall()
        ]

        prompt_template = PromptTemplate(
            input_variables=["manager_name", "employee_name", "manager_goals", "employee_goals"],
            template="""
### Reference Data (Use Only This Information)
**Manager:** {manager_name}  
**Employee:** {employee_name}

Manager Goals: {manager_goals}
Employee Goals: {employee_goals}

Compare the goals:  
- Does the employee’s goal structure align with the manager’s?  
- Are the success metrics matching? If not, suggest refinements.  
- Highlight any missing objectives.  
            """
        )

        return query_llm(prompt_template, {
            "manager_name": manager_name,
            "employee_name": employee_name,
            "manager_goals": manager_goals,
            "employee_goals": employee_goals
        })

    except oracledb.Error as error:
        print("Error checking vertical alignment:")
        print(error)
        return "Error checking vertical alignment."

def check_if_vertical_aligned(connection, manager_id, employee_id):
    """Checks vertical alignment between an employee and their manager."""
    try:
        cursor = connection.cursor()

        # Fetch manager and employee data
        cursor.execute(
            """
            SELECT e1.name, e1.role, e2.name, e2.role
            FROM Employees e1
            JOIN Employees e2 ON e1.employee_id = e2.manager_id
            WHERE e1.employee_id = :1 AND e2.employee_id = :2
            """,
            (manager_id, employee_id)
        )
        result = cursor.fetchone()

        if not result:
            return f"No record found for employee_id {employee_id} or manager_id {manager_id}."

        manager_name, manager_role, employee_name, employee_role = result

        # Fetch manager goals
        cursor.execute(
            """
            SELECT title, objective, metrics, timeline
            FROM Goals
            WHERE employee_id = :1
            """,
            (manager_id,)
        )
        manager_goals = [
            tuple(col.read() if isinstance(col, oracledb.LOB) else col for col in row)
            for row in cursor.fetchall()
        ]

        # Fetch employee goals
        cursor.execute(
            """
            SELECT title, objective, metrics, timeline
            FROM Goals
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        employee_goals = [
            tuple(col.read() if isinstance(col, oracledb.LOB) else col for col in row)
            for row in cursor.fetchall()
        ]

        prompt_template = PromptTemplate(
            input_variables=["manager_name", "employee_name", "manager_goals", "employee_goals"],
            template="""
                ### Vertical Alignment Assessment

                INSTRUCTIONS: Evaluate the vertical alignment score for **Employee {employee_name}** relative to **Manager {manager_name}** using SOLELY the reference data below. Return ONLY a single integer from **0 to 100** representing the overall vertical alignment.

                REFERENCE DATA:
                - Manager: {manager_name}
                - Manager Goals: {manager_goals}
                - Employee: {employee_name}
                - Employee Goals: {employee_goals}

                ASSESSMENT CRITERIA
                1. GOAL STRUCTURE ALIGNMENT (40%) – How closely the employee’s goal framework mirrors the manager’s stated goals.  
                - **0** : No structural overlap  
                - **20** : Partial alignment on some themes  
                - **40** : Full structural correspondence on all key themes  

                2. SUCCESS-METRIC CONSISTENCY (30%) – Degree to which the employee’s KPIs/OKRs use the same or compatible metrics as the manager’s.  
                - **0** : Metrics unrelated or absent  
                - **15** : Metrics partially match or are loosely comparable  
                - **30** : Metrics directly map to the manager’s success measures  

                3. OBJECTIVE COMPLETENESS (30%) – Coverage of all critical objectives set by the manager, plus identification of any missing elements.  
                - **0** : Several critical objectives missing  
                - **15** : Some objectives missing or vaguely addressed  
                - **30** : All manager objectives addressed and gaps proactively filled  

                OUTPUT FORMAT  
                Return **ONLY** a single integer between 0 and 100 with no additional text, punctuation, or formatting.

                EXAMPLE RESPONSE  
                87
            """
        )

        return query_llm(prompt_template, {
            "manager_name": manager_name,
            "employee_name": employee_name,
            "manager_goals": manager_goals,
            "employee_goals": employee_goals
        })

    except oracledb.Error as error:
        print("Error checking vertical alignment:")
        print(error)
        return "Error checking vertical alignment."

def check_horizontal_alignment(connection, employee_id):
    """Checks cross-team alignment using data from the database."""
    try:
        cursor = connection.cursor()

        # Get the list of peers who share the same manager
        list_horizontal_peers = get_horizontal_peers(connection, employee_id)

        # Fetch employee goals
        cursor.execute(
            """
            SELECT title, objective, metrics, timeline
            FROM Goals
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        employee_goals = [
                tuple(col.read() if isinstance(col, oracledb.LOB) else col for col in row)
                for row in cursor.fetchall()
            ]


        if not employee_goals:
            return f"⚠️ No goal data is available for horizontal alignment."

        prompt_template = PromptTemplate(
            input_variables=["employee_id", "employee_goals", "list_horizontal_peers"],
            template="""
            ### Reference Data (Use Only This Information)
            Evaluate the cross-functional alignment of goals for employee ID {employee_id}.
            Restrict your comparison to the following peers: {list_horizontal_peers}.

            - **Employee ID:** {employee_id}
            - **Goals:** {employee_goals}

            1. Are there dependencies on other departments?
            2. Are any key objectives missing that would improve alignment?
            3. Suggest ways to ensure better collaboration.
            """
        )

        return query_llm(prompt_template, {
            "employee_id": employee_id,
            "employee_goals": employee_goals,
            "list_horizontal_peers": list_horizontal_peers
        })

    except oracledb.Error as error:
        print("Error checking horizontal alignment:")
        print(error)
        return "Error checking horizontal alignment."
    
def check_if_horizontal_aligned(connection, employee_id):
    try:
        cursor = connection.cursor()

        # Get the list of peers who share the same manager
        list_horizontal_peers = get_horizontal_peers(connection, employee_id)

        # Fetch employee goals
        cursor.execute(
            """
            SELECT title, objective, metrics, timeline
            FROM Goals
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        employee_goals = [
                tuple(col.read() if isinstance(col, oracledb.LOB) else col for col in row)
                for row in cursor.fetchall()
            ]


        if not employee_goals:
            return f"⚠️ No goal data is available for horizontal alignment."

        prompt_template = PromptTemplate(
            input_variables=["employee_id", "employee_goals", "list_horizontal_peers"],
            template="""
            ### Horizontal Alignment Assessment

            INSTRUCTIONS: Analyze the cross-functional alignment score for employee ID {employee_id} based SOLELY on the provided data. Return ONLY a single numerical value from 0-100 representing the degree of horizontal alignment.

            REFERENCE DATA:
            - Employee ID: {employee_id}
            - Employee Goals: {employee_goals}
            - Relevant Horizontal Peers: {list_horizontal_peers}

            ASSESSMENT CRITERIA:
            1. DEPENDENCY ANALYSIS (40%): Measure how effectively the employee's goals account for dependencies with peer departments.
            - 0: No acknowledgment of cross-functional dependencies
            - 25: Basic recognition of dependencies
            - 40: Comprehensive integration of all relevant dependencies

            2. COMPLETENESS ASSESSMENT (30%): Evaluate if the goals include all necessary objectives for optimal horizontal alignment.
            - 0: Critical alignment objectives missing
            - 15: Some alignment objectives present
            - 30: All essential alignment objectives included

            3. COLLABORATION POTENTIAL (30%): Assess how well the goals facilitate collaborative execution.
            - 0: Goals create siloed work patterns
            - 15: Goals permit basic collaboration
            - 30: Goals actively enable optimal collaboration

            OUTPUT FORMAT:
            Return ONLY a single integer between 0-100 representing the total horizontal alignment score without additional text, explanations, or formatting.

            EXAMPLE RESPONSE:
            78
            """
        )

        return query_llm(prompt_template, {
            "employee_id": employee_id,
            "employee_goals": employee_goals,
            "list_horizontal_peers": list_horizontal_peers
        })

    except oracledb.Error as error:
        print("Error checking horizontal alignment:")
        print(error)
        return "Error checking horizontal alignment."

def generate_final_recommendations(connection, employee_id):
    """Creates a final summary of recommendations."""
    try:
        cursor = connection.cursor()

        # Get the manager ID
        cursor.execute(
            """
            SELECT manager_id
            FROM Employees
            WHERE employee_id = :1
            """,
            (employee_id,)
        )
        result = cursor.fetchone()
        if not result:
            return f"No manager found for employee ID {employee_id}."

        manager_id = result[0]

        # Get alignment results (already LLM-formatted strings)
        vertical = check_vertical_alignment_upward(connection, manager_id, employee_id)
        horizontal_peers = get_horizontal_peers(connection, employee_id)

        # Ensure horizontal is a string (not a list)
        horizontal_summary = ", ".join(horizontal_peers) if horizontal_peers else "No peers found."

        prompt_template = PromptTemplate(
            input_variables=["vertical", "horizontal", "employee_id"],
            template="""
**Final Recommendations for Employee ID {employee_id}:**

- **Vertical Alignment:** {vertical}  
- **Horizontal Collaboration Opportunities:** {horizontal}  

Provide a structured, clear, and actionable summary.
            """
        )

        response = query_llm(prompt_template, {
            "vertical": vertical,
            "horizontal": horizontal_summary,
            "employee_id": employee_id
        })

        # Ensure final output is a clean string (no LOBs sneaking in)
        return str(response)

    except oracledb.Error as error:
        print("Error generating final recommendations:")
        print(error)
        return "Error generating final recommendations."
    
def update_employee_goal_objective(connection, employee_id, new_objective):
    try:
        cursor = connection.cursor()

        # Extract numeric suffix and get max number from goal_id like 'goal_001'
        cursor.execute("""
            SELECT COALESCE(MAX(TO_NUMBER(REGEXP_SUBSTR(goal_id, '\\d+$'))), 0) + 1
            FROM Goals
        """)
        next_number = cursor.fetchone()[0]

        # Format as goal_001, goal_002, etc.
        next_goal_id = f"goal_{next_number:03d}"

        goal_title = "Updated Learning Goal"

        cursor.execute(
            """
            INSERT INTO Goals (goal_id, employee_id, title, objective, metrics, timeline)
            VALUES (:1, :2, :3, :4, NULL, NULL)
            """,
            (
                next_goal_id,
                str(employee_id),
                goal_title,
                new_objective
            )
        )

        connection.commit()
        return f"Inserted new goal objective with ID {next_goal_id}."

    except oracledb.Error as error:
        print("Error inserting goal:")
        print(error)
        return f"Error inserting new goal: {error}"


def extract_goal_lines(text):
    """
    Extract meaningful refined goals from chatbot messages, bullet lists, or paragraphs.
    Splits multi-goal messages into atomic blocks.
    """
    lines = []

    # Split by double line breaks, OR bullet symbols, OR numbered points
    chunks = re.split(r'(?:(?:\n\s*\n)|(?:^\d+\.\s)|(?:^[-*•]))', text, flags=re.MULTILINE)

    for chunk in chunks:
        chunk = chunk.strip()
        if len(chunk) < 30:
            continue
        if any(kw in chunk.lower() for kw in [
            "next topic", "final recommendations", "let me know", "we’ve", "you could also"
        ]):
            continue
        if re.match(r'^\*\*.+\*\*:$', chunk):  # e.g., "**Refined Metrics:**"
            continue
        lines.append(chunk)

    return lines


def extract_structured_goal(raw_text):
    prompt = PromptTemplate(
        input_variables=["raw_text"],
        template="""
You are an assistant that extracts structured, database-ready goal records.
The input may contain markdown, bullet points, or informal formatting.

Extract the following fields from the input:
- goal_title
- objective (one actionable sentence)
- metrics (list of concrete KPIs)
- timeline (inferred if not stated, e.g., "Q2 2025")
- stakeholders (list of names or roles mentioned)

Respond ONLY in this JSON format:
{{
  "goal_title": "...",
  "objective": "...",
  "metrics": ["..."],
  "timeline": "...",
  "stakeholders": ["..."]
}}

INPUT:
{raw_text}
        """
    )
    
    response = query_llm(prompt, {"raw_text": raw_text})
    try:
        structured = json.loads(response)
# --- Sanitize ---
        def clean_text(t):
            return (
                t.replace('\\"', '"')
                 .replace("**", "")
                 .replace("”", '"')
                 .replace("“", '"')
                 .strip()
            )

        for key in ["goal_title", "objective", "timeline"]:
            if key in structured and isinstance(structured[key], str):
                structured[key] = clean_text(structured[key])

        if "metrics" in structured and isinstance(structured["metrics"], list):
            structured["metrics"] = [clean_text(m) for m in structured["metrics"]]

        if "stakeholders" in structured and isinstance(structured["stakeholders"], list):
            structured["stakeholders"] = [clean_text(s) for s in structured["stakeholders"]]

        return structured

    except json.JSONDecodeError:
        print("LLM returned non-JSON:\n", response)
        return None