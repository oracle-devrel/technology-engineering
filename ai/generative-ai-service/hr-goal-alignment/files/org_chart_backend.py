import oracledb
import pandas as pd

import config
from gen_ai_service.inference import classify_smart_goal
from goal_alignment_backend import check_if_horizontal_aligned, check_if_vertical_aligned

try: 
    connection = oracledb.connect(
            **config.CONNECT_ARGS_VECTOR
        )
except oracledb.Error as err:
    print(f"Oracle connection error: {err}")
    connection = None

    
def mapping_all_employees() -> tuple[dict[str, list[str]], pd.DataFrame]:
    query = "SELECT employee_id, name, role, manager_id FROM Employees"
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        # Clean LOBs (just in case any column is a LOB)
        clean_rows = [
            [col.read() if isinstance(col, oracledb.LOB) else col for col in row]
            for row in rows
        ]

        df_db = pd.DataFrame(clean_rows, columns=[desc[0] for desc in cursor.description])
        return mapping_from_df(df_db), df_db

    except Exception as err:
        print(f"Query failed: {err}")
        connection.close()
        return {}, pd.DataFrame()


def build_label(df_row: pd.Series) -> str:
    """Helper – build multiline label *Name (Title)* for a row."""
    return (
        f"{df_row['NAME'].strip()}\n("
        f"{df_row['ROLE'].strip()})"
    )


def mapping_from_df(df: pd.DataFrame) -> dict[str, list[str]]:
    """Convert DataFrame into {manager_label: [direct_report_labels]} mapping."""
    df = df.copy()
    df["label"] = df.apply(build_label, axis=1)
    id_to_label: dict[int, str] = dict(zip(df["EMPLOYEE_ID"], df["label"]))
    mapping: dict[str, list[str]] = {}
    for _, row in df.iterrows():
        mgr_id = row.get("MANAGER_ID")
        if pd.notna(mgr_id):
            parent = id_to_label.get(mgr_id)
            child = id_to_label.get(row["EMPLOYEE_ID"])
            if parent and child:
                mapping.setdefault(parent, []).append(child)
    return mapping

def check_smart_goal(df_row: pd.Series) -> str:
    print(df_row.to_dict())
    goal_smart = classify_smart_goal(df_row.to_dict())
    return goal_smart.get("classification", "N/A")


def fetch_goals_from_emp(df, emp_data) -> pd.DataFrame:
    try:
        emp_id = search_employee(df, emp_data)
        query = f"SELECT title, objective, metrics, timeline FROM Goals WHERE employee_id = :1"
        cursor = connection.cursor()
        cursor.execute(query, (emp_id,))
        rows = cursor.fetchall()

        # Clean LOBs
        clean_rows = [
            [col.read() if isinstance(col, oracledb.LOB) else col for col in row]
            for row in rows
        ]

        df_db = pd.DataFrame(clean_rows, columns=[desc[0] for desc in cursor.description])

        # Check SMART criteria
        df_db["smart"] = df_db.apply(check_smart_goal, axis=1)

        return df_db

    except oracledb.Error as err:
        print(f"Oracle connection error: {err}")
        return pd.DataFrame()


def search_employee(df, param):
    parts = param.split('\n')
    
    if len(parts) < 2:
        return None  # Invalid input format
    
    full_name = parts[0]
    job_title = parts[1].replace('(', '').replace(')', '')  # Remove parentheses from job title

    filtered_df = df[(df['NAME'] == full_name) & 
                     (df['ROLE'] == job_title)]
    
    if not filtered_df.empty:
        return filtered_df['EMPLOYEE_ID'].iloc[0]
    else:
        return None
    

def check_goal_alignment(df, emp_data, manager_data):
    vertical = None
    print(manager_data)
    emp_id = search_employee(df, emp_data)
    if manager_data:
        manager_id = search_employee(df, manager_data)
        vertical = check_if_vertical_aligned(connection, manager_id, emp_id)
    horizontal = check_if_horizontal_aligned(connection, emp_id)
    if isinstance(horizontal, str) and horizontal.isdigit():
        horizontal = int(horizontal)
    else:
        horizontal = None
    if isinstance(vertical, str) and vertical.isdigit():
        vertical = int(vertical)
    else:
        vertical = None

    return vertical, horizontal