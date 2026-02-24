"""
Update metadata adding ID

SQL to check (it must return zero rows)

SELECT ID,
       RAWTOHEX(ID)         AS ID_COLONNA,
       JSON_VALUE(METADATA, '$.ID') AS ID_METADATA
FROM BOOKS
WHERE RAWTOHEX(ID) != JSON_VALUE(METADATA, '$.ID');

"""

from db_utils import get_connection

SQL = """
UPDATE BOOKS
SET METADATA = JSON_TRANSFORM(
  METADATA,
  SET '$.ID' = RAWTOHEX(ID)
)
"""

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(SQL)
        print(f"Rows updated: {cur.rowcount}")
    conn.commit()
