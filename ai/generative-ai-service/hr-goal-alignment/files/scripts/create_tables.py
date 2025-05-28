# Copyright (c) 2025 Oracle and/or its affiliates.
import oracledb
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

connection = None
cursor = None
try:
    # Create a connection to the database
    connection = oracledb.connect(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        dsn=config.DB_DSN
    )

    # Create a cursor object
    cursor = connection.cursor()

    # SQL scripts to create the tables
    create_table_scripts = [
        """
        CREATE TABLE Employees (
            employee_id VARCHAR2(255) PRIMARY KEY,
            name VARCHAR2(255),
            role VARCHAR2(255),
            manager_id VARCHAR2(255),
            FOREIGN KEY (manager_id) REFERENCES Employees(employee_id)
        )
        """,
        """
        CREATE TABLE Goals (
            goal_id VARCHAR2(255) PRIMARY KEY,
            employee_id VARCHAR2(255),
            title VARCHAR2(255),
            objective CLOB,
            metrics CLOB,
            timeline VARCHAR2(255),
            FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
        )
        """,
        """
        CREATE TABLE Self_Assessments (
            assessment_id VARCHAR2(255) PRIMARY KEY,
            employee_id VARCHAR2(255),
            key_achievements CLOB,
            skill_development CLOB,
            strengths CLOB,
            areas_for_improvement CLOB,
            alignment_with_career_goals CLOB,
            FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
        )
        """,
        """
        CREATE TABLE Manager_Briefings (
            briefing_id VARCHAR2(255) PRIMARY KEY,
            employee_id VARCHAR2(255),
            quantitative_performance CLOB,
            perception_gap CLOB,
            manager_context CLOB,
            tenure CLOB,
            cross_departmental_contributions CLOB,
            career_alignment_prompt CLOB,
            FOREIGN KEY (employee_id) REFERENCES Employees(employee_id)
        )
        """
    ]

    # Execute the SQL scripts
    for script in create_table_scripts:
        cursor.execute(script)

    # Commit the changes
    connection.commit()

    print("Tables created successfully!")

except oracledb.Error as error:
    print("Error creating tables:")
    print(error)

finally:
    # Close the cursor and connection
    if cursor:
        cursor.close()
    if connection:
        connection.close()
    print("Connection closed")
