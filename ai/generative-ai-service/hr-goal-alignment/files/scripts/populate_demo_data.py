# Copyright (c) 2025 Oracle and/or its affiliates.
import oracledb
import os
import sys
import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# --- Data Generation ---

# Helper function to format goal details into CLOB fields
def format_goal_details(goal_data):
    objective_str = goal_data.get('objective', '')
    metrics_str = goal_data.get('metrics', '')

    if 'key_actions' in goal_data:
        objective_str += "\n\nKey Actions:\n" + "\n".join([f"- {action}" for action in goal_data['key_actions']])
    if 'success_criteria' in goal_data:
        metrics_str += "\n\nSuccess Criteria:\n" + "\n".join([f"- {criteria}" for criteria in goal_data['success_criteria']])

    return objective_str.strip(), metrics_str.strip()

# Define Employees (11 total)
employees_data = [
    # Level 1
    {'employee_id': 'emp_001', 'name': 'Eleanor Vance', 'role': 'CEO', 'manager_id': None},
    # Level 2 - HR Head
    {'employee_id': 'emp_002', 'name': 'Ava Sharma', 'role': 'Head of Learning, Talent, Development, and Performance', 'manager_id': 'emp_001'},
    # Level 2 - Retail Head
    {'employee_id': 'emp_010', 'name': 'Ben Carter', 'role': 'Head of Retail Banking', 'manager_id': 'emp_001'},
    # Level 3 - HR Managers reporting to Ava (emp_002)
    {'employee_id': 'emp_003', 'name': 'Fatima Rossi', 'role': 'Line Manager', 'manager_id': 'emp_002'},
    {'employee_id': 'emp_004', 'name': 'George Martin', 'role': 'Head of Performance Management', 'manager_id': 'emp_002'},
    {'employee_id': 'emp_005', 'name': 'Isabelle Dubois', 'role': 'Head of Talent Management', 'manager_id': 'emp_002'},
    # Level 3 - Retail Manager reporting to Ben (emp_010)
    {'employee_id': 'emp_011', 'name': 'Olivia Green', 'role': 'Regional Branch Manager', 'manager_id': 'emp_010'},
    # Level 4 - HR Team reporting to Fatima (emp_003)
    {'employee_id': 'emp_006', 'name': 'David Lee', 'role': 'Head of Learning Content', 'manager_id': 'emp_003'},
    {'employee_id': 'emp_007', 'name': 'Maria Garcia', 'role': 'Head of Learning Coverage', 'manager_id': 'emp_003'},
    {'employee_id': 'emp_008', 'name': 'Kenji Tanaka', 'role': 'Head of Learning Admin', 'manager_id': 'emp_003'},
    # Level 4 - Retail Team reporting to Olivia (emp_011)
    {'employee_id': 'emp_012', 'name': 'Sam Wilson', 'role': 'Loan Officer', 'manager_id': 'emp_011'},
]

# Define Goals from JSON and generate others
goals_data = []
goal_counter = 1

