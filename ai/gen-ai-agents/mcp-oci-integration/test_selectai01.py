"""
Test Select AI on SH schema
"""

from db_utils import run_select_ai

PROFILE_NAME = "OCI_GENERATIVE_AI_PROFILE"
NL_REQUEST = "List top 10 customers by sales in Europe"

# Option A: one-shot (generate → execute)
cols, rows, sql_text = run_select_ai(NL_REQUEST, PROFILE_NAME)

print("=== Generated SQL ===")
print(sql_text)

print("----------------------")
print("Result columns:", cols)
for r in rows:
    print(r)
