"""
Test Select AI on SH schema
"""

import select_ai
from config_private import CONNECT_ARGS

PROFILE_NAME = "OCI_GENERATIVE_AI_PROFILE"
NL_REQUEST = "List top 10 customers by sales in Europe"

# generate
select_ai.connect(**CONNECT_ARGS)
print("Connected to DB...")
print("")

print(f"Using profile: {PROFILE_NAME}")
profile = select_ai.Profile(profile_name=PROFILE_NAME)

sql = profile.show_sql(prompt=NL_REQUEST)
print("Generated SQL:")
print(sql)
print()