# Process JSON data
json_data = {
    "Fatima": {
        "employee_id": "emp_003",
        "goals": [
            {
                "title": "Enhance Learning Programs",
                "objective": "enhance learning programs",
                "metrics": "better learning program effectiveness and completion",
                "timeline": "Q2 2025"
            }
        ]
    },
    "Head of Learning Content": {
        "employee_id": "emp_006",
        "goals": [
            {
                "title": "Improve Curriculum Development",
                "objective": "Develop high-quality, engaging, and relevant learning content for employees.",
                "key_actions": [
                    "Continue designing and updating curriculum based on employee needs and feedback.",
                    "Collaborate with internal subject matter experts (SMEs) to ensure content accuracy and relevancy."
                ],
                "success_criteria": [
                    "Complete 100% of the curriculum updates scheduled for the year.",
                    "Achieve a satisfaction rating of at least 85% for new content via feedback surveys."
                ],
                "timeline": "Q2 - Q4 2025"
            },
            {
                "title": "Measure Effectiveness of Learning Content",
                "objective": "Establish clear metrics and targets to measure the effectiveness of learning materials.",
                "key_actions": [
                    "Work with the Head of Learning Analytics (if applicable) to set clear KPIs for content effectiveness (e.g., post-training retention, completion rates).",
                    "Introduce mechanisms to collect feedback post-training, such as surveys or assessments.",
                    "Analyze feedback and revise content based on employee performance outcomes."
                ],
                "success_criteria": [
                    "Set and track KPIs such as a 90%+ completion rate for each course.",
                    "Post-training assessment scores to increase by 10% from baseline."
                ],
                "timeline": "Ongoing, with a review every quarter"
            },
            {
                "title": "Align Content with Company Needs",
                "objective": "Ensure that learning content is directly aligned with organizational goals and employee roles.",
                "key_actions": [
                    "Collaborate with leadership and department heads to identify key learning needs aligned with strategic goals.",
                    "Review and revise content quarterly to ensure alignment."
                ],
                "success_criteria": [
                    "100% of learning content is updated to align with business objectives by end of the year."
                ],
                "timeline": "Ongoing with quarterly check-ins"
            }
        ]
    },
    "Head of Learning Coverage": {
        "employee_id": "emp_007",
        "goals": [
            {
                "title": "Expand Learning Coverage Across Geographies",
                "objective": "Ensure that learning programs are accessible across all regions and geographies.",
                "metrics": "100% regional coverage, 80% completion rate",
                "timeline": "Q1 - Q3 2025"
            },
            {
                "title": "Set Completion Targets",
                "objective": "Establish measurable completion targets for learning programs across all regions.",
                "metrics": "90% completion rate for all employees in each geography",
                "timeline": "Q4 2025"
            },
            {
                "title": "Improve Regional Feedback Mechanism",
                "objective": "Collect region-specific feedback to ensure the learning content is relevant and engaging.",
                "metrics": "80% feedback collected, 85% satisfaction rate",
                "timeline": "Ongoing, review at the end of each quarter"
            }
        ]
    },
    "Head of Learning Admin": {
        "employee_id": "emp_008",
        "goals": [
            {
                "title": "Streamline Learning Administration",
                "objective": "Improve the efficiency and organization of learning administration processes.",
                "metrics": "25% reduction in manual tasks, 100% LMS tracking",
                "timeline": "Q2 - Q3 2025"
            },
            {
                "title": "Improve Learning Program Completion Tracking",
                "objective": "Ensure learning programs are completed on time and participation rates are tracked.",
                "metrics": "90% completion rate, 95% on-time completion for mandatory programs",
                "timeline": "Ongoing, with quarterly reviews"
            },
            {
                "title": "Link Administrative Metrics to Effectiveness",
                "objective": "Align operational metrics with the effectiveness of learning programs.",
                "metrics": "100% tracking of post-training performance, 80% retention rate",
                "timeline": "Ongoing, review in Q4 2025"
            }
        ]
    },
    "Head of Performance Management": {
        "employee_id": "emp_004",
        "goals": [
            {
                "title": "Integrate Learning Outcomes into Performance Reviews",
                "objective": "Ensure that learning achievements are considered during employee performance reviews.",
                "metrics": "100% performance reviews include learning outcomes, 90% alignment",
                "timeline": "By the end of Q2 2025"
            },
            {
                "title": "Measure Impact of Learning on Performance",
                "objective": "Track the relationship between learning outcomes and performance improvements.",
                "metrics": "80% of managers report performance improvements, 10% increase in performance reviews",
                "timeline": "Ongoing, with bi-annual reviews"
            },
            {
                "title": "Align Learning and Performance Strategies",
                "objective": "Ensure performance management systems and learning outcomes are working in tandem.",
                "metrics": "Full alignment between performance review metrics and learning goals",
                "timeline": "Ongoing, with review in Q3 2025"
            }
        ]
    },
    "Head of Talent Management": {
        "employee_id": "emp_005",
        "goals": [
            {
                "title": "Use Learning Data for Succession Planning",
                "objective": "Leverage learning and development data to identify high-potential employees.",
                "metrics": "Identify 5 high-potential employees, 75% linked to development programs",
                "timeline": "Q1 - Q3 2025"
            },
            {
                "title": "Align Learning Programs with Talent Development Needs",
                "objective": "Ensure learning and development programs are aligned with leadership and talent needs.",
                "metrics": "100% alignment between learning and talent development goals",
                "timeline": "Ongoing, with quarterly reviews"
            },
            {
                "title": "Increase the Use of Learning Data for Talent Reviews",
                "objective": "Improve the use of learning data in talent reviews.",
                "metrics": "90% of talent reviews include learning data, 85% leadership satisfaction",
                "timeline": "Ongoing, with bi-annual reviews"
            }
        ]
    },
    "Head of Learning, Talent, Development, and Performance": {
            "employee_id": "emp_002",
            "goals": [
                {
                    "title": "Improve Employee Capability Scores by 18%",
                    "objective": "Enhance employee skills and competencies across the organization",
                    "metrics": "18% improvement in employee capability scores, 85% training completion rate",
                    "timeline": "End of Q4 2025"
                },
                {
                    "title": "Enhance Learning and Development Programs",
                    "objective": "Improve effectiveness and reach of learning programs across departments",
                    "metrics": "75% employee participation, 85% training satisfaction rate, 10% increase in internal promotions",
                    "timeline": "Ongoing, with review at the end of Q2 2025"
                },
                {
                    "title": "Align Learning and Development with Business Goals",
                    "objective": "Ensure L&D initiatives align with strategic business goals",
                    "metrics": "100% alignment with business objectives, measurable impact on retention, productivity, and engagement",
                    "timeline": "Ongoing, with quarterly reviews"
                }
            ]
        }
}

for name, data in json_data.items():
    emp_id = data['employee_id']
    for goal in data['goals']:
        obj, met = format_goal_details(goal)
        goals_data.append({
            'goal_id': f'goal_{goal_counter:03d}',
            'employee_id': emp_id,
            'title': goal['title'],
            'objective': obj,
            'metrics': met,
            'timeline': goal['timeline']
        })
        goal_counter += 1

# Generate goals for remaining employees
remaining_employees = ['emp_001', 'emp_010', 'emp_011', 'emp_012']
generic_goals = {
    'emp_001': [{'title': 'Drive Overall Company Growth', 'objective': 'Achieve 15% YoY revenue growth.', 'metrics': 'Revenue figures, market share.', 'timeline': 'End of 2025'}],
    'emp_010': [{'title': 'Expand Retail Banking Market Share', 'objective': 'Increase market share by 5% in target regions.', 'metrics': 'Market share reports, customer acquisition rate.', 'timeline': 'End of 2025'}],
    'emp_011': [{'title': 'Improve Branch Performance', 'objective': 'Increase regional branch profitability by 10%.', 'metrics': 'Branch P&L statements, customer satisfaction scores.', 'timeline': 'End of Q3 2025'}],
    'emp_012': [{'title': 'Increase Loan Origination Volume', 'objective': 'Originate $5M in new loans.', 'metrics': 'Total loan value originated, approval rate.', 'timeline': 'End of Q2 2025'}],
}

for emp_id in remaining_employees:
    for goal in generic_goals[emp_id]:
         goals_data.append({
            'goal_id': f'goal_{goal_counter:03d}',
            'employee_id': emp_id,
            'title': goal['title'],
            'objective': goal['objective'],
            'metrics': goal['metrics'],
            'timeline': goal['timeline']
        })
         goal_counter += 1


# Define Self Assessments (Generate for all)
self_assessments_data = []
assessment_counter = 1
for emp in employees_data:
    self_assessments_data.append({
        'assessment_id': f'assess_{assessment_counter:03d}',
        'employee_id': emp['employee_id'],
        'key_achievements': f"Successfully completed project X related to {emp['role']}.",
        'skill_development': f"Attended workshop on Advanced {emp['role']} Techniques.",
        'strengths': f"Strong analytical skills, effective communication within the {emp['role']} domain.",
        'areas_for_improvement': f"Need to improve delegation skills for {emp['role']} tasks.",
        'alignment_with_career_goals': f"Current role provides good experience towards long-term goal of becoming Senior {emp['role']}."
    })
    assessment_counter += 1

# Define Manager Briefings (Generate for all except CEO)
manager_briefings_data = []
briefing_counter = 1
employee_map = {emp['employee_id']: emp for emp in employees_data}

for emp in employees_data:
    if emp['manager_id']: # Only generate for employees with managers
        manager_name = employee_map.get(emp['manager_id'], {}).get('name', 'Their Manager')
        manager_briefings_data.append({
            'briefing_id': f'brief_{briefing_counter:03d}',
            'employee_id': emp['employee_id'],
            'quantitative_performance': f"Met 95% of KPIs for the last quarter in their role as {emp['role']}.",
            'perception_gap': f"{emp['name']} rated their teamwork skills slightly lower than peer feedback indicated.",
            'manager_context': f"Upcoming 1:1 discussion with {manager_name} to review Q1 goals.",
            'tenure': f"{datetime.date.today().year - 2022}-year tenure; focus on skill progression.", # Example tenure
            'cross_departmental_contributions': f"Collaborated with Marketing on the recent product launch.",
            'career_alignment_prompt': f"Discuss how current {emp['role']} objectives align with {emp['name']}'s stated long-term career aspirations."
        })
        briefing_counter += 1


# --- Database Insertion ---

connection = None
cursor = None

try:
    print("Connecting to the database...")
    connection = oracledb.connect(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        dsn=config.DB_DSN
    )
    print("Connection successful.")
    cursor = connection.cursor()

    # Insert Employees
    print("Inserting Employees...")
    emp_sql = "INSERT INTO Employees (employee_id, name, role, manager_id) VALUES (:1, :2, :3, :4)"
    cursor.executemany(emp_sql, [
        (e['employee_id'], e['name'], e['role'], e['manager_id']) for e in employees_data
    ])
    print(f"{cursor.rowcount} Employees inserted.")

    # Insert Goals
    print("Inserting Goals...")
    goal_sql = "INSERT INTO Goals (goal_id, employee_id, title, objective, metrics, timeline) VALUES (:1, :2, :3, :4, :5, :6)"
    # Prepare data, ensuring CLOBs are handled correctly
    goal_tuples = []
    for g in goals_data:
        objective_clob = cursor.var(oracledb.DB_TYPE_CLOB)
        objective_clob.setvalue(0, g['objective'])
        metrics_clob = cursor.var(oracledb.DB_TYPE_CLOB)
        metrics_clob.setvalue(0, g['metrics'])
        goal_tuples.append((
            g['goal_id'], g['employee_id'], g['title'],
            objective_clob, metrics_clob, g['timeline']
        ))
    # Using individual execute calls for robustness with CLOBs
    inserted_goals = 0
    for data_tuple in goal_tuples:
        try:
            cursor.execute(goal_sql, data_tuple)
            inserted_goals += 1
        except oracledb.Error as insert_error:
            print(f"Error inserting goal {data_tuple[0]} for employee {data_tuple[1]}: {insert_error}")
            # Decide whether to continue or break/rollback
            # For now, we'll print and continue
    print(f"{inserted_goals} Goals processed.")


    # Insert Self Assessments
    print("Inserting Self Assessments...")
    sa_sql = """
        INSERT INTO Self_Assessments (
            assessment_id, employee_id, key_achievements, skill_development,
            strengths, areas_for_improvement, alignment_with_career_goals
        ) VALUES (:1, :2, :3, :4, :5, :6, :7)
    """
    # Prepare data for CLOBs
    sa_tuples = []
    for sa in self_assessments_data:
        clob_vars = {k: cursor.var(oracledb.DB_TYPE_CLOB) for k in sa if k not in ['assessment_id', 'employee_id']}
        for k, v in clob_vars.items():
            v.setvalue(0, sa[k])
        sa_tuples.append((
            sa['assessment_id'], sa['employee_id'],
            clob_vars['key_achievements'], clob_vars['skill_development'],
            clob_vars['strengths'], clob_vars['areas_for_improvement'],
            clob_vars['alignment_with_career_goals']
        ))
    # Using individual execute calls
    inserted_assessments = 0
    for data_tuple in sa_tuples:
        try:
            cursor.execute(sa_sql, data_tuple)
            inserted_assessments += 1
        except oracledb.Error as insert_error:
            print(f"Error inserting assessment {data_tuple[0]} for employee {data_tuple[1]}: {insert_error}")
    print(f"{inserted_assessments} Self Assessments processed.")


    # Insert Manager Briefings
    print("Inserting Manager Briefings...")
    mb_sql = """
        INSERT INTO Manager_Briefings (
            briefing_id, employee_id, quantitative_performance, perception_gap,
            manager_context, tenure, cross_departmental_contributions, career_alignment_prompt
        ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
    """
     # Prepare data for CLOBs
    mb_tuples = []
    for mb in manager_briefings_data:
        clob_vars = {k: cursor.var(oracledb.DB_TYPE_CLOB) for k in mb if k not in ['briefing_id', 'employee_id']}
        for k, v in clob_vars.items():
            v.setvalue(0, mb[k])
        mb_tuples.append((
            mb['briefing_id'], mb['employee_id'],
            clob_vars['quantitative_performance'], clob_vars['perception_gap'],
            clob_vars['manager_context'], clob_vars['tenure'],
            clob_vars['cross_departmental_contributions'], clob_vars['career_alignment_prompt']
        ))
    # Using individual execute calls
    inserted_briefings = 0
    for data_tuple in mb_tuples:
        try:
            cursor.execute(mb_sql, data_tuple)
            inserted_briefings += 1
        except oracledb.Error as insert_error:
            print(f"Error inserting briefing {data_tuple[0]} for employee {data_tuple[1]}: {insert_error}")
    print(f"{inserted_briefings} Manager Briefings processed.")


    # Commit the changes
    connection.commit()
    print("Data committed successfully!")

except oracledb.Error as error:
    print("Error during database operation:")
    print(error)
    if connection:
        connection.rollback()
        print("Transaction rolled back.")

except ImportError:
    print("Error: Could not import the 'oracledb' library.")
    print("Please ensure it is installed ('pip install oracledb') and accessible.")
    print("Also ensure your 'config.py' file exists in the same directory and has the correct credentials (ORACLE_USERNAME, ORACLE_PASSWORD, ORACLE_DSN).")

# Removed incorrect 'except config.Error' block
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    if connection:
        connection.rollback()
        print("Transaction rolled back due to unexpected error.")

finally:
    # Close the cursor and connection
    if cursor:
        cursor.close()
        print("Cursor closed.")
    if connection:
        connection.close()
        print("Connection closed.")
